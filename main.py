from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0"
CHAT_ID = "8006606779"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Received data:", data)

    try:
        signal = data.get("signal", "N/A")
        ticker = data.get("ticker", "N/A")
        price = data.get("price", "N/A")
        sl = data.get("sl", "N/A")
        tp1 = data.get("tp1", "N/A")
        tp2 = data.get("tp2", "N/A")
        tp3 = data.get("tp3", "N/A")
        confidence = data.get("confidence", "N/A")

        message = f"🚨 Signal: {signal}\n📈 Ticker: {ticker}\n💵 Price: {price}\n🛡️ SL: {sl}\n🎯 TP1: {tp1}\n🎯 TP2: {tp2}\n🎯 TP3: {tp3}\n⚡ Confidence: {confidence}"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        response = requests.post(url, json=payload)
        print("Telegram response:", response.text)
        return "OK", 200

    except Exception as e:
        print("Error:", e)
        return str(e), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
