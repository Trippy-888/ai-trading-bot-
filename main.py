# LSOB-Sim Core Engine
# Author: ShadowAI | Purpose: Institutional spoof/trap simulation bot with sniper logic

import requests
import time
import datetime
from statistics import mean
import numpy as np

# === USER CONFIG ===
FMP_API_KEY = '54kgcuCJpN9Yfwqb50Nx7e65UhuX1571'
TELEGRAM_BOT_TOKEN = '7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0'
TELEGRAM_CHAT_ID = '8006606779'
ASSETS = list(set([
    'XAUUSD', 'XAGUSD', 'NAS100', 'US30',
    'GBPJPY', 'GBPUSD', 'EURUSD', 'USDJPY',
    'AUDUSD', 'NZDUSD', 'USDCAD', 'CRUDE',
    'COPPER', 'USDZAR', 'USDMXN'
]))[:15]
]
TIMEFRAME = '1min'  # For ultra scalping


# === HELPER FUNCTIONS ===
def get_fmp_candles(symbol, interval='1min', limit=100):
    url = f'https://financialmodelingprep.com/api/v3/historical-chart/{interval}/{symbol}?apikey={FMP_API_KEY}'
    data = requests.get(url).json()
    return data[:limit]

def send_telegram_alert(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def is_spoof_wall(candles):
    latest = candles[0]
    body = abs(float(latest['close']) - float(latest['open']))
    wick = abs(float(latest['high']) - float(latest['low']))
    vol = float(latest['volume'])
    return body < (0.25 * wick) and vol > mean([float(c['volume']) for c in candles[1:6]]) * 1.5

def is_absorption(candles):
    vols = [float(c['volume']) for c in candles[:5]]
    closes = [float(c['close']) for c in candles[:5]]
    return vols == sorted(vols) and max(closes) - min(closes) < 0.2

def detect_void_zone(candles):
    wicks = [abs(float(c['high']) - float(c['low'])) for c in candles]
    return np.percentile(wicks, 90) > 2.5 and candles[0]['close'] < candles[2]['close']

def trigger_long(symbol, entry, sl, tp):
    send_telegram_alert(f"\n🟢 LONG ENTRY - {symbol}\nENTRY: {entry}\nSL: {sl}\nTP: {tp}\nReason: Trap + Absorption + Void")

def trigger_short(symbol, entry, sl, tp):
    send_telegram_alert(f"\n🔴 SHORT ENTRY - {symbol}\nENTRY: {entry}\nSL: {sl}\nTP: {tp}\nReason: Spoof + Trap + OB Mid")

# === MAIN LOOP ===
while True:
    for symbol in ASSETS:
        try:
            data = get_fmp_candles(symbol, interval=TIMEFRAME)
            if len(data) < 10:
                continue

            spoof = is_spoof_wall(data)
            absorp = is_absorption(data)
            void = detect_void_zone(data)

            entry = float(data[0]['close'])
            sl = entry + 2.5
            tp = entry - 6.0

            if spoof and void:
                trigger_short(symbol, entry, sl, tp)
            elif absorp and void:
                trigger_long(symbol, entry, entry - 2.5, entry + 6.0)

        except Exception as e:
            print(f"Error for {symbol}: {e}")

    time.sleep(60)
