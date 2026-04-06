"""
Run this to get a ready-to-paste payload for http://localhost:8000/docs
"""
import requests
import json
from datetime import datetime, timezone

raw = requests.get(
    'https://api.binance.com/api/v3/klines',
    params={'symbol': 'BTCUSDT', 'interval': '15m', 'limit': 300}
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

payload = {'candles': candles, 'atr_sl_multiplier': 1.5}

# Save to file so you can open it
with open('ml/swagger_payload.json', 'w') as f:
    json.dump(payload, f, indent=2)

print("Payload saved to ml/swagger_payload.json")
print("Open that file, copy all contents, paste into /docs > POST /predict > Try it out > Request body")
