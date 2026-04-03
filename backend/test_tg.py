import asyncio
import logging
from telegram_bot import run_telegram_bot

logging.basicConfig(level=logging.INFO)

async def main():
    await run_telegram_bot()

if __name__ == "__main__":
    asyncio.run(main())
