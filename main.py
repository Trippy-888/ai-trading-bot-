#🧠 OBLIVION ENGINE – FINAL UPGRADE

#✨ Market Memory + Fractal Trap Engine + Ghost Liquidity Detector

import requests import json import time import statistics import logging from datetime import datetime

#=== CONFIG ===

ASSETS = ["XAU/USD", "SILVER", "GBP/USD", "GBP/JPY", "EUR/USD", "USD/JPY", "US30", "CRUDE OIL"] FMP_API_KEY = "54kgcuCJpN9Yfwqb50Nx7e65UhuX1571" TELEGRAM_TOKEN = "7403427584:AAF5F0sZ4w5non_" TELEGRAM_CHAT_ID = "8006606779" TIMEFRAME = "1min" RR_THRESHOLD = 2.2 DELAY = 60 SCORE_MIN = 85 GHOST_ZONE_DECAY = 0.3

#=== MEMORY ===

pain_zones = {} pattern_memory = {} ob_cache = {} kill_zones = set()

logging.basicConfig(filename="oblivion_log.txt", level=logging.INFO)

#=== FETCH DATA ===

def get_data(symbol): try: symbol = symbol.replace("/", "") url = f"https://financialmodelingprep.com/api/v3/historical-chart/{TIMEFRAME}/{symbol}?apikey={FMP_API_KEY}" res = requests.get(url, timeout=10) return res.json()[:15] except Exception as e: logging.error(f"Data error: {symbol}: {e}") return []

#=== TRAP FILTERS ===

def trap_rejection(candles): try: body = abs(float(candles[0]['close']) - float(candles[0]['open'])) wick = float(candles[0]['high']) - float(candles[0]['low']) return (wick / (body + 0.001)) > 3 except: return False

def expansion_start(candles): try: r1 = abs(float(candles[1]['close']) - float(candles[1]['open'])) r0 = abs(float(candles[0]['close']) - float(candles[0]['open'])) return r0 > r1 * 1.6 except: return False

#=== MEMORY AI ===

def learn_pattern(asset, rr, score): memory = pattern_memory.get(asset, []) memory.append({"rr": rr, "score": score}) if len(memory) > 50: memory.pop(0) pattern_memory[asset] = memory

def is_pain_zone(asset, price): zones = pain_zones.get(asset, []) return any(abs(price - z) < 0.3 for z in zones)

def mark_pain(asset, price): pain_zones.setdefault(asset, []).append(price)

#=== ORDER BLOCK + GHOST ZONE ===

def detect_orderblock(c): try: last3 = c[2:5] body_sizes = [abs(float(cand['close']) - float(cand['open'])) for cand in last3] if statistics.mean(body_sizes) < 0.2: return float(last3[0]['open']) except: return None

def decay_ob_zone(asset): zones = ob_cache.get(asset, []) new_zones = [z * (1 - GHOST_ZONE_DECAY) for z in zones if z > 0.2] ob_cache[asset] = new_zones

#=== RR CALC ===

def calc_rr(c): entry = float(c[0]['close']) sl = float(c[0]['low']) if entry > float(c[0]['open']) else float(c[0]['high']) tp = entry + (entry - sl) * RR_THRESHOLD rr = abs(tp - entry) / abs(entry - sl) return rr, sl, tp, entry > float(c[0]['open'])

#=== SCORE ===

def score_pattern(c): try: vols = [abs(float(c[i]['high']) - float(c[i]['low'])) for i in range(3)] std = statistics.stdev(vols) if len(vols) > 2 else 0 return 90 if std > 0.3 else 75 except: return 60

#=== TELEGRAM ===

def send_alert(msg): try: url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage" data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"} requests.post(url, data=data) except Exception as e: logging.error(f"Telegram Fail: {e}")

#=== TRADE EVAL ===

def evaluate(asset): c = get_data(asset) if len(c) < 5: return price = float(c[0]['close'])

rr, sl, tp, is_long = calc_rr(c)
score = score_pattern(c)
ghost = detect_orderblock(c)

if ghost:
    ob_cache.setdefault(asset, []).append(ghost)

if any([
    is_pain_zone(asset, price),
    rr < RR_THRESHOLD,
    score < SCORE_MIN,
    not trap_rejection(c),
    not expansion_start(c)
]):
    mark_pain(asset, price)
    return

learn_pattern(asset, rr, score)
decay_ob_zone(asset)

msg = f"🔥 *OBLIVION SIGNAL* 🔥\nAsset: {asset}\nEntry: {price}\nSL: {sl}\nTP: {tp}\nRR: {rr:.2f}\nScore: {score}\nTime: {datetime.utcnow()} UTC"
send_alert(msg)
logging.info(msg)

#=== LOOP ===

while True: for asset in ASSETS: try: evaluate(asset) except Exception as e: logging.error(f"Eval fail {asset}: {e}") time.sleep(DELAY)
