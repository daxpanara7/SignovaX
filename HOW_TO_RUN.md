# How to Run the Trading Terminal

## Quick Start (3 terminals)

### Terminal 1 — Proxy Server (required for live data)
```bash
cd trading-terminal/proxy-server
npm install
node server.js
# Runs on http://localhost:4000
```

### Terminal 2 — Frontend
```bash
cd trading-terminal/frontend
npm install   # already done if you followed setup
npm start
# Opens http://localhost:3000
```

### Terminal 3 — Python Backend (optional — for full SMC analysis)
```bash
cd trading-terminal/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
# Runs on http://localhost:8000
```

## What works without the Python backend
- Live BTC/ETH/SOL prices from Binance (no API key needed)
- Real OHLCV candles (1m, 5m, 15m, 1h, 4h, 1d)
- Live signal engine (BUY/SELL/HOLD with EMA + RSI + ATR)
- CoinGecko price fallback
- Full trading terminal UI

## Test the proxy server
```bash
# Health
curl http://localhost:4000/health

# Live BTC price
curl "http://localhost:4000/api/binance/price?symbol=BTCUSDT"

# 15m candles
curl "http://localhost:4000/api/binance/candles?symbol=BTCUSDT&interval=15m&limit=10"

# Live signal
curl "http://localhost:4000/api/signals/live?symbol=BTCUSDT&interval=15m"

# ETH signal on 1h
curl "http://localhost:4000/api/signals/live?symbol=ETHUSDT&interval=1h"
```

## Environment Variables

### proxy-server/.env
```
PORT=4000
COINGECKO_API_KEY=   # optional free key from coingecko.com/en/api
APIFY_API_TOKEN=     # optional paid Apify key
```

### frontend/.env
```
REACT_APP_PROXY_URL=http://localhost:4000
REACT_APP_BACKEND_URL=http://localhost:8000
```
