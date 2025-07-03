import os
import json
import logging
import threading
import time
from datetime import datetime
from dataclasses import dataclass
from flask import Flask, request, jsonify
import requests
from queue import Queue

# === Configure Logging ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UltraSMC")

# === Telegram Bot Config ===
BOT_TOKEN = "7403427584:AAF5F0sZ4w5non_ 9WFHAN362-760e5dVZoO"
CHAT_ID = "8006606779"
WEBHOOK_SECRET = "https://ai-trading-bot-production-fd12.up.railway.app/webhook"  # optional, can be empty

# === Signal Dataclass ===
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

# === Telegram Bot Class ===
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
            logger.info("Message sent to Telegram successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False

    def send_alert(self, signal: TradingSignal) -> bool:
        try:
            message = self._format_alert_message(signal)
            return self.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False

    def _format_alert_message(self, signal: TradingSignal) -> str:
        action_emoji = "🟢" if signal.action.upper() == "BUY" else "🔴"
        risk = abs(signal.price - signal.sl)
        reward = abs(signal.tp1 - signal.price)
        rr_ratio = reward / risk if risk > 0 else 0
        confidence_emoji = "🔥" if signal.score >= 15 else "⚡"

        message = f"""
{action_emoji} <b>ULTRA PRECISION SMC SIGNAL</b> {action_emoji}

🚨 <b>Signal:</b> {signal.action.upper()}
📈 <b>Ticker:</b> {signal.ticker}
💰 <b>Entry:</b> ${signal.price:.4f}
🛡️ <b>SL:</b> ${signal.sl:.4f}

🎯 <b>Take Profits:</b>
TP1: ${signal.tp1:.4f} (1:1)
TP2: ${signal.tp2:.4f} (1:2)
TP3: ${signal.tp3:.4f} (1:3)
TP4: ${signal.tp4:.4f} (1:4)

📊 <b>Analysis:</b>
{confidence_emoji} <b>Confidence:</b> {signal.confidence}
🎯 <b>Score:</b> {signal.score:.1f}/20
🌊 <b>Confluence:</b> {signal.confluence:.1f}
💎 <b>Trap Zone:</b> {"✅" if signal.trap_zone else "❌"}
📈 <b>Volume Surge:</b> {"✅" if signal.volume_surge else "❌"}

🕐 <b>Time:</b> {signal.timestamp}
📍 <b>ATR:</b> ${signal.atr:.4f}

<i>🎯 Ultra High Conviction Setup - Perfect Trap Detection</i>
""".strip()
        return message

# === Signal Processor Class ===
class SignalProcessor:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self.last_signals = {}
        self.signal_queue = Queue()
        self.running = False

    def start_processing(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._process_signals, daemon=True).start()
            logger.info("Signal processing thread started")

    def _process_signals(self):
        while self.running:
            try:
                if not self.signal_queue.empty():
                    signal = self.signal_queue.get_nowait()
                    self._handle_signal(signal)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing signal: {str(e)}")

    def add_signal(self, data):
        try:
            signal = self._parse_signal(data)
            if signal and self._is_valid_signal(signal):
                self.signal_queue.put(signal)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add signal: {str(e)}")
            return False

    def _parse_signal(self, data):
        try:
            action = data.get('action', '').upper()
            price = float(data.get('price', 0))
            atr = float(data.get('atr', price * 0.02))

            sl = price - atr if action == 'BUY' else price + atr
            risk = abs(price - sl)
            tp1 = price + risk if action == 'BUY' else price - risk
            tp2 = price + 2 * risk if action == 'BUY' else price - 2 * risk
            tp3 = price + 3 * risk if action == 'BUY' else price - 3 * risk
            tp4 = price + 4 * risk if action == 'BUY' else price - 4 * risk

            return TradingSignal(
                action=action,
                ticker=data.get('ticker', 'UNKNOWN'),
                price=price,
                sl=sl,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                tp4=tp4,
                confidence="HIGH",
                timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                atr=atr,
                volume_surge=data.get('volume_surge', False),
                trap_zone=data.get('trap_zone', False),
                score=float(data.get('score', 0)),
                confluence=float(data.get('confluence', 0))
            )
        except Exception as e:
            logger.error(f"Failed to parse signal: {str(e)}")
            return None

    def _is_valid_signal(self, signal: TradingSignal):
        if signal.score < 10 or signal.confluence < 5 or not signal.trap_zone:
            return False
        key = f"{signal.ticker}_{signal.action}"
        now = datetime.now().timestamp()
        if key in self.last_signals and now - self.last_signals[key] < 300:
            return False
        self.last_signals[key] = now
        return True

    def _handle_signal(self, signal: TradingSignal):
        logger.info(f"Processing {signal.action} signal for {signal.ticker} at ${signal.price:.2f}")
        self.telegram_bot.send_alert(signal)

# === Flask App ===
app = Flask("UltraSMCBot")
telegram_bot = TelegramBot(BOT_TOKEN, CHAT_ID)
signal_processor = SignalProcessor(telegram_bot)
signal_processor.start_processing()

# === Routes ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if WEBHOOK_SECRET and request.headers.get('X-Webhook-Secret') != WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    accepted = signal_processor.add_signal(data)
    return jsonify({'status': 'success' if accepted else 'rejected'})

@app.route('/test', methods=['POST'])
def test():
    test_data = {
        'action': 'BUY',
        'ticker': 'XAUUSD',
        'price': 2365.0,
        'atr': 9.8,
        'score': 17.2,
        'confluence': 8.9,
        'volume_surge': True,
        'trap_zone': True
    }
    added = signal_processor.add_signal(test_data)
    return jsonify({'status': 'success' if added else 'error'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'bot': True})

# === App Start ===
if __name__ == '__main__':
    logger.info("🚀 Ultra Precision SMC Alert System Starting...")
    telegram_bot.send_message("🤖 Ultra Precision SMC Alert Bot Started!✅ System initialized successfully🔄 Ready to receive trading signals")
    app.run(host='0.0.0.0', port=5000)
