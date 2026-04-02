import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from graph import app_graph
from telegram_bot import run_telegram_bot
from model_watcher import model_watcher_loop
from langchain_core.messages import HumanMessage

load_dotenv()

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run the Telegram Bot polling loop and Model Watcher in the background
    telegram_task = asyncio.create_task(run_telegram_bot())
    watcher_task = asyncio.create_task(model_watcher_loop())
    yield
    # Shutdown
    telegram_task.cancel()
    watcher_task.cancel()
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

from langchain_core.messages import HumanMessage
from graph import app_graph

@app.post("/api/chat")
async def chat_endpoint(message: str):
    # Pass message to LangGraph orchestrator
    inputs = {"messages": [HumanMessage(content=message)]}
    result = app_graph.invoke(inputs)
    final_message = result['messages'][-1].content if result.get('messages') else "No response"
    return {"response": final_message}
