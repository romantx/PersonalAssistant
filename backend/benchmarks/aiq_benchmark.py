import os
import re
import json
import time
import subprocess
import yaml
import traceback
from pathlib import Path
from dotenv import load_dotenv

import google.generativeai as genai
from anthropic import Anthropic

# Load environment variables
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Domains
DOMAINS = {
    "wishlist": {
        "p1_prompt": """You are a senior system architect. Design a RESTful API for a Product Wishlist microservice.
Requirements:
- Users can create a wishlist
- Users can add and remove products from a wishlist
- Users can view their own wishlist only
- Products are identified by UUID
Deliverables:
1. OpenAPI 3.0 specification in YAML
2. JSON Schema for Wishlist and ProductItem resources
3. docker-compose.yml for the service and PostgreSQL database

Return the response clearly demarcating the files (e.g. using ```yaml or ```json blocks).""",
        "baseline_openapi": """openapi: 3.0.0
info:
  title: Wishlist API
  version: 1.0.0
paths:
  /wishlist:
    post:
      summary: Create a wishlist
      security:
        - BearerAuth: []
      responses:
        '201':
          description: Created
    get:
      summary: View own wishlist
      security:
        - BearerAuth: []
      responses:
        '200':
          description: OK
  /wishlist/{wishlist_id}/items:
    post:
      summary: Add product
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Added
  /wishlist/{wishlist_id}/items/{product_id}:
    delete:
      summary: Remove product
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Removed
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
"""
    },
    "auth_service": {
        "p1_prompt": """Design and implement a RESTful authentication service with JWT tokens, rate limiting (max 5 login attempts per minute per IP), and a PostgreSQL users table. Deliverables: OpenAPI 3.0 spec, JSON schemas, docker-compose.yml, and full implementation.
Return the response clearly demarcating the files (e.g. using ```yaml or ```json blocks).""",
        "baseline_openapi": """openapi: 3.0.0
info:
  title: Auth API
  version: 1.0.0
paths:
  /login:
    post:
      summary: Login user
      responses:
        '200':
          description: OK
  /register:
    post:
      summary: Register user
      responses:
        '201':
          description: Created
"""
    },
    "file_pipeline": {
        "p1_prompt": """Design and implement a service that accepts file uploads, queues them for async processing, extracts metadata, and stores results in PostgreSQL with a status endpoint. Deliverables: OpenAPI 3.0 spec, JSON schemas, docker-compose.yml, and full implementation.
Return the response clearly demarcating the files (e.g. using ```yaml or ```json blocks).""",
        "baseline_openapi": """openapi: 3.0.0
info:
  title: File Pipeline API
  version: 1.0.0
paths:
  /upload:
    post:
      summary: Upload file
      responses:
        '202':
          description: Accepted
  /status/{job_id}:
    get:
      summary: View status
      responses:
        '200':
          description: OK
"""
    }
}

gemini_key = os.environ.get("GEMINI_API_KEY", "")
anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

genai.configure(api_key=gemini_key)
anthropic_client = Anthropic(api_key=anthropic_key)

MODEL_CLAUDE = "claude-sonnet-4-20250514"
MODEL_GEMINI = "gemini-2.5-pro"

def call_gemini(prompt):
    try:
        model = genai.GenerativeModel(MODEL_GEMINI)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return f"API ERROR: {e}"

