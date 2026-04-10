"""
SignovaX Prediction API
POST /predict  — takes latest candles, returns signal + confidence + entry/SL/TP
GET  /health   — health check
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np
import pandas as pd

from features import build_features, FEATURE_COLS
from model import SignovaEnsemble

import os
import threading

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "ensemble.joblib")
model: SignovaEnsemble = None

# Global lock for yfinance to prevent database lock errors
_yfinance_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    try:
        model = SignovaEnsemble.load(MODEL_PATH)
        print("Model loaded.")
    except Exception as e:
        print(f"Warning: could not load model — {e}")
        print("Deploy with models/ensemble.joblib committed to the repo.")
    yield

app = FastAPI(title="SignovaX Signal API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class Candle(BaseModel):
    open_time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class PredictRequest(BaseModel):
    candles: List[Candle]   # send at least 250 candles for reliable features
    atr_sl_multiplier: float = 1.5


class PredictResponse(BaseModel):
    signal: str             # BUY | SELL | HOLD
    confidence: float       # 0–100
    entry: float
    stop_loss: float
    target: float
    rr_ratio: float
    xgb_pred: str
    rf_pred: str
    smc_pred: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.get("/index-candles")
def index_candles(symbol: str = "NIFTY50", interval: str = "15m", limit: int = 300):
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    ticker_map = {
        "NIFTY50": "^NSEI",
        "SENSEX": "^BSESN"
    }
    ticker = ticker_map.get(symbol.upper())
    if not ticker:
        raise HTTPException(status_code=400, detail=f"Unknown symbol: {symbol}")

    # Complete interval mapping for all requested timeframes
    period_map = {
        "1m": "7d",    # 1 minute - 7 days max
        "2m": "7d",    # 2 minutes - 7 days
        "5m": "60d",   # 5 minutes - 60 days
        "10m": "60d",  # 10 minutes - 60 days (not supported by yfinance, fallback to 15m)
        "15m": "60d",  # 15 minutes - 60 days
        "30m": "60d",  # 30 minutes - 60 days
        "1h": "730d",  # 1 hour - 2 years
        "4h": "730d",  # 4 hours - 2 years (simulated from 1h)
        "1d": "max",   # 1 day - max available
        "1w": "max",   # 1 week - max available
        "1mo": "max",  # 1 month - max available
    }

    # yfinance doesn't support 10m and 4h, we'll handle those specially
    interval_map = {
        "10m": "15m",  # Use 15m and filter
        "4h": "1h",    # Use 1h and aggregate
    }

    yf_interval = interval_map.get(interval, interval)
    period = period_map.get(interval, "60d")

    try:
        # Use global lock to prevent database conflicts across all requests
        with _yfinance_lock:
            # Download with reduced caching to avoid database locks
            t = yf.Ticker(ticker)
            # Disable yfinance cache to prevent SQLite lock errors
            df = t.history(period=period, interval=yf_interval, auto_adjust=True, actions=False)

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data available for this symbol/interval")

        # Handle 4h aggregation from 1h data
        if interval == "4h":
            df = df.resample('240T').agg({  # 240 minutes = 4 hours
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()

        # Take only the requested number of candles
        df = df.tail(limit)

        candles = []
        for ts, row in df.iterrows():
            try:
                candles.append({
                    "time":   int(ts.timestamp()),
                    "open":   round(float(row["Open"]), 2),
                    "high":   round(float(row["High"]), 2),
                    "low":    round(float(row["Low"]), 2),
                    "close":  round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                })
            except Exception:
                continue

        if not candles:
            raise HTTPException(status_code=404, detail="No candle data could be processed")

        return {"symbol": symbol, "interval": interval, "candles": candles}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if len(req.candles) < 250:
        raise HTTPException(status_code=400, detail="Send at least 250 candles")

    # Build DataFrame
    df = pd.DataFrame([c.dict() for c in req.candles])
    # Handle both ISO strings and numeric timestamps (ms)
    try:
        df["open_time"] = pd.to_datetime(df["open_time"])
    except Exception:
        df["open_time"] = pd.to_datetime(df["open_time"].astype(float), unit="ms")

    # Feature engineering
    try:
        featured = build_features(df)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Feature error: {e}")

    if len(featured) == 0:
        raise HTTPException(status_code=422, detail="Not enough data after feature engineering")

    # Use last row for prediction
    last = featured.tail(1).reset_index(drop=True)

    result = model.predict_with_confidence(last)
    row = result.iloc[0]

    signal     = row["signal"]
    confidence = row["confidence"]
    entry      = float(last["close"].iloc[0])
    atr        = float(last["atr"].iloc[0])
    sl_dist    = atr * req.atr_sl_multiplier
    tp_dist    = sl_dist * 2.0

    if signal == "BUY":
        stop_loss = round(entry - sl_dist, 4)
        target    = round(entry + tp_dist, 4)
    elif signal == "SELL":
        stop_loss = round(entry + sl_dist, 4)
        target    = round(entry - tp_dist, 4)
    else:
        stop_loss = round(entry - sl_dist, 4)
        target    = round(entry + tp_dist, 4)

    rr = round(tp_dist / (sl_dist + 1e-9), 2)

    return PredictResponse(
        signal=signal,
        confidence=confidence,
        entry=round(entry, 4),
        stop_loss=stop_loss,
        target=target,
        rr_ratio=rr,
        xgb_pred=row["xgb_pred"],
        rf_pred=row["rf_pred"],
        smc_pred=row["smc_pred"],
    )


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
