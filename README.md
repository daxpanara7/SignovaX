<<<<<<< HEAD
# SignovaX — AI Crypto Signal Terminal

Real-time crypto trading terminal powered by an ML ensemble (XGBoost + Random Forest + SMC rules) built on Binance data. No API key required.

**Live demo:** [signova-x.vercel.app](https://signova-x.vercel.app)

---

## What it does

- Live prices via Binance WebSocket (BTC, ETH, SOL, BNB, XRP)
- Real-time candlestick charts with TradingView Lightweight Charts
- ML ensemble signals: BUY / SELL / HOLD with confidence score
- Smart Money Concepts: Order Blocks, FVG, BOS, CHOCH, Liquidity Sweeps
- Entry, Stop Loss, Take Profit levels via ATR (min 1:2 RR)
- Only fires signals at 75%+ confidence — fewer trades, higher quality
- Falls back to EMA/RSI client-side if ML API is offline

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Zustand, TailwindCSS, Lightweight Charts |
| ML API | Python 3, FastAPI, XGBoost, Random Forest, scikit-learn |
| Data | Binance REST + WebSocket (public, no key needed) |
| Deploy | Vercel (frontend), local or any server (ML API) |

---

## Prerequisites

Before you start, install these:

- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **Python 3.10+** — [python.org](https://python.org)
- **Homebrew** (Mac only) — needed for OpenMP which XGBoost requires

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install OpenMP (required by XGBoost on Mac — skip this and you'll get a dylib error)
brew install libomp
```

---

## Setup — Step by Step

### 1. Clone the repo

```bash
git clone https://github.com/daxpanara7/SignovaX.git
cd SignovaX
```

### 2. Install ML dependencies

```bash
python3 -m pip install -r ml/requirements.txt
```

> If you see `xgboost.core.XGBoostError: libxgboost.dylib could not be loaded` — run `brew install libomp` first.

### 3. Train the model

This fetches 50,000 candles from Binance, engineers features, trains XGBoost + Random Forest, and saves the model. Takes ~5–10 minutes.

```bash
python3 ml/train.py
```

You'll see output like:
```
Fetching 50000 candles for BTCUSDT 15m...
Training XGBoost...
Training Random Forest...
Win rate: 71.3%
Model saved to models/ensemble.joblib
```

> Only needs to be run once. Re-run it anytime to retrain on fresh data.

### 4. Start the ML API

```bash
python3 ml/api.py
```

You should see:
```
Model loaded.
Uvicorn running on http://0.0.0.0:8000
```

Verify it's working: open [http://localhost:8000/health](http://localhost:8000/health)
```json
{"status": "ok", "model_loaded": true}
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

> If you see `react-scripts: command not found` — you skipped this step.

### 6. Set up environment variables

```bash
cp .env.example .env
```

The `.env` file should contain:
```
PORT=3001
REACT_APP_ML_API_URL=http://localhost:8000
REACT_APP_PROXY_URL=
```

### 7. Start the frontend

```bash
cd frontend
npm start
```

Opens at [http://localhost:3001](http://localhost:3001)

---

## Running Everything (Quick Reference)

Open two terminals:

**Terminal 1 — ML API:**
```bash
python3 ml/api.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend && npm start
```

---

## Testing the ML API

**Quick test with live Binance data:**
```bash
python3 ml/test_api.py
```

Output:
```json
{
  "signal": "BUY",
  "confidence": 78.4,
  "entry": 69450.0,
  "stop_loss": 68900.0,
  "target": 70550.0,
  "rr_ratio": 2.0,
  "xgb_pred": "BUY",
  "rf_pred": "BUY",
  "smc_pred": "BUY"
}
```

**Live terminal monitor (refreshes every 30s):**
```bash
python3 ml/live_monitor.py
```

**Swagger UI (interactive API docs):**

Open [http://localhost:8000/docs](http://localhost:8000/docs), click `POST /predict` → `Try it out`.

To get a ready-to-paste payload for Swagger:
```bash
python3 ml/gen_swagger_payload.py
# Opens ml/swagger_payload.json — copy contents into Swagger request body
```

---

## Signal Logic

Signals only fire when **all three models agree** or **confidence ≥ 75%**:

| Model | Role | Weight |
|---|---|---|
| XGBoost | Primary classifier | 50% |
| Random Forest | Support classifier | 30% |
| SMC Rule Filter | Hard rules (BOS, OB, FVG, liquidity) | 20% |

Features used: EMA 20/50/200, RSI, ATR, Volume spikes, Break of Structure, Change of Character, Order Blocks, Fair Value Gaps, Liquidity sweeps, Equal highs/lows, Bollinger Band width, trend strength.

Labels: BUY if price moves +1.5% in next 10 candles, SELL if -1.5%, HOLD otherwise.

---

## Project Structure

```
SignovaX/
├── frontend/               # React app
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── services/       # marketApi.js — calls ML API + Binance
│   │   ├── stores/         # Zustand state
│   │   └── hooks/          # WebSocket hook
│   └── .env                # Local env vars (create from .env.example)
│
└── ml/                     # Python ML pipeline
    ├── features.py         # Feature engineering (SMC + indicators)
    ├── dataset.py          # Fetch + label Binance data
    ├── model.py            # Ensemble model
    ├── train.py            # Train + evaluate + backtest
    ├── api.py              # FastAPI /predict endpoint
    ├── live_monitor.py     # Terminal signal monitor
    ├── test_api.py         # Quick API test
    ├── gen_swagger_payload.py
    ├── requirements.txt
    ├── data/               # Generated after training
    └── models/             # Generated after training
```

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| `python: command not found` | Use `python3` instead of `python` |
| `react-scripts: command not found` | Run `npm install` inside `frontend/` |
| `XGBoostError: libxgboost.dylib could not be loaded` | Run `brew install libomp` |
| `ModuleNotFoundError: No module named 'fastapi'` | Run `python3 -m pip install -r ml/requirements.txt` |
| `ImportError: Unable to find pyarrow` | Run `python3 -m pip install pyarrow` |
| `GET / → 404 Not Found` | Normal — use `/health` or `/docs`, not `/` |
| `model_loaded: false` | Run `python3 ml/train.py` first to generate the model |
| Frontend shows "Offline — EMA/RSI fallback" | Check ML API is running on port 8000 and `frontend/.env` has `REACT_APP_ML_API_URL=http://localhost:8000`, then restart frontend |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `REACT_APP_ML_API_URL` | No | `http://localhost:8000` | ML API URL |
| `REACT_APP_PROXY_URL` | No | `` | Legacy proxy (not needed) |
| `PORT` | No | `3001` | Frontend port |
=======
# Smart Money Concepts (SMC) Algorithmic Trading System 🎯

A production-ready algorithmic trading platform that detects Smart Money Concepts and generates professional-grade trading signals.

![SMC Trading System](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-18+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)

## 🚀 Features

### Smart Money Concepts Detection
- **Liquidity Zones**: Equal highs/lows identification
- **Order Blocks**: Last opposite candle before strong moves
- **Fair Value Gaps (FVG)**: Price imbalance detection
- **Break of Structure (BOS)**: Trend continuation signals
- **Change of Character (CHOCH)**: Trend reversal detection

### Trading Capabilities
- **Multi-timeframe Analysis**: 1m, 5m, 15m, 1h, 4h, 1d support
- **Real-time Signal Generation**: Live market analysis
- **Risk Management**: 1:2 risk/reward ratios, position sizing
- **Backtesting Engine**: Historical performance validation
- **Performance Analytics**: Win rate, profit factor, drawdown analysis

### Modern Interface
- **Interactive Charts**: TradingView Lightweight Charts with SMC overlays
- **Real-time Dashboard**: Live market data and system status
- **Signal Management**: Active signals with confidence scoring
- **Performance Tracking**: Comprehensive backtesting results

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, Pandas, NumPy, CCXT
- **Frontend**: React (Vite), TailwindCSS, Recharts
- **Charts**: TradingView Lightweight Charts
- **Database**: SQLite → PostgreSQL ready
- **API**: RESTful with automatic OpenAPI documentation

## ⚡ Quick Start

### Option 1: One-Click Setup (Recommended)
```bash
# Start backend
./start_backend.sh

# Start frontend (in new terminal)
./start_frontend.sh
```

### Option 2: Manual Setup
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📊 Demo Data

Generate realistic demo data with embedded SMC patterns:
```bash
python3 demo_data.py
```

## 🎯 Core SMC Strategies Implemented

### 1. Liquidity Zone Detection
```python
# Identifies areas where price repeatedly tests the same level
- Equal highs/lows detection
- Stop-loss cluster identification  
- Support/resistance strength scoring
```

### 2. Order Block Analysis
```python
# Finds institutional order areas
- Last bearish candle before bullish move (bullish OB)
- Last bullish candle before bearish move (bearish OB)
- Mitigation level calculation
```

### 3. Fair Value Gap (FVG) Detection
```python
# Identifies price imbalances
- Bullish FVG: Gap between previous high and next low
- Bearish FVG: Gap between previous low and next high
- Gap filling tracking
```

### 4. Structure Analysis
```python
# BOS (Break of Structure): Trend continuation
- Higher highs in uptrend
- Lower lows in downtrend

# CHOCH (Change of Character): Trend reversal
- Break of previous structure after opposite moves
```

## 📈 API Endpoints

### Market Data
- `GET /api/data/ohlcv` - Historical OHLCV data
- `GET /api/data/symbols` - Available trading pairs
- `GET /api/data/timeframes` - Supported timeframes

### Analysis
- `POST /api/analysis/smc` - Run complete SMC analysis
- `GET /api/analysis/patterns/{symbol}` - Pattern summary

### Signals
- `POST /api/signals/generate` - Generate trading signals
- `GET /api/signals/active/{symbol}` - Active signals
- `GET /api/signals/summary` - Multi-symbol overview

### Backtesting
- `POST /api/backtest/run` - Full historical backtest
- `GET /api/backtest/quick/{symbol}` - Quick performance test
- `GET /api/backtest/performance/{symbol}` - Detailed metrics

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Market Data    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Binance)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │ SMC Strategy    │              │
         └──────────────►│ Engine          │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Signal Generator│
                        │ & Backtester    │
                        └─────────────────┘
```

## 🎮 Usage Examples

### Generate Signals
```python
# Via API
POST /api/signals/generate
{
  "symbol": "BTCUSDT",
  "timeframe": "1h", 
  "min_confidence": 75.0
}

# Response
[
  {
    "signal_type": "BUY",
    "entry_price": 50000,
    "stop_loss": 49000,
    "take_profit": 52000,
    "confidence": 85.0,
    "reasoning": "Bullish Order Block at 50000"
  }
]
```

### Run Backtest
```python
POST /api/backtest/run
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "initial_capital": 10000
}

# Returns comprehensive performance metrics
```

## 📋 Configuration

### Environment Variables (.env)
```bash
DATABASE_URL=sqlite:///./trading.db
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here  
DEBUG=True
```

### Market Data Sources
- **Primary**: Binance API (real-time data)
- **Fallback**: Realistic mock data generator
- **Demo**: Pre-generated data with SMC patterns

## 🔧 Customization

### Adding New SMC Patterns
1. Extend `SMCStrategy` class
2. Implement pattern detection logic
3. Update signal generation rules
4. Add chart visualization

### Risk Management
- Modify position sizing algorithms
- Adjust risk/reward ratios
- Customize stop-loss strategies
- Implement portfolio-level risk controls

## 📊 Performance Metrics

The system tracks comprehensive performance metrics:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Average Trade Duration**: Time in market per trade

## 🚨 Important Notes

### Educational Purpose
This system is designed for educational and research purposes. Always:
- Paper trade before live implementation
- Understand the risks involved
- Never risk more than you can afford to lose
- Backtest thoroughly on historical data

### Production Considerations
- Add proper authentication and authorization
- Implement rate limiting and error handling
- Use PostgreSQL for production database
- Add comprehensive logging and monitoring
- Consider regulatory compliance requirements

## 📚 Documentation

- **Setup Guide**: [SETUP.md](SETUP.md) - Detailed installation instructions
- **API Documentation**: Available at `/docs` when backend is running
- **Architecture**: Modular design with clear separation of concerns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please ensure compliance with local regulations before any live trading implementation.

---

**⚠️ Risk Disclaimer**: Trading involves substantial risk of loss. This software is for educational purposes only and should not be used for live trading without proper testing and risk management.
>>>>>>> c7436fc (first push)