def call_claude(prompt):
    try:
        msg = anthropic_client.messages.create(
            model=MODEL_CLAUDE,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        print(f"Error calling Claude: {e}")
        return f"API ERROR: {e}"

def extract_code_blocks(text):
    blocks = re.findall(r"```([a-zA-Z0-9]+)?\n(.*?)\n```", text, re.DOTALL)
    if not blocks:
        return [("txt", text)]
    return blocks

def score_phase1(response_text, output_dir, model_name):
    blocks = extract_code_blocks(response_text)
    score = {
        "openapi_spec_quality": 0,
        "data_schema_quality": 0,
        "configuration_quality": 0,
        "total_phase1": 0
    }
    
    (output_dir / f"{model_name}_raw.txt").write_text(response_text, encoding="utf8")
    if "API ERROR" in response_text:
        return score
    
    has_bearer = False
    has_endpoints = 0
    schemas_valid = False
    wishlist_refs_items = False
    docker_has_services = False
    docker_ports = False
    docker_env = False
    
    for ext, content in blocks:
        lc_content = content.lower()
        if "openapi" in lc_content or "paths:" in lc_content:
            score["openapi_spec_quality"] += 10 # Baseline for YAML parsing
            if "bearerauth" in lc_content or "bearer" in lc_content:
                has_bearer = True
            if "post" in lc_content and "get" in lc_content:
                has_endpoints = 15
                
        elif "schema" in lc_content or "$schema" in lc_content or ("type" in lc_content and "properties" in lc_content):
            schemas_valid = True
            if "items" in lc_content or "productitem" in lc_content:
                wishlist_refs_items = True
                
        elif "services:" in lc_content and ("build:" in lc_content or "image:" in lc_content):
            docker_has_services = True
            if "ports:" in lc_content: docker_ports = True
            if "environment:" in lc_content or "env_file:" in lc_content: docker_env = True
            
    if has_bearer: score["openapi_spec_quality"] += 15
    score["openapi_spec_quality"] += has_endpoints
    
    if schemas_valid: score["data_schema_quality"] += 15
    if wishlist_refs_items: score["data_schema_quality"] += 15
    
    if docker_has_services: score["configuration_quality"] += 10
    if docker_ports: score["configuration_quality"] += 10
    if docker_env: score["configuration_quality"] += 10
    
    score["total_phase1"] = score["openapi_spec_quality"] + score["data_schema_quality"] + score["configuration_quality"]
    return score

def score_phase2(response_text, output_dir, model_name):
    blocks = extract_code_blocks(response_text)
    model_dir = output_dir / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the files
    py_files = []
    has_files = False
    for i, (ext, content) in enumerate(blocks):
        if not ext: ext = "txt"
        ext_lower = ext.lower()
        if ext_lower in ['python', 'py']:
            if "test" in content.lower():
                file_name = f"test_{i}.py"
            else:
                file_name = f"main_{i}.py"
            has_files = True
        else:
            file_name = f"file_{i}.{ext_lower}"
            
        file_path = model_dir / file_name
        file_path.write_text(content, encoding="utf8")
        if file_name.endswith('.py'):
            py_files.append(file_path)

    # Always generate at least one .py file if nothing else, so tools run and return 0
    if not has_files and not py_files:
        empty_py = model_dir / "dummy.py"
        empty_py.write_text("# API error or no Python code generated\n" + response_text, encoding="utf8")
        py_files.append(empty_py)

    score = {
        "functional_correctness": 0,
        "security": 0,
        "code_quality": 0,
        "total_phase2": 0,
        "tool_execution_log": {}
    }
    
    if "API ERROR" in response_text:
        score["tool_execution_log"]["API"] = "Failed API call."
        return score
    
    env_path = os.environ.get('VIRTUAL_ENV', '')
    pytest_bin = os.path.join(env_path, 'Scripts', 'pytest') if env_path else "pytest"
    bandit_bin = os.path.join(env_path, 'Scripts', 'bandit') if env_path else "bandit"
    pylint_bin = os.path.join(env_path, 'Scripts', 'pylint') if env_path else "pylint"

    # Pytest
    try:
        res = subprocess.run([pytest_bin, str(model_dir)], capture_output=True, text=True)
        score["tool_execution_log"]["pytest"] = res.stdout + res.stderr
        if "passed" in res.stdout:
            score["functional_correctness"] += 50
        elif "failed" in res.stdout:
            score["functional_correctness"] += 25
        else:
            score["functional_correctness"] += 20  # Code couldn't run tests
    except Exception as e:
        score["functional_correctness"] += 0
        score["tool_execution_log"]["pytest"] = f"CRASH: {traceback.format_exc()}"

    # Bandit
    bandit_log = []
    bandit_val = 25
    for file_path in py_files:
        try:
            res = subprocess.run([bandit_bin, "-r", str(file_path), "-f", "json"], capture_output=True, text=True)
            bandit_log.append(f"--- RUNNING BANDIT ON {file_path.name} ---")
            bandit_log.append(res.stdout + res.stderr)
            if res.stdout:
                try:
                    bjson = json.loads(res.stdout)
                    metrics = bjson.get("metrics", {}).get("_totals", {})
                    bandit_val -= (metrics.get("SEVERITY.MEDIUM", 0.0) * 5)
                    bandit_val -= (metrics.get("SEVERITY.HIGH", 0.0) * 10)
                except:
                    pass
        except Exception as e:
            bandit_log.append(f"CRASH: {e}")
    
    score["security"] = int(max(0, bandit_val))
    score["tool_execution_log"]["bandit"] = "\\n".join(bandit_log)

    # Pylint
    pylint_log = []
    has_8_score_or_higher = False
    for file_path in py_files:
        try:
            res = subprocess.run([pylint_bin, str(file_path), "--score=yes"], capture_output=True, text=True)
            pylint_log.append(f"--- RUNNING PYLINT ON {file_path.name} ---")
            pylint_log.append(res.stdout + res.stderr)
            if "Your code has been rated at" in res.stdout:
                m = re.search(r"rated at ([-]?\d+\.\d+)/10", res.stdout)
                if m and float(m.group(1)) >= 8.0:
                    has_8_score_or_higher = True
        except Exception as e:
            pylint_log.append(f"CRASH: {e}")

    if has_8_score_or_higher:
        score["code_quality"] = 25
    else:
        score["code_quality"] = 15

    score["tool_execution_log"]["pylint"] = "\\n".join(pylint_log)
    score["total_phase2"] = score["functional_correctness"] + score["security"] + score["code_quality"]
    
    return score

def run_single_domain(domain_id, config, results_dir, date_str):
    print(f"\\n=== RUNNING DOMAIN: {domain_id} ===")
    domain_res_dir = results_dir / f"domain_{domain_id}"
    phase1_dir = domain_res_dir / "phase1"
    phase2_dir = domain_res_dir / "phase2"
    phase1_dir.mkdir(parents=True, exist_ok=True)
    phase2_dir.mkdir(parents=True, exist_ok=True)
    
    p2_prompt = f"Implement the service defined in the provided OpenAPI spec.\\nWrite functional code, unit tests, and all necessary configuration files.\\nOpenAPI:\\n{config['baseline_openapi']}"
    
    print(" [1.1] Claude Phase 1...")
    c_p1_res = call_claude(config['p1_prompt'])
    c_p1_score = score_phase1(c_p1_res, phase1_dir, "claude")
    
    print(" [1.2] Gemini Phase 1...")
    g_p1_res = call_gemini(config['p1_prompt'])
    g_p1_score = score_phase1(g_p1_res, phase1_dir, "gemini")
    
    print(" [2.1] Claude Phase 2...")
    c_p2_res = call_claude(p2_prompt)
    c_p2_score = score_phase2(c_p2_res, phase2_dir, "claude")
    
    print(" [2.2] Gemini Phase 2...")
    g_p2_res = call_gemini(p2_prompt)
    g_p2_score = score_phase2(g_p2_res, phase2_dir, "gemini")

    decision = "Reject role swap. Current assignments stand."
    if c_p1_score["total_phase1"] > g_p1_score["total_phase1"] and c_p2_score["total_phase2"] > g_p2_score["total_phase2"]:
        decision = "Approve role swap. Update PAP-PLAN-001 role assignments accordingly."
    elif abs(c_p1_score["total_phase1"] - g_p1_score["total_phase1"]) <= 10 or abs(c_p2_score["total_phase2"] - g_p2_score["total_phase2"]) <= 10:
        decision = "Ambiguous. Run benchmark twice more with different problem domains, average results."

    # Return result dict
    result = {
        "date": date_str,
        "run_conditions": {
            "docker_execution": "Skipped per user mandate.",
            "spectral_validation": "Skipped or fallback.",
            "phase2_openapi": "Baseline injected."
        },
        "model_versions_tested": {
            "claude": MODEL_CLAUDE,
            "gemini": MODEL_GEMINI
        },
        "scores": {
            "claude": {"phase1_score": c_p1_score, "phase2_score": c_p2_score},
            "gemini": {"phase1_score": g_p1_score, "phase2_score": g_p2_score}
        },
        "decision_outcome": decision,
        "role_assignments_changed": "Approve" in decision
    }
    
    target_json = "ROLE-BENCH-001-v2.json" if domain_id == "wishlist" else f"ROLE-BENCH-001-{domain_id}.json"
    p = results_dir / target_json
    p.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(f" Saved to {p}")
    return result

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_dir = base_dir / "benchmark_results"
    results_dir.mkdir(exist_ok=True)
    date_str = time.strftime("%Y%m%d-%H%M%S")
    
    # Run all domains
    domain_results = {}
    for domain_id, config in DOMAINS.items():
        domain_results[domain_id] = run_single_domain(domain_id, config, results_dir, date_str)
        
    # Calculate Averages
    c_p1_avg = sum([r["scores"]["claude"]["phase1_score"]["total_phase1"] for r in domain_results.values()]) / 3.0
    c_p2_avg = sum([r["scores"]["claude"]["phase2_score"]["total_phase2"] for r in domain_results.values()]) / 3.0
    g_p1_avg = sum([r["scores"]["gemini"]["phase1_score"]["total_phase1"] for r in domain_results.values()]) / 3.0
    g_p2_avg = sum([r["scores"]["gemini"]["phase2_score"]["total_phase2"] for r in domain_results.values()]) / 3.0
    
    decision = "Reject role swap. Current assignments stand."
    if c_p1_avg > g_p1_avg and c_p2_avg > g_p2_avg:
        decision = "Approve role swap. Update PAP-PLAN-001 role assignments accordingly."
    elif abs(c_p1_avg - g_p1_avg) <= 10 or abs(c_p2_avg - g_p2_avg) <= 10:
        decision = "Ambiguous. Data inconclusive even after 3 domains."
        
    final_output = {
      "model_versions_tested": {
        "claude": MODEL_CLAUDE,
        "gemini": MODEL_GEMINI
      },
      "domain_results": domain_results,
      "averaged_scores": {
        "claude": {
          "phase1_avg": c_p1_avg,
          "phase2_avg": c_p2_avg
        },
        "gemini": {
          "phase1_avg": g_p1_avg,
          "phase2_avg": g_p2_avg
        }
      },
      "decision_outcome": decision,
      "role_assignments_changed": "Approve" in decision
    }
    
    final_path = results_dir / "ROLE-BENCH-001-FINAL.json"
    final_path.write_text(json.dumps(final_output, indent=2), encoding="utf8")
    print(f"\\nALL DOMAINS COMPLETE. Saved to {final_path}")

if __name__ == "__main__":
    main()
