def detect_breakout(df):
    if len(df) < 30:
        return False, None

    recent = df.iloc[-2:]
    prev_range = df['high'].rolling(20).max().iloc[-3]
    prev_low = df['low'].rolling(20).min().iloc[-3]

    if recent.iloc[-1]['close'] > prev_range:
        return True, "BULLISH"
    elif recent.iloc[-1]['close'] < prev_low:
        return True, "BEARISH"
    return False, None

def detect_false_breakout(df):
    if len(df) < 25:
        return False

    last = df.iloc[-1]
    prev = df.iloc[-2]
    range_high = df['high'].rolling(20).max().iloc[-3]
    range_low = df['low'].rolling(20).min().iloc[-3]

    if (prev['close'] > range_high and last['close'] < range_high):
        return True  # Bullish trap
    if (prev['close'] < range_low and last['close'] > range_low):
        return True  # Bearish trap

    return False

def confirm_breakout_strength(df):
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    range_ = last['high'] - last['low']
    vol_ratio = last['volume'] / df['volume'].rolling(20).mean().iloc[-1]

    score = 0
    if body > range_ * 0.6:
        score += 1
    if vol_ratio > 1.5:
        score += 1
    if last['close'] > df['ema_8'].iloc[-1] or last['close'] < df['ema_8'].iloc[-1]:
        score += 1
    return score >= 2
