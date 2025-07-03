from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7403427584:AAF5F0sZ4w5non_9WFHAN362-760e5dVZoO"
TELEGRAM_CHAT_ID = "8006606779"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get('message', '🚨 Alert Received')
    requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
    )
    return 'OK', 200

# ✅ THIS LINE IS REQUIRED ON RAILWAY
app.run(host="0.0.0.0", port=8000)
