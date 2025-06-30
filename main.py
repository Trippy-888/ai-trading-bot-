# Sniper Scalping Bot with Dynamic SL/TP and FMP Assets - v3.9 (Fixed Version)
# TF: 5-min | Strategy: Trap + CHoCH + Divergence + ATR Filter | Alerts: Telegram

import requests, time
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# ========== YOUR TELEGRAM + FMP CREDENTIALS ==========
FMP_API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571"
TELEGRAM_TOKEN = "7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0"
TELEGRAM_CHAT_ID = "8006606779"

# ========== CONFIGURATION ==========
SCAN_INTERVAL = 5 * 60  # every 5 minutes
ASSETS = {
    "GCUSD": "Gold",
}
LOOKBACK = 50  # candles to look back
ATR_PERIOD = 14
TP_MULTIPLIER = 1.8
SL_MULTIPLIER = 1.0

# ========== FUNCTIONS ==========
def fetch_data(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-chart/5min/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url)
print(f"📡 Requesting {symbol} | Status: {response.status_code}")
print(f"📄 Raw response: {response.text[:300]}")

        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            print(f"⚠️ Empty or invalid response for {symbol}: {data}")
            return pd.DataFrame()

        if 'date' not in data[0]:
            print(f"❌ 'date' key missing in response for {symbol}: {data[0]}")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df = df.rename(columns={'date': 'datetime'})
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        return df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

    except Exception as e:
        print(f"[ERROR FETCHING] {symbol}: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    df = df.copy()
    try:
        df.loc[:, 'rsi'] = RSIIndicator(df['close'], window=14).rsi()
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=ATR_PERIOD)
        df.loc[:, 'atr'] = atr.average_true_range()
        df.loc[:, 'divergence'] = df['close'].diff(3) * df['rsi'].diff(3) < 0
        df.loc[:, 'choch'] = df['close'].diff().abs() > df['atr'] * 1.2
        df.loc[:, 'trap'] = (df['close'].shift(1) < df['low'].rolling(3).min()) & (df['close'] > df['open'])
    except Exception as e:
        print(f"[ERROR INDICATORS]: {e}")
    return df

def check_entry(df):
    last = df.iloc[-1]
    if last['trap'] and last['divergence'] and last['choch']:
        entry = last['close']
        sl = entry - (last['atr'] * SL_MULTIPLIER)
        tp = entry + (last['atr'] * TP_MULTIPLIER)
        return entry, sl, tp, last['atr']
    return None

def send_telegram(asset, entry, sl, tp, atr):
    msg = f"\ud83d\udce1 *Scalp Entry Alert*\n\n\ud83d\udcb2 Asset: {asset}\n\ud83c\udfaf Entry: {entry:.3f}\n\u274e SL: {sl:.3f}\n\u2705 TP: {tp:.3f}\n\ud83d\udd22 ATR: {atr:.2f}\n\ud83d\udd39 Filters: Trap \u2705 | CHoCH \u2705 | Divergence \u2705\n\ud83d\udd52 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR TELEGRAM]: {e}")

# ========== MAIN LOOP ==========
print("\n\u23f0 Scalping Bot Running (TF: 5min)...")
while True:
    for symbol, asset in ASSETS.items():
        df = fetch_data(symbol)
        if not df.empty:
            df = calculate_indicators(df[-LOOKBACK:])
            result = check_entry(df)
            if result:
                entry, sl, tp, atr = result
                send_telegram(asset, entry, sl, tp, atr)
    time.sleep(SCAN_INTERVAL)
