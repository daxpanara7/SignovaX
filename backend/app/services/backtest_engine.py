import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from app.models.signals import TradingSignal, SignalType, BacktestResult
from app.services.smc_strategy import SMCStrategy
from app.services.signal_generator import SignalGenerator

class BacktestEngine:
    """Backtesting engine for SMC trading strategies"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.smc_strategy = SMCStrategy()
        self.signal_generator = SignalGenerator()
    
    def run_backtest(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> BacktestResult:
        """Run complete backtest on historical data"""
        
        # Filter data by date range if provided
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        if len(df) < 50:
            raise ValueError("Insufficient data for backtesting")
        
        # Initialize tracking variables
        trades = []
        equity_curve = []
        current_capital = self.initial_capital
        position = None  # Current open position
        
        # Process each candle
        for i in range(50, len(df)):  # Start after 50 candles for analysis
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            
            # Get historical data up to current point
            historical_data = df.iloc[:i+1]
            
            # Run SMC analysis on historical data
            smc_analysis = self.smc_strategy.analyze(historical_data, symbol, timeframe)
            
            # Generate signals
            signals = self.signal_generator.generate_signals(smc_analysis, current_price)
            signals = self.signal_generator.filter_signals(signals, min_confidence=75.0)
            
            # Check if we have an open position
            if position:
                # Check for exit conditions
                trade_result = self._check_exit_conditions(
                    position, current_price, current_time, df.iloc[i]
                )
                
                if trade_result:
                    trades.append(trade_result)
                    # Update capital
                    pnl_percent = trade_result['pnl_percent']
                    current_capital *= (1 + pnl_percent / 100)
                    position = None
            
            # Look for new entry if no position
            elif signals and not position:
                # Take the highest confidence signal
                best_signal = max(signals, key=lambda s: s.confidence)
                
                # Enter position
                position = {
                    'signal': best_signal,
                    'entry_time': current_time,
                    'entry_price': current_price,  # Use current price as actual entry
                    'stop_loss': best_signal.stop_loss,
                    'take_profit': best_signal.take_profit,
                    'signal_type': best_signal.signal_type
                }
            
            # Record equity curve
            equity_curve.append({
                'timestamp': current_time,
                'equity': current_capital
            })
        
        # Close any remaining position at the end
        if position:
            final_price = df['close'].iloc[-1]
            final_time = df.index[-1]
            trade_result = self._close_position(position, final_price, final_time, "End of data")
            trades.append(trade_result)
            pnl_percent = trade_result['pnl_percent']
            current_capital *= (1 + pnl_percent / 100)
        
        # Calculate performance metrics
        return self._calculate_performance_metrics(
            trades, equity_curve, symbol, timeframe, 
            df.index[0] if start_date is None else start_date,
            df.index[-1] if end_date is None else end_date
        )
    
    def _check_exit_conditions(
        self, 
        position: Dict, 
        current_price: float, 
        current_time: datetime,
        current_candle: pd.Series
    ) -> Dict:
        """Check if position should be closed based on stop loss or take profit"""
        
        signal_type = position['signal_type']
        entry_price = position['entry_price']
        stop_loss = position['stop_loss']
        take_profit = position['take_profit']
        
        # Check stop loss and take profit based on candle highs/lows
        if signal_type == SignalType.BUY:
            # Long position
            if current_candle['low'] <= stop_loss:
                # Stop loss hit
                return self._close_position(position, stop_loss, current_time, "Stop Loss")
            elif current_candle['high'] >= take_profit:
                # Take profit hit
                return self._close_position(position, take_profit, current_time, "Take Profit")
        
        else:  # SELL
            # Short position
            if current_candle['high'] >= stop_loss:
                # Stop loss hit
                return self._close_position(position, stop_loss, current_time, "Stop Loss")
            elif current_candle['low'] <= take_profit:
                # Take profit hit
                return self._close_position(position, take_profit, current_time, "Take Profit")
        
        return None
    
    def _close_position(
        self, 
        position: Dict, 
        exit_price: float, 
        exit_time: datetime, 
        exit_reason: str
    ) -> Dict:
        """Close position and calculate P&L"""
        
        entry_price = position['entry_price']
        signal_type = position['signal_type']
        
        if signal_type == SignalType.BUY:
            # Long position
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        else:
            # Short position
            pnl_percent = ((entry_price - exit_price) / entry_price) * 100
        
        return {
            'entry_time': position['entry_time'],
            'exit_time': exit_time,
            'signal_type': signal_type.value,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_percent': pnl_percent,
            'exit_reason': exit_reason,
            'confidence': position['signal'].confidence,
            'reasoning': position['signal'].reasoning
        }
    
    def _calculate_performance_metrics(
        self, 
        trades: List[Dict], 
        equity_curve: List[Dict],
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        
        if not trades:
            return BacktestResult(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                max_drawdown=0.0,
                trade_logs=[]
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl_percent'] > 0])
        losing_trades = len([t for t in trades if t['pnl_percent'] <= 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L calculation
        total_pnl_percent = sum(t['pnl_percent'] for t in trades)
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Calculate Sharpe ratio (simplified)
        returns = [t['pnl_percent'] for t in trades]
        sharpe_ratio = self._calculate_sharpe_ratio(returns) if returns else None
        
        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl_percent,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trade_logs=trades
        )
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not equity_curve:
            return 0.0
        
        equity_values = [point['equity'] for point in equity_curve]
        peak = equity_values[0]
        max_dd = 0.0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak * 100
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio (simplified, assuming 0% risk-free rate)"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe ratio (assuming daily returns)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        return sharpe