import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from telegram_bot import run_telegram_bot
from model_watcher import model_watcher_loop
from langchain_core.messages import HumanMessage
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from db.database import DB_PATH, init_db
from graph import build_graph

# Global app_graph for FastApi routes and telegram bot
app_graph_instance = None

load_dotenv()

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_graph_instance
    init_db()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    memory = SqliteSaver(conn)
    app_graph_instance = build_graph(memory=memory)

    # Startup: Run the Telegram Bot polling loop and Model Watcher in the background
    telegram_task = asyncio.create_task(run_telegram_bot(app_graph_instance))
    watcher_task = asyncio.create_task(model_watcher_loop())
    yield
    # Shutdown
    telegram_task.cancel()
    watcher_task.cancel()
    conn.close()
    print("Shutting down Agent Backend...")

app = FastAPI(title="Personal Agent Team", lifespan=lifespan)

# Allow React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Agent Backend is running"}

@app.post("/api/chat")
async def chat_endpoint(message: str, session_id: str = "web_ui_default"):
    # Pass message to LangGraph orchestrator
    inputs = {"messages": [HumanMessage(content=message)]}
    config = {"configurable": {"thread_id": session_id}}
    
    result = app_graph_instance.invoke(inputs, config=config)
    final_message = result['messages'][-1].content if result.get('messages') else "No response"
    return {"response": final_message}
