import os
import json
import time
import threading
import logging
from datetime import datetime
from dataclasses import dataclass
from flask import Flask, request
import requests
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - UltraSMC - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UltraSMC")

# Telegram Signal Format
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

class TelegramBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            logger.info("✅ Telegram message sent")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {str(e)}")
            return False

class SignalProcessor:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self.signal_queue = Queue()
        self.running = False
        self.last_signals = {}

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._worker, daemon=True).start()
            logger.info("✅ Signal processor started")

    def add(self, data):
        try:
            s = self._parse(data)
            if self._is_valid(s):
                self.signal_queue.put(s)
                return True
        except Exception as e:
            logger.error(f"Error parsing signal: {str(e)}")
        return False

    def _worker(self):
        while self.running:
            try:
                if not self.signal_queue.empty():
                    signal = self.signal_queue.get_nowait()
                    self._send(signal)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")

    def _send(self, signal: TradingSignal):
        try:
            msg = self._format(signal)
            self.telegram_bot.send_message(msg)
        except Exception as e:
            logger.error(f"Send error: {str(e)}")

    def _parse(self, d):
        action = d.get("action", "").upper()
        price = float(d.get("price", 0))
        atr = float(d.get("atr", price * 0.02))
        sl = price - atr if action == "BUY" else price + atr
        risk = abs(price - sl)
        return TradingSignal(
            action=action,
            ticker=d.get("ticker", "UNKNOWN"),
            price=price,
            sl=sl,
            tp1=price + risk if action == "BUY" else price - risk,
            tp2=price + 2*risk if action == "BUY" else price - 2*risk,
            tp3=price + 3*risk if action == "BUY" else price - 3*risk,
            tp4=price + 4*risk if action == "BUY" else price - 4*risk,
            confidence="HIGH",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            atr=atr,
            volume_surge=d.get("volume_surge", False),
            trap_zone=d.get("trap_zone", False),
            score=float(d.get("score", 0)),
            confluence=float(d.get("confluence", 0))
        )

    def _is_valid(self, s: TradingSignal):
        if s.score < 10 or not s.trap_zone or s.confluence < 5:
            return False
        key = f"{s.ticker}_{s.action}"
        now = datetime.now().timestamp()
        if key in self.last_signals and now - self.last_signals[key] < 300:
            return False
        self.last_signals[key] = now
        return True

    def _format(self, s: TradingSignal) -> str:
        emoji = "🟢" if s.action == "BUY" else "🔴"
        rr = round((s.tp1 - s.price) / (s.price - s.sl), 2) if s.price != s.sl else 1
        confidence = "🔥" if s.score >= 15 else "⚡"

        return f"""
{emoji} <b>ULTRA PRECISION SMC SIGNAL</b> {emoji}

🚨 <b>Signal:</b> {s.action} | <b>{s.ticker}</b>
💰 Entry: ${s.price:.2f}
🛡️ Stop Loss: ${s.sl:.2f}

🎯 Targets:
TP1: ${s.tp1:.2f}
TP2: ${s.tp2:.2f}
TP3: ${s.tp3:.2f}
TP4: ${s.tp4:.2f}

📊 Confidence: {confidence}
📈 Score: {s.score}/20
🧠 Confluence: {s.confluence}/10
💎 Trap Zone: {"✅" if s.trap_zone else "❌"}
📊 Volume Surge: {"✅" if s.volume_surge else "❌"}
⚖️ R:R = {rr} | ATR: ${s.atr:.2f}
🕐 Time: {s.timestamp}
        """.strip()

# Initialize app
app = Flask("UltraSMCBot")
telegram_bot = None
processor = None

def initialize_bot():
    global telegram_bot, processor
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or "7962012341:AAG1XJITypeyUkvo-K_2cM4cOqLa4c-Lx3s"
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or "8006606779"
    telegram_bot = TelegramBot(bot_token, chat_id)
    processor = SignalProcessor(telegram_bot)
    processor.start()
    return True

if __name__ == '__main__':
    logger.info("🚀 Ultra Precision SMC Alert System Starting...")
    if initialize_bot():
        # Send a test signal instantly when the app starts
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
        signal = processor._parse(sample)
        if processor._is_valid(signal):
            processor._send(signal)
        app.run(host='0.0.0.0', port=5000)
    else:
        logger.error("❌ Bot initialization failed.")
