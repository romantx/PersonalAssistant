"""
PAP-ADD-001 — LLM Council (Option D: Real Multi-Provider)
=========================================================
Standalone council tool that queries Real Claude, Real Gemini, and Real Grok
in parallel, anonymizes responses, and synthesizes via a Gemini chairman.

Usage:
  CLI:  python council_test.py "Should I use SQLite or Postgres for the agent platform?"
  Web:  python council_test.py --serve
        Then open http://localhost:8800

Reads API keys from backend/.env or environment variables.
"""

import asyncio
import json
import os
import random
import sys
if sys.stdout and getattr(sys.stdout, "reconfigure", None):
    sys.stdout.reconfigure(encoding='utf-8')
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Load .env ──────────────────────────────────────────────────────────────────
def load_env():
    """Load keys from backend/.env, falling back to env vars."""
    env_paths = [
        Path("backend/.env"),
        Path(".env"),
        Path(__file__).parent / "backend" / ".env",
    ]
    for p in env_paths:
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                val = val.strip().strip("'\"")
                os.environ.setdefault(key.strip(), val)
            break

load_env()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
COUNCIL_CHAIRMAN_MODEL = os.environ.get("COUNCIL_CHAIRMAN_MODEL", "gemini-2.5-pro")
COUNCIL_DAILY_LIMIT = int(os.environ.get("COUNCIL_DAILY_LIMIT", "50"))


# ── System Prompts (PAP-ADD-001 Section 3) ─────────────────────────────────────

MEMBER_SYSTEM_PROMPT = """You are a senior technical analyst conducting an independent review. Your job is to find problems, not to validate decisions. The team building this system does not want encouragement — they want to ship best-in-class technology.

Rules:
1. Respond based solely on your own reasoning. Do not hedge for consensus.
2. Be brutally specific. Name the exact failure modes, not vague risks. If something is wrong, say it directly.
3. Do NOT praise the architecture or team unless a specific design choice is genuinely exceptional and you can explain exactly why. Default posture is critical examination, not validation.
4. Generic advice is worthless. If your recommendation could apply to any project, it is too vague. Tie every recommendation to a specific detail in the query.
5. If you are uncertain about a claim, state your confidence level explicitly. Do not fill uncertainty gaps with generic best-practice filler.
6. Structure your response with clear sections: Problems Found, Recommendations, Risks. Note: there is no "Strengths" section. If something is fine, skip it — focus your tokens on what needs to change.
7. Do not reference other models, other responses, or collaboration. This is your independent assessment."""

CHAIRMAN_SYSTEM_PROMPT = """You are the chairman of a technical review council. Three panelists have reviewed an architecture document and submitted their critiques. Your job is to deliver a unified verdict — not a summary of what each panelist said.

RULES:
- Never restate or paraphrase individual panelist responses
- Never say a panelist "makes a good point" or use any praise language
- Do not soften findings
- Your entire response must be under 500 words
- Use no more than 3 headers

REQUIRED STRUCTURE:

### Consensus (what multiple panelists agree on — state the finding, not who said it)

### Sharpest finding (the single most actionable critique from any panelist — cite the specific schema column, step number, or component it targets)

### Verdict
SHIP IT / NEEDS REVISION / REDESIGN
One sentence reason.
One concrete change the builder must make before writing a single line of code."""


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class MemberResponse:
    model: str
    provider: str
    response: str
    latency_ms: int
    tokens_used: int = 0
    error: Optional[str] = None

@dataclass
class CouncilResult:
    query: str
    members: list  # list of MemberResponse
    chairman_model: str
    chairman_synthesis: str
    anonymization_map: dict  # {"Response A": "claude-4x", ...}
    total_latency_ms: int
    total_tokens: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Provider Calls ─────────────────────────────────────────────────────────────

