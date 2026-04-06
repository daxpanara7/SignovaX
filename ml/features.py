"""
Feature Engineering for SignovaX
Covers: SMC (BOS, CHOCH, OB, FVG), Liquidity, EMA, RSI, ATR, Volume, Trend
"""

import numpy as np
import pandas as pd


# ─── Trend Indicators ────────────────────────────────────────────────────────

def add_ema(df: pd.DataFrame) -> pd.DataFrame:
    df["ema_20"] = df["close"].ewm(span=20).mean()
    df["ema_50"] = df["close"].ewm(span=50).mean()
    df["ema_200"] = df["close"].ewm(span=200).mean()
    df["ema_trend"] = np.where(
        (df["ema_20"] > df["ema_50"]) & (df["ema_50"] > df["ema_200"]), 1,
        np.where((df["ema_20"] < df["ema_50"]) & (df["ema_50"] < df["ema_200"]), -1, 0)
    )
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi_zone"] = np.where(df["rsi"] > 70, 1, np.where(df["rsi"] < 30, -1, 0))
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(period).mean()
    df["atr_pct"] = df["atr"] / df["close"]  # normalized ATR
    return df


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    df["vol_ma"] = df["volume"].rolling(20).mean()
    df["vol_spike"] = (df["volume"] / (df["vol_ma"] + 1e-9)).round(3)
    df["vol_trend"] = df["volume"].rolling(5).mean() / (df["volume"].rolling(20).mean() + 1e-9)
    return df


# ─── Volatility + Trend Strength ─────────────────────────────────────────────

def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    # Bollinger Band width as volatility proxy
    sma = df["close"].rolling(20).mean()
    std = df["close"].rolling(20).std()
    df["bb_width"] = (2 * std) / (sma + 1e-9)

    # ADX-like trend strength using EMA slope
    df["ema_slope"] = df["ema_20"].diff(5) / (df["ema_20"].shift(5) + 1e-9)
    df["is_trending"] = (df["ema_slope"].abs() > df["ema_slope"].abs().rolling(20).mean()).astype(int)
    df["is_consolidating"] = (df["bb_width"] < df["bb_width"].rolling(20).quantile(0.3)).astype(int)
    return df


# ─── Market Structure: BOS + CHOCH ───────────────────────────────────────────

def add_market_structure(df: pd.DataFrame, swing_len: int = 10) -> pd.DataFrame:
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)

    bos_bull = np.zeros(n)
    bos_bear = np.zeros(n)
    choch = np.zeros(n)

    prev_hh = prev_hl = prev_lh = prev_ll = None
    trend = 0  # 1 = bullish, -1 = bearish

    for i in range(swing_len, n - swing_len):
        # Detect swing high/low
        is_swing_high = highs[i] == max(highs[i - swing_len:i + swing_len])
        is_swing_low = lows[i] == min(lows[i - swing_len:i + swing_len])

        if is_swing_high:
            if prev_hh is not None and highs[i] > prev_hh:
                bos_bull[i] = 1  # Break of Structure bullish
                if trend == -1:
                    choch[i] = 1  # Change of Character
                trend = 1
            prev_hh = highs[i]

        if is_swing_low:
            if prev_ll is not None and lows[i] < prev_ll:
                bos_bear[i] = 1  # Break of Structure bearish
                if trend == 1:
                    choch[i] = -1  # Change of Character
                trend = -1
            prev_ll = lows[i]

    df["bos_bull"] = bos_bull
    df["bos_bear"] = bos_bear
    df["choch"] = choch
    df["market_trend"] = trend  # last known trend (scalar, will be overwritten)

    # Rolling market trend
    df["market_trend"] = (df["bos_bull"].rolling(20).sum() - df["bos_bear"].rolling(20).sum()).apply(
        lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
    )
    return df


# ─── Liquidity: Equal Highs/Lows + Sweeps ────────────────────────────────────

def add_liquidity_features(df: pd.DataFrame, tolerance: float = 0.001) -> pd.DataFrame:
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)

    eq_highs = np.zeros(n)
    eq_lows = np.zeros(n)
    liq_sweep_high = np.zeros(n)
    liq_sweep_low = np.zeros(n)

    for i in range(5, n):
        # Equal highs: current high within tolerance of recent high
        recent_highs = highs[max(0, i - 20):i]
        if len(recent_highs) > 0:
            closest_high = recent_highs[np.argmax(recent_highs)]
            if abs(highs[i] - closest_high) / (closest_high + 1e-9) < tolerance:
                eq_highs[i] = 1

        # Equal lows
        recent_lows = lows[max(0, i - 20):i]
        if len(recent_lows) > 0:
            closest_low = recent_lows[np.argmin(recent_lows)]
            if abs(lows[i] - closest_low) / (closest_low + 1e-9) < tolerance:
                eq_lows[i] = 1

        # Liquidity sweep: wick beyond equal high/low then closes back
        if eq_highs[i - 1] and df["close"].iloc[i] < highs[i]:
            liq_sweep_high[i] = 1  # swept highs, bearish
        if eq_lows[i - 1] and df["close"].iloc[i] > lows[i]:
            liq_sweep_low[i] = 1   # swept lows, bullish

    df["eq_highs"] = eq_highs
    df["eq_lows"] = eq_lows
    df["liq_sweep_high"] = liq_sweep_high
    df["liq_sweep_low"] = liq_sweep_low
    return df


