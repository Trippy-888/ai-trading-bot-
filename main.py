
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

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            logger.error(f"Response status: {getattr(response, 'status_code', 'N/A')}")
            logger.error(f"Response text: {getattr(response, 'text', 'N/A')}")
            return False

    def send_alert(self, signal: TradingSignal) -> bool:
        """Send formatted trading alert to Telegram"""
        try:
            # Determine confidence emoji
            confidence_emoji = "🔥" if signal.confidence == "HIGH" else "⚡" if signal.confidence == "MEDIUM" else "⚠️"
            
            # Format message
            message = f"""
🚨 <b>ULTRA PRECISION SMC {signal.action} SIGNAL</b> 🚨

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

⏰ <b>Time:</b> {signal.timestamp}
"""

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
        logger.info("Alert processor stopped")

    def add_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Add alert to processing queue"""
        try:
            self.alert_queue.put(alert_data, timeout=1)
            logger.info(f"Alert added to queue: {alert_data.get('ticker', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to add alert to queue: {str(e)}")
            return False

    def _process_alerts(self):
        """Process alerts from queue"""
        while self.is_running:
            try:
                if not self.alert_queue.empty():
                    alert_data = self.alert_queue.get(timeout=1)
                    self._handle_alert(alert_data)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing alert: {str(e)}")
                time.sleep(1)

    def _handle_alert(self, alert_data: Dict[str, Any]):
        """Handle individual alert"""
        try:
            # Parse alert data
            signal = TradingSignal(
                action=alert_data.get('action', ''),
                ticker=alert_data.get('ticker', ''),
                price=float(alert_data.get('price', 0)),
                sl=float(alert_data.get('sl', 0)),
                tp1=float(alert_data.get('tp1', 0)),
                tp2=float(alert_data.get('tp2', 0)),
                tp3=float(alert_data.get('tp3', 0)),
                tp4=float(alert_data.get('tp4', 0)),
                confidence=self._determine_confidence(float(alert_data.get('score', 0))),
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                atr=float(alert_data.get('atr', 0)),
                volume_surge=alert_data.get('volume_surge', 'false').lower() == 'true',
                trap_zone=alert_data.get('trap_zone', 'false').lower() == 'true',
                score=float(alert_data.get('score', 0)),
                confluence=float(alert_data.get('confluence', 0))
            )

            # Log the signal
            logger.info(f"Processing {signal.action} signal for {signal.ticker} at ${signal.price}")

            # Send to Telegram if bot is configured
            if self.telegram_bot:
                success = self.telegram_bot.send_alert(signal)
                if success:
                    logger.info(f"Alert sent successfully for {signal.ticker}")
                else:
                    logger.error(f"Failed to send alert for {signal.ticker}")

            # Store to file
            self._store_signal(signal)

        except Exception as e:
            logger.error(f"Error handling alert: {str(e)}")

    def _determine_confidence(self, score: float) -> str:
        """Determine confidence level based on score"""
        if score >= 15.0:
            return "HIGH"
        elif score >= 12.0:
            return "MEDIUM"
        else:
            return "LOW"

    def _store_signal(self, signal: TradingSignal):
        """Store signal to JSON file"""
        try:
            # Create signals directory if it doesn't exist
            os.makedirs('signals', exist_ok=True)
            
            # Prepare signal data
            signal_data = {
                'timestamp': signal.timestamp,
                'action': signal.action,
                'ticker': signal.ticker,
                'price': signal.price,
                'sl': signal.sl,
                'tp1': signal.tp1,
                'tp2': signal.tp2,
                'tp3': signal.tp3,
                'tp4': signal.tp4,
                'confidence': signal.confidence,
                'atr': signal.atr,
                'volume_surge': signal.volume_surge,
                'trap_zone': signal.trap_zone,
                'score': signal.score,
                'confluence': signal.confluence
            }

            # Save to daily file
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f'signals/signals_{date_str}.json'

            # Load existing data or create new
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
            else:
                data = []

            # Add new signal
            data.append(signal_data)

            # Save back to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Signal stored to {filename}")

        except Exception as e:
            logger.error(f"Failed to store signal: {str(e)}")

# Initialize Flask app
app = Flask(__name__)

# Initialize components
telegram_bot = None
alert_processor = None

def initialize_telegram():
    """Initialize Telegram bot if credentials are available"""
    global telegram_bot
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id and bot_token.strip() and chat_id.strip():
        telegram_bot = TelegramBot(bot_token, chat_id)
        logger.info("✅ Telegram bot initialized successfully")
    else:
        logger.info("ℹ️ Telegram credentials not configured. Telegram notifications disabled. (This is optional)")

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Ultra Precision SMC Alert Server',
        'timestamp': datetime.now().isoformat(),
        'telegram_enabled': telegram_bot is not None
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for TradingView alerts"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        logger.info(f"Received webhook data: {data}")

        # Validate required fields
        required_fields = ['action', 'ticker', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Add alert to processor
        if alert_processor:
            success = alert_processor.add_alert(data)
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Alert received and queued for processing',
                    'ticker': data.get('ticker'),
                    'action': data.get('action')
                })
            else:
                return jsonify({'error': 'Failed to queue alert'}), 500
        else:
            return jsonify({'error': 'Alert processor not initialized'}), 500

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['POST', 'GET'])
def test_alert():
    """Test endpoint for sending sample alerts"""
    try:
        # If GET request, return HTML page with test button
        if request.method == 'GET':
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>Test Alert</title></head>
            <body>
                <h2>🚀 Ultra Precision SMC Test Alert</h2>
                <button onclick="sendTest()">Send Test Alert to Telegram</button>
                <div id="result"></div>
                <script>
                    function sendTest() {
                        fetch('/test', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('result').innerHTML = 
                                '<p style="color:green">✅ ' + data.message + '</p>';
                        })
                        .catch(error => {
                            document.getElementById('result').innerHTML = 
                                '<p style="color:red">❌ Error: ' + error + '</p>';
                        });
                    }
                </script>
            </body>
            </html>
            '''
        
        sample_data = {
            'action': 'BUY',
            'ticker': 'EURUSD',
            'price': 1.0850,
            'sl': 1.0820,
            'tp1': 1.0880,
            'tp2': 1.0910,
            'tp3': 1.0940,
            'tp4': 1.0970,
            'atr': 0.0025,
            'score': 16.5,
            'confluence': 8.5,
            'volume_surge': 'true',
            'trap_zone': 'true'
        }

        if alert_processor:
            success = alert_processor.add_alert(sample_data)
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Test alert sent successfully'
                })
            else:
                return jsonify({'error': 'Failed to send test alert'}), 500
        else:
            return jsonify({'error': 'Alert processor not initialized'}), 500

    except Exception as e:
        logger.error(f"Test alert error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/signals', methods=['GET'])
def get_signals():
    """Get recent signals"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        filename = f'signals/signals_{date_str}.json'
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify([])

    except Exception as e:
        logger.error(f"Error retrieving signals: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Initialize Telegram bot
        initialize_telegram()
        
        # Initialize and start alert processor
        alert_processor = AlertProcessor(telegram_bot)
        alert_processor.start()
        
        logger.info("🚀 Ultra Precision SMC Alert Server starting...")
        # Get port configuration
        port = int(os.getenv('PORT', 5000))
        
        logger.info("📡 Webhook endpoint: /webhook")
        logger.info("🧪 Test endpoint: /test")
        logger.info("📊 Signals endpoint: /signals")
        logger.info("🔍 Health check endpoint: /")
        logger.info(f"🌐 Server will run on: http://0.0.0.0:{port}")
        logger.info("✅ All systems ready!")
        
        # Send startup notification to Telegram
        if telegram_bot:
            startup_message = """
🚀 <b>ULTRA PRECISION SMC SYSTEM STARTED</b> 🚀

✅ <b>Status:</b> Online and Scanning
📡 <b>Webhook:</b> Ready for TradingView alerts
🎯 <b>Monitoring:</b> Market signals active
⏰ <b>Started:</b> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """

<i>System is now actively scanning for high-precision trading opportunities...</i>
"""
            telegram_bot.send_message(startup_message.strip())
            logger.info("📱 Startup notification sent to Telegram")
        
        # Start Flask app
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        if alert_processor:
            alert_processor.stop()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        if alert_processor:
            alert_processor.stop()
