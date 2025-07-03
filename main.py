import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from flask import Flask, request, jsonify
import requests
import threading
from queue import Queue
import time
import os  # only this is enough

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        """Send message to Telegram chat"""
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

            logger.info(f"Message sent to Telegram successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False

    def send_alert(self, signal: TradingSignal) -> bool:
        """Send formatted trading alert to Telegram"""
        try:
            # Format the message with proper calculations
            message = self._format_alert_message(signal)
            return self.send_message(message)

        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False

    def _format_alert_message(self, signal: TradingSignal) -> str:
        """Format trading signal into a readable message"""
        # Determine emoji based on action
        action_emoji = "🟢" if signal.action.upper() == "BUY" else "🔴"

        # Calculate risk/reward ratio
        if signal.action.upper() == "BUY":
            risk = signal.price - signal.sl
            reward = signal.tp1 - signal.price
        else:
            risk = signal.sl - signal.price
            reward = signal.price - signal.tp1

        rr_ratio = reward / risk if risk > 0 else 0

        # Format confidence based on score
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

class SignalProcessor:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self.last_signals = {}  # Prevent duplicate signals
        self.signal_queue = Queue()
        self.processing_thread = None
        self.running = False

    def start_processing(self):
        """Start the signal processing thread"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_signals)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            logger.info("Signal processing thread started")

    def stop_processing(self):
        """Stop the signal processing thread"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
            logger.info("Signal processing thread stopped")

    def _process_signals(self):
        """Process signals from the queue"""
        while self.running:
            try:
                if not self.signal_queue.empty():
                    signal = self.signal_queue.get_nowait()
                    self._handle_signal(signal)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing signal: {str(e)}")
                time.sleep(1)

    def add_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Add a new signal to the processing queue"""
        try:
            signal = self._parse_signal(signal_data)
            if signal and self._is_valid_signal(signal):
                self.signal_queue.put(signal)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add signal: {str(e)}")
            return False

    def _parse_signal(self, data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Parse incoming signal data"""
        try:
            # Extract basic signal info
            action = data.get('action', '').upper()
            ticker = data.get('ticker', 'UNKNOWN')
            price = float(data.get('price', 0))

            # Calculate SL and TP based on action and ATR
            atr = float(data.get('atr', price * 0.02))  # Default 2% ATR

            if action == 'BUY':
                sl = price - (atr * 1.0)  # 1x ATR stop loss
                risk = price - sl
                tp1 = price + (risk * 1.0)  # 1:1 risk/reward
                tp2 = price + (risk * 2.0)  # 1:2 risk/reward  
                tp3 = price + (risk * 3.0)  # 1:3 risk/reward
                tp4 = price + (risk * 4.0)  # 1:4 risk/reward
            else:  # SELL
                sl = price + (atr * 1.0)  # 1x ATR stop loss
                risk = sl - price
                tp1 = price - (risk * 1.0)  # 1:1 risk/reward
                tp2 = price - (risk * 2.0)  # 1:2 risk/reward
                tp3 = price - (risk * 3.0)  # 1:3 risk/reward
                tp4 = price - (risk * 4.0)  # 1:4 risk/reward

            # Extract additional data
            score = float(data.get('score', 0))
            confluence = float(data.get('confluence', 0))
            volume_surge = data.get('volume_surge', False)
            trap_zone = data.get('trap_zone', False)

            # Determine confidence level
            if score >= 15 and confluence >= 8:
                confidence = "ULTRA HIGH"
            elif score >= 12 and confluence >= 6:
                confidence = "HIGH"
            elif score >= 10 and confluence >= 5:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            return TradingSignal(
                action=action,
                ticker=ticker,
                price=price,
                sl=sl,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                tp4=tp4,
                confidence=confidence,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                atr=atr,
                volume_surge=volume_surge,
                trap_zone=trap_zone,
                score=score,
                confluence=confluence
            )

        except Exception as e:
            logger.error(f"Failed to parse signal: {str(e)}")
            return None

    def _is_valid_signal(self, signal: TradingSignal) -> bool:
        """Validate signal quality and prevent duplicates"""
        try:
            # Check minimum requirements
            if signal.score < 10 or signal.confluence < 5:
                logger.info(f"Signal rejected: Low quality (Score: {signal.score}, Confluence: {signal.confluence})")
                return False

            # Check for trap zone requirement
            if not signal.trap_zone:
                logger.info("Signal rejected: No trap zone detected")
                return False

            # Check for duplicates (within 5 minutes)
            signal_key = f"{signal.ticker}_{signal.action}"
            current_time = datetime.now().timestamp()

            if signal_key in self.last_signals:
                time_diff = current_time - self.last_signals[signal_key]
                if time_diff < 300:  # 5 minutes
                    logger.info(f"Signal rejected: Duplicate within 5 minutes")
                    return False

            self.last_signals[signal_key] = current_time
            return True

        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False

    def _handle_signal(self, signal: TradingSignal):
        """Handle a validated signal"""
        try:
            logger.info(f"Processing {signal.action} signal for {signal.ticker} at ${signal.price:.2f}")

            # Send to Telegram
            success = self.telegram_bot.send_alert(signal)

            if success:
                logger.info(f"Alert sent successfully for {signal.ticker}")
            else:
                logger.error(f"Failed to send alert for {signal.ticker}")

        except Exception as e:
            logger.error(f"Error handling signal: {str(e)}")

# Flask app for webhook
app = Flask(__name__)

# Global variables
telegram_bot = None
signal_processor = None

def initialize_bot():
    """Initialize Telegram bot and signal processor"""
    global telegram_bot, signal_processor

    # Get configuration from environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Missing required environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        logger.info("Please create a .env file with your Telegram bot credentials")
        logger.info("Example: TELEGRAM_BOT_TOKEN=your_token_here")
        logger.info("Example: TELEGRAM_CHAT_ID=your_chat_id_here")
        return False

    try:
        # Test the bot token format
        if not bot_token.startswith(('bot', '')) or ':' not in bot_token:
            logger.warning("Bot token format might be incorrect. Should be like: 123456789:ABCDEF...")

        telegram_bot = TelegramBot(bot_token, chat_id)
        signal_processor = SignalProcessor(telegram_bot)
        signal_processor.start_processing()

        # Test connection
        test_msg = "🤖 Ultra Precision SMC Alert Bot Started!\n\n✅ System initialized successfully\n🔄 Ready to receive trading signals"
        if telegram_bot.send_message(test_msg):
            logger.info("Bot initialized successfully - Test message sent")
        else:
            logger.warning("Bot initialized but test message failed")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize bot: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from TradingView"""
    try:
        if not signal_processor:
            return jsonify({'error': 'Bot not initialized'}), 500

        # Optional webhook secret validation
        webhook_secret = os.getenv('WEBHOOK_SECRET')
        if webhook_secret:
            provided_secret = request.headers.get('X-Webhook-Secret')
            if provided_secret != webhook_secret:
                logger.warning("Webhook secret mismatch - unauthorized request")
                return jsonify({'error': 'Unauthorized'}), 401

        # Get JSON data from request
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        logger.info(f"📨 Received webhook data: {data}")

        # Process the signal
        success = signal_processor.add_signal(data)

        if success:
            logger.info("✅ Signal accepted and queued for processing")
            return jsonify({'status': 'success', 'message': 'Signal queued for processing'}), 200
        else:
            logger.info("❌ Signal rejected - quality threshold not met")
            return jsonify({'status': 'error', 'message': 'Signal rejected'}), 400

    except Exception as e:
        logger.error(f"🚨 Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_initialized': telegram_bot is not None
    })

@app.route('/test', methods=['POST'])
def test_signal():
    """Test endpoint for sending sample signals"""
    try:
        if not signal_processor:
            return jsonify({'error': 'Bot not initialized'}), 500

        # Sample test signal
        test_data = {
            'action': 'BUY',
            'ticker': 'BTCUSD',
            'price': 45000.00,
            'atr': 900.00,
            'score': 16.5,
            'confluence': 8.2,
            'volume_surge': True,
            'trap_zone': True
        }

        success = signal_processor.add_signal(test_data)

        if success:
            return jsonify({'status': 'success', 'message': 'Test signal sent'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Test signal rejected'}), 400

    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 Ultra Precision SMC Alert System Starting...")
    logger.info("=" * 50)

    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.warning("⚠️  No .env file found. Please create one with your credentials.")
        logger.info("📝 Copy .env.example to .env and fill in your values")

    # Initialize the bot
    if not initialize_bot():
        logger.error("❌ Failed to initialize bot.")
        logger.info("🔧 Please check your environment variables and try again")
        logger.info("📋 Required variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        exit(1)

    # Start Flask app
    try:
        logger.info("🌐 Starting Flask webhook server on 0.0.0.0:5000")
        logger.info("📡 Webhook URL: https://your-repl-url.replit.dev/webhook")
        logger.info("🔍 Health check: https://your-repl-url.replit.dev/health")
        logger.info("🧪 Test endpoint: https://your-repl-url.replit.dev/test")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        if signal_processor:
            signal_processor.stop_processing()
    except Exception as e:
        logger.error(f"❌ Failed to start Flask app: {str(e)}")
        exit(1)
