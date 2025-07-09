
import os
import json
from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Your Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7962012341:AAG1XJITypeyUkvo-K_2cM4cOqLa4c-Lx3s"
TELEGRAM_CHAT_ID = "8006606779"

def send_telegram_message(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending telegram message: {e}")
        return False

def format_alert_message(data):
    """Format the alert data into a readable message"""
    action = data.get('action', 'UNKNOWN')
    ticker = data.get('ticker', 'UNKNOWN')
    price = data.get('price', 'N/A')
    sl = data.get('sl', 'N/A')
    tp1 = data.get('tp1', 'N/A')
    score = data.get('score', 'N/A')
    confluence = data.get('confluence', 'N/A')
    
    emoji = "🟢" if action == "BUY" else "🔴"
    
    message = f"""
{emoji} <b>SMC AI SNIPER ALERT</b> {emoji}

<b>Action:</b> {action}
<b>Ticker:</b> {ticker}
<b>Price:</b> {price}
<b>Stop Loss:</b> {sl}
<b>Take Profit:</b> {tp1}
<b>Score:</b> {score}
<b>Confluence:</b> {confluence}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 Trade wisely and manage your risk!
"""
    return message

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for TradingView alerts"""
    try:
        # Get the JSON data from TradingView
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        print(f"Received alert: {data}")
        
        # Format and send the message
        message = format_alert_message(data)
        success = send_telegram_message(message)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Alert sent to Telegram'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send to Telegram'}), 500
            
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the server is running"""
    return jsonify({'status': 'Server is running', 'timestamp': datetime.now().isoformat()})

@app.route('/test-telegram', methods=['GET'])
def test_telegram():
    """Test Telegram integration"""
    test_message = "🤖 Test message from TradingView Alert Bot!\n\nIf you see this, the integration is working correctly."
    success = send_telegram_message(test_message)
    
    if success:
        return jsonify({'status': 'success', 'message': 'Test message sent to Telegram'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send test message'})

if __name__ == '__main__':
    print("Starting TradingView Alert Bot...")
    print("Webhook URL will be: https://your-repl-url.replit.dev/webhook")
    app.run(host='0.0.0.0', port=5000, debug=True)
