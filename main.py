import os
import json
import time
import logging
import requests
import threading
from datetime import datetime
from queue import Queue
from flask import Flask, request, jsonify
from dataclasses import dataclass

# === Telegram Credentials (You already tested ✅) ===
BOT_TOKEN = "7962012341:AAG1XJITypeyUkvo-K_2cM4cOqLa4c-Lx3s"
CHAT_ID = "8006606779"

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - UltraSMC - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_alerts.log')
    ]
)
logger = logging.getLogger("UltraSMC")

# === Telegram Handler ===
class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{token}"

    def send_message(self, text: str) -> bool:
        try:
            response = requests.post(
                f"{self.url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10
            )
            response.raise_for_status()
            logger.info("✅ Telegram message sent")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram send failed: {e}")
            return False

# === Data Model for Trading Signal ===
@dataclass
class TradingSignal:
    action: str
    ticker: str
    price: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    tp4: float
    confidence: str
    timestamp: str
    atr: float
    volume_surge: bool
    trap_zone: bool
    score: float
    confluence: float

# === Formatter & Sender ===
class SignalProcessor:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self.signal_queue = Queue()
        self.last_signals = {}
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._worker, daemon=True).start()
            logger.info("✅ Signal processor started")

    def _worker(self):
        while self.running:
            if not self.signal_queue.empty():
                signal = self.signal_queue.get_nowait()
                self._send(signal)
            time.sleep(0.1)

    def _send(self, signal: TradingSignal):
        msg = self._format(signal)
        self.telegram_bot.send_message(msg)

    def _format(self, s: TradingSignal) -> str:
        emoji = "🟢" if s.action == "BUY" else "🔴"
        rr = round((s.tp1 - s.price) / (s.price - s.sl), 2) if s.price != s.sl else 1
        return f"""
{emoji} <b>ULTRA PRECISION SMC SIGNAL</b> {emoji}

📈 <b>{s.action}</b> <b>{s.ticker}</b> @ ${s.price:.2f}
🛡️ SL: ${s.sl:.2f}
🎯 TP1: ${s.tp1:.2f}, TP2: ${s.tp2:.2f}, TP3: ${s.tp3:.2f}, TP4: ${s.tp4:.2f}

📊 Score: {s.score}/20 | Confidence: {s.confidence}
⚡ Volume Surge: {"✅" if s.volume_surge else "❌"}
🧠 Trap Zone: {"✅" if s.trap_zone else "❌"}
🔁 R:R: {rr} | ATR: ${s.atr:.2f}
🕐 Time: {s.timestamp}
""".strip()

    def add(self, data):
        try:
            s = self._parse(data)
            if not self._is_valid(s):
                return False
            self.signal_queue.put(s)
            return True
        except Exception as e:
            logger.error(f"Signal parse error: {e}")
            return False

    def _parse(self, d) -> TradingSignal:
        action = d["action"].upper()
        price = float(d["price"])
        atr = float(d.get("atr", price * 0.02))
        sl = price - atr if action == "BUY" else price + atr
        r = abs(price - sl)
        return TradingSignal(
            action=action,
            ticker=d["ticker"],
            price=price,
            sl=sl,
            tp1=price + r if action == "BUY" else price - r,
            tp2=price + 2 * r if action == "BUY" else price - 2 * r,
            tp3=price + 3 * r if action == "BUY" else price - 3 * r,
            tp4=price + 4 * r if action == "BUY" else price - 4 * r,
            confidence=d.get("confidence", "HIGH"),
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            atr=atr,
            volume_surge=d.get("volume_surge", False),
            trap_zone=d.get("trap_zone", False),
            score=float(d.get("score", 0)),
            confluence=float(d.get("confluence", 0))
        )

    def _is_valid(self, s: TradingSignal):
        key = f"{s.ticker}_{s.action}"
        now = time.time()
        if self.last_signals.get(key, 0) > now - 300:
            return False
        self.last_signals[key] = now
        return s.score >= 10 and s.trap_zone

# === Flask Web Server ===
app = Flask("UltraSMCBot")
telegram = TelegramBot(BOT_TOKEN, CHAT_ID)
processor = SignalProcessor(telegram)
processor.start()
telegram.send_message("🤖 Ultra Precision SMC Alert Bot Started!✅ System initialized successfully🔄 Ready to receive trading signals")

@app.route('/webhook', methods=['POST'])
def webhook():
    if not request.is_json:
        return jsonify({'error': 'Invalid format'}), 400
    data = request.get_json()
    accepted = processor.add(data)
    return jsonify({'status': 'success' if accepted else 'rejected'})

@app.route('/test', methods=['GET', 'POST'])
def test():
    try:
        sample = {
            "action": "BUY",
            "ticker": "XAUUSD",
            "price": 2322.50,
            "atr": 8.5,
            "score": 16.5,
            "confluence": 9.3,
            "volume_surge": True,
            "trap_zone": True
        }
        ok = processor.add(sample)
        return f"Test signal {'sent ✅' if ok else 'rejected ❌'}", 200
    except Exception as e:
        logger.error(f"/test failed: {str(e)}")
        return "Internal Server Error", 500

# === Entry Point ===
if __name__ == '__main__':
    logger.info("🚀 Starting Ultra SMC Flask Server...")
    app.run(host="0.0.0.0", port=5000)