async def call_claude(query: str) -> MemberResponse:
    """Call Claude 4.x via Anthropic SDK (httpx direct)."""
    import httpx
    start = time.perf_counter_ns()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4096,
                    "system": MEMBER_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": query}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = "".join(b["text"] for b in data["content"] if b["type"] == "text")
            tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
            elapsed = (time.perf_counter_ns() - start) // 1_000_000
            return MemberResponse(
                model="claude-sonnet-4-20250514",
                provider="Anthropic",
                response=text,
                latency_ms=elapsed,
                tokens_used=tokens,
            )
    except Exception as e:
        elapsed = (time.perf_counter_ns() - start) // 1_000_000
        return MemberResponse(
            model="claude-sonnet-4-20250514",
            provider="Anthropic",
            response="",
            latency_ms=elapsed,
            error=str(e),
        )


async def call_gemini(query: str) -> MemberResponse:
    """Call Gemini via Google Generative AI REST API."""
    import httpx
    start = time.perf_counter_ns()
    model_name = "gemini-2.5-pro"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_API_KEY}",
                headers={"content-type": "application/json"},
                json={
                    "system_instruction": {"parts": [{"text": MEMBER_SYSTEM_PROMPT}]},
                    "contents": [{"parts": [{"text": query}]}],
                    "generationConfig": {"maxOutputTokens": 4096},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            tokens = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)
            elapsed = (time.perf_counter_ns() - start) // 1_000_000
            return MemberResponse(
                model=model_name,
                provider="Google",
                response=text,
                latency_ms=elapsed,
                tokens_used=tokens,
            )
    except Exception as e:
        elapsed = (time.perf_counter_ns() - start) // 1_000_000
        return MemberResponse(
            model=model_name,
            provider="Google",
            response="",
            latency_ms=elapsed,
            error=str(e),
        )


async def call_grok(query: str) -> MemberResponse:
    """Call Grok via xAI API (OpenAI-compatible endpoint)."""
    import httpx
    start = time.perf_counter_ns()
    model_name = "grok-3-mini"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": MEMBER_SYSTEM_PROMPT},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 4096,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            elapsed = (time.perf_counter_ns() - start) // 1_000_000
            return MemberResponse(
                model=model_name,
                provider="xAI",
                response=text,
                latency_ms=elapsed,
                tokens_used=tokens,
            )
    except Exception as e:
        elapsed = (time.perf_counter_ns() - start) // 1_000_000
        err_msg = str(e)
        if hasattr(e, "response") and e.response is not None:
            err_msg += f" | Details: {e.response.text}"
        return MemberResponse(
            model=model_name,
            provider="xAI",
            response="",
            latency_ms=elapsed,
            error=err_msg,
        )


async def call_chairman(query: str, anonymized_responses: dict) -> MemberResponse:
    """Chairman synthesis via Gemini (configurable model)."""
    import httpx
    start = time.perf_counter_ns()
    model_name = COUNCIL_CHAIRMAN_MODEL

    # Build the chairman's input
    chairman_input = f"## Original Query\n{query}\n\n"
    for label, text in anonymized_responses.items():
        chairman_input += f"## {label}\n{text}\n\n"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_API_KEY}",
                headers={"content-type": "application/json"},
                json={
                    "system_instruction": {"parts": [{"text": CHAIRMAN_SYSTEM_PROMPT}]},
                    "contents": [{"parts": [{"text": chairman_input}]}],
                    "generationConfig": {"maxOutputTokens": 8192},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            tokens = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)
            elapsed = (time.perf_counter_ns() - start) // 1_000_000
            return MemberResponse(
                model=model_name,
                provider="Google (Chairman)",
                response=text,
                latency_ms=elapsed,
                tokens_used=tokens,
            )
    except Exception as e:
        elapsed = (time.perf_counter_ns() - start) // 1_000_000
        return MemberResponse(
            model=model_name,
            provider="Google (Chairman)",
            response="",
            latency_ms=elapsed,
            error=str(e),
        )


