# LSOB-Railway Sniper Bot - v4 (Final)
# Institutional Entry Logic | Telegram Alerts | Railway Ready

import requests
import time
import datetime
import os
from statistics import mean
import numpy as np

# === Load from Railway Environment Variables ===
FMP_API_KEY = os.getenv("54kgcuCJpN9Yfwqb50Nx7e65UhuX1571")
TELEGRAM_BOT_TOKEN = os.getenv("7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0")
TELEGRAM_CHAT_ID = os.getenv("8006606779")

# === Astro-Optimized Asset List ===
ASSETS = [
    'XAUUSD', 'XAGUSD', 'NAS100', 'US30',
    'GBPJPY', 'GBPUSD', 'EURUSD', 'USDJPY',
    'AUDUSD', 'NZDUSD', 'USDCAD', 'CRUDE',
    'COPPER', 'USDZAR', 'USDMXN'
]

TIMEFRAME = '1min'

# === Boot Log ===
print("\ud83d\ude80 Boot sequence started: LSOB engine waking up...")
print(f"\ud83d\udee0\ufe0f Debug: Starting scan loop with {len(ASSETS)} assets\n")

# === Utility Functions ===
def get_fmp_candles(symbol, interval='1min', limit=100):
    url = f'https://financialmodelingprep.com/api/v3/historical-chart/{interval}/{symbol}?apikey={FMP_API_KEY}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[:limit]
        else:
            print(f"FMP API error for {symbol}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching data for {symbol}: {e}")
        return []

def send_telegram_alert(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print(f"Telegram response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

# === Institutional Filters ===
def is_spoof_wall(candles):
    if len(candles) < 6: return False
    latest = candles[0]
    body = abs(float(latest['close']) - float(latest['open']))
    wick = abs(float(latest['high']) - float(latest['low']))
    vol = float(latest['volume'])
    avg_vol = mean([float(c['volume']) for c in candles[1:6]])
    return body < (0.25 * wick) and vol > avg_vol * 1.5

def is_absorption(candles):
    if len(candles) < 5: return False
    vols = [float(c['volume']) for c in candles[:5]]
    closes = [float(c['close']) for c in candles[:5]]
    return vols == sorted(vols) and max(closes) - min(closes) < 0.2

def detect_void_zone(candles):
    if len(candles) < 3: return False
    wicks = [abs(float(c['high']) - float(c['low'])) for c in candles]
    return np.percentile(wicks, 90) > 2.5 and float(candles[0]['close']) < float(candles[2]['close'])

# === Signal Triggers ===
def trigger_long(symbol, entry, sl, tp):
    msg = f"\n\U0001f7e2 LONG ENTRY - {symbol}\nENTRY: {entry}\nSL: {sl}\nTP: {tp}\nReason: Trap + Absorption + Void"
    send_telegram_alert(msg)

def trigger_short(symbol, entry, sl, tp):
    msg = f"\n\U0001f534 SHORT ENTRY - {symbol}\nENTRY: {entry}\nSL: {sl}\nTP: {tp}\nReason: Spoof + Trap + OB Mid"
    send_telegram_alert(msg)

# === Sniper Loop ===
while True:
    print(f"\ud83e\uddd0 Scan Start - {datetime.datetime.now()} | Total Assets: {len(ASSETS)}\n")
    for symbol in ASSETS:
        print(f"\uD83D\uDD01 Scanning {symbol} at {datetime.datetime.now()}")
        data = get_fmp_candles(symbol, interval=TIMEFRAME)

        if len(data) < 6:
            print(f"\u26a0\ufe0f Not enough data for {symbol}, skipping.\n")
            continue

        spoof = is_spoof_wall(data)
        absorp = is_absorption(data)
        void = detect_void_zone(data)

        print(f"\ud83d\udd0e Signal Check: Spoof={spoof}, Absorption={absorp}, Void={void}")

        entry = float(data[0]['close'])

        if spoof and void:
            trigger_short(symbol, entry, entry + 2.5, entry - 6.0)
        elif absorp and void:
            trigger_long(symbol, entry, entry - 2.5, entry + 6.0)
        else:
            print(f"\u274c No sniper setup for {symbol} this round.\n")

    print("\u23f3 Sleeping for 60 seconds before next scan...\n")
    time.sleep(60)
