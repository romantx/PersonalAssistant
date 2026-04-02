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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    inputs = {"messages": [HumanMessage(content=user_msg)]}
    
    # Invoke LangGraph
    try:
        result = app_graph.invoke(inputs)
        final_message = result['messages'][-1].content if result.get('messages') else "No response"
        await update.message.reply_text(final_message)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def run_telegram_bot():
    token = settings.telegram_bot_token
    if not token or token == "your_telegram_bot_token_here":
        print("TELEGRAM_BOT_TOKEN missing from .env. Skipping Telegram polling.")
        # Hold the thread open infinitely so asyncio task doesn't crash
        while True:
            await asyncio.sleep(3600)
        
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve-swap", approve_swap))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Starting Telegram Poller...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep the task alive
    while True:
        await asyncio.sleep(3600)
