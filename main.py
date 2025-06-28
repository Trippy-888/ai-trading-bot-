# === HOW TO SETUP `.env` FILE ===
# In the same folder as this script, create a file named `.env` with the following contents:
# FMP_API_KEY=your_fmp_api_key_here
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
# TELEGRAM_USER_ID=your_telegram_user_id_here

import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

# Debugging: Uncomment to test if env vars are loaded
# print("ENV CHECK:", FMP_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)

# Asset list (12 astro-aligned assets)
ASSETS = [
    "XAUUSD", "XAGUSD", "NAS100", "US30", "GBPJPY", "USDJPY",
    "EURUSD", "AUDUSD", "NZDJPY", "GBPUSD", "USOIL", "SPX500"
]

# Send alert to Telegram
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_USER_ID, "text": message}
    requests.post(url, data=data)

# Fetch latest 1-min candle data from FMP
def fetch_candles(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{symbol}?apikey={FMP_API_KEY}"
    try:
        df = pd.DataFrame(requests.get(url).json())
        df = df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"})
        df = df[["date", "o", "h", "l", "c", "v"]].sort_values("date").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# Primary sniper logic (6+ confluences)
def evaluate_primary_sniper(df):
    if df is None or len(df) < 10:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    wick = abs(last["h"] - last["l"])
    body = abs(last["o"] - last["c"])
    wick_ratio = wick / body if body else float('inf')
    trap = wick_ratio > 3
    sweep = last["h"] > df["h"].iloc[-5:-1].max() or last["l"] < df["l"].iloc[-5:-1].min()
    reversal = last["c"] < last["o"] if last["h"] > prev["h"] else last["c"] > last["o"]
    vol_spike = last["v"] > df["v"].rolling(10).mean().iloc[-1] * 1.5
    if trap and sweep and reversal and vol_spike:
        direction = "SELL" if last["c"] < last["o"] else "BUY"
        sl = last["h"] if direction == "SELL" else last["l"]
        tp = last["c"] - (sl - last["c"]) * 2 if direction == "SELL" else last["c"] + (last["c"] - sl) * 2
        return direction, last["c"], sl, tp, 97
    return None

# Secondary smart sniper logic (3–4 confluences)
def evaluate_secondary_sniper(df):
    if df is None or len(df) < 10:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    wick = abs(last["h"] - last["l"])
    body = abs(last["o"] - last["c"])
    wick_ratio = wick / body if body else float('inf')
    trap = wick_ratio > 2
    sweep = last["h"] > df["h"].iloc[-5:-1].max() or last["l"] < df["l"].iloc[-5:-1].min()
    reversal = last["c"] < last["o"] if last["h"] > prev["h"] else last["c"] > last["o"]
    vol_ok = last["v"] > df["v"].rolling(5).mean().iloc[-1]
    if (trap and sweep and vol_ok) or (trap and reversal and vol_ok):
        direction = "SELL" if last["c"] < last["o"] else "BUY"
        sl = last["h"] if direction == "SELL" else last["l"]
        tp = last["c"] - (sl - last["c"]) * 1.5 if direction == "SELL" else last["c"] + (last["c"] - sl) * 1.5
        return direction, last["c"], sl, tp, 93
    return None

# Main loop
while True:
    for asset in ASSETS:
        df = fetch_candles(asset)
        primary = evaluate_primary_sniper(df)
        if primary:
            side, entry, sl, tp, conf = primary
            msg = f"🔹 ULTRA SNIPER ENTRY\n\nAsset: {asset}\nSide: {side}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nConfidence: {conf}%\nTime: {datetime.now().strftime('%H:%M:%S')}"
            send_telegram_alert(msg)
            continue
        secondary = evaluate_secondary_sniper(df)
        if secondary:
            side, entry, sl, tp, conf = secondary
            msg = f"✨ SMART SNIPER ENTRY\n\nAsset: {asset}\nSide: {side}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nConfidence: {conf}%\nTime: {datetime.now().strftime('%H:%M:%S')}"
            send_telegram_alert(msg)
    time.sleep(60)


