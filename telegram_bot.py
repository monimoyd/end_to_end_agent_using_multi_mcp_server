# telegram_bot.py
import asyncio
import aiohttp
import traceback

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
load_dotenv()

FASTAPI_ENDPOINT = "http://localhost:8000/put_telegram_message"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def forward_to_mcp(user_id, message):
    async with aiohttp.ClientSession() as session:
        #await session.post(FASTAPI_ENDPOINT, json={"user_id": user_id, "message": message})
        await session.post(FASTAPI_ENDPOINT, params={"user_id": user_id, "message": message})

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        user_id = update.message.from_user.id
        await forward_to_mcp(user_id, user_message)
        print(f"Forwarded successfully user_id: {user_id} user_message: {user_message} ")
    except:
        print(f"Failed to forward: user_id: {user_id} user_message: {user_message} ")
        traceback.print_exc()

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
