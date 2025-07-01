
import requests, time
from datetime import datetime
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.trend import EMAIndicator, MACD, SMAIndicator

# ========== CONFIG ==========
FMP_API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571"
TELEGRAM_TOKEN = "7403427584:AAF5FOsZ4w5non_9WFHAN362-76Oe5dVZo0"
TELEGRAM_CHAT_ID = "8006606779"

# Premium forex pairs with high liquidity
ASSETS = {
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD", 
    "USDJPY": "USD/JPY",
    "AUDUSD": "AUD/USD",
    "USDCAD": "USD/CAD",
    "XAUUSD": "Gold",
    "GBPJPY": "GBP/JPY",
    "EURJPY": "EUR/JPY"
}

TF = "15min"  # Higher timeframe for quality
SCAN_INTERVAL = 900  # 15 minutes - no rushing
LOOKBACK = 100  # More data for better analysis
MIN_SIGNAL_STRENGTH = 7  # Only high-quality signals
MAX_DAILY_TRADES = 8
MIN_DAILY_TRADES = 7

# Risk management like institutions
SL_MULTIPLIER = 0.8  # Tight stops
TP_MULTIPLIERS = {
    "premium": 4.0,   # 1:5 RR
    "high": 3.0,      # 1:3.75 RR  
    "medium": 2.5     # 1:3.1 RR
}

trades_today = 0
today_date = datetime.utcnow().date()
last_trade_time = {}  # Prevent overtrading same pair

# ========== INSTITUTIONAL FUNCTIONS ==========

def fetch_data(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-chart/{TF}/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=20)
        
        if response.status_code != 200:
            print(f"[API ERROR] {symbol}: HTTP {response.status_code}")
            return pd.DataFrame()

        data = response.json()  # Add this line here

        if not data or not isinstance(data, list) or len(data) < 50:
            print(f"[API] {symbol}: Insufficient data")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        if 'date' in df.columns:
            df = df.rename(columns={'date': 'datetime'})

        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)

        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=numeric_cols).reset_index(drop=True)

        if len(df) < 50:
            return pd.DataFrame()

        return df[['datetime'] + numeric_cols].copy()

    except Exception as e:
        print(f"[ERROR] {symbol}: {str(e)}")
        return pd.DataFrame()

