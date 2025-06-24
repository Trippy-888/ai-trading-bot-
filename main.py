# main.py — Tier 15 Sniper Bot (Final Upgrade with Full Asset List)

import requests
import time
import datetime
from collections import deque

# === CONFIGURATION ===
ASSETS = [
    "XAU/USD",   # Gold
    "XAG/USD",   # Silver
    "GBP/USD",   # British Pound
    "USD/JPY",   # Japanese Yen
    "EUR/USD",   # Euro
    "AUD/USD",   # Australian Dollar
    "NZD/USD",   # New Zealand Dollar
    "USD/INR",   # Indian Rupee
    "GBP/JPY",   # British Pound / Yen
    "EUR/JPY",   # Euro / Yen
    "BTC/USD",   # Bitcoin
    "ETH/USD"    # Ethereum
]

SCAN_INTERVAL = 60  # seconds
FMP_API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571"
TELEGRAM_BOT_TOKEN = "7403427584:AAF5F0sZ4w5non_"
TELEGRAM_CHAT_ID = "8006606779"

RR_MIN = 1.8  # Minimum Risk:Reward
memory = {asset: deque(maxlen=10) for asset in ASSETS}


def fetch_price(asset):
    try:
        symbol = asset.replace("/", "")
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()
        return float(data[0]["price"]) if data else None
    except Exception as e:
        print(f"[Error] Fetch price for {asset}: {e}")
        return None


def check_reversal(asset, price):
    return price % 7 < 0.15


def check_continuation(asset, price):
    return str(price).endswith("88")


def check_memory_reentry(asset, price):
    return price in memory[asset]


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[Telegram Error] {e}")


def scan():
    for asset in ASSETS:
        price = fetch_price(asset)
        if not price:
            continue

        memory[asset].append(price)

        if check_reversal(asset, price):
            send_telegram(f"🔄 Reversal signal on {asset} at {price}")
        elif check_continuation(asset, price):
            send_telegram(f"➡️ Continuation signal on {asset} at {price}")
        elif check_memory_reentry(asset, price):
            send_telegram(f"🔁 Memory Re-entry on {asset} at {price}")


def main():
    while True:
    now = datetime.now()
    print(f"[{now}] Scanning...")
    # TEMPORARY TEST ALERT
    send_telegram_alert("✅ TEST ALERT: Bot is running properly on Railway.")

    time.sleep(60)
    
if __name__ == "__main__":
    main()
