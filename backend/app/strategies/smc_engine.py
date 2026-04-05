"""
Precise SMC Logic Engine with Mathematical Definitions
Implements Order Blocks, Fair Value Gaps, Liquidity Zones, and Structure Events
with exact mathematical rules and validation criteria.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from app.models.smc_models import (
    OrderBlock, FairValueGap, LiquidityZone, StructureEvent, SMCAnalysis,
    OrderBlockType, FVGType, LiquidityType, StructureType, ConfidenceLevel,
    SignalType, SMCDetectionConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreciseSMCEngine:
    """
    Precise Smart Money Concepts Engine
    Implements mathematically precise SMC pattern detection
    """
    
    def __init__(self, config: SMCDetectionConfig = None):
        self.config = config or SMCDetectionConfig()
        logger.info("Precise SMC Engine initialized")
    
    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> SMCAnalysis:
        """
        Complete SMC analysis with precise mathematical rules
        
        Args:
            df: OHLCV DataFrame with timestamp index
            symbol: Trading pair symbol
            timeframe: Timeframe string
            
        Returns:
            SMCAnalysis with all detected patterns
        """
        logger.info(f"Starting precise SMC analysis for {symbol} {timeframe}")
        
        # Validate DataFrame
        if len(df) < 50:
            raise ValueError("Insufficient data for SMC analysis (minimum 50 candles required)")
        
        # Calculate ATR for validation
        atr_14 = self._calculate_atr(df, self.config.atr_period)
        current_price = df['close'].iloc[-1]
        
        # Detect all SMC patterns with precise rules
        order_blocks = self.detect_order_blocks(df, atr_14, timeframe)
        fair_value_gaps = self.detect_fvg(df, atr_14, timeframe)
        liquidity_zones = self.detect_liquidity(df, timeframe)
        structure_events = self.detect_structure(df, timeframe)
        
        # Calculate analysis metrics
        detection_summary = {
            "order_blocks": len(order_blocks),
            "fair_value_gaps": len(fair_value_gaps),
            "liquidity_zones": len(liquidity_zones),
            "structure_events": len(structure_events)
        }
        
        high_confidence_patterns = sum([
            len([ob for ob in order_blocks if ob.confidence == ConfidenceLevel.HIGH]),
            len([fvg for fvg in fair_value_gaps if fvg.confidence == ConfidenceLevel.HIGH]),
            len([lz for lz in liquidity_zones if lz.confidence == ConfidenceLevel.HIGH]),
            len([se for se in structure_events if se.confidence == ConfidenceLevel.HIGH])
        ])
        
        active_patterns = sum([
            len([ob for ob in order_blocks if not ob.mitigated]),
            len([fvg for fvg in fair_value_gaps if not fvg.filled]),
            len([lz for lz in liquidity_zones if not lz.swept])
        ])
        
        # Determine current trend from structure events
        current_trend = self._determine_current_trend(structure_events)
        
        analysis = SMCAnalysis(
            symbol=symbol,
            timeframe=timeframe,
            analysis_timestamp=datetime.now(),
            order_blocks=order_blocks,
            fair_value_gaps=fair_value_gaps,
            liquidity_zones=liquidity_zones,
            structure_events=structure_events,
            current_trend=current_trend,
            atr_14=atr_14,
            current_price=current_price,
            candles_analyzed=len(df),
            detection_summary=detection_summary,
            high_confidence_patterns=high_confidence_patterns,
            active_patterns=active_patterns
        )
        
        logger.info(f"SMC analysis complete: {detection_summary}")
        return analysis
    
    def detect_order_blocks(self, df: pd.DataFrame, atr_14: float, timeframe: str) -> List[OrderBlock]:
        """
        Detect Order Blocks with precise mathematical rules
        
        Rules:
        - Bullish OB: Last RED candle before a strong bullish impulse
        - Bearish OB: Last GREEN candle before a strong bearish impulse
        - "Strong impulse" = next candle closes beyond last 3 candles' high/low
        - "Displacement" required: impulse candle body > 1.5x ATR(14)
        - OB is INVALID (mitigated) if price closes inside the OB zone
        
        Args:
            df: OHLCV DataFrame
            atr_14: 14-period ATR value
            timeframe: Timeframe string
            
        Returns:
            List of OrderBlock objects
        """
        logger.info("Detecting Order Blocks with precise rules")
        order_blocks = []
        
        # Need at least 5 candles for pattern detection
        if len(df) < 5:
            return order_blocks
        
        for i in range(4, len(df) - 1):  # Leave room for impulse candle
            current_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Get last 3 candles for high/low reference
            last_3_highs = df['high'].iloc[i-3:i].max()
            last_3_lows = df['low'].iloc[i-3:i].min()
            
            # Check for bullish Order Block
            if self._is_bearish_candle(current_candle):  # Last RED candle
                # Check for strong bullish impulse
                impulse_body = abs(next_candle['close'] - next_candle['open'])
                displacement_valid = impulse_body > (self.config.min_displacement_atr_multiple * atr_14)
                
                # Check if next candle closes beyond last 3 candles' high
                strong_impulse = next_candle['close'] > last_3_highs
                
                if displacement_valid and strong_impulse:
                    # Create bullish Order Block
                    ob = self._create_order_block(
                        candle=current_candle,
                        candle_index=i,
                        impulse_candle_index=i + 1,
                        ob_type=OrderBlockType.BULLISH,
                        displacement_size=impulse_body,
                        atr_14=atr_14,
                        timeframe=timeframe,
                        df=df
                    )
                    
                    # Check if already mitigated
                    ob = self._check_ob_mitigation(ob, df, i + 2)
                    order_blocks.append(ob)
            
            # Check for bearish Order Block
            elif self._is_bullish_candle(current_candle):  # Last GREEN candle
                # Check for strong bearish impulse
                impulse_body = abs(next_candle['close'] - next_candle['open'])
                displacement_valid = impulse_body > (self.config.min_displacement_atr_multiple * atr_14)
                
                # Check if next candle closes beyond last 3 candles' low
                strong_impulse = next_candle['close'] < last_3_lows
                
                if displacement_valid and strong_impulse:
                    # Create bearish Order Block
                    ob = self._create_order_block(
                        candle=current_candle,
                        candle_index=i,
                        impulse_candle_index=i + 1,
                        ob_type=OrderBlockType.BEARISH,
                        displacement_size=impulse_body,
                        atr_14=atr_14,
                        timeframe=timeframe,
                        df=df
                    )
                    
                    # Check if already mitigated
                    ob = self._check_ob_mitigation(ob, df, i + 2)
                    order_blocks.append(ob)
        
        logger.info(f"Detected {len(order_blocks)} Order Blocks")
        return order_blocks
    
    def detect_fvg(self, df: pd.DataFrame, atr_14: float, timeframe: str) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps with precise mathematical rules
        
        Rules:
        - Bullish FVG: candle[i+1].low > candle[i-1].high (gap between them)
        - Bearish FVG: candle[i+1].high < candle[i-1].low
        - MINIMUM SIZE filter: gap_size > 0.3 * ATR(14) — ignore micro gaps
        - Track fill status: { filled: bool, fill_pct: float, fill_time: timestamp }
        - Partially filled FVGs remain valid until 100% filled
        
        Args:
            df: OHLCV DataFrame
            atr_14: 14-period ATR value
            timeframe: Timeframe string
            
        Returns:
            List of FairValueGap objects
        """
        logger.info("Detecting Fair Value Gaps with precise rules")
        fair_value_gaps = []
        
        # Need at least 3 candles for FVG detection
        if len(df) < 3:
            return fair_value_gaps
        
        min_gap_size = self.config.min_fvg_atr_multiple * atr_14
        
        for i in range(1, len(df) - 1):  # i is the middle candle
            candle_before = df.iloc[i - 1]  # i-1
            candle_middle = df.iloc[i]      # i
            candle_after = df.iloc[i + 1]   # i+1
            
            # Check for Bullish FVG
            if candle_after['low'] > candle_before['high']:
                gap_size = candle_after['low'] - candle_before['high']
                
                if gap_size > min_gap_size:  # Minimum size filter
                    fvg = self._create_fvg(
                        top=candle_after['low'],
                        bottom=candle_before['high'],
                        gap_size=gap_size,
                        candle_index=i,
                        fvg_type=FVGType.BULLISH,
                        atr_14=atr_14,
                        timeframe=timeframe,
                        candle_before_index=i - 1,
                        candle_middle_index=i,
                        candle_after_index=i + 1,
                        df=df
                    )
                    
                    # Check if already filled
                    fvg = self._check_fvg_fill(fvg, df, i + 2)
                    fair_value_gaps.append(fvg)
            
            # Check for Bearish FVG
            elif candle_after['high'] < candle_before['low']:
                gap_size = candle_before['low'] - candle_after['high']
                
                if gap_size > min_gap_size:  # Minimum size filter
                    fvg = self._create_fvg(
                        top=candle_before['low'],
                        bottom=candle_after['high'],
                        gap_size=gap_size,
                        candle_index=i,
                        fvg_type=FVGType.BEARISH,
                        atr_14=atr_14,
                        timeframe=timeframe,
                        candle_before_index=i - 1,
                        candle_middle_index=i,
                        candle_after_index=i + 1,
                        df=df
                    )
                    
                    # Check if already filled
                    fvg = self._check_fvg_fill(fvg, df, i + 2)
                    fair_value_gaps.append(fvg)
        
        logger.info(f"Detected {len(fair_value_gaps)} Fair Value Gaps")
        return fair_value_gaps
    
    def detect_liquidity(self, df: pd.DataFrame, timeframe: str, tolerance: float = None) -> List[LiquidityZone]:
        """
        Detect Liquidity Zones with precise mathematical rules
        
        Rules:
        - Equal Highs: two or more highs within 0.1% price tolerance
        - Equal Lows: two or more lows within 0.1% price tolerance
        - Minimum 5 candles between equal levels
        - Liquidity "swept" when price closes beyond the level
        - Mark as swept with timestamp
        - Swept liquidity = potential reversal zone (high priority signal)
        
        Args:
            df: OHLCV DataFrame
            timeframe: Timeframe string
            tolerance: Price tolerance (default from config)
            
        Returns:
            List of LiquidityZone objects
        """
        logger.info("Detecting Liquidity Zones with precise rules")
        liquidity_zones = []
        
        if len(df) < 10:
            return liquidity_zones
        
        tolerance = tolerance or self.config.liquidity_price_tolerance
        min_distance = self.config.min_candles_between_levels
        
        # Find swing highs and lows
        swing_highs = self._find_swing_points(df, 'high')
        swing_lows = self._find_swing_points(df, 'low')
        
        # Group equal highs
        equal_highs_groups = self._group_equal_levels(swing_highs, tolerance, min_distance)
        for price_level, indices in equal_highs_groups.items():
            if len(indices) >= 2:  # At least 2 equal levels
                lz = self._create_liquidity_zone(
                    price=price_level,
                    zone_type=LiquidityType.EQUAL_HIGHS,
                    equal_levels=indices,
                    tolerance=tolerance,
                    timeframe=timeframe,
                    df=df
                )
                
                # Check if already swept
                lz = self._check_liquidity_sweep(lz, df)
                liquidity_zones.append(lz)
        
        # Group equal lows
        equal_lows_groups = self._group_equal_levels(swing_lows, tolerance, min_distance)
        for price_level, indices in equal_lows_groups.items():
            if len(indices) >= 2:  # At least 2 equal levels
                lz = self._create_liquidity_zone(
                    price=price_level,
                    zone_type=LiquidityType.EQUAL_LOWS,
                    equal_levels=indices,
                    tolerance=tolerance,
                    timeframe=timeframe,
                    df=df
                )
                
                # Check if already swept
                lz = self._check_liquidity_sweep(lz, df)
                liquidity_zones.append(lz)
        
        logger.info(f"Detected {len(liquidity_zones)} Liquidity Zones")
        return liquidity_zones
    
    def detect_structure(self, df: pd.DataFrame, timeframe: str) -> List[StructureEvent]:
        """
        Detect Structure Events (BOS vs CHOCH) with precise distinction
        
        BOS Rules:
        - In uptrend: price breaks above previous Higher High → BOS bullish
        - In downtrend: price breaks below previous Lower Low → BOS bearish  
        - Signal type: CONTINUATION
        - Position size: 100% of calculated size
        
        CHOCH Rules:
        - In uptrend: price breaks below most recent Higher Low → CHOCH bearish
        - In downtrend: price breaks above most recent Lower High → CHOCH bullish
        - Signal type: REVERSAL (higher risk)
        - Position size: 50% of calculated size (half size for reversals)
        
        Args:
            df: OHLCV DataFrame
            timeframe: Timeframe string
            
        Returns:
            List of StructureEvent objects
        """
        logger.info("Detecting Structure Events (BOS vs CHOCH) with precise rules")
        structure_events = []
        
        if len(df) < self.config.structure_lookback_periods:
            return structure_events
        
        # Find swing points for structure analysis
        swing_highs = self._find_swing_points(df, 'high')
        swing_lows = self._find_swing_points(df, 'low')
        
        # Create combined swing points timeline
        all_swings = []
        for price, indices in swing_highs.items():
            for idx in indices:
                all_swings.append({
                    'index': idx,
                    'price': price,
                    'type': 'high',
                    'timestamp': df.index[idx]
                })
        
        for price, indices in swing_lows.items():
            for idx in indices:
                all_swings.append({
                    'index': idx,
                    'price': price,
                    'type': 'low',
                    'timestamp': df.index[idx]
                })
        
        # Sort by index to get chronological order
        all_swings.sort(key=lambda x: x['index'])
        
        if len(all_swings) < 4:  # Need at least 4 swing points
            return structure_events
        
        # Analyze structure sequence
        for i in range(3, len(all_swings)):
            current_swing = all_swings[i]
            previous_swings = all_swings[max(0, i-10):i]  # Look back up to 10 swings
            
            # Determine current trend from recent swings
            trend = self._determine_trend_from_swings(previous_swings)
            
            # Check for BOS or CHOCH
            structure_event = self._analyze_structure_break(
                current_swing, previous_swings, trend, df, timeframe
            )
            
            if structure_event:
                structure_events.append(structure_event)
        
        logger.info(f"Detected {len(structure_events)} Structure Events")
        return structure_events
    
    # Helper methods for precise calculations
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else (df['high'].iloc[-1] - df['low'].iloc[-1])
    
    def _is_bullish_candle(self, candle) -> bool:
        """Check if candle is bullish (green)"""
        return candle['close'] > candle['open']
    
    def _is_bearish_candle(self, candle) -> bool:
        """Check if candle is bearish (red)"""
        return candle['close'] < candle['open']
    
    def _create_order_block(
        self, candle, candle_index: int, impulse_candle_index: int,
        ob_type: OrderBlockType, displacement_size: float, atr_14: float,
        timeframe: str, df: pd.DataFrame
    ) -> OrderBlock:
        """Create OrderBlock object with all required fields"""
        
        # Calculate confidence based on displacement size
        atr_multiple = displacement_size / atr_14
        if atr_multiple >= self.config.ob_confidence_thresholds["high"]:
            confidence = ConfidenceLevel.HIGH
        elif atr_multiple >= self.config.ob_confidence_thresholds["medium"]:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Set invalidation price
        if ob_type == OrderBlockType.BULLISH:
            invalidation_price = candle['low'] - (0.1 * atr_14)  # 10% ATR buffer below
        else:
            invalidation_price = candle['high'] + (0.1 * atr_14)  # 10% ATR buffer above
        
        return OrderBlock(
            top=candle['high'],
            bottom=candle['low'],
            timestamp=candle.name,
            candle_index=candle_index,
            ob_type=ob_type,
            timeframe=timeframe,
            displacement_size=displacement_size,
            atr_multiple=atr_multiple,
            confidence=confidence,
            invalidation_price=invalidation_price,
            impulse_candle_index=impulse_candle_index,
            strength=min(5, max(1, int(atr_multiple)))  # 1-5 scale based on ATR multiple
        )
    
    def _check_ob_mitigation(self, ob: OrderBlock, df: pd.DataFrame, start_index: int) -> OrderBlock:
        """Check if Order Block has been mitigated"""
        for i in range(start_index, len(df)):
            candle = df.iloc[i]
            
            # OB is mitigated if price closes inside the OB zone
            if ob.bottom <= candle['close'] <= ob.top:
                ob.mitigated = True
                ob.mitigation_time = candle.name
                ob.mitigation_price = candle['close']
                break
        
        return ob
    
    def _create_fvg(
        self, top: float, bottom: float, gap_size: float, candle_index: int,
        fvg_type: FVGType, atr_14: float, timeframe: str,
        candle_before_index: int, candle_middle_index: int, candle_after_index: int,
        df: pd.DataFrame
    ) -> FairValueGap:
        """Create FairValueGap object with all required fields"""
        
        # Calculate confidence based on gap size
        atr_multiple = gap_size / atr_14
        if atr_multiple >= self.config.fvg_confidence_thresholds["high"]:
            confidence = ConfidenceLevel.HIGH
        elif atr_multiple >= self.config.fvg_confidence_thresholds["medium"]:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Set invalidation price
        if fvg_type == FVGType.BULLISH:
            invalidation_price = bottom - (0.1 * atr_14)  # Below the gap
        else:
            invalidation_price = top + (0.1 * atr_14)     # Above the gap
        
        return FairValueGap(
            top=top,
            bottom=bottom,
            gap_size=gap_size,
            timestamp=df.index[candle_index],
            candle_index=candle_index,
            fvg_type=fvg_type,
            timeframe=timeframe,
            atr_multiple=atr_multiple,
            min_size_met=True,  # Already filtered by minimum size
            confidence=confidence,
            invalidation_price=invalidation_price,
            candle_before_index=candle_before_index,
            candle_middle_index=candle_middle_index,
            candle_after_index=candle_after_index
        )
    
    def _check_fvg_fill(self, fvg: FairValueGap, df: pd.DataFrame, start_index: int) -> FairValueGap:
        """Check if Fair Value Gap has been filled"""
        gap_range = fvg.top - fvg.bottom
        
        for i in range(start_index, len(df)):
            candle = df.iloc[i]
            
            # Calculate how much of the gap has been filled
            if fvg.fvg_type == FVGType.BULLISH:
                # For bullish FVG, filling happens when price goes down into the gap
                if candle['low'] <= fvg.top:
                    fill_amount = min(fvg.top - candle['low'], gap_range)
                    fill_percentage = (fill_amount / gap_range) * 100
                    
                    fvg.fill_percentage = max(fvg.fill_percentage, fill_percentage)
                    fvg.partial_fill_prices.append(candle['low'])
                    
                    if candle['low'] <= fvg.bottom:  # Completely filled
                        fvg.filled = True
                        fvg.fill_time = candle.name
                        fvg.fill_percentage = 100.0
                        break
            
            else:  # Bearish FVG
                # For bearish FVG, filling happens when price goes up into the gap
                if candle['high'] >= fvg.bottom:
                    fill_amount = min(candle['high'] - fvg.bottom, gap_range)
                    fill_percentage = (fill_amount / gap_range) * 100
                    
                    fvg.fill_percentage = max(fvg.fill_percentage, fill_percentage)
                    fvg.partial_fill_prices.append(candle['high'])
                    
                    if candle['high'] >= fvg.top:  # Completely filled
                        fvg.filled = True
                        fvg.fill_time = candle.name
                        fvg.fill_percentage = 100.0
                        break
        
        return fvg
    
    def _find_swing_points(self, df: pd.DataFrame, price_type: str, period: int = 5) -> Dict[float, List[int]]:
        """Find swing highs or lows"""
        swing_points = {}
        
        if price_type == 'high':
            for i in range(period, len(df) - period):
                current_high = df['high'].iloc[i]
                
                # Check if current high is higher than surrounding candles
                left_highs = df['high'].iloc[i-period:i]
                right_highs = df['high'].iloc[i+1:i+period+1]
                
                if (current_high > left_highs.max()) and (current_high > right_highs.max()):
                    if current_high not in swing_points:
                        swing_points[current_high] = []
                    swing_points[current_high].append(i)
        
        else:  # 'low'
            for i in range(period, len(df) - period):
                current_low = df['low'].iloc[i]
                
                # Check if current low is lower than surrounding candles
                left_lows = df['low'].iloc[i-period:i]
                right_lows = df['low'].iloc[i+1:i+period+1]
                
                if (current_low < left_lows.min()) and (current_low < right_lows.min()):
                    if current_low not in swing_points:
                        swing_points[current_low] = []
                    swing_points[current_low].append(i)
        
        return swing_points
    
    def _group_equal_levels(self, swing_points: Dict[float, List[int]], tolerance: float, min_distance: int) -> Dict[float, List[Dict]]:
        """Group swing points that are within tolerance of each other"""
        equal_groups = {}
        processed_prices = set()
        
        for price1, indices1 in swing_points.items():
            if price1 in processed_prices:
                continue
            
            group = []
            for idx1 in indices1:
                group.append({'price': price1, 'index': idx1})
            
            # Find other prices within tolerance
            for price2, indices2 in swing_points.items():
                if price2 == price1 or price2 in processed_prices:
                    continue
                
                # Check if prices are within tolerance
                if abs(price1 - price2) / price1 <= tolerance:
                    for idx2 in indices2:
                        # Check minimum distance requirement
                        min_distance_met = all(abs(idx2 - existing['index']) >= min_distance for existing in group)
                        if min_distance_met:
                            group.append({'price': price2, 'index': idx2})
                    processed_prices.add(price2)
            
            if len(group) >= 2:  # At least 2 equal levels
                avg_price = sum(point['price'] for point in group) / len(group)
                equal_groups[avg_price] = group
            
            processed_prices.add(price1)
        
        return equal_groups
    
    def _create_liquidity_zone(
        self, price: float, zone_type: LiquidityType, equal_levels: List[Dict],
        tolerance: float, timeframe: str, df: pd.DataFrame
    ) -> LiquidityZone:
        """Create LiquidityZone object with all required fields"""
        
        # Calculate confidence based on number of equal levels
        level_count = len(equal_levels)
        if level_count >= self.config.liquidity_confidence_thresholds["high"]:
            confidence = ConfidenceLevel.HIGH
        elif level_count >= self.config.liquidity_confidence_thresholds["medium"]:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Set invalidation price
        if zone_type == LiquidityType.EQUAL_HIGHS:
            invalidation_price = price + (price * tolerance * 2)  # 2x tolerance above
        else:
            invalidation_price = price - (price * tolerance * 2)  # 2x tolerance below
        
        # Get earliest timestamp
        earliest_index = min(level['index'] for level in equal_levels)
        timestamp = df.index[earliest_index]
        
        return LiquidityZone(
            price=price,
            zone_type=zone_type,
            timestamp=timestamp,
            equal_levels=equal_levels,
            level_count=level_count,
            price_tolerance=tolerance,
            min_candle_distance_met=True,  # Already validated
            timeframe=timeframe,
            confidence=confidence,
            strength=min(5, level_count),  # 1-5 scale
            invalidation_price=invalidation_price
        )
    
    def _check_liquidity_sweep(self, lz: LiquidityZone, df: pd.DataFrame) -> LiquidityZone:
        """Check if liquidity has been swept"""
        latest_level_index = max(level['index'] for level in lz.equal_levels)
        
        for i in range(latest_level_index + 1, len(df)):
            candle = df.iloc[i]
            
            # Check for sweep based on zone type
            if lz.zone_type == LiquidityType.EQUAL_HIGHS:
                # Swept when price closes above the high
                if candle['close'] > lz.price:
                    lz.swept = True
                    lz.sweep_time = candle.name
                    lz.sweep_price = candle['close']
                    lz.sweep_candle_index = i
                    break
            
            else:  # EQUAL_LOWS
                # Swept when price closes below the low
                if candle['close'] < lz.price:
                    lz.swept = True
                    lz.sweep_time = candle.name
                    lz.sweep_price = candle['close']
                    lz.sweep_candle_index = i
                    break
        
        return lz
    
    def _determine_trend_from_swings(self, swings: List[Dict]) -> str:
        """Determine trend from swing sequence"""
        if len(swings) < 4:
            return "neutral"
        
        # Look at recent 4 swings to determine trend
        recent_swings = swings[-4:]
        
        # Count higher highs/lows and lower highs/lows
        hh_count = 0  # Higher Highs
        hl_count = 0  # Higher Lows
        lh_count = 0  # Lower Highs
        ll_count = 0  # Lower Lows
        
        for i in range(1, len(recent_swings)):
            current = recent_swings[i]
            previous = recent_swings[i-1]
            
            if current['type'] == 'high':
                if current['price'] > previous['price']:
                    hh_count += 1
                else:
                    lh_count += 1
            else:  # 'low'
                if current['price'] > previous['price']:
                    hl_count += 1
                else:
                    ll_count += 1
        
        # Determine trend
        if hh_count > 0 and hl_count > 0:
            return "uptrend"
        elif lh_count > 0 and ll_count > 0:
            return "downtrend"
        else:
            return "neutral"
    
    def _analyze_structure_break(
        self, current_swing: Dict, previous_swings: List[Dict], 
        trend: str, df: pd.DataFrame, timeframe: str
    ) -> Optional[StructureEvent]:
        """Analyze if current swing represents a structure break (BOS or CHOCH)"""
        
        if trend == "neutral" or len(previous_swings) < 3:
            return None
        
        current_index = current_swing['index']
        current_price = current_swing['price']
        current_type = current_swing['type']
        
        # Find relevant previous levels
        if trend == "uptrend":
            # In uptrend, look for previous HH and HL
            previous_hh = self._find_previous_level(previous_swings, 'high', 'highest')
            previous_hl = self._find_previous_level(previous_swings, 'low', 'highest')
            
            if current_type == 'high' and previous_hh:
                # Check for BOS bullish (break above previous HH)
                if current_price > previous_hh['price']:
                    return self._create_structure_event(
                        structure_type=StructureType.BOS_BULLISH,
                        current_swing=current_swing,
                        break_price=previous_hh['price'],
                        signal_type=SignalType.CONTINUATION,
                        position_multiplier=1.0,
                        trend=trend,
                        timeframe=timeframe,
                        df=df
                    )
            
            elif current_type == 'low' and previous_hl:
                # Check for CHOCH bearish (break below previous HL)
                if current_price < previous_hl['price']:
                    return self._create_structure_event(
                        structure_type=StructureType.CHOCH_BEARISH,
                        current_swing=current_swing,
                        break_price=previous_hl['price'],
                        signal_type=SignalType.REVERSAL,
                        position_multiplier=0.5,
                        trend=trend,
                        timeframe=timeframe,
                        df=df
                    )
        
        elif trend == "downtrend":
            # In downtrend, look for previous LL and LH
            previous_ll = self._find_previous_level(previous_swings, 'low', 'lowest')
            previous_lh = self._find_previous_level(previous_swings, 'high', 'lowest')
            
            if current_type == 'low' and previous_ll:
                # Check for BOS bearish (break below previous LL)
                if current_price < previous_ll['price']:
                    return self._create_structure_event(
                        structure_type=StructureType.BOS_BEARISH,
                        current_swing=current_swing,
                        break_price=previous_ll['price'],
                        signal_type=SignalType.CONTINUATION,
                        position_multiplier=1.0,
                        trend=trend,
                        timeframe=timeframe,
                        df=df
                    )
            
            elif current_type == 'high' and previous_lh:
                # Check for CHOCH bullish (break above previous LH)
                if current_price > previous_lh['price']:
                    return self._create_structure_event(
                        structure_type=StructureType.CHOCH_BULLISH,
                        current_swing=current_swing,
                        break_price=previous_lh['price'],
                        signal_type=SignalType.REVERSAL,
                        position_multiplier=0.5,
                        trend=trend,
                        timeframe=timeframe,
                        df=df
                    )
        
        return None
    
    def _find_previous_level(self, swings: List[Dict], swing_type: str, selection: str) -> Optional[Dict]:
        """Find previous swing level of specified type"""
        matching_swings = [s for s in swings if s['type'] == swing_type]
        
        if not matching_swings:
            return None
        
        if selection == 'highest':
            return max(matching_swings, key=lambda x: x['price'])
        elif selection == 'lowest':
            return min(matching_swings, key=lambda x: x['price'])
        else:
            return matching_swings[-1]  # Most recent
    
    def _create_structure_event(
        self, structure_type: StructureType, current_swing: Dict, break_price: float,
        signal_type: SignalType, position_multiplier: float, trend: str,
        timeframe: str, df: pd.DataFrame
    ) -> StructureEvent:
        """Create StructureEvent object"""
        
        # Determine confidence based on break size
        break_percentage = abs(current_swing['price'] - break_price) / break_price
        if break_percentage >= 0.01:  # 1% break
            confidence = ConfidenceLevel.HIGH
        elif break_percentage >= 0.005:  # 0.5% break
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Set invalidation price
        if structure_type in [StructureType.BOS_BULLISH, StructureType.CHOCH_BULLISH]:
            invalidation_price = break_price * 0.99  # 1% below break level
            new_trend = "uptrend"
        else:
            invalidation_price = break_price * 1.01  # 1% above break level
            new_trend = "downtrend"
        
        # Get close price at the break
        close_price = df['close'].iloc[current_swing['index']]
        
        return StructureEvent(
            structure_type=structure_type,
            timestamp=df.index[current_swing['index']],
            candle_index=current_swing['index'],
            break_price=break_price,
            close_price=close_price,
            previous_structure_price=current_swing['price'],
            signal_type=signal_type,
            position_size_multiplier=position_multiplier,
            previous_trend=trend,
            new_trend=new_trend,
            timeframe=timeframe,
            confidence=confidence,
            invalidation_price=invalidation_price
        )
    
    def _determine_current_trend(self, structure_events: List[StructureEvent]) -> str:
        """Determine current trend from recent structure events"""
        if not structure_events:
            return "neutral"
        
        # Look at most recent structure event
        latest_event = max(structure_events, key=lambda x: x.candle_index)
        return latest_event.new_trend