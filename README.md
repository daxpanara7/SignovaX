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
