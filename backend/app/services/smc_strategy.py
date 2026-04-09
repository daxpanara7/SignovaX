import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime
from app.models.market_data import LiquidityZone, OrderBlock, FairValueGap, SMCAnalysis

class SMCStrategy:
    """Smart Money Concepts Strategy Implementation"""
    
    def __init__(self):
        self.lookback_period = 20
        self.liquidity_threshold = 3  # Minimum touches for liquidity zone
    
    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> SMCAnalysis:
        """Main analysis function that detects all SMC concepts"""
        
        # Detect all SMC patterns
        liquidity_zones = self.detect_liquidity_zones(df)
        order_blocks = self.detect_order_blocks(df)
        fair_value_gaps = self.detect_fair_value_gaps(df)
        bos_signals = self.detect_break_of_structure(df)
        choch_signals = self.detect_change_of_character(df)
        
        return SMCAnalysis(
            symbol=symbol,
            timeframe=timeframe,
            liquidity_zones=liquidity_zones,
            order_blocks=order_blocks,
            fair_value_gaps=fair_value_gaps,
            bos_signals=bos_signals,
            choch_signals=choch_signals,
            analysis_timestamp=datetime.now()
        )
    
    def detect_liquidity_zones(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """Detect equal highs/lows that represent liquidity zones"""
        zones = []
        
        # Find swing highs and lows
        swing_highs = self._find_swing_points(df['high'], 'high')
        swing_lows = self._find_swing_points(df['low'], 'low')
        
        # Group similar levels (within 0.5% tolerance)
        tolerance = 0.005
        
        # Process resistance zones (swing highs)
        high_groups = self._group_similar_levels(swing_highs, tolerance)
        for level, timestamps in high_groups.items():
            if len(timestamps) >= self.liquidity_threshold:
                zones.append(LiquidityZone(
                    level=level,
                    zone_type="resistance",
                    strength=min(len(timestamps), 5),
                    timestamp=timestamps[-1]
                ))
        
        # Process support zones (swing lows)
        low_groups = self._group_similar_levels(swing_lows, tolerance)
        for level, timestamps in low_groups.items():
            if len(timestamps) >= self.liquidity_threshold:
                zones.append(LiquidityZone(
                    level=level,
                    zone_type="support",
                    strength=min(len(timestamps), 5),
                    timestamp=timestamps[-1]
                ))
        
        return zones
    
    def detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """Detect order blocks - last opposite candle before strong move"""
        order_blocks = []
        
        # Calculate price changes
        df['price_change'] = df['close'].pct_change()
        
        # Define strong move threshold (2% move)
        strong_move_threshold = 0.02
        
        for i in range(2, len(df) - 1):
            current_change = df['price_change'].iloc[i]
            
            # Check for strong bullish move
            if current_change > strong_move_threshold:
                # Look for last bearish candle before this move
                for j in range(i-1, max(0, i-5), -1):
                    if df['close'].iloc[j] < df['open'].iloc[j]:  # Bearish candle
                        order_blocks.append(OrderBlock(
                            high=df['high'].iloc[j],
                            low=df['low'].iloc[j],
                            timestamp=df.index[j],
                            block_type="bullish",
                            mitigation_level=(df['high'].iloc[j] + df['low'].iloc[j]) / 2
                        ))
                        break
            
            # Check for strong bearish move
            elif current_change < -strong_move_threshold:
                # Look for last bullish candle before this move
                for j in range(i-1, max(0, i-5), -1):
                    if df['close'].iloc[j] > df['open'].iloc[j]:  # Bullish candle
                        order_blocks.append(OrderBlock(
                            high=df['high'].iloc[j],
                            low=df['low'].iloc[j],
                            timestamp=df.index[j],
                            block_type="bearish",
                            mitigation_level=(df['high'].iloc[j] + df['low'].iloc[j]) / 2
                        ))
                        break
        
        return order_blocks
    
    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:
        """Detect Fair Value Gaps (imbalances)"""
        gaps = []
        
        for i in range(1, len(df) - 1):
            prev_candle = df.iloc[i-1]
            current_candle = df.iloc[i]
            next_candle = df.iloc[i+1]
            
            # Bullish FVG: gap between previous high and next low
            if (prev_candle['high'] < next_candle['low'] and 
                current_candle['close'] > current_candle['open']):
                
                gaps.append(FairValueGap(
                    top=next_candle['low'],
                    bottom=prev_candle['high'],
                    timestamp=df.index[i],
                    gap_type="bullish"
                ))
            
            # Bearish FVG: gap between previous low and next high
            elif (prev_candle['low'] > next_candle['high'] and 
                  current_candle['close'] < current_candle['open']):
                
                gaps.append(FairValueGap(
                    top=prev_candle['low'],
                    bottom=next_candle['high'],
                    timestamp=df.index[i],
                    gap_type="bearish"
                ))
        
        return gaps
    
    def detect_break_of_structure(self, df: pd.DataFrame) -> List[Dict]:
        """Detect Break of Structure (BOS) - trend continuation signal"""
        bos_signals = []
        
        # Find swing points
        swing_highs = self._find_swing_points(df['high'], 'high')
        swing_lows = self._find_swing_points(df['low'], 'low')
        
        # Check for higher highs (bullish BOS)
        high_levels = list(swing_highs.keys())
        for i in range(1, len(high_levels)):
            if high_levels[i] > high_levels[i-1]:
                bos_signals.append({
                    'type': 'bullish_bos',
                    'level': high_levels[i],
                    'timestamp': swing_highs[high_levels[i]],
                    'previous_level': high_levels[i-1]
                })
        
        # Check for lower lows (bearish BOS)
        low_levels = list(swing_lows.keys())
        for i in range(1, len(low_levels)):
            if low_levels[i] < low_levels[i-1]:
                bos_signals.append({
                    'type': 'bearish_bos',
                    'level': low_levels[i],
                    'timestamp': swing_lows[low_levels[i]],
                    'previous_level': low_levels[i-1]
                })
        
        return bos_signals
    
    def detect_change_of_character(self, df: pd.DataFrame) -> List[Dict]:
        """Detect Change of Character (CHOCH) - trend reversal signal"""
        choch_signals = []
        
        # Simple CHOCH detection based on structure breaks
        swing_highs = self._find_swing_points(df['high'], 'high')
        swing_lows = self._find_swing_points(df['low'], 'low')
        
        # Detect bullish CHOCH (break above previous swing high in downtrend)
        high_levels = list(swing_highs.keys())
        for i in range(2, len(high_levels)):
            # Check if we're breaking a previous high after making lower highs
            if (high_levels[i] > high_levels[i-2] and 
                high_levels[i-1] < high_levels[i-2]):
                
                choch_signals.append({
                    'type': 'bullish_choch',
                    'level': high_levels[i],
                    'timestamp': swing_highs[high_levels[i]],
                    'broken_level': high_levels[i-2]
                })
        
        # Detect bearish CHOCH (break below previous swing low in uptrend)
        low_levels = list(swing_lows.keys())
        for i in range(2, len(low_levels)):
            # Check if we're breaking a previous low after making higher lows
            if (low_levels[i] < low_levels[i-2] and 
                low_levels[i-1] > low_levels[i-2]):
                
                choch_signals.append({
                    'type': 'bearish_choch',
                    'level': low_levels[i],
                    'timestamp': swing_lows[low_levels[i]],
                    'broken_level': low_levels[i-2]
                })
        
        return choch_signals
    
    def _find_swing_points(self, series: pd.Series, point_type: str) -> Dict[float, datetime]:
        """Find swing highs or lows in price series"""
        swing_points = {}
        window = 5  # Look 5 periods back and forward
        
        for i in range(window, len(series) - window):
            current_value = series.iloc[i]
            
            if point_type == 'high':
                # Check if current point is highest in window
                is_swing = all(current_value >= series.iloc[j] for j in range(i-window, i+window+1))
            else:  # low
                # Check if current point is lowest in window
                is_swing = all(current_value <= series.iloc[j] for j in range(i-window, i+window+1))
            
            if is_swing:
                swing_points[current_value] = series.index[i]
        
        return swing_points
    
    def _group_similar_levels(self, swing_points: Dict[float, datetime], tolerance: float) -> Dict[float, List[datetime]]:
        """Group swing points that are within tolerance of each other"""
        groups = {}
        
        for level, timestamp in swing_points.items():
            # Find if this level belongs to an existing group
            group_found = False
            for group_level in groups.keys():
                if abs(level - group_level) / group_level <= tolerance:
                    groups[group_level].append(timestamp)
                    group_found = True
                    break
            
            # Create new group if no existing group found
            if not group_found:
                groups[level] = [timestamp]
        
        return groups