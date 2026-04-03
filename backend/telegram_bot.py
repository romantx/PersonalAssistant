import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import settings
from graph import app_graph
from langchain_core.messages import HumanMessage

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your Agent Orchestrator. Send me a task!")

async def approve_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Stub for the Canary Mode / OpenRouter approval
    await update.message.reply_text("Approved! Model swapped to latest OpenRouter top choice in Canary Mode.")

import time
from db.crud import log_conversation, log_agent_run
from db.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()

# We pass 'app_graph' globally, or store it in context
_graph = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    session_id = str(update.message.chat_id)
    inputs = {"messages": [HumanMessage(content=user_msg)]}
    config = {"configurable": {"thread_id": session_id}}
    
    # Dual-Write - Log user input
    db = get_db()
    log_conversation(db, session_id, 'user', user_msg)
    
    start_time = time.time()
    try:
        result = _graph.invoke(inputs, config=config)
        final_message = result['messages'][-1].content if result.get('messages') else "No response"
        duration_ms = (time.time() - start_time) * 1000
        
        # Dual-Write - Log system output and agent run
        log_conversation(db, session_id, 'assistant', final_message)
        agent_name = result.get('next_agent', 'terminal_agent')
        log_agent_run(db, session_id, agent_name, duration_ms, 'success', user_msg)
        
        # Chunk the response
        for i in range(0, len(final_message), 4000):
            await update.message.reply_text(final_message[i:i+4000])
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_agent_run(db, session_id, 'system', duration_ms, f'error_{str(e)}', user_msg)
        await update.message.reply_text(f"Error: {e}")
    finally:
        db.close()

async def run_telegram_bot(app_graph_instance):
    global _graph
    _graph = app_graph_instance

    token = settings.telegram_bot_token
    if not token or token.startswith("your"):
        print("TELEGRAM_BOT_TOKEN missing from .env. Skipping Telegram polling.")
        while True:
            await asyncio.sleep(3600)
        
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve_swap", approve_swap))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Starting Telegram Poller...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)
