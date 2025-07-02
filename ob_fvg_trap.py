import pandas as pd

def detect_ob_fvg_trap(df):
    df = df.copy()
    df['bullish_ob'] = False
    df['bearish_ob'] = False
    df['fvg_up'] = False
    df['fvg_down'] = False
    df['trap_buy'] = False
    df['trap_sell'] = False

    for i in range(2, len(df)):
        # Bullish Order Block (OB)
        if df['close'].iloc[i - 2] < df['open'].iloc[i - 2] and df['close'].iloc[i - 1] > df['open'].iloc[i - 1]:
            if df['low'].iloc[i - 2] < df['low'].iloc[i - 1]:
                df.loc[i, 'bullish_ob'] = True

        # Bearish Order Block (OB)
        if df['close'].iloc[i - 2] > df['open'].iloc[i - 2] and df['close'].iloc[i - 1] < df['open'].iloc[i - 1]:
            if df['high'].iloc[i - 2] > df['high'].iloc[i - 1]:
                df.loc[i, 'bearish_ob'] = True

        # Fair Value Gap (FVG) Up
        if df['low'].iloc[i - 1] > df['high'].iloc[i - 2] and df['close'].iloc[i] > df['open'].iloc[i]:
            df.loc[i, 'fvg_up'] = True

        # Fair Value Gap (FVG) Down
        if df['high'].iloc[i - 1] < df['low'].iloc[i - 2] and df['close'].iloc[i] < df['open'].iloc[i]:
            df.loc[i, 'fvg_down'] = True

        # Trap buy: strong bullish candle followed by full bearish engulfing
        if df['close'].iloc[i - 1] > df['open'].iloc[i - 1] and df['close'].iloc[i] < df['open'].iloc[i] and df['close'].iloc[i] < df['open'].iloc[i - 1]:
            df.loc[i, 'trap_buy'] = True

        # Trap sell: strong bearish candle followed by full bullish engulfing
        if df['close'].iloc[i - 1] < df['open'].iloc[i - 1] and df['close'].iloc[i] > df['open'].iloc[i] and df['close'].iloc[i] > df['open'].iloc[i - 1]:
            df.loc[i, 'trap_sell'] = True

    return df
