"""
SignovaX Pro - High-Probability Signal Generation Engine
Target Accuracy: 85-90%
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Signal:
    """Trading signal with complete information"""
    symbol: str
    signal: str  # BUY, SELL, NO_TRADE
    confidence: float  # 0-100
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reasoning: List[str]
    timestamp: datetime
    timeframe: str

    # Additional metrics
    trend_score: float
    momentum_score: float
    structure_score: float
    liquidity_score: float
    volume_score: float

    # ML prediction (if available)
    ml_probability: Optional[float] = None


class SignalEngine:
    """
    Professional signal generation engine using multi-factor confirmation.
    Only generates signals with 80%+ confidence score.
    """

    # Scoring weights (total = 100)
    WEIGHTS = {
        'trend_alignment': 25,
        'momentum': 20,
        'price_structure': 25,
        'liquidity': 15,
        'volume': 10,
        'risk_reward': 5
    }

    # Minimum scores for signal generation
    MIN_CONFIDENCE = 80
    MIN_RISK_REWARD = 2.0

    def __init__(self):
        self.signals_history = []

    def generate_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = '15m'
    ) -> Signal:
        """
        Generate high-probability trading signal.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            df: DataFrame with OHLCV + indicators
            timeframe: Chart timeframe

        Returns:
            Signal object with complete trade information
        """

        # Calculate all scores
        trend_score = self._score_trend_alignment(df)
        momentum_score = self._score_momentum(df)
        structure_score = self._score_price_structure(df)
        liquidity_score = self._score_liquidity(df)
        volume_score = self._score_volume(df)

        # Calculate total confidence
        confidence = (
            trend_score * self.WEIGHTS['trend_alignment'] / 100 +
            momentum_score * self.WEIGHTS['momentum'] / 100 +
            structure_score * self.WEIGHTS['price_structure'] / 100 +
            liquidity_score * self.WEIGHTS['liquidity'] / 100 +
            volume_score * self.WEIGHTS['volume'] / 100
        )

        # Collect reasoning
        reasoning = []

        # Determine signal direction
        signal_type = "NO_TRADE"

        # BULLISH CONDITIONS
        if (trend_score >= 80 and momentum_score >= 70 and
            structure_score >= 75):
            signal_type = "BUY"
            reasoning.extend(self._get_bullish_reasons(df))

        # BEARISH CONDITIONS
        elif (trend_score <= 20 and momentum_score <= 30 and
              structure_score <= 25):
            signal_type = "SELL"
            reasoning.extend(self._get_bearish_reasons(df))

        # NOT ENOUGH CONVICTION
        else:
            signal_type = "NO_TRADE"
            reasoning.append("Insufficient confluence for high-probability setup")
            confidence = min(confidence, 50)

        # Calculate trade levels
        entry, stop_loss, take_profit, rr = self._calculate_levels(
            df, signal_type
        )

        # Add RR score
        if rr >= self.MIN_RISK_REWARD:
            rr_score = min(100, (rr / self.MIN_RISK_REWARD) * 100)
            confidence += rr_score * self.WEIGHTS['risk_reward'] / 100
            reasoning.append(f"Excellent R:R = 1:{rr:.1f}")
        else:
            confidence *= 0.8  # Penalize poor R:R

        # Normalize confidence to 0-100
        confidence = min(100, max(0, confidence))

        # Create signal
        signal = Signal(
            symbol=symbol,
            signal=signal_type,
            confidence=round(confidence, 2),
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=rr,
            reasoning=reasoning,
            timestamp=datetime.now(),
            timeframe=timeframe,
            trend_score=trend_score,
            momentum_score=momentum_score,
            structure_score=structure_score,
            liquidity_score=liquidity_score,
            volume_score=volume_score
        )

        # Only return if high confidence
        if signal.signal != "NO_TRADE" and signal.confidence < self.MIN_CONFIDENCE:
            signal.signal = "NO_TRADE"
            signal.reasoning = ["Confidence below 80% threshold - no trade"]

        self.signals_history.append(signal)
        return signal

    def _score_trend_alignment(self, df: pd.DataFrame) -> float:
        """
        Score trend alignment (0-100).
        Perfect bullish = 100, Perfect bearish = 0
        """
        last = df.iloc[-1]
        score = 50  # Neutral

        # Price vs EMAs
        if 'ema_20' in df.columns and 'ema_50' in df.columns and 'ema_200' in df.columns:
            # Perfect bullish alignment
            if (last['close'] > last['ema_20'] >
                last['ema_50'] > last['ema_200']):
                score = 100

            # Strong bullish
            elif last['close'] > last['ema_20'] > last['ema_50']:
                score = 85

            # Moderate bullish
            elif last['close'] > last['ema_20']:
                score = 70

            # Perfect bearish alignment
            elif (last['close'] < last['ema_20'] <
                  last['ema_50'] < last['ema_200']):
                score = 0

            # Strong bearish
            elif last['close'] < last['ema_20'] < last['ema_50']:
                score = 15

            # Moderate bearish
            elif last['close'] < last['ema_20']:
                score = 30

        # EMA slope confirmation
        if len(df) >= 10:
            ema20_slope = (df['ema_20'].iloc[-1] - df['ema_20'].iloc[-10]) / df['ema_20'].iloc[-10]
            if ema20_slope > 0.001:  # Rising
                score += 10
            elif ema20_slope < -0.001:  # Falling
                score -= 10

        return max(0, min(100, score))

    def _score_momentum(self, df: pd.DataFrame) -> float:
        """Score momentum indicators (0-100)"""
        last = df.iloc[-1]
        score = 50

        # RSI analysis
        if 'rsi' in df.columns:
            rsi = last['rsi']

            # Optimal buy zone
            if 50 <= rsi <= 70:
                score = 90
            elif 40 <= rsi < 50:
                score = 75
            elif 70 < rsi <= 80:
                score = 65

            # Optimal sell zone
            elif 30 <= rsi <= 50:
                score = 10
            elif 20 <= rsi < 30:
                score = 25
            elif 50 < rsi <= 60:
                score = 35

            # Extreme zones (caution)
            elif rsi > 80:
                score = 40  # Overbought
            elif rsi < 20:
                score = 60  # Oversold (potential bounce)

        # MACD confirmation
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            macd_diff = last['macd'] - last['macd_signal']

            # Bullish crossover
            if macd_diff > 0 and df['macd'].iloc[-2] <= df['macd_signal'].iloc[-2]:
                score += 15
            # Bearish crossover
            elif macd_diff < 0 and df['macd'].iloc[-2] >= df['macd_signal'].iloc[-2]:
                score -= 15
            # Continued bullish
            elif macd_diff > 0:
                score += 10
            # Continued bearish
            elif macd_diff < 0:
                score -= 10

        return max(0, min(100, score))

    def _score_price_structure(self, df: pd.DataFrame) -> float:
        """Score price structure and market structure shifts"""
        score = 50

        # Detect swing highs and lows
        swing_high, swing_low = self._detect_swing_points(df)

        # Break of Structure (BOS)
        bos_bull = self._detect_bos_bullish(df, swing_high)
        bos_bear = self._detect_bos_bearish(df, swing_low)

        if bos_bull:
            score = 90
        elif bos_bear:
            score = 10

        # Change of Character (CHoCH)
        choch = self._detect_choch(df)
        if choch == 'bullish':
            score += 10
        elif choch == 'bearish':
            score -= 10

        # Higher highs and higher lows (bullish)
        if self._is_higher_highs_higher_lows(df):
            score += 15
        # Lower highs and lower lows (bearish)
        elif self._is_lower_highs_lower_lows(df):
            score -= 15

        return max(0, min(100, score))

    def _score_liquidity(self, df: pd.DataFrame) -> float:
        """Score liquidity conditions"""
        score = 50

        # Detect liquidity sweeps
        sweep_low = self._detect_liquidity_sweep_low(df)
        sweep_high = self._detect_liquidity_sweep_high(df)

        if sweep_low:
            score = 85  # Bullish (swept lows, ready to reverse)
        elif sweep_high:
            score = 15  # Bearish (swept highs, ready to reverse)

        # Order blocks
        near_demand = self._near_demand_zone(df)
        near_supply = self._near_supply_zone(df)

        if near_demand:
            score += 15
        elif near_supply:
            score -= 15

        return max(0, min(100, score))

    def _score_volume(self, df: pd.DataFrame) -> float:
        """Score volume confirmation"""
        if 'volume' not in df.columns:
            return 50

        score = 50
        last = df.iloc[-1]

        # Volume moving average
        vol_ma = df['volume'].rolling(20).mean().iloc[-1]

        # Volume spike with price increase = bullish
        if last['volume'] > vol_ma * 1.5 and last['close'] > last['open']:
            score = 90
        # Volume spike with price decrease = bearish
        elif last['volume'] > vol_ma * 1.5 and last['close'] < last['open']:
            score = 10
        # Above average volume, bullish candle
        elif last['volume'] > vol_ma and last['close'] > last['open']:
            score = 70
        # Above average volume, bearish candle
        elif last['volume'] > vol_ma and last['close'] < last['open']:
            score = 30

        return score

    def _calculate_levels(
        self,
        df: pd.DataFrame,
        signal_type: str
    ) -> Tuple[float, float, float, float]:
        """Calculate entry, stop loss, and take profit levels"""
        last = df.iloc[-1]
        atr = df['atr'].iloc[-1] if 'atr' in df.columns else (last['high'] - last['low'])

        entry = last['close']

        if signal_type == "BUY":
            # Stop loss below recent swing low or 1.5 ATR
            swing_low = self._find_recent_swing_low(df)
            sl_atr = entry - (atr * 1.5)
            stop_loss = min(swing_low, sl_atr) if swing_low else sl_atr

            # Take profit at 2-3x risk
            risk = entry - stop_loss
            take_profit = entry + (risk * 2.5)

        elif signal_type == "SELL":
            # Stop loss above recent swing high or 1.5 ATR
            swing_high = self._find_recent_swing_high(df)
            sl_atr = entry + (atr * 1.5)
            stop_loss = max(swing_high, sl_atr) if swing_high else sl_atr

            # Take profit at 2-3x risk
            risk = stop_loss - entry
            take_profit = entry - (risk * 2.5)

        else:  # NO_TRADE
            stop_loss = entry
            take_profit = entry

        # Calculate risk-reward ratio
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        rr = reward / risk if risk > 0 else 0

        return (
            round(entry, 2),
            round(stop_loss, 2),
            round(take_profit, 2),
            round(rr, 2)
        )

    # ---- Helper Methods ----

    def _detect_swing_points(self, df: pd.DataFrame, window: int = 5) -> Tuple[List, List]:
        """Detect swing highs and lows"""
        swing_highs = []
        swing_lows = []

        for i in range(window, len(df) - window):
            # Swing high
            if df['high'].iloc[i] == df['high'].iloc[i-window:i+window+1].max():
                swing_highs.append((i, df['high'].iloc[i]))

            # Swing low
            if df['low'].iloc[i] == df['low'].iloc[i-window:i+window+1].min():
                swing_lows.append((i, df['low'].iloc[i]))

        return swing_highs, swing_lows

    def _detect_bos_bullish(self, df: pd.DataFrame, swing_highs: List) -> bool:
        """Detect bullish break of structure"""
        if len(swing_highs) < 2:
            return False

        # Check if we recently broke above previous swing high
        recent_high = swing_highs[-1][1]
        current_price = df['close'].iloc[-1]

        return current_price > recent_high * 1.001  # 0.1% above

    def _detect_bos_bearish(self, df: pd.DataFrame, swing_lows: List) -> bool:
        """Detect bearish break of structure"""
        if len(swing_lows) < 2:
            return False

        recent_low = swing_lows[-1][1]
        current_price = df['close'].iloc[-1]

        return current_price < recent_low * 0.999

    def _detect_choch(self, df: pd.DataFrame) -> Optional[str]:
        """Detect change of character"""
        # Simplified: look for trend reversal patterns
        if len(df) < 20:
            return None

        recent = df.tail(20)

        # Was bearish, now turning bullish
        if (recent['close'].iloc[:10].mean() < recent['close'].iloc[-10:].mean() and
            recent['ema_20'].iloc[-1] > recent['ema_20'].iloc[-5]):
            return 'bullish'

        # Was bullish, now turning bearish
        elif (recent['close'].iloc[:10].mean() > recent['close'].iloc[-10:].mean() and
              recent['ema_20'].iloc[-1] < recent['ema_20'].iloc[-5]):
            return 'bearish'

        return None

    def _is_higher_highs_higher_lows(self, df: pd.DataFrame, periods: int = 3) -> bool:
        """Check for higher highs and higher lows pattern"""
        if len(df) < periods * 5:
            return False

        highs = df['high'].rolling(5).max().dropna().tail(periods)
        lows = df['low'].rolling(5).min().dropna().tail(periods)

        return highs.is_monotonic_increasing and lows.is_monotonic_increasing

    def _is_lower_highs_lower_lows(self, df: pd.DataFrame, periods: int = 3) -> bool:
        """Check for lower highs and lower lows pattern"""
        if len(df) < periods * 5:
            return False

        highs = df['high'].rolling(5).max().dropna().tail(periods)
        lows = df['low'].rolling(5).min().dropna().tail(periods)

        return highs.is_monotonic_decreasing and lows.is_monotonic_decreasing

    def _detect_liquidity_sweep_low(self, df: pd.DataFrame) -> bool:
        """Detect if we swept below previous lows and reversed"""
        if len(df) < 10:
            return False

        recent_low = df['low'].iloc[-10:-1].min()
        current_candle = df.iloc[-1]

        # Swept low and closed back above
        return (current_candle['low'] < recent_low and
                current_candle['close'] > recent_low)

    def _detect_liquidity_sweep_high(self, df: pd.DataFrame) -> bool:
        """Detect if we swept above previous highs and reversed"""
        if len(df) < 10:
            return False

        recent_high = df['high'].iloc[-10:-1].max()
        current_candle = df.iloc[-1]

        return (current_candle['high'] > recent_high and
                current_candle['close'] < recent_high)

    def _near_demand_zone(self, df: pd.DataFrame) -> bool:
        """Check if price is near a demand zone (bullish order block)"""
        # Simplified: strong bullish candles in recent past
        if len(df) < 20:
            return False

        for i in range(-20, -1):
            candle = df.iloc[i]
            if (candle['close'] > candle['open'] * 1.02 and  # 2% bullish candle
                abs(df['close'].iloc[-1] - candle['low']) / candle['low'] < 0.01):  # Within 1%
                return True
        return False

    def _near_supply_zone(self, df: pd.DataFrame) -> bool:
        """Check if price is near a supply zone (bearish order block)"""
        if len(df) < 20:
            return False

        for i in range(-20, -1):
            candle = df.iloc[i]
            if (candle['close'] < candle['open'] * 0.98 and
                abs(df['close'].iloc[-1] - candle['high']) / candle['high'] < 0.01):
                return True
        return False

    def _find_recent_swing_low(self, df: pd.DataFrame, lookback: int = 20) -> Optional[float]:
        """Find recent swing low for stop loss"""
        if len(df) < lookback:
            return None
        return df['low'].iloc[-lookback:].min()

    def _find_recent_swing_high(self, df: pd.DataFrame, lookback: int = 20) -> Optional[float]:
        """Find recent swing high for stop loss"""
        if len(df) < lookback:
            return None
        return df['high'].iloc[-lookback:].max()

    def _get_bullish_reasons(self, df: pd.DataFrame) -> List[str]:
        """Get list of bullish reasons"""
        reasons = []
        last = df.iloc[-1]

        if last['close'] > last.get('ema_20', 0):
            reasons.append("Price above EMA20 (short-term bullish)")
        if last.get('ema_20', 0) > last.get('ema_50', 0):
            reasons.append("EMA20 > EMA50 (trend confirmation)")
        if 50 <= last.get('rsi', 50) <= 70:
            reasons.append(f"RSI in healthy bullish zone ({last.get('rsi', 0):.1f})")
        if last.get('macd', 0) > last.get('macd_signal', 0):
            reasons.append("MACD bullish crossover")
        if last['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.2:
            reasons.append("Above-average volume confirmation")

        return reasons

    def _get_bearish_reasons(self, df: pd.DataFrame) -> List[str]:
        """Get list of bearish reasons"""
        reasons = []
        last = df.iloc[-1]

        if last['close'] < last.get('ema_20', 0):
            reasons.append("Price below EMA20 (short-term bearish)")
        if last.get('ema_20', 0) < last.get('ema_50', 0):
            reasons.append("EMA20 < EMA50 (downtrend confirmation)")
        if 30 <= last.get('rsi', 50) <= 50:
            reasons.append(f"RSI in bearish zone ({last.get('rsi', 0):.1f})")
        if last.get('macd', 0) < last.get('macd_signal', 0):
            reasons.append("MACD bearish crossover")
        if last['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.2:
            reasons.append("Above-average volume confirmation")

        return reasons


# Example usage
if __name__ == "__main__":
    # This would be called with real data
    engine = SignalEngine()

    # Mock data for demonstration
    mock_df = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105],
        'open': [99, 100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105, 106],
        'low': [99, 100, 101, 102, 103, 104],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500],
        'ema_20': [98, 99, 100, 101, 102, 103],
        'ema_50': [97, 98, 99, 100, 101, 102],
        'ema_200': [95, 96, 97, 98, 99, 100],
        'rsi': [55, 58, 60, 62, 65, 68],
        'macd': [1, 1.2, 1.5, 1.8, 2.1, 2.5],
        'macd_signal': [0.8, 1.0, 1.2, 1.5, 1.8, 2.0],
        'atr': [2, 2, 2, 2, 2, 2]
    })

    signal = engine.generate_signal('BTCUSDT', mock_df, '15m')

    print(f"\n{'='*60}")
    print(f"SIGNAL: {signal.signal}")
    print(f"Confidence: {signal.confidence}%")
    print(f"Entry: ${signal.entry}")
    print(f"Stop Loss: ${signal.stop_loss}")
    print(f"Take Profit: ${signal.take_profit}")
    print(f"Risk:Reward = 1:{signal.risk_reward}")
    print(f"\nReasons:")
    for reason in signal.reasoning:
        print(f"  • {reason}")
    print(f"{'='*60}\n")
