# PAP-ADD-001 — LLM Council Pattern

**Document Ref:** PAP-ADD-001
**Parent Document:** PAP-PLAN-001 (Personal AI Agent Platform)
**Prepared:** April 2026
**Status:** Approved & Fast-Tracked Prototype Built

---

## Purpose

This addendum defines the LLM Council — an ensemble reasoning pattern available to the Strategist's DECIDE node for high-stakes queries. Multiple independent models generate responses in parallel, a chairman model anonymously evaluates and ranks them, then synthesizes the strongest elements into a single authoritative output.

The Council is NOT a replacement for single-agent routing. It is an additional dispatch mode. All existing agent assignments, SDK patterns, and OODA loop mechanics from PAP-PLAN-001 remain unchanged.

**Inspiration:** Andrej Karpathy's LLM Council concept — ensemble method reduces hallucination, single-model bias, and reasoning blind spots.

---

## Section 1 — Design Rationale

### 1.1 The Problem

The Strategist routes each query to the single best-fit agent. This works for domain-specific tasks (code → Claude, calendar → Gemini, social → Grok). For open-ended planning, strategy, and recommendation queries, any single model has characteristic blind spots.

For queries where a bad recommendation has real consequences, the cost of a single model's blind spot justifies the latency and token cost of consulting multiple models.

### 1.2 Ensemble Benefits

| Benefit | Mechanism |
|---|---|
| Reduced hallucination | Claims appearing in 2/3 or 3/3 responses have higher confidence. |
| Diversity of reasoning | Each model approaches problems from different training distributions. |
| Bias cancellation | Provider-specific biases cancel out when anonymized. |
| Quality floor guarantee | Chairman synthesis ensures the final output reflects the best reasoning. |

---

## Section 2 — Architecture

### 2.1 Council as Strategist Subgraph

The Council is a LangGraph subgraph callable from the Strategist's DECIDE node. 

### 2.3 Council Member Assignment

| Council Role | Model | SDK | Already in PAP-PLAN-001 |
|---|---|---|---|
| Member 1 | Claude 4.x (Sonnet) | anthropic Python SDK | Yes |
| Member 2 | Gemini 3 Pro | google-generativeai SDK | Yes |
| Member 3 | Grok 4.x | xai-sdk | Yes |
| Chairman | Gemini 3 Pro / 2.5 Pro | google-generativeai SDK | Yes |

---

## Section 3 — System Prompts

**Council Member System Prompt:**
> You are an independent analyst providing your best response to the query below. Respond based solely on your own reasoning. Do not hedge for consensus. Be specific and decisive.

**Chairman System Prompt:**
> You are the chairman of an expert council. Three independent analysts have each responded to the same query... EVALUATE, IDENTIFY consensus, FLAG disagreements, SYNTHESIZE, and RANK.

---

## Section 4 — Routing Rules

**Route to Council:** Financial planning, business strategy, major purchases, career planning.
**Keep Single-Agent:** Code generation, scheduling, web search, image generation.

---

## Section 5 — Implementation Requirements

### Modified Files / Phase Placement
- `agents/council.py` -> Step 11.5
- `db/schema.py` -> Add `council_runs` table.

---

## Section 6 — Observability & Logging

### 6.1 council_runs Table Schema
Table added for auditing and querying the history of the ensemble.

---

## Section 7 — Cost & Latency 
**Cost control:** `COUNCIL_DAILY_LIMIT` added.

*End Addendum*
