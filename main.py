import requests, time
from datetime import datetime
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# ========== CONFIG ==========
FMP_API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571"
TELEGRAM_TOKEN = "7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0"
TELEGRAM_CHAT_ID = "8006606779"

ASSETS = {
    "XAUUSD": "Gold",
    "XAGUSD": "Silver",
    "NDX100": "NASDAQ100",
    "DJI": "Dow Jones",
    "SPX": "S&P500",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "GBPJPY": "GBP/JPY",
    "AUDUSD": "AUD/USD"
}
TF = "3min"
SCAN_INTERVAL = 15 * 60  # every 15 minutes
LOOKBACK = 80
ATR_PERIOD = 14
TP_MULTIPLIER = 1.6
SL_MULTIPLIER = 1.0

# ========== FUNCTIONS ==========
def fetch_data(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-chart/15min/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Invalid or empty data received")

        df = pd.DataFrame(data)
        df = df.rename(columns={'date': 'datetime'})
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        return df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
    except Exception as e:
        print(f"[ERROR FETCHING] {symbol}: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    df = df.copy()
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    atr = AverageTrueRange(df['high'], df['low'], df['close'], window=ATR_PERIOD)
    df['atr'] = atr.average_true_range()
    df['divergence'] = df['close'].diff(3) * df['rsi'].diff(3) < 0
    df['choch'] = df['close'].diff().abs() > df['atr'] * 1.4
    df['trap'] = (df['close'].shift(1) < df['low'].rolling(3).min()) & (df['close'] > df['open'])
    return df

def check_entry(df):
    last = df.iloc[-1]
    filters = {
        'trap': bool(last['trap']),
        'divergence': bool(last['divergence']),
        'choch': bool(last['choch'])
    }
    confidence = int((sum(filters.values()) / len(filters)) * 100)

    if sum(filters.values()) >= 2:
        entry = last['close']
        sl = entry - (last['atr'] * SL_MULTIPLIER)
        tp = entry + (last['atr'] * TP_MULTIPLIER)
        return entry, sl, tp, confidence, filters
    return None

def send_telegram(asset, entry, sl, tp, conf, filters):
    reason = " | ".join([f"{k} {'✅' if v else '❌'}" for k, v in filters.items()])
    msg = f"""
📡 *Sniper Entry Alert*

🪙 *Asset:* {asset}
🎯 *Entry:* {entry:.3f}
🛑 *SL:* {sl:.3f}
✅ *TP:* {tp:.3f}
📊 *Confidence:* {conf}%
📎 *Reason:* {reason}
🕒 *Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

# ========== MAIN LOOP ==========
print(f"\n⏰ Sniper Bot v5 Running (TF: {TF})...")
while True:
    for symbol, asset in ASSETS.items():
        df = fetch_data(symbol)
        if not df.empty:
            df = calculate_indicators(df[-LOOKBACK:])
            result = check_entry(df)
            if result:
                entry, sl, tp, conf, filters = result
                send_telegram(asset, entry, sl, tp, conf, filters)
    time.sleep(SCAN_INTERVAL)
