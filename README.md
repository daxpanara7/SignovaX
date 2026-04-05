# SMC Trading Terminal

Real-time crypto trading terminal with Smart Money Concepts (SMC) analysis.

## Features
- Live prices via Binance WebSocket (no API key needed)
- Real-time candlestick charts with TradingView Lightweight Charts
- BUY/SELL/HOLD signals with EMA, RSI, ATR analysis
- Order Blocks, FVG, Liquidity Zone overlays
- Multi-symbol watchlist (BTC, ETH, SOL, BNB, XRP)

## Tech Stack
- React 18 + Zustand + TailwindCSS
- Binance WebSocket API (public, no key required)
- TradingView Lightweight Charts v5
- Optional: Node.js proxy for server-side signal engine

## Run Locally

```bash
cd frontend
npm install
npm start
# Opens at http://localhost:3001
```

Optional signal proxy:
```bash
cd proxy-server
npm install
node server.js
# Runs at http://localhost:4000
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `REACT_APP_PROXY_URL` | No | Proxy server URL for signal engine. Leave empty to use client-side signals |

## Architecture

```
Browser
  ├── Binance WebSocket (wss://stream.binance.com)
  │     ├── miniTicker → live prices (watchlist, header)
  │     └── kline      → real-time candle updates (chart)
  └── Binance REST API (https://api.binance.com)
        └── /api/v3/klines → historical candles on load
```
