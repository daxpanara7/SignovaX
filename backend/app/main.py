from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import threading
import pandas as pd
from dotenv import load_dotenv

from app.routes import data, analysis, signals, backtest

load_dotenv()

app = FastAPI(
    title="SMC Trading System",
    description="Smart Money Concepts Algorithmic Trading Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global lock to prevent yfinance SQLite database conflicts
_yfinance_lock = threading.Lock()

# Include routers
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])

@app.get("/")
async def root():
    return {"message": "SMC Trading System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "smc-trading-system"}


@app.get("/index-candles")
def index_candles(
    symbol: str = Query("NIFTY50", description="Index symbol: NIFTY50 or SENSEX"),
    interval: str = Query("15m", description="Timeframe interval"),
    limit: int = Query(300, description="Number of candles to return"),
):
    """Fetch OHLCV candles for Indian indices (NIFTY50, SENSEX) via yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed. Run: pip3 install yfinance")

    ticker_map = {
        "NIFTY50": "^NSEI",
        "SENSEX":  "^BSESN",
    }
    ticker = ticker_map.get(symbol.upper())
    if not ticker:
        raise HTTPException(status_code=400, detail=f"Unknown symbol: {symbol}. Supported: NIFTY50, SENSEX")

    period_map = {
        "1m":  "7d",
        "2m":  "7d",
        "5m":  "60d",
        "10m": "60d",
        "15m": "60d",
        "30m": "60d",
        "1h":  "730d",
        "4h":  "730d",
        "1d":  "max",
        "1w":  "max",
        "1mo": "max",
    }
    # yfinance doesn't support 10m or 4h natively
    interval_map = {
        "10m": "15m",
        "4h":  "1h",
    }

    yf_interval = interval_map.get(interval, interval)
    period = period_map.get(interval, "60d")

    try:
        with _yfinance_lock:
            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=yf_interval, auto_adjust=True, actions=False)

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol} at interval {interval}")

        # Aggregate 1h → 4h if needed
        if interval == "4h":
            df = df.resample("240min").agg({
                "Open":   "first",
                "High":   "max",
                "Low":    "min",
                "Close":  "last",
                "Volume": "sum",
            }).dropna()

        df = df.tail(limit)

        candles = []
        for ts, row in df.iterrows():
            try:
                candles.append({
                    "time":   int(ts.timestamp()),
                    "open":   round(float(row["Open"]),   2),
                    "high":   round(float(row["High"]),   2),
                    "low":    round(float(row["Low"]),    2),
                    "close":  round(float(row["Close"]),  2),
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
        raise HTTPException(status_code=500, detail=f"Error fetching {symbol} data: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)