def calculate_institutional_indicators(df):
    """Advanced multi-timeframe analysis like hedge funds use"""
    if df.empty or len(df) < 50:
        return df

    df = df.copy()

    try:
        # Core momentum indicators
        df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        df['stoch_k'] = StochasticOscillator(df['high'], df['low'], df['close']).stoch()
        df['stoch_d'] = StochasticOscillator(df['high'], df['low'], df['close']).stoch_signal()

        # MACD for trend confirmation
        macd = MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()

        # Multi-timeframe EMAs
        df['ema_8'] = EMAIndicator(df['close'], window=8).ema_indicator()
        df['ema_21'] = EMAIndicator(df['close'], window=21).ema_indicator()
        df['ema_50'] = EMAIndicator(df['close'], window=50).ema_indicator()
        df['ema_200'] = EMAIndicator(df['close'], window=200).ema_indicator()

        # Volatility analysis
        df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        bb = BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_mid'] = bb.bollinger_mavg()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']

        # Volume analysis
        df['vol_sma'] = SMAIndicator(df['volume'], window=20).sma_indicator()
        df['vol_ratio'] = df['volume'] / df['vol_sma']

        # Price action patterns
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - np.maximum(df['open'], df['close'])
        df['lower_shadow'] = np.minimum(df['open'], df['close']) - df['low']
        df['total_range'] = df['high'] - df['low']

        # Market structure & Big Move Detection
        df['higher_high'] = (df['high'] > df['high'].shift(1)) & (df['high'].shift(1) > df['high'].shift(2))
        df['lower_low'] = (df['low'] < df['low'].shift(1)) & (df['low'].shift(1) < df['low'].shift(2))
        df['support'] = df['low'].rolling(20).min()
        df['resistance'] = df['high'].rolling(20).max()

        # Big Move Detection (Institutional breakouts)
        df['price_change_1h'] = df['close'].pct_change(4) * 100  # 4 periods = 1 hour in 15min TF
        df['price_change_4h'] = df['close'].pct_change(16) * 100  # 16 periods = 4 hours
        df['volatility_spike'] = df['atr'] > df['atr'].rolling(20).mean() * 1.5
        df['big_move_up'] = (df['price_change_1h'] > 0.5) & df['volatility_spike'] & (df['vol_ratio'] > 1.8)
        df['big_move_down'] = (df['price_change_1h'] < -0.5) & df['volatility_spike'] & (df['vol_ratio'] > 1.8)

        # Confluence zones - Calculate trend_alignment first
        df['trend_alignment'] = (
            (df['ema_8'] > df['ema_21']) & 
            (df['ema_21'] > df['ema_50']) & 
            (df['ema_50'] > df['ema_200'])
        ).astype(int) - (
            (df['ema_8'] < df['ema_21']) & 
            (df['ema_21'] < df['ema_50']) & 
            (df['ema_50'] < df['ema_200'])
        ).astype(int)

        # Momentum divergence
        df['price_momentum'] = df['close'].pct_change(5) * 100
        df['rsi_momentum'] = df['rsi'].diff(5)

        # Sideways Market Detection (Avoid choppy conditions)
        df['range_bound'] = (df['bb_width'] < df['bb_width'].rolling(20).mean() * 0.7)
        df['low_volatility'] = df['atr'] < df['atr'].rolling(20).mean() * 0.8
        df['sideways_market'] = df['range_bound'] & df['low_volatility']

        # Trending Market Confirmation
        df['strong_trend'] = (abs(df['trend_alignment']) == 1) & ~df['sideways_market'] & (df['bb_width'] > df['bb_width'].rolling(10).mean())

        # Institutional flow indicators
        df['smart_money'] = (df['vol_ratio'] > 1.5) & (df['body_size'] > df['total_range'] * 0.7)
        df['accumulation'] = (df['close'] > df['open']) & (df['vol_ratio'] > 1.3) & (df['close'] > df['ema_21'])
        df['distribution'] = (df['close'] < df['open']) & (df['vol_ratio'] > 1.3) & (df['close'] < df['ema_21'])

    except Exception as e:
        print(f"[INDICATOR ERROR]: {e}")

    return df