# ── Council Orchestrator ───────────────────────────────────────────────────────

async def run_council(query: str) -> CouncilResult:
    """Execute the full LLM Council pipeline per PAP-ADD-001."""
    total_start = time.perf_counter_ns()

    # Step 1: Parallel member dispatch
    members = await asyncio.gather(
        call_claude(query),
        call_gemini(query),
        call_grok(query),
    )

    # Step 2: Filter out errors
    valid = [m for m in members if not m.error]
    if not valid:
        errors = "; ".join(f"{m.provider}: {m.error}" for m in members)
        return CouncilResult(
            query=query,
            members=[asdict(m) for m in members],
            chairman_model=COUNCIL_CHAIRMAN_MODEL,
            chairman_synthesis=f"ALL MEMBERS FAILED. Errors: {errors}",
            anonymization_map={},
            total_latency_ms=(time.perf_counter_ns() - total_start) // 1_000_000,
            total_tokens=0,
        )

    # Step 3: Anonymize — randomize order to prevent positional bias
    shuffled = valid.copy()
    random.shuffle(shuffled)
    labels = ["Response A", "Response B", "Response C"]
    anon_map = {}
    anon_responses = {}
    for i, member in enumerate(shuffled[:3]):
        label = labels[i]
        anon_map[label] = f"{member.provider} ({member.model})"
        anon_responses[label] = member.response

    # Step 4: Chairman synthesis
    chairman = await call_chairman(query, anon_responses)

    total_elapsed = (time.perf_counter_ns() - total_start) // 1_000_000
    total_tokens = sum(m.tokens_used for m in members) + chairman.tokens_used

    return CouncilResult(
        query=query,
        members=[asdict(m) for m in members],
        chairman_model=COUNCIL_CHAIRMAN_MODEL,
        chairman_synthesis=chairman.response if not chairman.error else f"CHAIRMAN FAILED: {chairman.error}",
        anonymization_map=anon_map,
        total_latency_ms=total_elapsed,
        total_tokens=total_tokens,
    )


# ── CLI Mode ───────────────────────────────────────────────────────────────────

