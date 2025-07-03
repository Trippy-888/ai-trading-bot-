from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ✅ Replace with YOUR Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '7403427584:AAF5F0sZ4w5non_'
TELEGRAM_CHAT_ID = '8006606779'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=data)
    return response

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return 'No data received', 400

    signal = data.get("signal", "UNKNOWN")
    ticker = data.get("ticker", "UNKNOWN")
    price = data.get("price", "N/A")
    sl = data.get("sl", "N/A")
    tp1 = data.get("tp1", "N/A")
    tp2 = data.get("tp2", "N/A")
    tp3 = data.get("tp3", "N/A")
    confidence = data.get("confidence", "N/A")
    market = data.get("market", "Active")  # Optional: "Sideways" flag

    message = f"""
🚨 *AI Trading Alert*
——————————————
📉 *Signal:* `{signal}`
📊 *Ticker:* `{ticker}`
💵 *Price:* `{price}`
🛡 *SL:* `{sl}`
🎯 *TP1:* `{tp1}`
🎯 *TP2:* `{tp2}`
🎯 *TP3:* `{tp3}`
📈 *Confidence:* `{confidence}`
📍 *Market:* `{market}`
——————————————
⏰ Trade triggered by Ultra Precision Sniper AI
"""
    send_telegram_message(message)
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
