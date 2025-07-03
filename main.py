from flask import Flask, request
import requests

app = Flask(__name__)

# === Telegram Bot Setup ===
TELEGRAM_BOT_TOKEN = "7403427584:AAF5F0sZ4w5non_"
TELEGRAM_CHAT_ID = "8006606779"

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=data)

# === Webhook Endpoint for TradingView ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    signal = data.get("signal")
    ticker = data.get("ticker")
    price = float(data.get("price", 0))
    confidence = data.get("confidence", "N/A")  # Optional field from TradingView alert

    if not signal or not ticker or not price:
        return "Invalid alert format", 400

    # === SL & TP Calculation ===
    rr_ratio = 2  # 1:2 risk
    risk = price * 0.002  # 0.2% price risk - you can adjust this base

    if signal.upper() == "BUY":
        sl = price - risk * rr_ratio
        tp1 = price + risk * 4
        tp2 = price + risk * 5
        tp3 = price + risk * 6
    else:
        sl = price + risk * rr_ratio
        tp1 = price - risk * 4
        tp2 = price - risk * 5
        tp3 = price - risk * 6

    # === Format Telegram Message ===
    message = (
        f"🚨 *TRADE ALERT*\n"
        f"Asset: `{ticker}`\n"
        f"Signal: *{signal.upper()}*\n"
        f"Entry Price: `{round(price, 2)}`\n"
        f"Stop Loss (1:2): `{round(sl, 2)}`\n"
        f"Take Profit 1 (1:4): `{round(tp1, 2)}`\n"
        f"Take Profit 2 (1:5): `{round(tp2, 2)}`\n"
        f"Take Profit 3 (1:6): `{round(tp3, 2)}`\n"
        f"Confidence: *{confidence}*"
    )

    send_telegram_message(message)
    return "Alert processed", 200

if __name__ == '__main__':
    app.run(port=8080)
