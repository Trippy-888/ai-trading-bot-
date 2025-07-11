import os
import json
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Telegram Bot Configuration
# Replace these with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = "7962012341:AAG1XJITypeyUkvo-K_2cM4cOqLa4c-Lx3s"
TELEGRAM_CHAT_ID = "8006606779"

def send_telegram_message(message):
    """Send message to Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Telegram message sent successfully: {response.status_code}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {str(e)}")
        return False

def format_trading_message(data):
    """Format trading signal data into beautiful Telegram message"""
    try:
        action = data.get('action', 'UNKNOWN').upper()
        ticker = data.get('ticker', 'UNKNOWN')
        price = data.get('price', 'N/A')
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
        
        # Extract additional data if available
        sl = data.get('sl', 'N/A')
        tp1 = data.get('tp1', 'N/A')
        tp2 = data.get('tp2', 'N/A')
        tp3 = data.get('tp3', 'N/A')
        tp4 = data.get('tp4', 'N/A')
        atr = data.get('atr', 'N/A')
        score = data.get('score', 'N/A')
        confluence = data.get('confluence', 'N/A')
        volume_surge = data.get('volume_surge', 'false').lower() == 'true'
        trap_zone = data.get('trap_zone', 'false').lower() == 'true'
        
        # Determine signal emoji and color
        signal_emoji = "🚀" if action == "BUY" else "📉"
        direction_emoji = "📈" if action == "BUY" else "📉"
        
        # Calculate confidence level
        try:
            score_int = int(score) if score != 'N/A' else 0
            if score_int >= 16:
                confidence = "ULTRA HIGH"
                confidence_emoji = "🔥"
            elif score_int >= 12:
                confidence = "HIGH"
                confidence_emoji = "💎"
            elif score_int >= 8:
                confidence = "MEDIUM"
                confidence_emoji = "⚡"
            else:
                confidence = "LOW"
                confidence_emoji = "⚠️"
        except:
            confidence = "UNKNOWN"
            confidence_emoji = "❓"
        
        # Build the message (simplified without HTML formatting)
        message = f"""🚨 SMC AI SNIPER {action} SIGNAL 🚨

{signal_emoji} Ticker: {ticker}
{direction_emoji} Entry: ${price}
🛡️ Stop Loss: ${sl}

🎯 Take Profits:
├ TP1: ${tp1}
├ TP2: ${tp2}
├ TP3: ${tp3}
└ TP4: ${tp4}

📊 Score: {score}/20
🌊 Confluence: {confluence}
{confidence_emoji} Confidence: {confidence}

💎 Trap Zone: {"✅" if trap_zone else "❌"}
📈 Volume Surge: {"✅" if volume_surge else "❌"}
📍 ATR: {atr}

⏰ Time: {timestamp}

Generated by SMC AI Sniper Alert Bot"""
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting message: {str(e)}")
        return f"🚨 TRADING SIGNAL RECEIVED 🚨\n\nAction: {data.get('action', 'UNKNOWN')}\nTicker: {data.get('ticker', 'UNKNOWN')}\nPrice: {data.get('price', 'N/A')}\n\nError formatting full message: {str(e)}"

@app.route('/')
def index():
    """Simple status page"""
    return jsonify({
        'status': 'online',
        'service': 'SMC AI Sniper Alert Bot - TradingView to Telegram Webhook',
        'endpoints': {
            'webhook': '/webhook (POST)',
            'test': '/test (GET)',
            'status': '/status (GET)'
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle TradingView webhook alerts"""
    try:
        # Log the incoming request
        logger.info(f"Webhook received: {request.method} {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Get the JSON data
        if request.is_json:
            data = request.get_json()
        else:
            # Try to parse as JSON string
            raw_data = request.get_data(as_text=True)
            logger.info(f"Raw data: {raw_data}")
            data = json.loads(raw_data)
        
        logger.info(f"Parsed data: {data}")
        
        # Validate required fields
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON format")
        
        if 'action' not in data:
            raise ValueError("Missing 'action' field")
        
        # Format and send the message
        message = format_trading_message(data)
        success = send_telegram_message(message)
        
        if success:
            logger.info("Alert processed successfully")
            return jsonify({
                'status': 'success',
                'message': 'Alert sent to Telegram successfully'
            }), 200
        else:
            logger.error("Failed to send alert to Telegram")
            return jsonify({
                'status': 'error',
                'message': 'Failed to send alert to Telegram'
            }), 500
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid JSON format: {str(e)}'
        }), 400
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/test')
def test():
    """Test endpoint to verify webhook functionality"""
    try:
        # Create test data
        test_data = {
            'action': 'BUY',
            'ticker': 'XAUUSD',
            'price': '2368.25',
            'sl': '2365.00',
            'tp1': '2370.00',
            'tp2': '2373.00',
            'tp3': '2376.00',
            'tp4': '2379.00',
            'atr': '0.0025',
            'score': '16',
            'confluence': '8',
            'volume_surge': 'true',
            'trap_zone': 'false',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Format and send test message
        message = format_trading_message(test_data)
        success = send_telegram_message(message)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Test alert sent to Telegram successfully',
                'data': test_data
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test alert to Telegram'
            }), 500
            
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'bot_configured': TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE",
        'chat_configured': TELEGRAM_CHAT_ID != "YOUR_CHAT_ID_HERE"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
