"""
Multi-Timeframe Confluence Engine for Smart Money Concepts
Analyzes multiple timeframes to find high-probability trading setups
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass

from app.services.market_data_service import MarketDataService
from app.services.smc_strategy import SMCStrategy
from app.models.market_data import OrderBlock, LiquidityZone, FairValueGap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeframeType(Enum):
    """Timeframe classification"""
    HTF = "htf"  # Higher Timeframe
    MTF = "mtf"  # Medium Timeframe  
    LTF = "ltf"  # Lower Timeframe


@dataclass
class ConfluenceResult:
    """Result of confluence analysis"""
    confluence_score: int
    bias: str
    entry: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasons: List[str]
    htf_analysis: Dict
    mtf_analysis: Dict
    ltf_analysis: Dict


class TimeframeHierarchy:
    """Defines timeframe hierarchy for multi-timeframe analysis"""
    
    HTF_TIMEFRAMES = ["4h", "1d"]  # Higher Timeframes
    MTF_TIMEFRAMES = ["1h", "15m"]  # Medium Timeframes
    LTF_TIMEFRAMES = ["5m", "1m"]   # Lower Timeframes
    
    @classmethod
    def get_timeframe_type(cls, timeframe: str) -> TimeframeType:
        """Classify timeframe into HTF, MTF, or LTF"""
        if timeframe in cls.HTF_TIMEFRAMES:
            return TimeframeType.HTF
        elif timeframe in cls.MTF_TIMEFRAMES:
            return TimeframeType.MTF
        elif timeframe in cls.LTF_TIMEFRAMES:
            return TimeframeType.LTF
        else:
            raise ValueError(f"Unknown timeframe: {timeframe}")
    
    @classmethod
    def get_higher_timeframe(cls, current_tf: str) -> str:
        """Get the next higher timeframe"""
        tf_hierarchy = cls.LTF_TIMEFRAMES + cls.MTF_TIMEFRAMES + cls.HTF_TIMEFRAMES
        try:
            current_idx = tf_hierarchy.index(current_tf)
            if current_idx < len(tf_hierarchy) - 1:
                return tf_hierarchy[current_idx + 1]
            return tf_hierarchy[-1]  # Return highest if already at top
        except ValueError:
            return "4h"  # Default fallback


class ConfluenceEngine:
    """Multi-Timeframe Confluence Analysis Engine"""
    
    def __init__(self):
        self.market_data_service = MarketDataService()
        self.smc_strategy = SMCStrategy()
        self.timeframe_hierarchy = TimeframeHierarchy()
    
    async def analyze_htf_bias(self, symbol: str, htf: str = "4h") -> Dict:
        """
        Analyze Higher Timeframe bias and key levels
        
        Args:
            symbol: Trading pair symbol
            htf: Higher timeframe (4h, 1d)
            
        Returns:
            Dict with bias, htf_ob, htf_liquidity
        """
        logger.info(f"Analyzing HTF bias for {symbol} on {htf}")
        
        try:
            # Fetch HTF data
            market_data = await self.market_data_service.fetch_ohlcv(
                symbol=symbol, 
                timeframe=htf, 
                limit=200
            )
            df = self.market_data_service.to_dataframe(market_data)
            
            # Run SMC analysis
            smc_analysis = self.smc_strategy.analyze(df, symbol, htf)
            
            # Determine overall bias based on recent price action
            bias = self._determine_htf_bias(df, smc_analysis)
            
            # Find active HTF Order Blocks
            htf_ob = self._find_active_order_blocks(smc_analysis.order_blocks, df)
            
            # Find HTF liquidity zones
            htf_liquidity = self._find_key_liquidity_levels(smc_analysis.liquidity_zones, df)
            
            result = {
                "bias": bias,
                "htf_ob": htf_ob,
                "htf_liquidity": htf_liquidity,
                "timeframe": htf,
                "analysis_time": datetime.now().isoformat()
            }
            
            logger.info(f"HTF Analysis complete: {bias} bias with {len(htf_ob) if htf_ob else 0} OBs")
            return result
            
        except Exception as e:
            logger.error(f"Error in HTF analysis: {str(e)}")
            return {
                "bias": "neutral",
                "htf_ob": None,
                "htf_liquidity": None,
                "error": str(e)
            }
    
    async def find_mtf_confirmation(self, symbol: str, mtf: str = "1h", htf_bias: Dict = None) -> Dict:
        """
        Find Medium Timeframe confirmation aligned with HTF bias
        
        Args:
            symbol: Trading pair symbol
            mtf: Medium timeframe (1h, 15m)
            htf_bias: HTF analysis result
            
        Returns:
            Dict with confirmed status and MTF BOS level
        """
        logger.info(f"Finding MTF confirmation for {symbol} on {mtf}")
        
        if not htf_bias or htf_bias.get("bias") == "neutral":
            return {"confirmed": False, "reason": "No clear HTF bias"}
        
        try:
            # Fetch MTF data
            market_data = await self.market_data_service.fetch_ohlcv(
                symbol=symbol,
                timeframe=mtf,
                limit=100
            )
            df = self.market_data_service.to_dataframe(market_data)
            
            # Run SMC analysis
            smc_analysis = self.smc_strategy.analyze(df, symbol, mtf)
            
            # Look for BOS confirming HTF direction
            mtf_bos = self._find_confirming_bos(
                smc_analysis.break_of_structure, 
                htf_bias["bias"],
                df
            )
            
            result = {
                "confirmed": mtf_bos is not None,
                "mtf_bos_level": mtf_bos["level"] if mtf_bos else None,
                "mtf_bos_direction": mtf_bos["direction"] if mtf_bos else None,
                "timeframe": mtf,
                "analysis_time": datetime.now().isoformat()
            }
            
            logger.info(f"MTF Confirmation: {'Found' if result['confirmed'] else 'Not found'}")
            return result
            
        except Exception as e:
            logger.error(f"Error in MTF confirmation: {str(e)}")
            return {"confirmed": False, "error": str(e)}
    
    async def find_ltf_entry(self, symbol: str, ltf: str = "5m", mtf_confirmation: Dict = None) -> Dict:
        """
        Find precise Lower Timeframe entry point
        
        Args:
            symbol: Trading pair symbol
            ltf: Lower timeframe (5m, 1m)
            mtf_confirmation: MTF confirmation result
            
        Returns:
            Dict with entry, sl, tp prices
        """
        logger.info(f"Finding LTF entry for {symbol} on {ltf}")
        
        if not mtf_confirmation or not mtf_confirmation.get("confirmed"):
            return {"entry": None, "reason": "No MTF confirmation"}
        
        try:
            # Fetch LTF data
            market_data = await self.market_data_service.fetch_ohlcv(
                symbol=symbol,
                timeframe=ltf,
                limit=100
            )
            df = self.market_data_service.to_dataframe(market_data)
            
            # Run SMC analysis
            smc_analysis = self.smc_strategy.analyze(df, symbol, ltf)
            
            # Find entry model near MTF confirmation level
            entry_model = self._find_entry_model(
                smc_analysis,
                mtf_confirmation["mtf_bos_level"],
                mtf_confirmation["mtf_bos_direction"],
                df
            )
            
            if entry_model:
                # Calculate stop loss and take profit
                sl, tp = self._calculate_risk_reward(
                    entry_model["entry"],
                    entry_model["direction"],
                    df
                )
                
                result = {
                    "entry": entry_model["entry"],
                    "sl": sl,
                    "tp": tp,
                    "direction": entry_model["direction"],
                    "entry_type": entry_model["type"],
                    "timeframe": ltf,
                    "analysis_time": datetime.now().isoformat()
                }
            else:
                result = {
                    "entry": None,
                    "sl": None,
                    "tp": None,
                    "reason": "No valid entry model found"
                }
            
            logger.info(f"LTF Entry: {'Found' if result['entry'] else 'Not found'}")
            return result
            
        except Exception as e:
            logger.error(f"Error in LTF entry: {str(e)}")
            return {"entry": None, "error": str(e)}
    
    def confluence_score(
        self, 
        htf_analysis: Dict, 
        mtf_analysis: Dict, 
        ltf_analysis: Dict,
        smc_data: Dict = None
    ) -> Tuple[int, List[str]]:
        """
        Calculate confluence score from 0-100 based on multiple factors
        
        Scoring criteria:
        - HTF OB present at level: +25 points
        - MTF BOS confirmed: +20 points  
        - LTF entry model found: +20 points
        - FVG present: +15 points
        - Liquidity swept before entry: +20 points
        
        Args:
            htf_analysis: HTF analysis result
            mtf_analysis: MTF confirmation result
            ltf_analysis: LTF entry result
            smc_data: Additional SMC pattern data
            
        Returns:
            Tuple of (score, reasons_list)
        """
        score = 0
        reasons = []
        
        # HTF Order Block present (+25 points)
        if htf_analysis.get("htf_ob") and len(htf_analysis["htf_ob"]) > 0:
            score += 25
            reasons.append("HTF Order Block present at key level")
        
        # MTF BOS confirmed (+20 points)
        if mtf_analysis.get("confirmed"):
            score += 20
            reasons.append("MTF Break of Structure confirmed")
        
        # LTF entry model found (+20 points)
        if ltf_analysis.get("entry") is not None:
            score += 20
            reasons.append(f"LTF entry model found: {ltf_analysis.get('entry_type', 'Unknown')}")
        
        # FVG present (+15 points)
        if smc_data and smc_data.get("fvg_present"):
            score += 15
            reasons.append("Fair Value Gap present at entry level")
        
        # Liquidity swept before entry (+20 points)
        if smc_data and smc_data.get("liquidity_swept"):
            score += 20
            reasons.append("Liquidity swept before entry signal")
        
        logger.info(f"Confluence score calculated: {score}/100 with {len(reasons)} factors")
        return score, reasons
    
    async def analyze_mtf_confluence(
        self, 
        symbol: str, 
        entry_tf: str = "5m",
        htf: str = "4h", 
        mtf: str = "1h"
    ) -> ConfluenceResult:
        """
        Complete Multi-Timeframe confluence analysis
        
        Args:
            symbol: Trading pair symbol
            entry_tf: Entry timeframe (LTF)
            htf: Higher timeframe
            mtf: Medium timeframe
            
        Returns:
            ConfluenceResult with complete analysis
        """
        logger.info(f"Starting MTF confluence analysis for {symbol}")
        
        # Step 1: Analyze HTF bias
        htf_analysis = await self.analyze_htf_bias(symbol, htf)
        
        # Step 2: Find MTF confirmation
        mtf_analysis = await self.find_mtf_confirmation(symbol, mtf, htf_analysis)
        
        # Step 3: Find LTF entry
        ltf_analysis = await self.find_ltf_entry(symbol, entry_tf, mtf_analysis)
        
        # Step 4: Check for additional SMC patterns
        smc_data = await self._check_additional_smc_patterns(symbol, entry_tf, ltf_analysis)
        
        # Step 5: Calculate confluence score
        score, reasons = self.confluence_score(htf_analysis, mtf_analysis, ltf_analysis, smc_data)
        
        # Determine final bias and signal validity
        bias = htf_analysis.get("bias", "neutral")
        entry = ltf_analysis.get("entry") if score >= 60 else None
        
        # Apply bias rules
        if bias == "bearish" and ltf_analysis.get("direction") == "buy":
            entry = None
            reasons.append("Signal rejected: BUY signal conflicts with bearish HTF bias")
        elif bias == "bullish" and ltf_analysis.get("direction") == "sell":
            entry = None
            reasons.append("Signal rejected: SELL signal conflicts with bullish HTF bias")
        
        result = ConfluenceResult(
            confluence_score=score,
            bias=bias,
            entry=entry,
            stop_loss=ltf_analysis.get("sl"),
            take_profit=ltf_analysis.get("tp"),
            reasons=reasons,
            htf_analysis=htf_analysis,
            mtf_analysis=mtf_analysis,
            ltf_analysis=ltf_analysis
        )
        
        logger.info(f"MTF Confluence analysis complete: Score {score}, Entry: {entry}")
        return result
    
    # Helper methods
    def _determine_htf_bias(self, df: pd.DataFrame, smc_analysis) -> str:
        """Determine overall HTF bias based on price action and SMC patterns"""
        try:
            # Get recent price data
            recent_closes = df['close'].tail(20)
            current_price = df['close'].iloc[-1]
            
            # Simple trend analysis
            sma_20 = recent_closes.mean()
            price_above_sma = current_price > sma_20
            
            # Check for recent BOS
            recent_bos = [bos for bos in smc_analysis.break_of_structure if bos.get('recent', False)]
            
            if recent_bos:
                latest_bos = recent_bos[-1]
                if latest_bos.get('direction') == 'bullish' and price_above_sma:
                    return "bullish"
                elif latest_bos.get('direction') == 'bearish' and not price_above_sma:
                    return "bearish"
            
            # Fallback to price vs SMA
            return "bullish" if price_above_sma else "bearish"
            
        except Exception as e:
            logger.error(f"Error determining HTF bias: {str(e)}")
            return "neutral"
    
    def _find_active_order_blocks(self, order_blocks: List[OrderBlock], df: pd.DataFrame) -> List[Dict]:
        """Find active HTF Order Blocks near current price"""
        if not order_blocks:
            return []
        
        current_price = df['close'].iloc[-1]
        active_obs = []
        
        for ob in order_blocks:
            # Check if OB is within reasonable distance of current price
            distance_pct = abs(ob.price - current_price) / current_price
            if distance_pct <= 0.05:  # Within 5%
                active_obs.append({
                    "price": ob.price,
                    "type": ob.ob_type,
                    "strength": getattr(ob, 'strength', 1),
                    "distance_pct": distance_pct
                })
        
        return sorted(active_obs, key=lambda x: x['distance_pct'])
    
    def _find_key_liquidity_levels(self, liquidity_zones: List[LiquidityZone], df: pd.DataFrame) -> List[Dict]:
        """Find key HTF liquidity levels"""
        if not liquidity_zones:
            return []
        
        current_price = df['close'].iloc[-1]
        key_levels = []
        
        for lz in liquidity_zones:
            distance_pct = abs(lz.price - current_price) / current_price
            if distance_pct <= 0.1:  # Within 10%
                key_levels.append({
                    "price": lz.price,
                    "type": lz.zone_type,
                    "strength": getattr(lz, 'strength', 1),
                    "distance_pct": distance_pct
                })
        
        return sorted(key_levels, key=lambda x: x['distance_pct'])
    
    def _find_confirming_bos(self, bos_list: List[Dict], htf_bias: str, df: pd.DataFrame) -> Optional[Dict]:
        """Find MTF BOS that confirms HTF bias"""
        if not bos_list:
            return None
        
        # Look for recent BOS in the same direction as HTF bias
        for bos in reversed(bos_list):  # Start with most recent
            if bos.get('direction') == htf_bias:
                return {
                    "level": bos.get('level'),
                    "direction": bos.get('direction'),
                    "timestamp": bos.get('timestamp')
                }
        
        return None
    
    def _find_entry_model(
        self, 
        smc_analysis, 
        mtf_level: float, 
        direction: str, 
        df: pd.DataFrame
    ) -> Optional[Dict]:
        """Find LTF entry model near MTF confirmation level"""
        if not mtf_level:
            return None
        
        current_price = df['close'].iloc[-1]
        
        # Look for Order Block near MTF level
        for ob in smc_analysis.order_blocks:
            distance_pct = abs(ob.price - mtf_level) / mtf_level
            if distance_pct <= 0.02:  # Within 2%
                return {
                    "entry": ob.price,
                    "direction": "buy" if direction == "bullish" else "sell",
                    "type": "Order Block"
                }
        
        # Look for FVG near MTF level
        for fvg in smc_analysis.fair_value_gaps:
            fvg_mid = (fvg.high + fvg.low) / 2
            distance_pct = abs(fvg_mid - mtf_level) / mtf_level
            if distance_pct <= 0.02:  # Within 2%
                return {
                    "entry": fvg_mid,
                    "direction": "buy" if direction == "bullish" else "sell",
                    "type": "Fair Value Gap"
                }
        
        # Fallback to MTF level itself
        return {
            "entry": mtf_level,
            "direction": "buy" if direction == "bullish" else "sell",
            "type": "MTF Level"
        }
    
    def _calculate_risk_reward(self, entry: float, direction: str, df: pd.DataFrame) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        atr = self._calculate_atr(df)
        
        if direction == "buy":
            sl = entry - (2 * atr)  # 2 ATR stop loss
            tp = entry + (3 * atr)  # 1:1.5 risk reward
        else:  # sell
            sl = entry + (2 * atr)  # 2 ATR stop loss
            tp = entry - (3 * atr)  # 1:1.5 risk reward
        
        return round(sl, 2), round(tp, 2)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else (df['high'].iloc[-1] - df['low'].iloc[-1])
    
    async def _check_additional_smc_patterns(self, symbol: str, timeframe: str, ltf_analysis: Dict) -> Dict:
        """Check for additional SMC patterns to boost confluence score"""
        try:
            # Fetch fresh data for pattern analysis
            market_data = await self.market_data_service.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=50
            )
            df = self.market_data_service.to_dataframe(market_data)
            smc_analysis = self.smc_strategy.analyze(df, symbol, timeframe)
            
            # Check for FVG near entry
            fvg_present = False
            if ltf_analysis.get("entry"):
                entry_price = ltf_analysis["entry"]
                for fvg in smc_analysis.fair_value_gaps:
                    if fvg.low <= entry_price <= fvg.high:
                        fvg_present = True
                        break
            
            # Check for liquidity sweep (simplified)
            liquidity_swept = len(smc_analysis.liquidity_zones) > 0
            
            return {
                "fvg_present": fvg_present,
                "liquidity_swept": liquidity_swept
            }
            
        except Exception as e:
            logger.error(f"Error checking additional SMC patterns: {str(e)}")
            return {"fvg_present": False, "liquidity_swept": False}