def institutional_signal_score(df):
    """Hedge fund grade signal scoring system"""
    if df.empty or len(df) < 20:
        return 0, None, None

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    score = 0
    signals = []
    direction = None

    try:
        # 1. Trend Alignment (30% weight)
        trend_score = 0
        if last['trend_alignment'] == 1:  # Strong uptrend
            trend_score = 3
            direction = "BUY"
        elif last['trend_alignment'] == -1:  # Strong downtrend
            trend_score = 3
            direction = "SELL"
        elif abs(last['trend_alignment']) == 0:  # Neutral/ranging
            trend_score = 0

        score += trend_score
        if trend_score > 0:
            signals.append(f"Trend: {trend_score}/3")

        # 2. Momentum Confluence (25% weight)
        momentum_score = 0

        # RSI conditions
        if 25 <= last['rsi'] <= 35 and direction == "BUY":
            momentum_score += 2
        elif 65 <= last['rsi'] <= 75 and direction == "SELL":
            momentum_score += 2
        elif last['rsi'] < 30 and direction == "BUY":
            momentum_score += 1
        elif last['rsi'] > 70 and direction == "SELL":
            momentum_score += 1

        # MACD confirmation
        if direction == "BUY" and last['macd'] > last['macd_signal'] and last['macd_histogram'] > prev['macd_histogram']:
            momentum_score += 1
        elif direction == "SELL" and last['macd'] < last['macd_signal'] and last['macd_histogram'] < prev['macd_histogram']:
            momentum_score += 1

        # Stochastic confirmation
        if direction == "BUY" and last['stoch_k'] < 20 and last['stoch_k'] > last['stoch_d']:
            momentum_score += 1
        elif direction == "SELL" and last['stoch_k'] > 80 and last['stoch_k'] < last['stoch_d']:
            momentum_score += 1

        score += momentum_score
        if momentum_score > 0:
            signals.append(f"Momentum: {momentum_score}/4")

        # 3. Volume & Flow Analysis (20% weight)
        volume_score = 0

        if last['smart_money']:
            volume_score += 2
            signals.append("Smart Money Flow")

        if direction == "BUY" and last['accumulation']:
            volume_score += 1
        elif direction == "SELL" and last['distribution']:
            volume_score += 1

        if last['vol_ratio'] > 2.0:
            volume_score += 1

        score += volume_score

        # 4. Price Action Quality (15% weight)
        pa_score = 0

        # Strong directional candle
        if last['body_size'] > last['total_range'] * 0.6:
            pa_score += 1

        # Rejection patterns
        if direction == "BUY" and last['lower_shadow'] > last['body_size'] * 1.5:
            pa_score += 1
        elif direction == "SELL" and last['upper_shadow'] > last['body_size'] * 1.5:
            pa_score += 1

        # Key level interaction
        if direction == "BUY" and last['low'] <= last['support'] * 1.001:
            pa_score += 1
        elif direction == "SELL" and last['high'] >= last['resistance'] * 0.999:
            pa_score += 1

        score += pa_score
        if pa_score > 0:
            signals.append(f"Price Action: {pa_score}/3")

        # 5. Market Structure & Big Move Bonus (15% weight)
        structure_score = 0

        # Normal structure points
        if direction == "BUY" and last['higher_high']:
            structure_score += 1
        elif direction == "SELL" and last['lower_low']:
            structure_score += 1

        # BIG MOVE DETECTION - Bonus points for institutional breakouts
        if last['big_move_up'] and direction == "BUY":
            structure_score += 2
            signals.append("🚀 BIG MOVE UP")
        elif last['big_move_down'] and direction == "SELL":
            structure_score += 2
            signals.append("🚀 BIG MOVE DOWN")

        # Strong trending market bonus
        if last['strong_trend']:
            structure_score += 1
            signals.append("💪 Strong Trend")

        score += structure_score

        # SIDEWAYS MARKET PENALTY - Reduce score in choppy conditions
        if last['sideways_market']:
            score -= 2
            signals.append("⚠️ Sideways Market")
            print(f"[SIDEWAYS DETECTED] Reducing signal strength")

    except Exception as e:
        print(f"[SCORING ERROR]: {e}")

    return score, direction, signals

def check_trade_quality(symbol, df):
    """Institutional grade trade validation"""
    if df.empty or len(df) < 50:
        return None

    # Prevent overtrading same pair
    now = datetime.utcnow()
    if symbol in last_trade_time:
        time_diff = (now - last_trade_time[symbol]).total_seconds() / 3600
        if time_diff < 2:  # Minimum 2 hours between trades on same pair
            return None

    try:
        last_row = df.iloc[-1]
        score, direction, signals = institutional_signal_score(df)

        # Only take premium quality signals
        if score < MIN_SIGNAL_STRENGTH or not direction:
            return None

        entry_price = last_row['close']
        atr_value = last_row['atr']

        # Determine risk level based on score
        if score >= 10:
            risk_level = "premium"
        elif score >= 8:
            risk_level = "high"
        else:
            risk_level = "medium"

        # Calculate precise entry/exit levels
        if direction == "BUY":
            sl_price = entry_price - (atr_value * SL_MULTIPLIER)
            tp_price = entry_price + (atr_value * TP_MULTIPLIERS[risk_level])
        else:
            sl_price = entry_price + (atr_value * SL_MULTIPLIER)
            tp_price = entry_price - (atr_value * TP_MULTIPLIERS[risk_level])

        # Risk-reward validation
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0

        if rr_ratio < 2.5:  # Minimum 1:2.5 RR
            return None

        return {
            'entry': entry_price,
            'sl': sl_price,
            'tp': tp_price,
            'score': score,
            'risk_level': risk_level,
            'direction': direction,
            'rr_ratio': rr_ratio,
            'signals': signals,
            'atr': atr_value
        }

    except Exception as e:
        print(f"[QUALITY CHECK ERROR]: {e}")
        return None

