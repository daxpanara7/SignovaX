import requests
import json
from datetime import datetime, timezone

# Fetch 300 live candles from Binance
raw = requests.get(
    'https://api.binance.com/api/v3/klines',
    params={'symbol': 'BTCUSDT', 'interval': '15m', 'limit': 300}
).json()

from datetime import datetime, timezone

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
    json={'candles': candles, 'atr_sl_multiplier': 1.5}
)

print("Status:", resp.status_code)
print("Raw:", resp.text[:2000])

if resp.text:
    print(json.dumps(resp.json(), indent=2))
