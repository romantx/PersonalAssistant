# 🤖 Personal Agent Team

A fully autonomous, locally-hosted multi-agent AI environment. This project uses a sophisticated **LangGraph** orchestrator to dynamically route intents to the most capable AI models in the world — seamlessly blending Google, Anthropic, and xAI toolsets into a single cohesive interface, guarded by a brutal AI peer-review council.

> **Architectural Note — Abstraction Layers:** The use of LangGraph abstraction layers to manage agent state and routing was a deliberate implementation choice to accelerate initial development speed, despite the general preference for direct SDK calls. Future system expansions will continue to isolate abstraction layers strictly to routing, maintaining direct un-abstracted SDK calls wherever possible for explicit tasks.

![Agent Team Diagram](https://img.shields.io/badge/Architecture-LangGraph-blue?style=for-the-badge)
![FastAPI Backend](https://img.shields.io/badge/Backend-FastAPI-green?style=for-the-badge)
![React Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-cyan?style=for-the-badge)

## 🏗️ The Multi-Agent Architecture

The core of this system operates by avoiding a "one-model-fits-all" approach. Instead, an ultra-fast Master Router parses your request and maps it to specialized agents depending on the required logic.

### 1. The Strategist 🧠 (Gemini 2.5 Pro)
Google's Gemini 2.5 Pro sits at the front of the pipeline acting as the primary Strategist. It executes a strict OODA Loop (Observe, Orient, Validate, Decide, Act), handling full conversation history, generating plans, and locking to absolute `AgentType` Enum boundaries before dispatching control to sub-agents. 

### 2. The Coding Agent 💻 (Claude 4 Sonnet)
Claude 4 Sonnet acts as the dedicated Coding Agent, chosen for its unparalleled reasoning coherence in complex multi-file refactors. It receives the Strategist's blueprint and leverages native `bash_execute`, `read_file`, and `write_file` tools. *Security Constraint:* All file operations are strictly sandboxed via hardcoded ABSPATH guards to the `backend/agent-workspace/` directory to prevent host contamination.

### 3. The LLM Council 🏛️ (PAP-ADD-001)
For high-stakes architectural, financial, or career decisions, the system detours to the LLM Council. A prompt is parallel-dispatched to Claude, Gemini, and Grok 3 independently. Their responses are anonymized to strip provider bias and handed to a Gemini 2.5 Pro Chairman, which is hard-coded to deliver a hyper-critical, brutal synthesis identifying exact flaws in the logic without "participation trophies."

### 4. The Communications Agent 📬 (Pending Phase)
This logic block will handle quick drafting, intent understanding, and sending emails without over-engineering text generation.
- **Proton Mail:** Connects locally to `127.0.0.1` via the Proton Bridge for end-to-end encrypted inbox management.
- **Gmail:** Connects conventionally using TLS application passwords to manage standard inboxes.

## 💾 SQLite State Layer & Concurrency
The system leverages SQLite to maintain a highly persistent context. Following the Council's Phase 2 architectural review, SQLite was heavily optimized for a continuous asynchronous environment.

**Concurrency Hardening:**
- Enabled `PRAGMA journal_mode=WAL` and `synchronous=NORMAL`.
- Bound `BEGIN IMMEDIATE` locks globally via SQLAlchemy event listeners to prevent dreaded `database is locked` deadlocks during multi-agent node traversal.

| Table | Purpose |
|---|---|
| `conversations` | Full chat history per session, per agent |
| `agent_runs` | Execution log. Includes `SHADOW_MODE` metric tracking and pipeline latency profiling |
| `tasks` | Relational Task graph (Graph Node -> Parent Node), strictly bound by `AgentType` Enum routers |
| `agent_state` | Strategist OODA persistent context across sessions |
| `calendar_cache` | Local cache of Google Calendar events |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js
- Local credentials for Anthropic, Google AI Studio, and xAI (Grok).

### 1. Configure the Environment
Ensure your `.env` file is set up correctly in the `backend/` directory by copying `.env.example` to `.env`. 
*Note:* The orchestrator respects a `SHADOW_MODE=true` environment flag which forces the LangGraph router to mock traversals and log them to SQLite instead of firing expensive external tools. Turn to `false` for active execution.

### 2. Boot up the Team
From the root directory, simply run:
```bash
.\start.bat
```
This will automatically launch the **FastAPI Backend** and the **React Dashboard** simultaneously. 

### 3. Start Chatting
Once the two terminals finish bootstrapping, navigate to:
👉 **[http://localhost:5173/](http://localhost:5173/)**
