
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
from dotenv import load_dotenv

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

            logger.info(f"Sending Telegram message to chat_id: {self.chat_id}")
            logger.info(f"Bot token (last 10 chars): ...{self.bot_token[-10:]}")
            
            response = requests.post(url, json=data, timeout=10)
            
            logger.info(f"Telegram API response status: {response.status_code}")
            logger.info(f"Telegram API response: {response.text}")
            
            response.raise_for_status()

            logger.info(f"Message sent to Telegram successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {str(e)}")
            return False

    def send_alert(self, signal: TradingSignal) -> bool:
        """Send formatted trading alert to Telegram"""
        try:
            # Determine confidence emoji
            confidence_emoji = "🔥" if signal.confidence == "HIGH" else "⚡" if signal.confidence == "MEDIUM" else "⚠️"
            
            # Format message with proper escaping
            message = f"""🚨 <b>ULTRA PRECISION SMC {signal.action} SIGNAL</b> 🚨

📈 <b>Ticker:</b> {signal.ticker}
💰 <b>Entry:</b> ${signal.price:.4f}
🛡️ <b>Stop Loss:</b> ${signal.sl:.4f}

🎯 <b>Take Profits:</b>
├ TP1: ${signal.tp1:.4f}
├ TP2: ${signal.tp2:.4f}
├ TP3: ${signal.tp3:.4f}
└ TP4: ${signal.tp4:.4f}

📊 <b>Score:</b> {signal.score}/20
🌊 <b>Confluence:</b> {signal.confluence}
{confidence_emoji} <b>Confidence:</b> {signal.confidence}

💎 <b>Trap Zone:</b> {"✅" if signal.trap_zone else "❌"}
📈 <b>Volume Surge:</b> {"✅" if signal.volume_surge else "❌"}
📍 <b>ATR:</b> {signal.atr:.4f}

⏰ <b>Time:</b> {signal.timestamp}"""

            return self.send_message(message.strip())

        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False

class AlertProcessor:
    def __init__(self, telegram_bot: Optional[TelegramBot] = None):
        self.telegram_bot = telegram_bot
        self.alert_queue = Queue()
        self.is_running = False
        self.processor_thread = None

    def start(self):
        """Start the alert processor"""
        if not self.is_running:
            self.is_running = True
            self.processor_thread = threading.Thread(target=self._process_alerts, daemon=True)
            self.processor_thread.start()
            logger.info("Alert processor started")

    def stop(self):
        """Stop the alert processor"""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)

    def _process_alerts(self):
        """Process alerts from the queue"""
        while self.is_running:
            try:
                if not self.alert_queue.empty():
                    signal = self.alert_queue.get(timeout=1)
                    logger.info(f"Processing alert for {signal.ticker}")
                    
                    if self.telegram_bot:
                        self.telegram_bot.send_alert(signal)
                    
                    self.alert_queue.task_done()
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing alert: {str(e)}")

    def add_alert(self, signal: TradingSignal):
        """Add an alert to the processing queue"""
        self.alert_queue.put(signal)
        logger.info(f"Alert added to queue for {signal.ticker}")

# Flask app
app = Flask(__name__)

# Initialize components
telegram_bot = None
alert_processor = None

def initialize_services():
    """Initialize Telegram bot and alert processor"""
    global telegram_bot, alert_processor
    
    # Get environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id:
        telegram_bot = TelegramBot(bot_token, chat_id)
        logger.info("Telegram bot initialized")
    else:
        logger.warning("Telegram credentials not found in environment variables")
    
    alert_processor = AlertProcessor(telegram_bot)
    alert_processor.start()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook alerts"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        # Parse the trading signal
        signal = TradingSignal(
            action=data.get('action', ''),
            ticker=data.get('ticker', ''),
            price=float(data.get('price', 0)),
            sl=float(data.get('sl', 0)),
            tp1=float(data.get('tp1', 0)),
            tp2=float(data.get('tp2', 0)),
            tp3=float(data.get('tp3', 0)),
            tp4=float(data.get('tp4', 0)),
            confidence=data.get('confidence', 'LOW'),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            atr=float(data.get('atr', 0)),
            volume_surge=data.get('volume_surge', False),
            trap_zone=data.get('trap_zone', False),
            score=float(data.get('score', 0)),
            confluence=float(data.get('confluence', 0))
        )
        
        # Add to processing queue
        if alert_processor:
            alert_processor.add_alert(signal)
        
        return jsonify({"status": "success", "message": "Alert received and queued"}), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": "Invalid JSON format"}), 400
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return jsonify({"error": "Invalid data format"}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({"status": "ok", "message": "Trading alerts service is running"}), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "telegram_bot": telegram_bot is not None,
        "alert_processor": alert_processor is not None and alert_processor.is_running
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        "service": "Trading Alerts Service",
        "status": "running",
        "endpoints": {
            "/webhook": "POST - Receive trading signals",
            "/test": "GET - Test endpoint",
            "/health": "GET - Health check"
        }
    }), 200

if __name__ == '__main__':
    logger.info("Starting Trading Alerts Service...")
    
    # Initialize services
    initialize_services()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

