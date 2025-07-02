def boost_confluence(symbol, direction, api_key):
    # Mock version — always return True for testing
    return True

def adjust_filters_based_on_volatility(df):
    last = df.iloc[-1]
    avg_atr = df['atr'].rolling(20).mean().iloc[-1]
    offset = 0
    rr_min = 2.0

    if last['atr'] > avg_atr * 1.5:
        offset += 1
        rr_min = 1.8
    elif last['atr'] < avg_atr * 0.8:
        offset -= 1
        rr_min = 2.2

    return {"score_offset": offset, "rr_min": rr_min}

def ai_adjust_filters_based_on_context(df):
    last = df.iloc[-1]
    result = {"accept_median_signals": False, "skip_signal": False}

    if last['sideways_market']:
        result['skip_signal'] = True

    if last.get("big_move_up", False) or last.get("big_move_down", False):
        result['accept_median_signals'] = True

    return result

def detect_range_volume_trap(df):
    recent = df[-6:]
    if recent['bb_width'].mean() < df['bb_width'].rolling(20).mean().iloc[-1] * 0.75:
        if recent['vol_ratio'].mean() > 1.5:
            return True
    return False
