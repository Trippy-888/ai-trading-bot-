from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# Get your Telegram bot token and chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("7403427584:AAF5F0sZ4w5non_ 9WFHAN362-760e5dVZoO")
TELEGRAM_CHAT_ID = os.getenv("8006606779")

@app.post("/signal")
async def receive_signal(request: Request):
    data = await request.json()
    message = f"📈 Trade Signal Received:\n\n{data}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(telegram_url, data=payload)
    
    return {"status": "success"}