# ─── Order Blocks ─────────────────────────────────────────────────────────────

def add_order_blocks(df: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:
    """
    Bullish OB: last bearish candle before a strong bullish move
    Bearish OB: last bullish candle before a strong bearish move
    """
    closes = df["close"].values
    opens = df["open"].values
    n = len(df)

    bull_ob = np.zeros(n)
    bear_ob = np.zeros(n)

    for i in range(lookback + 1, n):
        # Strong bullish move: close > open by > 0.5%
        if (closes[i] - opens[i]) / (opens[i] + 1e-9) > 0.005:
            # Find last bearish candle in lookback
            for j in range(i - 1, max(i - lookback - 1, 0), -1):
                if closes[j] < opens[j]:
                    bull_ob[j] = 1
                    break

        # Strong bearish move
        if (opens[i] - closes[i]) / (opens[i] + 1e-9) > 0.005:
            for j in range(i - 1, max(i - lookback - 1, 0), -1):
                if closes[j] > opens[j]:
                    bear_ob[j] = 1
                    break

    df["bull_ob"] = bull_ob
    df["bear_ob"] = bear_ob

    # Price currently inside an OB zone (rolling 10 candles)
    df["near_bull_ob"] = df["bull_ob"].rolling(10).max()
    df["near_bear_ob"] = df["bear_ob"].rolling(10).max()
    return df


# ─── Fair Value Gaps ──────────────────────────────────────────────────────────

def add_fvg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bullish FVG: candle[i-2].high < candle[i].low  (gap up)
    Bearish FVG: candle[i-2].low > candle[i].high  (gap down)
    """
    n = len(df)
    bull_fvg = np.zeros(n)
    bear_fvg = np.zeros(n)

    for i in range(2, n):
        if df["low"].iloc[i] > df["high"].iloc[i - 2]:
            bull_fvg[i] = 1
        if df["high"].iloc[i] < df["low"].iloc[i - 2]:
            bear_fvg[i] = 1

    df["bull_fvg"] = bull_fvg
    df["bear_fvg"] = bear_fvg
    df["fvg_signal"] = bull_fvg - bear_fvg
    return df


# ─── Price Action Features ────────────────────────────────────────────────────

def add_price_action(df: pd.DataFrame) -> pd.DataFrame:
    df["body_size"] = (df["close"] - df["open"]).abs() / (df["open"] + 1e-9)
    df["upper_wick"] = (df["high"] - df[["close", "open"]].max(axis=1)) / (df["open"] + 1e-9)
    df["lower_wick"] = (df[["close", "open"]].min(axis=1) - df["low"]) / (df["open"] + 1e-9)
    df["candle_dir"] = np.where(df["close"] > df["open"], 1, -1)

    # Returns
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_3"] = df["close"].pct_change(3)
    df["ret_5"] = df["close"].pct_change(5)
    return df


# ─── Master Feature Builder ───────────────────────────────────────────────────

FEATURE_COLS = [
    "ema_20", "ema_50", "ema_200", "ema_trend",
    "rsi", "rsi_zone",
    "atr", "atr_pct",
    "vol_spike", "vol_trend",
    "bb_width", "ema_slope", "is_trending", "is_consolidating",
    "bos_bull", "bos_bear", "choch", "market_trend",
    "eq_highs", "eq_lows", "liq_sweep_high", "liq_sweep_low",
    "bull_ob", "bear_ob", "near_bull_ob", "near_bear_ob",
    "bull_fvg", "bear_fvg", "fvg_signal",
    "body_size", "upper_wick", "lower_wick", "candle_dir",
    "ret_1", "ret_3", "ret_5",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps to a raw OHLCV dataframe."""
    df = df.copy()
    df = add_ema(df)
    df = add_rsi(df)
    df = add_atr(df)
    df = add_volume_features(df)
    df = add_volatility_features(df)
    df = add_market_structure(df)
    df = add_liquidity_features(df)
    df = add_order_blocks(df)
    df = add_fvg(df)
    df = add_price_action(df)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
