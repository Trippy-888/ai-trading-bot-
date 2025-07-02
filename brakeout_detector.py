#breakout_detector.py

import pandas as pd

#=== Breakout Detection Module ===

def detect_breakout(df): if df.empty or len(df) < 20: return False

last = df.iloc[-1]
prev = df.iloc[-2]

# Detect if price has broken above resistance or below support with strong body
breakout_up = last['close'] > df['resistance'].iloc[-2] * 1.002 and last['body_size'] > last['total_range'] * 0.6
breakout_down = last['close'] < df['support'].iloc[-2] * 0.998 and last['body_size'] > last['total_range'] * 0.6

return breakout_up or breakout_down

def detect_false_breakout(df): if df.empty or len(df) < 20: return False

last = df.iloc[-1]
prev = df.iloc[-2]

# Wick-only breakout reversal (false breakout)
false_up = last['high'] > df['resistance'].iloc[-2] and last['close'] < prev['close']
false_down = last['low'] < df['support'].iloc[-2] and last['close'] > prev['close']

return false_up or false_down

def confirm_breakout_strength(df): if df.empty or len(df) < 20: return 0

last = df.iloc[-1]

# Strength = volume + candle size + volatility alignment
strength = 0
if last['vol_ratio'] > 1.5:
    strength += 1
if last['body_size'] > last['total_range'] * 0.5:
    strength += 1
if last['volatility_spike']:
    strength += 1
if last['strong_trend']:
    strength += 1

return strength