def send_premium_signal(asset, signal_data):
    try:
        signal_details = " | ".join(signal_data['signals'])

        # Determine if this is a big move alert
        is_big_move = "🚀 BIG MOVE" in signal_details
        alert_type = "🚨 BIG MOVE ALERT" if is_big_move else "🏆 PREMIUM SIGNAL"

        msg = f"""🚨 *{alert_type}*

💎 *Asset:* {asset}
📈 *Direction:* {signal_data['direction']}
🎯 *Entry:* {signal_data['entry']:.5f}
🛑 *Stop Loss:* {signal_data['sl']:.5f}
🎯 *Take Profit:* {signal_data['tp']:.5f}

📊 *Quality Score:* {signal_data['score']}/12
🔥 *Risk Level:* {signal_data['risk_level'].upper()}
💰 *Risk:Reward:* 1:{signal_data['rr_ratio']:.1f}
⚡ *ATR:* {signal_data['atr']:.5f}

🧠 *Confluence:* {signal_details}

🕒 *Time:* {datetime.utcnow().strftime('%H:%M:%S')} UTC
📈 *Timeframe:* 15M

⚠️ *INSTITUTIONAL GRADE SETUP*
"""

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": msg, 
            "parse_mode": "Markdown"
        }

        response = requests.post(url, data=payload, timeout=10)
        return response.status_code == 200

    except Exception as e:
        print(f"[TELEGRAM ERROR]: {e}")
        return False

# ========== MAIN EXECUTION ==========

print(f"🏆 INSTITUTIONAL TRADING SYSTEM")
print(f"📊 Monitoring {len(ASSETS)} premium pairs")
print(f"⏰ Timeframe: {TF}")
print(f"🎯 Daily target: {MIN_DAILY_TRADES}-{MAX_DAILY_TRADES} quality trades")
print(f"📈 Minimum signal strength: {MIN_SIGNAL_STRENGTH}/12")

# Test Telegram connection
try:
    test_msg = "🤖 Trading System ONLINE\n\n✅ All systems operational\n🔍 Scanning for institutional setups..."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": test_msg}
    response = requests.post(url, data=payload, timeout=10)
    if response.status_code == 200:
        print("✅ Telegram alerts: CONNECTED")
    else:
        print("❌ Telegram alerts: FAILED")
except:
    print("❌ Telegram alerts: ERROR")

print("-" * 60)

while True:
    try:
        now = datetime.utcnow()

        # Reset daily counter
        if now.date() != today_date:
            trades_today = 0
            today_date = now.date()
            last_trade_time.clear()
            print(f"📅 New trading session: {today_date}")

        # Skip if daily target reached
        if trades_today >= MAX_DAILY_TRADES:
            print(f"✅ Daily target reached ({trades_today}/{MAX_DAILY_TRADES})")
            time.sleep(SCAN_INTERVAL)
            continue

        print(f"\n🔍 Market Analysis @ {now.strftime('%H:%M:%S')} UTC")
        premium_signals = []

        for symbol, asset_name in ASSETS.items():
            try:
                print(f"📡 Analyzing {asset_name}...", end=" ")

                df = fetch_data(symbol)
                if df.empty:
                    print("❌ No data")
                    continue

                df_analysis = calculate_institutional_indicators(df[-LOOKBACK:])
                signal = check_trade_quality(symbol, df_analysis)

                if signal:
                    print(f"🏆 PREMIUM SIGNAL!")
                    premium_signals.append((symbol, asset_name, signal))

                    if send_premium_signal(asset_name, signal):
                        trades_today += 1
                        last_trade_time[symbol] = now
                        print(f"   ✅ Signal sent | Score: {signal['score']}/12 | RR: 1:{signal['rr_ratio']:.1f}")
                else:
                    print("⏳ No quality setup")

                time.sleep(2)  # Respect API limits

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                continue

        # Session Summary
        if premium_signals:
            print(f"\n🎊 {len(premium_signals)} INSTITUTIONAL SIGNALS FOUND!")
            for symbol, asset, signal in premium_signals:
                print(f"   🏆 {asset}: {signal['direction']} | Score: {signal['score']}/12")
        else:
            print(f"\n⏳ No institutional grade setups this scan")

        print(f"📈 Today's trades: {trades_today}/{MIN_DAILY_TRADES}-{MAX_DAILY_TRADES}")
        print(f"⏱️ Next analysis in {SCAN_INTERVAL//60} minutes...")
        print("-" * 60)

        time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print("\n👋 Trading system stopped")
        break
    except Exception as e:
        print(f"\n🚨 System error: {str(e)}")
        print("🔄 Restarting in 60 seconds...")
        time.sleep(60)

