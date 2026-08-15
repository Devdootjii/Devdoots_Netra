import asyncio
import os
from telegram import Bot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

async def send_test_message():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="Hello Netra")
    print("Test Successful: Message Telegram par bhej diya gaya hai!")

if __name__ == "__main__":
    asyncio.run(send_test_message())