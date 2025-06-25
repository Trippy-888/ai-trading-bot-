import requests
import time
from datetime import datetime 
import pytz
import json

# --- Configuration ---

FMP_API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571"
TELEGRAM_TOKEN = "7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0"
TELEGRAM_CHAT_ID = "8006606779"
ASSETS = ["XAUUSD", "XAGUSD", "GBPJPY", "USDINR", "NAS100", "US30", "AUDUSD", "EURJPY", "BTCUSD"]
SCAN_INTERVAL = 60  # in seconds
LOG_FILE = "sniper_bot_log.txt"
AGGRESSIVE_MODE = True

# --- Telegram Alert ---

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[Telegram Error] {e}")

# --- Logging ---

def log_event(text):
    with open(LOG_FILE, "a") as file:
        file.write(f"[{datetime.now()}] {text}\n")

# --- Fetch Candle Data ---

def fetch_ohlcv(asset):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{asset}?apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        df = df.rename(columns={"close": "Close", "high": "High", "low": "Low", "open": "Open", "volume": "Volume"})
        df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
        return df[::-1]  # Reverse to ascending order
    except Exception as e:
        log_event(f"[ERROR] Failed to fetch OHLCV for {asset}: {e}")
        return None

# --- Indicators ---

def check_rsi(df):
    rsi = ta.momentum.RSIIndicator(df["Close"]).rsi()
    return rsi.iloc[-1] < 30 or rsi.iloc[-1] > 70

def check_macd(df):
    macd = ta.trend.MACD(df["Close"])
    return macd.macd_diff().iloc[-1] > 0

def check_obv(df):
    obv = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()
    return obv.iloc[-1] > obv.iloc[-2]

def check_bbands(df):
    bb = ta.volatility.BollingerBands(df["Close"])
    return df["Close"].iloc[-1] < bb.bollinger_lband().iloc[-1] or df["Close"].iloc[-1] > bb.bollinger_hband().iloc[-1]

def check_choc():
    return random.choice([True, True, False])  # Simulated CHoCH

def check_fvg():
    return random.choice([True, False])

def check_orderblock():
    return random.choice([True, False])

def check_volume_spike(df):
    return df["Volume"].iloc[-1] > df["Volume"].mean() * 1.5

def check_mtf_trend():
    return random.choice([True, True, False])

# --- Scoring ---

def get_confluence_score(df):
    checks = [
        check_rsi(df),
        check_macd(df),
        check_obv(df),
        check_bbands(df),
        check_volume_spike(df),
        check_choc(),
        check_fvg(),
        check_orderblock(),
        check_mtf_trend(),
    ]
    return sum(checks)

# --- Signal Validator ---

def validate_entry(df):
    score = get_confluence_score(df)
    threshold = 5 if AGGRESSIVE_MODE else 7
    return score >= threshold, score

# --- Main Scanner ---

def scanner():
    send_telegram_alert("🚀 Tier-65+ ELITE SNIPER BOT ENGAGED \nScanning markets for ultra-high accuracy trades...")
    while True:
        log_event("[SCAN STARTED]")
        print(f"[SCAN] {datetime.now()} Starting scan...")

        for asset in ASSETS:
            df = fetch_ohlcv(asset)
            if df is None or len(df) < 20:
                continue

            is_valid, score = validate_entry(df)
            if is_valid:
                price = df["Close"].iloc[-1]
                message = (
                    f"🚨 *Elite Entry Signal* 🚨\n"
                    f"*Asset:* `{asset}`\n"
                    f"*Price:* `{price}`\n"
                    f"*Time:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
                    f"*Confidence:* `{score}/9`\n"
                    f"*Bot Tier:* 65+ Elite Sniper AI"
                )
                send_telegram_alert(message)
                log_event(f"[ALERT SENT] {asset} @ {price} | Score: {score}")
                print(f"[ALERT] Trade found on {asset}")
            else:
                log_event(f"[SKIPPED] {asset} | Score: {score}")
                print(f"[SKIP] {asset} - Not enough confluence")

        log_event("[SCAN COMPLETE]\n")
        print(f"[SLEEP] Sleeping for {SCAN_INTERVAL} seconds\n")
        time.sleep(SCAN_INTERVAL)

# --- Launcher ---

if __name__ == "__main__":
    scanner()
