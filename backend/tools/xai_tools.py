import os
import httpx
from langchain_core.tools import tool
from config import settings

@tool("search_x")
def search_x(query: str) -> str:
    """
    Search X/Twitter for real-time trending topics, breaking news, live discussions, sentiment, and what people are posting about a topic. Use this instead of search_web when the query is specifically about X/Twitter activity, trends, or social media reactions.
    """
    api_key = settings.xai_api_key or os.environ.get("XAI_API_KEY")
    if not api_key:
        return "Search error: XAI_API_KEY is not set. Please check your .env"
    
    try:
        response = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-3-mini-fast",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You have real-time access to X/Twitter. Answer the user's question about current trends, posts, discussions, or sentiment on X. Be specific with usernames, post counts, and timestamps when available. Keep it concise."
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ]
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])
    except Exception as e:
        return f"Search error from Grok API: {str(e)}"
