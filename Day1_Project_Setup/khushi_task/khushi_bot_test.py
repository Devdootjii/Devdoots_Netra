import asyncio
from telegram import Bot

BOT_TOKEN = "8794032397:AAFxslHQEQ72ArMcg8fNTF-mPQGZrIFBHXs"
CHAT_ID = "8350768886"

async def send_test_message():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="Hello Netra")
    print("Test Successful: Message Telegram par bhej diya gaya hai!")

if __name__ == "__main__":
    asyncio.run(send_test_message())