import pandas as pd
from typing import List, Optional
from datetime import datetime
from app.models.signals import TradingSignal, SignalType, SignalStatus
from app.models.market_data import SMCAnalysis

class SignalGenerator:
    """Generate trading signals based on SMC analysis"""
    
    def __init__(self):
        self.risk_reward_ratio = 2.0  # 1:2 risk reward
        self.max_risk_percent = 0.02  # 2% max risk per trade
    
    def generate_signals(self, smc_analysis: SMCAnalysis, current_price: float) -> List[TradingSignal]:
        """Generate trading signals based on SMC analysis"""
        signals = []
        
        # Generate signals from order blocks
        ob_signals = self._signals_from_order_blocks(smc_analysis, current_price)
        signals.extend(ob_signals)
        
        # Generate signals from fair value gaps
        fvg_signals = self._signals_from_fvg(smc_analysis, current_price)
        signals.extend(fvg_signals)
        
        # Generate signals from BOS/CHOCH
        structure_signals = self._signals_from_structure(smc_analysis, current_price)
        signals.extend(structure_signals)
        
        return signals
    
    def _signals_from_order_blocks(self, analysis: SMCAnalysis, current_price: float) -> List[TradingSignal]:
        """Generate signals when price approaches order blocks"""
        signals = []
        
        for ob in analysis.order_blocks:
            # Check if current price is near order block (within 1%)
            distance_to_ob = abs(current_price - ob.mitigation_level) / current_price
            
            if distance_to_ob <= 0.01:  # Within 1% of order block
                if ob.block_type == "bullish" and current_price <= ob.mitigation_level:
                    # Bullish signal from bullish order block
                    entry_price = ob.mitigation_level
                    stop_loss = ob.low * 0.995  # 0.5% below order block low
                    take_profit = entry_price + (entry_price - stop_loss) * self.risk_reward_ratio
                    
                    signals.append(TradingSignal(
                        symbol=analysis.symbol,
                        timeframe=analysis.timeframe,
                        signal_type=SignalType.BUY,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=75.0,
                        reasoning=f"Bullish Order Block at {entry_price:.2f}",
                        timestamp=datetime.now()
                    ))
                
                elif ob.block_type == "bearish" and current_price >= ob.mitigation_level:
                    # Bearish signal from bearish order block
                    entry_price = ob.mitigation_level
                    stop_loss = ob.high * 1.005  # 0.5% above order block high
                    take_profit = entry_price - (stop_loss - entry_price) * self.risk_reward_ratio
                    
                    signals.append(TradingSignal(
                        symbol=analysis.symbol,
                        timeframe=analysis.timeframe,
                        signal_type=SignalType.SELL,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=75.0,
                        reasoning=f"Bearish Order Block at {entry_price:.2f}",
                        timestamp=datetime.now()
                    ))
        
        return signals
    
    def _signals_from_fvg(self, analysis: SMCAnalysis, current_price: float) -> List[TradingSignal]:
        """Generate signals when price approaches unfilled Fair Value Gaps"""
        signals = []
        
        for fvg in analysis.fair_value_gaps:
            if fvg.filled:
                continue
            
            # Check if current price is approaching the gap
            if fvg.gap_type == "bullish" and fvg.bottom <= current_price <= fvg.top:
                # Price is in bullish FVG - expect bounce up
                entry_price = current_price
                stop_loss = fvg.bottom * 0.995
                take_profit = entry_price + (entry_price - stop_loss) * self.risk_reward_ratio
                
                signals.append(TradingSignal(
                    symbol=analysis.symbol,
                    timeframe=analysis.timeframe,
                    signal_type=SignalType.BUY,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=65.0,
                    reasoning=f"Bullish Fair Value Gap {fvg.bottom:.2f}-{fvg.top:.2f}",
                    timestamp=datetime.now()
                ))
            
            elif fvg.gap_type == "bearish" and fvg.bottom <= current_price <= fvg.top:
                # Price is in bearish FVG - expect rejection down
                entry_price = current_price
                stop_loss = fvg.top * 1.005
                take_profit = entry_price - (stop_loss - entry_price) * self.risk_reward_ratio
                
                signals.append(TradingSignal(
                    symbol=analysis.symbol,
                    timeframe=analysis.timeframe,
                    signal_type=SignalType.SELL,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=65.0,
                    reasoning=f"Bearish Fair Value Gap {fvg.bottom:.2f}-{fvg.top:.2f}",
                    timestamp=datetime.now()
                ))
        
        return signals
    
    def _signals_from_structure(self, analysis: SMCAnalysis, current_price: float) -> List[TradingSignal]:
        """Generate signals from BOS and CHOCH patterns"""
        signals = []
        
        # Process BOS signals
        for bos in analysis.bos_signals:
            if bos['type'] == 'bullish_bos':
                # Bullish BOS - look for pullback entry
                entry_price = bos['previous_level']  # Enter on pullback to previous resistance
                stop_loss = entry_price * 0.98  # 2% stop loss
                take_profit = bos['level'] * 1.02  # Target above new high
                
                signals.append(TradingSignal(
                    symbol=analysis.symbol,
                    timeframe=analysis.timeframe,
                    signal_type=SignalType.BUY,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=80.0,
                    reasoning=f"Bullish Break of Structure at {bos['level']:.2f}",
                    timestamp=datetime.now()
                ))
            
            elif bos['type'] == 'bearish_bos':
                # Bearish BOS - look for pullback entry
                entry_price = bos['previous_level']  # Enter on pullback to previous support
                stop_loss = entry_price * 1.02  # 2% stop loss
                take_profit = bos['level'] * 0.98  # Target below new low
                
                signals.append(TradingSignal(
                    symbol=analysis.symbol,
                    timeframe=analysis.timeframe,
                    signal_type=SignalType.SELL,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=80.0,
                    reasoning=f"Bearish Break of Structure at {bos['level']:.2f}",
                    timestamp=datetime.now()
                ))
        
        # Process CHOCH signals (higher confidence due to trend change)
        for choch in analysis.choch_signals:
            if choch['type'] == 'bullish_choch':
                # Bullish CHOCH - trend reversal to upside
                entry_price = choch['level'] * 1.001  # Enter slightly above break level
                stop_loss = choch['broken_level'] * 0.995  # Stop below broken level
                take_profit = entry_price + (entry_price - stop_loss) * self.risk_reward_ratio
                
                signals.append(TradingSignal(
                    symbol=analysis.symbol,
                    timeframe=analysis.timeframe,
                    signal_type=SignalType.BUY,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=85.0,
                    reasoning=f"Bullish Change of Character at {choch['level']:.2f}",
                    timestamp=datetime.now()
                ))
            
            elif choch['type'] == 'bearish_choch':
                # Bearish CHOCH - trend reversal to downside
                entry_price = choch['level'] * 0.999  # Enter slightly below break level
                stop_loss = choch['broken_level'] * 1.005  # Stop above broken level
                take_profit = entry_price - (stop_loss - entry_price) * self.risk_reward_ratio
                
                signals.append(TradingSignal(
                    symbol=analysis.symbol,
                    timeframe=analysis.timeframe,
                    signal_type=SignalType.SELL,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=85.0,
                    reasoning=f"Bearish Change of Character at {choch['level']:.2f}",
                    timestamp=datetime.now()
                ))
        
        return signals
    
    def filter_signals(self, signals: List[TradingSignal], min_confidence: float = 70.0) -> List[TradingSignal]:
        """Filter signals based on confidence and other criteria"""
        filtered_signals = []
        
        for signal in signals:
            # Filter by minimum confidence
            if signal.confidence < min_confidence:
                continue
            
            # Check risk-reward ratio
            if signal.signal_type == SignalType.BUY:
                risk = signal.entry_price - signal.stop_loss
                reward = signal.take_profit - signal.entry_price
            else:
                risk = signal.stop_loss - signal.entry_price
                reward = signal.entry_price - signal.take_profit
            
            if reward / risk >= 1.5:  # Minimum 1:1.5 RR
                filtered_signals.append(signal)
        
        return filtered_signals