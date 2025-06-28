# ✅ sniper.py — FINAL NO ERROR VERSION

import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv("54kgcuCJpN9Yfwqb50Nx7e65UhuX1571")
TELEGRAM_BOT_TOKEN = os.getenv("7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0")
TELEGRAM_USER_ID = os.getenv("8006606779")

ASSETS = [
    "XAUUSD", "XAGUSD", "GBPJPY", "USDJPY",
    "EURUSD", "AUDUSD", "NZDJPY", "GBPUSD",
    "USDCHF", "CADJPY", "EURJPY", "CHFJPY"
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_USER_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR] Telegram failed: {e}")

def fetch_candles(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        if not data or not isinstance(data, list):
            print(f"[ERROR] Empty data: {symbol}")
            return None
        df = pd.DataFrame(data)
        df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"}, inplace=True)
        return df[["date", "o", "h", "l", "c", "v"]].sort_values("date").reset_index(drop=True)
    except Exception as e:
        print(f"[ERROR] Fetch fail {symbol}: {e}")
        return None

def evaluate_sniper(df):
    if df is None or len(df) < 10:
        return None
    last = df.iloc[-1]; prev = df.iloc[-2]
    wick = abs(last.h - last.l)
    body = abs(last.o - last.c)
    wick_ratio = wick / body if body != 0 else 0
    trap = wick_ratio > 2.5
    sweep = last.h > df.h.iloc[-5:-1].max() or last.l < df.l.iloc[-5:-1].min()
    reversal = last.c < last.o if last.h > prev.h else last.c > last.o
    vol_spike = last.v > df.v.rolling(10).mean().iloc[-1] * 1.2
    if trap and sweep and reversal and vol_spike:
        side = "SELL" if last.c < last.o else "BUY"
        sl = last.h if side == "SELL" else last.l
        tp = last.c - (sl - last.c) * 2 if side == "SELL" else last.c + (last.c - sl) * 2
        return side, last.c, sl, tp, 96
    return None

def run_bot():
    print(f"[{datetime.now()}] ✅ Sniper Bot Started")
    while True:
        for asset in ASSETS:
            df = fetch_candles(asset)
            result = evaluate_sniper(df)
            if result:
                side, entry, sl, tp, conf = result
                msg = f"🔥 SNIPER TRADE\nAsset: {asset}\nSide: {side}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nConfidence: {conf}%"
                send_telegram_alert(msg)
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
