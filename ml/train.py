"""
Training + Evaluation script for SignovaX
Run: python train.py
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from model import SignovaEnsemble
from features import FEATURE_COLS
from dataset import build_dataset

# ─── Config ───────────────────────────────────────────────────────────────────

SYMBOL           = "BTCUSDT"
INTERVAL         = "15m"
TARGET_CANDLES   = 50000
FORWARD_CANDLES  = 10
BUY_THRESHOLD    = 0.015   # 1.5%
SELL_THRESHOLD   = 0.015
CONFIDENCE_THR   = 0.70
DATASET_PATH     = "data/dataset.parquet"
MODEL_PATH       = "models/ensemble.joblib"


# ─── Load or Build Dataset ────────────────────────────────────────────────────

def load_or_build() -> pd.DataFrame:
    import os
    if os.path.exists(DATASET_PATH):
        print(f"Loading existing dataset from {DATASET_PATH}")
        return pd.read_parquet(DATASET_PATH)
    return build_dataset(
        symbol=SYMBOL,
        interval=INTERVAL,
        target_candles=TARGET_CANDLES,
        forward_candles=FORWARD_CANDLES,
        buy_threshold=BUY_THRESHOLD,
        sell_threshold=SELL_THRESHOLD,
        balance=True,
        save_path=DATASET_PATH,
    )


# ─── Evaluation ───────────────────────────────────────────────────────────────

def evaluate(model: SignovaEnsemble, X_test: pd.DataFrame, y_test: np.ndarray):
    print("\n=== Evaluation (all predictions) ===")
    y_pred_all = model.xgb.predict(X_test[FEATURE_COLS])
    print(classification_report(y_test, y_pred_all, target_names=["HOLD", "BUY", "SELL"]))

    print("\n=== Evaluation (filtered by confidence >= {:.0f}%) ===".format(CONFIDENCE_THR * 100))
    result = model.predict_with_confidence(X_test)
    label_map = {"HOLD": 0, "BUY": 1, "SELL": 2}
    y_pred_filtered = result["signal"].map(label_map).values

    # Only evaluate non-HOLD filtered signals
    mask = y_pred_filtered != 0
    if mask.sum() > 0:
        print(f"Signals fired: {mask.sum()} / {len(y_test)} ({mask.mean()*100:.1f}%)")
        print(classification_report(
            y_test[mask], y_pred_filtered[mask],
            target_names=["HOLD", "BUY", "SELL"],
            zero_division=0,
        ))
    else:
        print("No signals passed confidence threshold.")

    # Confusion matrix
    print("Confusion Matrix (all):")
    print(confusion_matrix(y_test, y_pred_all))


# ─── Backtest Simulation ──────────────────────────────────────────────────────

def backtest(df_test: pd.DataFrame, model: SignovaEnsemble, atr_multiplier_sl: float = 1.5):
    """
    Simple backtest: enter on signal, SL = ATR * multiplier, TP = 2x SL
    """
    result = model.predict_with_confidence(df_test)
    df_test = df_test.reset_index(drop=True)

    trades = []
    for i, row in result.iterrows():
        if row["signal"] == "HOLD":
            continue
        if i + 20 >= len(df_test):
            break

        entry  = df_test.loc[i, "close"]
        atr    = df_test.loc[i, "atr"]
        sl_dist = atr * atr_multiplier_sl
        tp_dist = sl_dist * 2.0

        if row["signal"] == "BUY":
            sl = entry - sl_dist
            tp = entry + tp_dist
            future = df_test.loc[i + 1: i + 20, "close"]
            hit_tp = (future >= tp).any()
            hit_sl = (future <= sl).any()
        else:  # SELL
            sl = entry + sl_dist
            tp = entry - tp_dist
            future = df_test.loc[i + 1: i + 20, "close"]
            hit_tp = (future <= tp).any()
            hit_sl = (future >= sl).any()

        if hit_tp and hit_sl:
            # Whichever hit first
            tp_idx = future[future >= tp].index[0] if row["signal"] == "BUY" else future[future <= tp].index[0]
            sl_idx = future[future <= sl].index[0] if row["signal"] == "BUY" else future[future >= sl].index[0]
            outcome = "WIN" if tp_idx < sl_idx else "LOSS"
        elif hit_tp:
            outcome = "WIN"
        elif hit_sl:
            outcome = "LOSS"
        else:
            outcome = "OPEN"

        trades.append({
            "signal":     row["signal"],
            "confidence": row["confidence"],
            "entry":      entry,
            "sl":         sl,
            "tp":         tp,
            "outcome":    outcome,
        })

    if not trades:
        print("No trades in backtest.")
        return

    trades_df = pd.DataFrame(trades)
    closed = trades_df[trades_df["outcome"].isin(["WIN", "LOSS"])]
    wins   = (closed["outcome"] == "WIN").sum()
    losses = (closed["outcome"] == "LOSS").sum()
    total  = len(closed)

    print(f"\n=== Backtest Results ===")
    print(f"Total signals : {len(trades_df)}")
    print(f"Closed trades : {total}")
    print(f"Win rate      : {wins/total*100:.1f}%" if total > 0 else "N/A")
    print(f"Wins / Losses : {wins} / {losses}")
    print(f"Avg confidence: {trades_df['confidence'].mean():.1f}%")

    # P&L (1R = 1 unit risk)
    pnl = wins * 2 - losses * 1  # RR = 1:2
    print(f"Net P&L (1R units, RR=1:2): {pnl:+.1f}R")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Load dataset
    df = load_or_build()
    print(f"Dataset shape: {df.shape}")
    print(df["label_name"].value_counts())

    # 2. Split
    X = df[FEATURE_COLS]
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False  # time-series: no shuffle
    )
    df_test = df.iloc[len(X_train):].reset_index(drop=True)

    # 3. Train
    model = SignovaEnsemble(confidence_threshold=CONFIDENCE_THR)
    model.fit(X_train, y_train)

    # 4. Evaluate
    evaluate(model, X_test, y_test)

    # 5. Backtest
    backtest(df_test, model)

    # 6. Save
    model.save(MODEL_PATH)