def print_result(result: CouncilResult):
    """Pretty-print council result to terminal."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  LLM COUNCIL RESULT{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"\n{DIM}Query: {result.query}{RESET}\n")

    # Individual member responses
    colors = [GREEN, CYAN, MAGENTA]
    for i, member in enumerate(result.members):
        m = member if isinstance(member, dict) else asdict(member)
        color = colors[i % 3]
        status = f"{color}{m['provider']} ({m['model']}){RESET}"
        if m.get("error"):
            print(f"  {status}: {YELLOW}ERROR — {m['error']}{RESET}")
        else:
            print(f"  {status}: {m['latency_ms']}ms, {m['tokens_used']} tokens")
            # Print first 200 chars as preview
            preview = m["response"][:200].replace("\n", " ")
            print(f"  {DIM}{preview}...{RESET}\n")

    # Anonymization map
    print(f"{BOLD}{YELLOW}Anonymization Map:{RESET}")
    for label, model in result.anonymization_map.items():
        print(f"  {label} -> {model}")

    # Chairman synthesis
    print(f"\n{BOLD}{'-'*70}{RESET}")
    print(f"{BOLD}{GREEN}  CHAIRMAN SYNTHESIS ({result.chairman_model}){RESET}")
    print(f"{BOLD}{'-'*70}{RESET}\n")
    print(result.chairman_synthesis)

    # Stats
    print(f"\n{BOLD}{'-'*70}{RESET}")
    print(f"{DIM}  Total latency: {result.total_latency_ms}ms | Total tokens: {result.total_tokens} | {result.timestamp}{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")


async def cli_mode(query: str):
    """Run a single council query from the command line."""
    print(f"\033[2mDispatching to Claude, Gemini, and Grok in parallel...\033[0m")
    result = await run_council(query)
    print_result(result)

    # Save to JSON log
    log_dir = Path("council_logs")
    log_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"council_{ts}.json"
    log_file.write_text(json.dumps(asdict(result), indent=2, default=str))
    print(f"\033[2mFull result saved to {log_file}\033[0m")


# ── Web UI Mode ────────────────────────────────────────────────────────────────

WEB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Council — PAP-ADD-001</title>
<style>
  :root {
    --bg: #0f0f0f; --surface: #181818; --surface2: #222222;
    --border: #2a2a2a; --text: #e0e0e0; --text-dim: #888;
    --accent: #e8f04a; --green: #4af0a0; --blue: #4a90f0;
    --orange: #f0a04a; --purple: #c04af0; --red: #f04a4a;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Syne', 'Inter', system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    min-height: 100vh; display: flex; flex-direction: column;
  }
  .header {
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 20px 32px; display: flex; align-items: center; gap: 16px;
  }
  .header h1 { font-size: 20px; font-weight: 700; }
  .header .badge {
    font-family: 'DM Mono', monospace; font-size: 11px;
    padding: 3px 10px; border-radius: 4px;
    background: var(--surface2); color: var(--text-dim);
    border: 1px solid var(--border);
  }
  .provider-dots { display: flex; gap: 6px; margin-left: auto; }
  .provider-dots .dot {
    width: 10px; height: 10px; border-radius: 50%;
  }
  .dot-claude { background: var(--green); }
  .dot-gemini { background: var(--blue); }
  .dot-grok { background: var(--orange); }

  .main { flex: 1; max-width: 900px; width: 100%; margin: 0 auto; padding: 32px; }

  .input-area {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; margin-bottom: 24px;
  }
  .input-area textarea {
    width: 100%; background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text); font-family: inherit;
    font-size: 15px; padding: 14px 16px; resize: vertical;
    min-height: 80px; outline: none;
  }
  .input-area textarea:focus { border-color: var(--accent); }
  .input-area .controls {
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 12px;
  }
  .btn {
    background: var(--accent); color: #000; border: none;
    padding: 10px 24px; border-radius: 8px; font-weight: 700;
    font-size: 14px; cursor: pointer; font-family: inherit;
    transition: opacity 0.15s;
  }
  .btn:hover { opacity: 0.85; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .status { font-family: 'DM Mono', monospace; font-size: 12px; color: var(--text-dim); }

  .result-section { margin-bottom: 24px; }
  .result-section h2 {
    font-size: 14px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
  }
  .result-section h2 .indicator {
    width: 8px; height: 8px; border-radius: 50; display: inline-block;
  }

  .member-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
    transition: border-color 0.2s;
  }
  .member-card:hover { border-color: #444; }
  .member-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px;
  }
  .member-name { font-weight: 700; font-size: 14px; }
  .member-meta {
    font-family: 'DM Mono', monospace; font-size: 11px; color: var(--text-dim);
  }
  .member-body {
    font-size: 14px; line-height: 1.65; color: var(--text);
    white-space: pre-wrap; max-height: 300px; overflow-y: auto;
  }
  .member-body::-webkit-scrollbar { width: 4px; }
  .member-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .member-claude { border-left: 3px solid var(--green); }
  .member-gemini { border-left: 3px solid var(--blue); }
  .member-grok { border-left: 3px solid var(--orange); }
  .member-error { border-left: 3px solid var(--red); opacity: 0.6; }

  .synthesis-card {
    background: var(--surface); border: 1px solid var(--accent);
    border-radius: 12px; padding: 24px; margin-bottom: 24px;
  }
  .synthesis-card h3 {
    font-size: 16px; color: var(--accent); margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
  }
  .synthesis-body {
    font-size: 14px; line-height: 1.7; white-space: pre-wrap;
  }

  .anon-map {
    background: var(--surface2); border-radius: 8px; padding: 12px 16px;
    font-family: 'DM Mono', monospace; font-size: 12px;
    display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 24px;
  }
  .anon-entry { color: var(--text-dim); }
  .anon-label { color: var(--accent); font-weight: 700; }

  .stats-bar {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 20px;
    display: flex; gap: 32px; font-family: 'DM Mono', monospace;
    font-size: 12px; color: var(--text-dim);
  }
  .stats-bar .stat-val { color: var(--accent); font-weight: 700; }

  .spinner {
    display: inline-block; width: 16px; height: 16px;
    border: 2px solid var(--border); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .hidden { display: none; }

  @media (max-width: 640px) {
    .main { padding: 16px; }
    .anon-map { flex-direction: column; gap: 8px; }
    .stats-bar { flex-direction: column; gap: 8px; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>LLM Council</h1>
  <span class="badge">PAP-ADD-001</span>
  <div class="provider-dots">
    <div class="dot dot-claude" title="Claude"></div>
    <div class="dot dot-gemini" title="Gemini"></div>
    <div class="dot dot-grok" title="Grok"></div>
  </div>
</div>

<div class="main">
  <div class="input-area">
    <textarea id="query" placeholder="Enter your query for the council...&#10;&#10;Best for: strategy, planning, architecture decisions, financial analysis, risk assessment"></textarea>
    <div class="controls">
      <span class="status" id="status"></span>
      <button class="btn" id="submit" onclick="runCouncil()">Convene Council</button>
    </div>
  </div>

  <div id="results" class="hidden">
    <!-- Synthesis first — primary deliverable -->
    <div class="result-section">
      <h2>Chairman Synthesis</h2>
      <div class="synthesis-card">
        <h3 id="chairman-model"></h3>
        <div class="synthesis-body" id="synthesis-body"></div>
      </div>
    </div>

    <!-- Anonymization map -->
    <div class="anon-map" id="anon-map"></div>

    <!-- Individual responses -->
    <div class="result-section">
      <h2>Individual Member Responses</h2>
      <div id="member-cards"></div>
    </div>

    <!-- Stats -->
    <div class="stats-bar" id="stats-bar"></div>
  </div>
</div>

<script>
async function runCouncil() {
  const query = document.getElementById('query').value.trim();
  if (!query) return;

  const btn = document.getElementById('submit');
  const status = document.getElementById('status');
  const results = document.getElementById('results');

  btn.disabled = true;
  btn.textContent = 'Council in session...';
  status.innerHTML = '<span class="spinner"></span> Dispatching to Claude, Gemini, Grok in parallel...';
  results.classList.add('hidden');

  try {
    const resp = await fetch('/api/council', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query}),
    });
    const data = await resp.json();

    if (data.error) {
      status.textContent = 'Error: ' + data.error;
      btn.disabled = false;
      btn.textContent = 'Convene Council';
      return;
    }

    renderResult(data);
    results.classList.remove('hidden');
    status.textContent = 'Council complete.';
  } catch (e) {
    status.textContent = 'Network error: ' + e.message;
  }

  btn.disabled = false;
  btn.textContent = 'Convene Council';
}

function renderResult(data) {
  // Synthesis
  document.getElementById('chairman-model').textContent =
    'Chairman: ' + data.chairman_model;
  document.getElementById('synthesis-body').textContent = data.chairman_synthesis;

  // Anon map
  const mapEl = document.getElementById('anon-map');
  mapEl.innerHTML = Object.entries(data.anonymization_map || {}).map(([label, model]) =>
    `<span class="anon-entry"><span class="anon-label">${label}</span> → ${model}</span>`
  ).join('');

  // Member cards
  const cardsEl = document.getElementById('member-cards');
  const providerClass = {Anthropic: 'member-claude', Google: 'member-gemini', xAI: 'member-grok'};
  cardsEl.innerHTML = (data.members || []).map(m => {
    const cls = m.error ? 'member-error' : (providerClass[m.provider] || '');
    if (m.error) {
      return `<div class="member-card ${cls}">
        <div class="member-header">
          <span class="member-name">${m.provider} (${m.model})</span>
          <span class="member-meta">ERROR</span>
        </div>
        <div class="member-body" style="color: var(--red);">${m.error}</div>
      </div>`;
    }
    return `<div class="member-card ${cls}">
      <div class="member-header">
        <span class="member-name">${m.provider} (${m.model})</span>
        <span class="member-meta">${m.latency_ms}ms · ${m.tokens_used} tokens</span>
      </div>
      <div class="member-body">${escapeHtml(m.response)}</div>
    </div>`;
  }).join('');

  // Stats
  document.getElementById('stats-bar').innerHTML = `
    <span>Latency: <span class="stat-val">${data.total_latency_ms}ms</span></span>
    <span>Tokens: <span class="stat-val">${data.total_tokens}</span></span>
    <span>Timestamp: <span class="stat-val">${data.timestamp}</span></span>
  `;
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// Submit on Ctrl+Enter
document.getElementById('query').addEventListener('keydown', e => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    runCouncil();
  }
});
</script>
</body>
</html>"""


