"""
Ensemble Model for SignovaX
XGBoost + Random Forest + SMC Rule Filter
Signal only fires when ensemble agrees OR confidence > threshold
"""

import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from features import FEATURE_COLS

CLASSES = {0: "HOLD", 1: "BUY", 2: "SELL"}


# ─── SMC Rule-Based Filter ────────────────────────────────────────────────────

class SMCFilter:
    """
    Hard rules based on Smart Money Concepts.
    Returns: 1 (BUY), 2 (SELL), 0 (HOLD/no opinion)
    """

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        signals = np.zeros(len(X), dtype=int)

        for i, row in X.iterrows():
            bull_score = 0
            bear_score = 0

            # Trend alignment
            if row.get("ema_trend", 0) == 1:
                bull_score += 2
            elif row.get("ema_trend", 0) == -1:
                bear_score += 2

            # BOS / CHOCH
            if row.get("bos_bull", 0):
                bull_score += 2
            if row.get("bos_bear", 0):
                bear_score += 2
            if row.get("choch", 0) == 1:
                bull_score += 3
            elif row.get("choch", 0) == -1:
                bear_score += 3

            # Liquidity sweeps
            if row.get("liq_sweep_low", 0):
                bull_score += 2  # swept lows = bullish reversal
            if row.get("liq_sweep_high", 0):
                bear_score += 2

            # Order blocks
            if row.get("near_bull_ob", 0):
                bull_score += 1
            if row.get("near_bear_ob", 0):
                bear_score += 1

            # FVG
            if row.get("fvg_signal", 0) > 0:
                bull_score += 1
            elif row.get("fvg_signal", 0) < 0:
                bear_score += 1

            # RSI
            if row.get("rsi_zone", 0) == -1:
                bull_score += 1  # oversold
            elif row.get("rsi_zone", 0) == 1:
                bear_score += 1  # overbought

            # Volume confirmation
            if row.get("vol_spike", 1) > 1.5:
                if bull_score > bear_score:
                    bull_score += 1
                else:
                    bear_score += 1

            # Avoid consolidation
            if row.get("is_consolidating", 0):
                bull_score = max(0, bull_score - 2)
                bear_score = max(0, bear_score - 2)

            threshold = 5
            if bull_score >= threshold and bull_score > bear_score:
                signals[i] = 1
            elif bear_score >= threshold and bear_score > bull_score:
                signals[i] = 2

        return signals

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return soft probabilities based on score ratio."""
        preds = self.predict(X)
        proba = np.zeros((len(X), 3))
        for idx, p in enumerate(preds):
            if p == 1:
                proba[idx] = [0.1, 0.8, 0.1]
            elif p == 2:
                proba[idx] = [0.1, 0.1, 0.8]
            else:
                proba[idx] = [0.8, 0.1, 0.1]
        return proba


# ─── Ensemble ─────────────────────────────────────────────────────────────────

class SignovaEnsemble:
    def __init__(
        self,
        confidence_threshold: float = 0.70,
        require_all_agree: bool = False,
    ):
        self.confidence_threshold = confidence_threshold
        self.require_all_agree = require_all_agree

        self.xgb = XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        )
        self.rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        )
        self.smc = SMCFilter()

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        print("Training XGBoost...")
        self.xgb.fit(X[FEATURE_COLS], y)
        print("Training Random Forest...")
        self.rf.fit(X[FEATURE_COLS], y)
        print("SMC filter is rule-based, no training needed.")
        return self

    def predict_with_confidence(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Returns DataFrame with columns:
        signal, confidence, xgb_pred, rf_pred, smc_pred
        """
        X_feat = X[FEATURE_COLS].reset_index(drop=True)

        xgb_proba = self.xgb.predict_proba(X_feat)   # (n, 3)
        rf_proba  = self.rf.predict_proba(X_feat)     # (n, 3)
        smc_proba = self.smc.predict_proba(X_feat)    # (n, 3)

        # Weighted average: XGB 50%, RF 30%, SMC 20%
        ensemble_proba = 0.5 * xgb_proba + 0.3 * rf_proba + 0.2 * smc_proba

        xgb_pred = np.argmax(xgb_proba, axis=1)
        rf_pred  = np.argmax(rf_proba, axis=1)
        smc_pred = self.smc.predict(X_feat)

        final_signals = []
        confidences   = []

        for i in range(len(X_feat)):
            proba     = ensemble_proba[i]
            pred      = np.argmax(proba)
            conf      = proba[pred]
            all_agree = (xgb_pred[i] == rf_pred[i] == smc_pred[i])

            if self.require_all_agree:
                signal = pred if all_agree else 0
            else:
                signal = pred if conf >= self.confidence_threshold else 0

            final_signals.append(signal)
            confidences.append(round(float(conf) * 100, 1))

        result = pd.DataFrame({
            "signal":     [CLASSES[s] for s in final_signals],
            "confidence": confidences,
            "xgb_pred":   [CLASSES[p] for p in xgb_pred],
            "rf_pred":    [CLASSES[p] for p in rf_pred],
            "smc_pred":   [CLASSES[p] for p in smc_pred],
        })
        return result

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        result = self.predict_with_confidence(X)
        label_map = {"HOLD": 0, "BUY": 1, "SELL": 2}
        return result["signal"].map(label_map).values

    def save(self, path: str = "models/ensemble.joblib"):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self, path)
        print(f"Model saved to {path}")

    @staticmethod
    def load(path: str = "models/ensemble.joblib") -> "SignovaEnsemble":
        return joblib.load(path)
