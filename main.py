# 🧠 TIER-21 SNIPER BOT
# Supports: Gold, Silver, GBP, EUR/USD, USD/JPY, Crude Oil (WTI), NASDAQ (NDX), BTC/USD, ETH/USD
# Platform: Railway ($5 plan), FMP ($29 plan)
# Alerts: Telegram

import os
import time
import requests
from datetime import datetime

# === ENVIRONMENT VARIABLES ===
FMP_API_KEY = os.getenv("54kgcuCJpN9Yfwqb50Nx7e65UhuX1571")
TELEGRAM_BOT_TOKEN = os.getenv("7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0")
TELEGRAM_CHAT_ID = os.getenv("8006606779")

# === CONFIGURATION ===
ASSETS = {
    "XAUUSD": "Gold",
    "XAGUSD": "Silver",
    "GBPUSD": "GBP/USD",
    "EURUSD": "EUR/USD",
    "USDJPY": "USD/JPY",
    "WTIUSD": "Crude Oil",
    "NDX": "NASDAQ",
    "BTCUSD": "Bitcoin",
    "ETHUSD": "Ethereum"
}

SCAN_INTERVAL = 60  # seconds
SIGNAL_THRESHOLD = 0.25  # % price wiggle to trigger signal (fake logic)

# === FETCH PRICE ===
def fetch_price(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return float(data[0]['price']) if data else None
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fetching {symbol}: {e}")
        return None

# === TELEGRAM ALERT ===
def send_telegram_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Telegram error: {e}")

# === MAIN SCANNER ===
def scan():
    print(f"[{datetime.now()}] 🔍 Scanning {len(ASSETS)} assets...")
    for symbol, label in ASSETS.items():
        price = fetch_price(symbol)
        if price:
            # Placeholder signal logic — this should be replaced with real conditions
            if round(price) % 2 == 0:
                msg = f"🚨 <b>Signal on {label}</b>\nPrice: <code>{price}</code>\nTime: {datetime.now().strftime('%H:%M:%S')}"
                send_telegram_alert(msg)

# === LOOP ===
if __name__ == "__main__":
    while True:
        scan()
        time.sleep(SCAN_INTERVAL)
