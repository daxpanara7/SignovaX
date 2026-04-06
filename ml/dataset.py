"""
Dataset creation for SignovaX
Fetches Binance OHLCV data and labels candles as BUY / SELL / HOLD
"""

import time
import requests
import numpy as np
import pandas as pd
from features import build_features, FEATURE_COLS

BINANCE_BASE = "https://api.binance.com/api/v3/klines"

LABEL_MAP = {0: "HOLD", 1: "BUY", 2: "SELL"}
LABEL_INT  = {"HOLD": 0, "BUY": 1, "SELL": 2}


# ─── Fetch ────────────────────────────────────────────────────────────────────

def fetch_klines(symbol: str, interval: str, limit: int = 1000) -> pd.DataFrame:
    """Fetch up to 1000 candles per call from Binance REST API."""
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(BINANCE_BASE, params=params, timeout=10)
    resp.raise_for_status()
    raw = resp.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_vol", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    df = df[["open_time", "open", "high", "low", "close", "volume"]].copy()
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


def fetch_large_dataset(
    symbol: str,
    interval: str,
    target_candles: int = 50000,
    end_time: int = None,
) -> pd.DataFrame:
    """
    Paginate backwards through Binance history to collect target_candles rows.
    Binance max per request = 1000.
    """
    all_frames = []
    fetched = 0
    params = {"symbol": symbol, "interval": interval, "limit": 1000}
    if end_time:
        params["endTime"] = end_time

    print(f"Fetching {target_candles} candles for {symbol} {interval}...")

    while fetched < target_candles:
        resp = requests.get(BINANCE_BASE, params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
        if not raw:
            break

        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_vol", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        df = df[["open_time", "open", "high", "low", "close", "volume"]].copy()
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        all_frames.append(df)
        fetched += len(df)

        # Move end_time back to fetch older data
        params["endTime"] = int(raw[0][0]) - 1
        time.sleep(0.2)  # respect rate limits

        print(f"  Fetched {fetched}/{target_candles}", end="\r")

    print()
    combined = pd.concat(all_frames, ignore_index=True)
    combined.sort_values("open_time", inplace=True)
    combined.drop_duplicates("open_time", inplace=True)
    combined.reset_index(drop=True, inplace=True)
    return combined


# ─── Labeling ─────────────────────────────────────────────────────────────────

def label_candles(
    df: pd.DataFrame,
    forward_candles: int = 10,
    buy_threshold: float = 0.015,   # +1.5% = BUY
    sell_threshold: float = 0.015,  # -1.5% = SELL
) -> pd.DataFrame:
    """
    Label each candle based on future price movement.
    BUY  = max future return in N candles >= buy_threshold
    SELL = min future return in N candles <= -sell_threshold
    HOLD = neither
    Priority: if both triggered, whichever hits first wins.
    """
    closes = df["close"].values
    n = len(closes)
    labels = np.zeros(n, dtype=int)  # 0 = HOLD

    for i in range(n - forward_candles):
        future = closes[i + 1: i + forward_candles + 1]
        returns = (future - closes[i]) / closes[i]

        max_ret = returns.max()
        min_ret = returns.min()

        hit_buy  = max_ret >= buy_threshold
        hit_sell = min_ret <= -sell_threshold

        if hit_buy and hit_sell:
            # Whichever hits first
            buy_idx  = np.argmax(returns >= buy_threshold)
            sell_idx = np.argmax(returns <= -sell_threshold)
            labels[i] = 1 if buy_idx <= sell_idx else 2
        elif hit_buy:
            labels[i] = 1
        elif hit_sell:
            labels[i] = 2
        # else HOLD (0)

    df = df.copy()
    df["label"] = labels
    df["label_name"] = df["label"].map(LABEL_MAP)
    return df


# ─── Balance Dataset ──────────────────────────────────────────────────────────

def balance_dataset(df: pd.DataFrame, strategy: str = "undersample") -> pd.DataFrame:
    """
    Balance BUY / SELL / HOLD classes.
    strategy: 'undersample' (default) or 'oversample'
    """
    counts = df["label"].value_counts()
    print(f"Class distribution before balancing:\n{counts}\n")

    if strategy == "undersample":
        min_count = counts.min()
        balanced = pd.concat([
            df[df["label"] == cls].sample(min_count, random_state=42)
            for cls in counts.index
        ])
    else:
        max_count = counts.max()
        balanced = pd.concat([
            df[df["label"] == cls].sample(max_count, replace=True, random_state=42)
            for cls in counts.index
        ])

    balanced = balanced.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Class distribution after balancing:\n{balanced['label'].value_counts()}\n")
    return balanced


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def build_dataset(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    target_candles: int = 50000,
    forward_candles: int = 10,
    buy_threshold: float = 0.015,
    sell_threshold: float = 0.015,
    balance: bool = True,
    save_path: str = "data/dataset.parquet",
) -> pd.DataFrame:

    # 1. Fetch raw OHLCV
    raw = fetch_large_dataset(symbol, interval, target_candles)
    print(f"Raw candles: {len(raw)}")

    # 2. Feature engineering
    featured = build_features(raw)
    print(f"After feature engineering: {len(featured)}")

    # 3. Label
    labeled = label_candles(featured, forward_candles, buy_threshold, sell_threshold)

    # 4. Drop last N rows (no valid labels)
    labeled = labeled.iloc[:-forward_candles].copy()

    # 5. Balance
    if balance:
        labeled = balance_dataset(labeled)

    # 6. Save
    import os
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    labeled.to_parquet(save_path, index=False)
    print(f"Dataset saved to {save_path} — {len(labeled)} rows")

    return labeled


if __name__ == "__main__":
    df = build_dataset(
        symbol="BTCUSDT",
        interval="15m",
        target_candles=50000,
        forward_candles=10,
        buy_threshold=0.015,
        sell_threshold=0.015,
        balance=True,
        save_path="data/dataset.parquet",
    )
    print(df[["open_time", "close", "label_name"]].tail(10))