async def serve_web(port: int = 8800):
    """Run minimal async HTTP server for the council web UI."""
    from http.server import BaseHTTPRequestHandler
    import socketserver
    import threading

    loop = asyncio.get_event_loop()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # Suppress default logging

        def do_GET(self):
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(WEB_HTML.encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/api/council":
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                query = body.get("query", "")

                if not query:
                    self._json_response({"error": "Empty query"})
                    return

                # Run council in the event loop
                future = asyncio.run_coroutine_threadsafe(run_council(query), loop)
                result = future.result(timeout=180)

                self._json_response(asdict(result))
            else:
                self.send_response(404)
                self.end_headers()

        def _json_response(self, data):
            payload = json.dumps(data, default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = socketserver.TCPServer(("0.0.0.0", port), Handler)
    server.allow_reuse_address = True

    print(f"\033[1m\033[96m")
    print(f"  ╔══════════════════════════════════════════╗")
    print(f"  ║   LLM Council — PAP-ADD-001              ║")
    print(f"  ║   http://localhost:{port}                  ║")
    print(f"  ║   Ctrl+C to stop                         ║")
    print(f"  ╚══════════════════════════════════════════╝")
    print(f"\033[0m")
    print(f"  Providers: Claude (Anthropic) · Gemini (Google) · Grok (xAI)")
    print(f"  Chairman:  {COUNCIL_CHAIRMAN_MODEL}")
    print(f"  Daily cap: {COUNCIL_DAILY_LIMIT}\n")

    # Run HTTP server in a thread so asyncio loop stays available
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


# ── Entrypoint ─────────────────────────────────────────────────────────────────

def check_keys():
    """Verify all three API keys are present."""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not GOOGLE_API_KEY:
        missing.append("GOOGLE_GEMINI_API_KEY or GOOGLE_API_KEY")
    if not XAI_API_KEY:
        missing.append("XAI_API_KEY")
    if missing:
        print(f"\033[91mMissing API keys: {', '.join(missing)}\033[0m")
        print("Set them in backend/.env or as environment variables.")
        sys.exit(1)


def main():
    check_keys()

    if len(sys.argv) < 2:
        print("Usage:")
        print('  python council_test.py "Your query here"')
        print("  python council_test.py --serve [--port 8800]")
        sys.exit(0)

    if sys.argv[1] == "--serve":
        port = 8800
        if "--port" in sys.argv:
            port = int(sys.argv[sys.argv.index("--port") + 1])
        asyncio.run(serve_web(port))
    else:
        query = " ".join(sys.argv[1:])
        asyncio.run(cli_mode(query))


if __name__ == "__main__":
    main()
