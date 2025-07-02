from datetime import datetime

def session_allows_entry():
    now = datetime.utcnow()
    hour = now.hour
    return (6 <= hour <= 20)  # Allow entries during London + NY sessions

def detect_revenge_trap(candles):
    if len(candles) < 5:
        return False

    bearish_engulf = candles[-2]['close'] < candles[-2]['open'] and candles[-1]['close'] < candles[-1]['open'] and candles[-1]['close'] < candles[-2]['close']
    bullish_engulf = candles[-2]['close'] > candles[-2]['open'] and candles[-1]['close'] > candles[-1]['open'] and candles[-1]['close'] > candles[-2]['close']

    return bearish_engulf or bullish_engulf
