import asyncio
import httpx
from config import settings

seen_models = set()

async def model_watcher_loop():
    """Background cron task that pings OpenRouter daily to find new model releases."""
    global seen_models
    
    # Wait a few seconds for the server to fully boot before starting
    await asyncio.sleep(5)
    
    while True:
        try:
            print("\n[OpenRouter Watcher] Polling for new cutting-edge models...")
            async with httpx.AsyncClient() as client:
                response = await client.get("https://openrouter.ai/api/v1/models")
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    current_models = {model["id"] for model in data}
                    
                    if not seen_models:
                        # First run, just seed the baseline
                        seen_models = current_models
                        print(f"[OpenRouter Watcher] Seeded {len(seen_models)} baseline models. Watching for new competitive drops!")
                    else:
                        new_models = current_models - seen_models
                        if new_models:
                            print(f"\n🚨 [BREAKING AI NEWS] 🚨 New Models deployed to OpenRouter!")
                            for nm in new_models:
                                print(f" 👉 {nm}")
                            # In production, we'd fire an alert to your Telegram chat_id here!
                            seen_models = current_models
                        else:
                            print("[OpenRouter Watcher] No new models detected. Your current team remains cutting-edge.")
                            
        except Exception as e:
            print(f"[OpenRouter Watcher] Error polling OpenRouter: {e}")
            
        # Run once every 24 hours (86400 seconds)
        await asyncio.sleep(86400)
