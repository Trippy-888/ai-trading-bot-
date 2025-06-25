import requests
import time
from datetime import datetime
import pandas as pd
import ta

TELEGRAM_BOT_TOKEN = "7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0"
TELEGRAM_CHAT_ID = "8006606779"
API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571"

ASSETS = [
    "XAU/USD", "NAS100", "GBP/JPY", "GBP/USD",
    "BTC/USD", "AUD/USD", "CAD/USD", "NZD/USD",
    "Crude Oil", "Silver", "Copper", "US30",
    "USD/INR", "EUR/USD", "USD/JPY", "ETH/USD", "XAG/USD"
]

SCAN_INTERVAL = 60  # seconds


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")


def fetch_price_data(asset):
    asset_clean = asset.replace("/", "").replace(" ", "")
    url = f"https://api.twelvedata.com/time_series?symbol={asset_clean}&interval=1min&apikey={API_KEY}&outputsize=30"
    try:
        response = requests.get(url)
        data = response.json()
        if "values" not in data:
            return None
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")
        df.set_index("datetime", inplace=True)
        df = df.astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {asset}: {e}")
        return None


def analyze(asset, df):
    df["ema"] = ta.trend.ema_indicator(df["close"], window=14).ema_indicator()
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    entry_price = latest["close"]
    signal = None

    if previous["rsi"] > 70 and latest["close"] < latest["ema"]:
        signal = "SELL"
    elif previous["rsi"] < 30 and latest["close"] > latest["ema"]:
        signal = "BUY"

    if signal:
        sl = round(entry_price * (1.003 if signal == "BUY" else 0.997), 2)
        tp = round(entry_price * (0.997 if signal == "BUY" else 1.003), 2)
        send_telegram(
            f"🚨 {signal} Signal\nAsset: {asset}\nEntry: {round(entry_price, 2)}\nSL: {sl}\nTP: {tp}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )


def main():
    while True:
        print(f"[{datetime.now()}] 🔍 Scanning {len(ASSETS)} assets...")
        for asset in ASSETS:
            df = fetch_price_data(asset)
            if df is not None and not df.empty:
                analyze(asset, df)
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
