# PAP-ADD-003 — Model Role Assignment Benchmark

**Document Ref:** PAP-ADD-003
**Prepared:** April 2026
**Status:** Council Mandated

---

## Purpose

The LLM Council was asked to evaluate a proposed role swap between two models in the agent platform. The Council unanimously rejected the proposal as biased and anecdotal, and mandated an objective benchmark test before any role changes can be made. This addendum defines that benchmark.

Current role assignments (to be validated or revised by benchmark results):
- Model A (Claude): Coding Executor
- Model B (Gemini): Strategist / Planner

Proposed role swap under evaluation:
- Model A (Claude): Architect / System Designer / Review Gate
- Model B (Gemini): Code Generator / Implementation

---

## Section 1 — Benchmark Overview

The AIQ Benchmark (Architecture & Implementation Quality) is a two-phase automated test that measures each model's independent capability in system design and code implementation. It produces a quantitative scorecard requiring no human interpretation.

**Test subject:** A RESTful API for a Product Wishlist microservice.
**Scope:** State management, multiple endpoints, data schemas, authentication.
**Stack:** Python 3.11+, FastAPI, PostgreSQL, Pytest, Bandit, Spectral.

Both models receive identical inputs. Scoring is fully automated.

---

## Section 2 — Phase 1: Architectural Competence

Each model independently receives this prompt:

> "You are a senior system architect. Design a RESTful API for a Product Wishlist microservice.
> Requirements:
> - Users can create a wishlist
> - Users can add and remove products from a wishlist
> - Users can view their own wishlist only
> - Products are identified by UUID
> Deliverables:
> 1. OpenAPI 3.0 specification in YAML
> 2. JSON Schema for Wishlist and ProductItem resources
> 3. docker-compose.yml for the service and PostgreSQL database"

### Automated Scoring (100 points total):

**OpenAPI Spec Quality (40 pts)**
- Passes `spectral:oas` ruleset validation: 10 pts
- Correctly defines a security scheme (JWT Bearer): 15 pts
- Endpoint completeness (3 pts per required endpoint): 15 pts

**Data Schema Quality (30 pts)**
- Both schemas validate against JSON Schema standard: 15 pts
- Wishlist schema references a list of ProductItem: 15 pts

**Configuration Quality (30 pts)**
- `docker-compose.yml` defines both services: 10 pts
- Ports are mapped: 10 pts
- Environment variables used for secrets (no hardcoded credentials): 10 pts

---

## Section 3 — Phase 2: Implementation Competence

Each model receives the same professionally authored OpenAPI spec for the Wishlist service with this prompt:

> "Implement the service defined in the provided OpenAPI spec. Write functional code, unit tests, and all necessary configuration files."

### Automated Scoring (100 points total):

**Functional Correctness (50 pts)**
- Scored as percentage of passing tests in standardized pytest suite

**Security (25 pts)**
- Scanned with Bandit
- Score inversely proportional to medium/high severity vulnerabilities found
- Zero vulnerabilities = 25 pts; each medium = -5 pts; each high = -10 pts

**Code Quality (25 pts)**
- Cyclomatic complexity within acceptable range
- Linting adherence (Pylint score > 8/10)

---

## Section 4 — Role Assignment Decision Rules

After both phases are scored:

- **If Model A scores higher on Phase 1 AND Model B scores higher on Phase 2:**
  &rarr; Approve role swap. Update PAP-PLAN-001 role assignments accordingly.
- **If scores are within 10 points of each other on either phase:**
  &rarr; Run benchmark twice more with different problem domains, average results.
- **If Model B scores higher on Phase 1:**
  &rarr; Reject role swap. Current assignments stand.
- **If results are ambiguous:**
  &rarr; Escalate to Council for synthesis verdict.

---

## Section 5 — Repeatability

**Run schedule:**
- Upon any major version update to either model
- Quarterly as a standing benchmark
- When production quality drift is observed

**Results are stored in `ROLE-BENCH-001` log with:**
- Date
- Model versions tested
- Phase 1 and Phase 2 scores for each model
- Decision outcome
- Whether role assignments changed

---

## Section 6 — Implementation Instructions

Build the benchmark as a standalone Python script: `backend/benchmarks/aiq_benchmark.py`

The script must:
1. Send identical Phase 1 prompt to both models via their native SDKs
2. Parse outputs and run automated scoring (Spectral for OpenAPI, JSON Schema validator for schemas, YAML parser for docker-compose)
3. Save Phase 1 outputs and scores to `benchmark_results/{timestamp}/phase1/`
4. Send identical Phase 2 spec to both models
5. Execute generated code in isolated Docker containers
6. Run pytest suite, Bandit scan, and Pylint against each output
7. Save Phase 2 outputs and scores to `benchmark_results/{timestamp}/phase2/`
8. Write final scorecard to `benchmark_results/{timestamp}/ROLE-BENCH-001.json`

No human input required after initial execution. Output is a JSON scorecard.

---

## Council Mandate

This benchmark was mandated by the LLM Council following rejection of a role swap proposal. The Council's exact verdict: 

> *"The proposal is rejected as it is based on biased, anecdotal evidence and a flawed interpretation of a model's core capabilities. Before any role changes are considered, you must design and execute an objective, automated benchmark."*

No role changes may be implemented until this benchmark has been run and scored.

*End Addendum*
