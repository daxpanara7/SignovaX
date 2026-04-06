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

MODEL_PATH = "models/ensemble.joblib"
model: SignovaEnsemble = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    try:
        model = SignovaEnsemble.load(MODEL_PATH)
        print("Model loaded.")
    except Exception:
        print("No model found — training now (this takes ~5 min on first boot)...")
        try:
            import subprocess, sys
            subprocess.run([sys.executable, "train.py"], check=True)
            model = SignovaEnsemble.load(MODEL_PATH)
            print("Model trained and loaded.")
        except Exception as e:
            print(f"Auto-train failed: {e} — API will return 503 until model is available.")
    yield

app = FastAPI(title="SignovaX Signal API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
