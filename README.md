# 🤖 Personal Agent Team

A fully autonomous, locally-hosted multi-agent AI environment. This project uses a sophisticated **LangGraph** orchestrator to dynamically route intents to the most capable AI models in the world — seamlessly blending Google, Anthropic, and OpenAI toolsets into a single cohesive interface.

![Agent Team Diagram](https://img.shields.io/badge/Architecture-LangGraph-blue?style=for-the-badge)
![FastAPI Backend](https://img.shields.io/badge/Backend-FastAPI-green?style=for-the-badge)
![React Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-cyan?style=for-the-badge)

## 🏗️ The Multi-Agent Architecture

The core of this system operates by avoiding a "one-model-fits-all" approach. Instead, an ultra-fast Master Router parses your request and maps it to specialized agents depending on the required logic.

### 1. The Planner 🧠 (Gemini 2.5 Flash)
Google's Gemini 2.5 Flash sits at the front of the pipeline. It reads your intent, natively searches the web if required, and drafts the overall logic blueprint. If the task requires execution, it flags a `HANDOFF_TO_CODER`.

### 2. The Execution Engineer 💻 (Claude 3.7 Sonnet)
Claude 3.7 Sonnet is universally known as the best coding model. It takes Gemini's blueprint and perfectly writes the script. It is equipped with a heavily sandboxed **Python Execution Tool**, allowing Claude to natively test and run background scripts directly on your local system filesystem.

### 3. The Communications Agent 📬 (GPT-4o)
To flawlessly read and send emails without facing strict AWS Bedrock proxy errors, this Agent utilizes GPT-4 Omni. It is physically bound to Python's native `imaplib` and `smtplib`.
- **Proton Mail:** Connects locally to `127.0.0.1` via the Proton Bridge for end-to-end encrypted inbox management.
- **Gmail:** Connects conventionally using TLS application passwords to manage standard inboxes.

### 4. The Model Watcher 👁️ (Background Async Daemon)
AI moves at lightning speed. To make sure you never fall behind, an asynchronous background cron-job queries the OpenRouter API every 24 hours. It builds a mathematical baseline matrix of current models and instantly alerts you if a ground-breaking new model drops that dethrones your current active stack.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js
- Local credentials for OpenRouter, Proton Bridge (optional), and Gmail App Passwords (optional).

### 1. Configure the Environment
Ensure your `.env` file is set up correctly in the `backend/` directory:
```properties
# LLM Providers
OPENROUTER_API_KEY="your_key"
GEMINI_API_KEY="your_key"

# Email Configuration
PROTON_EMAIL="your_email@protonmail.com"
PROTON_PASSWORD="your_bridge_credential"
GMAIL_EMAIL="your_email@gmail.com"
GMAIL_APP_PASSWORD="your_google_app_password"

# Telegram Bot
TELEGRAM_BOT_TOKEN="your_bot_token"
```

### 2. Boot up the Team
You no longer need to manually manage separate server instances. We built a unified startup script.

From the root directory, simply run:
```bash
.\start.bat
```
This will automatically launch the **FastAPI Backend** and the **React Dashboard** simultaneously. 

### 3. Start Chatting
Once the two terminals finish bootstrapping, click or navigate to:
👉 **[http://localhost:5173/](http://localhost:5173/)**

Type a prompt like *"Check my Gmail"* or *"Write a Python script that calculates Pi and execute it"* and watch the Multi-Agent pipeline go to work!
