import requests

# ✅ Your new Telegram bot credentials
BOT_TOKEN = "7962012341:AAG1XJITypeyUkvo-K_2cM4cOqLa4c-Lx3s"
CHAT_ID = "7962012341"

def send_test_message():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": "✅ Telegram Bot is working! This is a live test from Railway.",
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=data)
        print("Status:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Error sending message:", str(e))

# 📤 Fire test message
send_test_message()
