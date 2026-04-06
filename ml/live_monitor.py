"""
Live signal monitor — prints a new signal every 30 seconds
Run: python3 ml/live_monitor.py
"""
import requests
import json
import time
from datetime import datetime, timezone

SYMBOL   = "BTCUSDT"
INTERVAL = "15m"
INTERVAL_SECS = 30

def fetch_signal():
    raw = requests.get(
        'https://api.binance.com/api/v3/klines',
        params={'symbol': SYMBOL, 'interval': INTERVAL, 'limit': 300},
        timeout=10
    ).json()

    candles = [
        {
            'open_time': datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).isoformat(),
            'open':   float(k[1]),
            'high':   float(k[2]),
            'low':    float(k[3]),
            'close':  float(k[4]),
            'volume': float(k[5]),
        }
        for k in raw
    ]

    resp = requests.post(
        'http://localhost:8000/predict',
        json={'candles': candles, 'atr_sl_multiplier': 1.5},
        timeout=15
    )
    return resp.json()

def color(signal):
    return {'BUY': '\033[92m', 'SELL': '\033[91m', 'HOLD': '\033[93m'}.get(signal, '')

RESET = '\033[0m'

print(f"SignovaX Live Monitor — {SYMBOL} {INTERVAL} — refreshing every {INTERVAL_SECS}s")
print("Press CTRL+C to stop\n")

while True:
    try:
        s = fetch_signal()
        sig  = s['signal']
        conf = s['confidence']
        c    = color(sig)
        high = ' ★ HIGH CONFIDENCE' if conf >= 75 and sig != 'HOLD' else ''

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"{c}{sig}{RESET} | Conf: {conf}% | "
              f"Entry: {s['entry']} | SL: {s['stop_loss']} | TP: {s['target']} | "
              f"RR: 1:{s['rr_ratio']} | XGB:{s['xgb_pred']} RF:{s['rf_pred']} SMC:{s['smc_pred']}"
              f"{c}{high}{RESET}")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")

    time.sleep(INTERVAL_SECS)
