"""
Advanced Backtesting Engine with Professional-Grade Features
Includes realistic trade simulation, walk-forward testing, Monte Carlo simulation,
and comprehensive professional metrics.
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
from scipy import stats
import random

from app.models.backtest_models import (
    TradeSimulatorConfig, TradeResult, WalkForwardResult, WalkForwardPeriod,
    MonteCarloResult, ProfessionalMetrics, AdvancedBacktestResult,
    BacktestConfig, BacktestSummary, SavedBacktestResult
)
from app.strategies.smc_engine import PreciseSMCEngine
from app.services.risk_manager import RiskManager
from app.services.market_data_service import MarketDataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedBacktester:
    """
    Professional-grade backtesting engine with advanced features
    """
    
    def __init__(self, db_path: str = "backtest_results.db"):
        self.db_path = db_path
        self.smc_engine = PreciseSMCEngine()
        self.risk_manager = RiskManager()
        self.market_data_service = MarketDataService()
        
        # Initialize database
        self._init_database()
        
        logger.info("Advanced Backtester initialized")
    
    def _init_database(self):
        """Initialize SQLite database for backtest results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    trade_log_json TEXT NOT NULL,
                    equity_curve_json TEXT NOT NULL,
                    total_return_pct REAL,
                    max_drawdown_pct REAL,
                    sharpe_ratio REAL,
                    win_rate REAL,
                    total_trades INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Backtest database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    async def run_backtest(self, config: BacktestConfig) -> AdvancedBacktestResult:
        """
        Run complete advanced backtest with realistic trade simulation
        
        Args:
            config: Backtesting configuration
            
        Returns:
            AdvancedBacktestResult with comprehensive analysis
        """
        logger.info(f"Starting advanced backtest: {config.symbol} {config.timeframe}")
        
        # Fetch market data
        market_data = await self.market_data_service.fetch_ohlcv(
            symbol=config.symbol,
            timeframe=config.timeframe,
            limit=2000  # More data for comprehensive backtest
        )
        df = self.market_data_service.to_dataframe(market_data)
        
        # Filter by date range
        if config.start_date:
            df = df[df.index >= config.start_date]
        if config.end_date:
            df = df[df.index <= config.end_date]
        
        if len(df) < 100:
            raise ValueError("Insufficient data for advanced backtesting (minimum 100 candles)")
        
        # Run simulation
        trades, equity_curve = self._simulate_trading(df, config)
        
        # Calculate professional metrics
        metrics = self.calculate_metrics(trades, equity_curve, df, config)
        
        # Create result
        result = AdvancedBacktestResult(
            symbol=config.symbol,
            timeframe=config.timeframe,
            start_date=df.index[0],
            end_date=df.index[-1],
            config=config,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            analysis_timestamp=datetime.now(),
            monthly_returns=self._calculate_monthly_returns(equity_curve),
            yearly_returns=self._calculate_yearly_returns(equity_curve),
            drawdown_periods=self._calculate_drawdown_periods(equity_curve)
        )
        
        # Save to database
        backtest_id = self._save_backtest_result(result)
        
        logger.info(f"Advanced backtest complete: {len(trades)} trades, {metrics.total_return_pct:.2f}% return")
        return result
    
    def _simulate_trading(self, df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[TradeResult], List[Dict]]:
        """
        Simulate realistic trading with slippage, commissions, and spreads
        
        Args:
            df: OHLCV DataFrame
            config: Backtesting configuration
            
        Returns:
            Tuple of (trades, equity_curve)
        """
        trades = []
        equity_curve = []
        current_capital = config.initial_capital
        position = None
        
        simulator_config = config.trade_simulator
        
        # Process each candle
        for i in range(50, len(df)):
            current_time = df.index[i]
            current_candle = df.iloc[i]
            current_price = current_candle['close']
            
            # Get historical data up to current point
            historical_data = df.iloc[:i+1]
            
            # Run SMC analysis
            smc_analysis = self.smc_engine.analyze(historical_data, config.symbol, config.timeframe)
            
            # Check for exit conditions first
            if position:
                exit_result = self._check_realistic_exit(
                    position, current_candle, current_time, simulator_config
                )
                
                if exit_result:
                    trades.append(exit_result)
                    # Update capital with realistic costs
                    current_capital += exit_result.net_pnl
                    position = None
            
            # Look for new entry if no position
            elif not position and len(smc_analysis.structure_events) > 0:
                # Get most recent structure event for signal
                latest_structure = smc_analysis.structure_events[-1]
                
                # Check if it's a valid entry signal
                if self._is_valid_entry_signal(latest_structure, current_price):
                    # Calculate position size using risk management
                    entry_price = self._apply_realistic_entry(
                        current_price, latest_structure.structure_type.value, simulator_config
                    )
                    
                    # Calculate stop loss and take profit
                    stop_loss, take_profit = self._calculate_sl_tp(
                        entry_price, latest_structure, current_price
                    )
                    
                    # Calculate position size
                    risk_amount = current_capital * config.risk_per_trade
                    pip_risk = abs(entry_price - stop_loss)
                    position_size = risk_amount / pip_risk if pip_risk > 0 else 0
                    
                    if position_size > 0:
                        # Create position
                        position = {
                            'entry_time': current_time,
                            'signal_entry_price': current_price,
                            'actual_entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'position_size': position_size,
                            'signal_type': 'BUY' if 'bullish' in latest_structure.structure_type.value else 'SELL',
                            'structure_event': latest_structure,
                            'risk_amount': risk_amount
                        }
                        
                        # Deduct entry commission
                        entry_commission = position_size * entry_price * simulator_config.commission_pct
                        current_capital -= entry_commission
            
            # Record equity curve
            unrealized_pnl = 0
            if position:
                unrealized_pnl = self._calculate_unrealized_pnl(position, current_price)
            
            equity_curve.append({
                'timestamp': current_time,
                'equity': current_capital + unrealized_pnl,
                'realized_equity': current_capital,
                'unrealized_pnl': unrealized_pnl
            })
        
        # Close any remaining position
        if position:
            final_candle = df.iloc[-1]
            final_exit = self._force_close_position(
                position, final_candle, df.index[-1], simulator_config
            )
            trades.append(final_exit)
            current_capital += final_exit.net_pnl
        
        return trades, equity_curve
    
    def _apply_realistic_entry(self, signal_price: float, signal_type: str, config: TradeSimulatorConfig) -> float:
        """Apply realistic entry with slippage"""
        if 'bullish' in signal_type.lower() or signal_type == 'BUY':
            # BUY entry = signal_entry * (1 + slippage_pct)
            return signal_price * (1 + config.slippage_pct)
        else:
            # SELL entry = signal_entry * (1 - slippage_pct)
            return signal_price * (1 - config.slippage_pct)
    
    def _check_realistic_exit(
        self, position: Dict, current_candle: pd.Series, 
        current_time: datetime, config: TradeSimulatorConfig
    ) -> Optional[TradeResult]:
        """Check for exit with realistic execution"""
        
        signal_type = position['signal_type']
        stop_loss = position['stop_loss']
        take_profit = position['take_profit']
        
        exit_price = None
        exit_reason = None
        
        if signal_type == 'BUY':
            # Long position
            if current_candle['low'] <= stop_loss:
                exit_price = stop_loss * (1 - config.slippage_pct)  # Slippage on SL
                exit_reason = "Stop Loss"
            elif current_candle['high'] >= take_profit:
                exit_price = take_profit * (1 - config.slippage_pct)  # Slippage on TP
                exit_reason = "Take Profit"
        else:
            # Short position
            if current_candle['high'] >= stop_loss:
                exit_price = stop_loss * (1 + config.slippage_pct)  # Slippage on SL
                exit_reason = "Stop Loss"
            elif current_candle['low'] <= take_profit:
                exit_price = take_profit * (1 + config.slippage_pct)  # Slippage on TP
                exit_reason = "Take Profit"
        
        if exit_price:
            return self._create_trade_result(position, exit_price, current_time, exit_reason, config)
        
        return None
    
    def _create_trade_result(
        self, position: Dict, exit_price: float, exit_time: datetime, 
        exit_reason: str, config: TradeSimulatorConfig
    ) -> TradeResult:
        """Create detailed trade result with realistic costs"""
        
        entry_price = position['actual_entry_price']
        signal_entry = position['signal_entry_price']
        position_size = position['position_size']
        signal_type = position['signal_type']
        risk_amount = position['risk_amount']
        
        # Calculate gross P&L
        if signal_type == 'BUY':
            gross_pnl = (exit_price - entry_price) * position_size
        else:
            gross_pnl = (entry_price - exit_price) * position_size
        
        # Calculate costs
        entry_slippage = abs(entry_price - signal_entry) * position_size
        exit_slippage = abs(exit_price - (position['take_profit'] if exit_reason == "Take Profit" else position['stop_loss'])) * position_size
        total_slippage = entry_slippage + exit_slippage
        
        entry_commission = position_size * entry_price * config.commission_pct
        exit_commission = position_size * exit_price * config.commission_pct
        total_commission = entry_commission + exit_commission
        
        # Net P&L
        net_pnl = gross_pnl - total_slippage - total_commission
        
        # Calculate percentage and R-multiple
        pnl_percent = (net_pnl / (position_size * entry_price)) * 100
        r_multiple = net_pnl / risk_amount if risk_amount > 0 else 0
        
        # Trade duration
        duration = (exit_time - position['entry_time']).total_seconds() / 3600
        
        return TradeResult(
            entry_time=position['entry_time'],
            exit_time=exit_time,
            signal_type=signal_type,
            entry_price=entry_price,
            exit_price=exit_price,
            signal_entry_price=signal_entry,
            signal_exit_price=position['take_profit'] if exit_reason == "Take Profit" else position['stop_loss'],
            position_size=position_size,
            gross_pnl=gross_pnl,
            slippage_cost=total_slippage,
            commission_cost=total_commission,
            net_pnl=net_pnl,
            pnl_percent=pnl_percent,
            r_multiple=r_multiple,
            exit_reason=exit_reason,
            confidence=position['structure_event'].confidence.value,
            reasoning=f"Structure: {position['structure_event'].structure_type.value}",
            trade_duration_hours=duration
        )
    
    async def walk_forward_test(self, config: BacktestConfig, n_splits: int = 5) -> WalkForwardResult:
        """
        Implement Walk-Forward Testing
        
        Split data into n equal periods
        For each split: train on 70%, test on 30%
        Run strategy on each test period independently
        
        Args:
            config: Backtesting configuration
            n_splits: Number of splits for walk-forward testing
            
        Returns:
            WalkForwardResult with per-period and overall results
        """
        logger.info(f"Starting walk-forward test: {n_splits} splits")
        
        # Fetch data
        market_data = await self.market_data_service.fetch_ohlcv(
            symbol=config.symbol,
            timeframe=config.timeframe,
            limit=2000
        )
        df = self.market_data_service.to_dataframe(market_data)
        
        # Split data into periods
        total_length = len(df)
        period_length = total_length // n_splits
        
        per_period_results = []
        
        for i in range(n_splits):
            start_idx = i * period_length
            end_idx = min((i + 1) * period_length, total_length)
            
            period_data = df.iloc[start_idx:end_idx]
            
            # Split into train (70%) and test (30%)
            train_length = int(len(period_data) * 0.7)
            train_data = period_data.iloc[:train_length]
            test_data = period_data.iloc[train_length:]
            
            if len(test_data) < 20:  # Minimum test data
                continue
            
            # Run backtest on test period
            period_config = config.copy()
            period_config.start_date = test_data.index[0]
            period_config.end_date = test_data.index[-1]
            
            # Simulate trading on test period
            trades, equity_curve = self._simulate_trading(test_data, period_config)
            
            # Calculate period metrics
            period_metrics = self._calculate_period_metrics(trades, equity_curve)
            
            period_result = WalkForwardPeriod(
                period_number=i + 1,
                train_start=train_data.index[0],
                train_end=train_data.index[-1],
                test_start=test_data.index[0],
                test_end=test_data.index[-1],
                total_trades=len(trades),
                winning_trades=len([t for t in trades if t.net_pnl > 0]),
                win_rate=len([t for t in trades if t.net_pnl > 0]) / len(trades) * 100 if trades else 0,
                total_return_pct=period_metrics['total_return_pct'],
                max_drawdown_pct=period_metrics['max_drawdown_pct'],
                profit_factor=period_metrics['profit_factor'],
                sharpe_ratio=period_metrics['sharpe_ratio'],
                trades=trades
            )
            
            per_period_results.append(period_result)
        
        # Calculate overall metrics
        overall_metrics = self._calculate_walk_forward_overall_metrics(per_period_results)
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(per_period_results)
        
        # Calculate degradation factor
        degradation_factor = self._calculate_degradation_factor(per_period_results)
        
        return WalkForwardResult(
            n_splits=n_splits,
            per_period_results=per_period_results,
            overall_metrics=overall_metrics,
            consistency_score=consistency_score,
            degradation_factor=degradation_factor
        )
    
    def monte_carlo(self, trades: List[TradeResult], n_simulations: int = 1000) -> MonteCarloResult:
        """
        Implement Monte Carlo Simulation
        
        Take historical trade results and randomly shuffle trade order
        Calculate equity curves for each simulation
        
        Args:
            trades: Historical trade results
            n_simulations: Number of simulations to run
            
        Returns:
            MonteCarloResult with statistical analysis
        """
        logger.info(f"Starting Monte Carlo simulation: {n_simulations} simulations")
        
        if not trades:
            raise ValueError("No trades provided for Monte Carlo simulation")
        
        # Extract R-multiples from trades
        r_multiples = [trade.r_multiple for trade in trades]
        
        simulation_results = []
        equity_curves_sample = []
        
        initial_capital = 10000.0  # Normalized starting capital
        
        for sim in range(n_simulations):
            # Randomly shuffle trade order
            shuffled_r_multiples = random.sample(r_multiples, len(r_multiples))
            
            # Calculate equity curve for this simulation
            equity = initial_capital
            equity_curve = [equity]
            
            for r_mult in shuffled_r_multiples:
                # Assume 1% risk per trade
                risk_amount = equity * 0.01
                pnl = risk_amount * r_mult
                equity += pnl
                equity_curve.append(equity)
            
            # Calculate final return
            final_return = (equity - initial_capital) / initial_capital * 100
            
            # Calculate max drawdown for this simulation
            max_dd = self._calculate_max_drawdown_from_curve(equity_curve)
            
            simulation_results.append({
                'final_return': final_return,
                'max_drawdown': max_dd,
                'final_equity': equity,
                'equity_curve': equity_curve
            })
            
            # Save sample equity curves (first 10)
            if len(equity_curves_sample) < 10:
                equity_curves_sample.append(equity_curve)
        
        # Calculate statistics
        returns = [result['final_return'] for result in simulation_results]
        drawdowns = [result['max_drawdown'] for result in simulation_results]
        
        # Calculate percentiles
        worst_dd_95 = np.percentile(drawdowns, 95)
        best_return_95 = np.percentile(returns, 95)
        median_return = np.median(returns)
        
        # Calculate ruin probability (equity drops below 50% of initial)
        ruin_count = sum(1 for result in simulation_results if result['final_equity'] < initial_capital * 0.5)
        ruin_probability = (ruin_count / n_simulations) * 100
        
        # Calculate confidence intervals
        confidence_intervals = {
            '95%': {
                'return_lower': np.percentile(returns, 2.5),
                'return_upper': np.percentile(returns, 97.5),
                'drawdown_lower': np.percentile(drawdowns, 2.5),
                'drawdown_upper': np.percentile(drawdowns, 97.5)
            },
            '99%': {
                'return_lower': np.percentile(returns, 0.5),
                'return_upper': np.percentile(returns, 99.5),
                'drawdown_lower': np.percentile(drawdowns, 0.5),
                'drawdown_upper': np.percentile(drawdowns, 99.5)
            }
        }
        
        return MonteCarloResult(
            n_simulations=n_simulations,
            original_trades=len(trades),
            worst_drawdown_95pct=worst_dd_95,
            best_return_95pct=best_return_95,
            median_return=median_return,
            ruin_probability=ruin_probability,
            confidence_intervals=confidence_intervals,
            equity_curves_sample=equity_curves_sample
        )
    
    def calculate_metrics(
        self, trades: List[TradeResult], equity_curve: List[Dict], 
        df: pd.DataFrame, config: BacktestConfig
    ) -> ProfessionalMetrics:
        """
        Calculate professional-grade backtesting metrics
        
        Args:
            trades: List of trade results
            equity_curve: Equity curve data
            df: Original OHLCV data
            config: Backtesting configuration
            
        Returns:
            ProfessionalMetrics with comprehensive analysis
        """
        if not trades:
            return self._empty_metrics()
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.net_pnl > 0])
        losing_trades = len([t for t in trades if t.net_pnl <= 0])
        win_rate = (winning_trades / total_trades) * 100
        
        # P&L analysis
        gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0)
        gross_loss = abs(sum(t.net_pnl for t in trades if t.net_pnl < 0))
        net_profit = sum(t.net_pnl for t in trades)
        
        initial_capital = config.initial_capital
        total_return_pct = (net_profit / initial_capital) * 100
        
        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # R-multiple analysis
        r_multiples = [t.r_multiple for t in trades]
        winning_r = [r for r in r_multiples if r > 0]
        losing_r = [r for r in r_multiples if r <= 0]
        
        avg_win_r = np.mean(winning_r) if winning_r else 0
        avg_loss_r = np.mean(losing_r) if losing_r else 0
        expectancy = np.mean(r_multiples)
        
        # Drawdown analysis
        equity_values = [point['equity'] for point in equity_curve]
        max_drawdown_pct = self._calculate_max_drawdown_from_curve(equity_values)
        
        # Risk-adjusted metrics
        returns = [t.pnl_percent for t in trades]
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        calmar_ratio = total_return_pct / max_drawdown_pct if max_drawdown_pct > 0 else 0
        
        # Trade analysis
        best_trade = max(t.net_pnl for t in trades)
        worst_trade = min(t.net_pnl for t in trades)
        avg_duration = np.mean([t.trade_duration_hours for t in trades])
        avg_trade_duration = f"{avg_duration:.1f} hours"
        
        # Benchmark comparison (buy and hold)
        benchmark_return = self._calculate_benchmark_return(df)
        benchmark_comparison = total_return_pct - benchmark_return
        
        # Additional professional metrics
        recovery_factor = net_profit / (initial_capital * max_drawdown_pct / 100) if max_drawdown_pct > 0 else 0
        payoff_ratio = abs(avg_win_r / avg_loss_r) if avg_loss_r != 0 else 0
        sterling_ratio = self._calculate_sterling_ratio(equity_values, total_return_pct)
        ulcer_index = self._calculate_ulcer_index(equity_values)
        var_95 = np.percentile(returns, 5) if returns else 0
        cvar_95 = np.mean([r for r in returns if r <= var_95]) if returns else 0
        
        return ProfessionalMetrics(
            total_return_pct=total_return_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown_pct=max_drawdown_pct,
            avg_win_r=avg_win_r,
            avg_loss_r=avg_loss_r,
            expectancy=expectancy,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_trade_duration=avg_trade_duration,
            benchmark_comparison=benchmark_comparison,
            recovery_factor=recovery_factor,
            payoff_ratio=payoff_ratio,
            sterling_ratio=sterling_ratio,
            ulcer_index=ulcer_index,
            var_95=var_95,
            cvar_95=cvar_95
        )
    
    # Helper methods for calculations
    def _calculate_max_drawdown_from_curve(self, equity_values: List[float]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not equity_values:
            return 0.0
        
        peak = equity_values[0]
        max_dd = 0.0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak * 100
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate annualized Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Annualized (assuming daily returns)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation only)"""
        if not returns:
            return 0.0
        
        mean_return = np.mean(returns)
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf')
        
        downside_deviation = np.std(negative_returns, ddof=1)
        
        if downside_deviation == 0:
            return 0.0
        
        sortino = (mean_return / downside_deviation) * np.sqrt(252)
        return sortino
    
    def _calculate_sterling_ratio(self, equity_values: List[float], total_return: float) -> float:
        """Calculate Sterling ratio (return / average drawdown)"""
        if not equity_values:
            return 0.0
        
        drawdowns = []
        peak = equity_values[0]
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            else:
                drawdown = (peak - equity) / peak * 100
                if drawdown > 0:
                    drawdowns.append(drawdown)
        
        if not drawdowns:
            return 0.0
        
        avg_drawdown = np.mean(drawdowns)
        return total_return / avg_drawdown if avg_drawdown > 0 else 0
    
    def _calculate_ulcer_index(self, equity_values: List[float]) -> float:
        """Calculate Ulcer Index (measure of downside volatility)"""
        if not equity_values:
            return 0.0
        
        drawdowns = []
        peak = equity_values[0]
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak * 100
            drawdowns.append(drawdown ** 2)
        
        return np.sqrt(np.mean(drawdowns))
    
    def _calculate_benchmark_return(self, df: pd.DataFrame) -> float:
        """Calculate buy and hold return"""
        if len(df) < 2:
            return 0.0
        
        start_price = df['close'].iloc[0]
        end_price = df['close'].iloc[-1]
        
        return ((end_price - start_price) / start_price) * 100
    
    def _save_backtest_result(self, result: AdvancedBacktestResult) -> str:
        """Save backtest result to database"""
        try:
            backtest_id = str(uuid.uuid4())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO backtest_results 
                (id, symbol, timeframe, config_json, metrics_json, trade_log_json, 
                 equity_curve_json, total_return_pct, max_drawdown_pct, sharpe_ratio, 
                 win_rate, total_trades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backtest_id,
                result.symbol,
                result.timeframe,
                json.dumps(result.config.dict()),
                json.dumps(result.metrics.dict()),
                json.dumps([trade.dict() for trade in result.trades]),
                json.dumps(result.equity_curve),
                result.metrics.total_return_pct,
                result.metrics.max_drawdown_pct,
                result.metrics.sharpe_ratio,
                result.metrics.win_rate,
                result.metrics.total_trades
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Backtest result saved with ID: {backtest_id}")
            return backtest_id
            
        except Exception as e:
            logger.error(f"Error saving backtest result: {str(e)}")
            return ""
    
    def get_saved_result(self, backtest_id: str) -> Optional[SavedBacktestResult]:
        """Retrieve saved backtest result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM backtest_results WHERE id = ?
            """, (backtest_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return SavedBacktestResult(
                    id=result[0],
                    symbol=result[1],
                    timeframe=result[2],
                    config_json=result[3],
                    metrics_json=result[4],
                    trade_log_json=result[5],
                    equity_curve_json=result[6],
                    total_return_pct=result[7],
                    max_drawdown_pct=result[8],
                    timestamp=datetime.fromisoformat(result[12])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving backtest result: {str(e)}")
            return None
    
    def _empty_metrics(self) -> ProfessionalMetrics:
        """Return empty metrics for cases with no trades"""
        return ProfessionalMetrics(
            total_return_pct=0.0, win_rate=0.0, profit_factor=0.0, total_trades=0,
            sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0, max_drawdown_pct=0.0,
            avg_win_r=0.0, avg_loss_r=0.0, expectancy=0.0, best_trade=0.0, worst_trade=0.0,
            avg_trade_duration="0 hours", benchmark_comparison=0.0, recovery_factor=0.0,
            payoff_ratio=0.0, sterling_ratio=0.0, ulcer_index=0.0, var_95=0.0, cvar_95=0.0
        )
    
    # Additional helper methods
    def _is_valid_entry_signal(self, structure_event, current_price: float) -> bool:
        """Check if structure event represents a valid entry signal"""
        # Simple validation - can be enhanced with more sophisticated logic
        price_distance = abs(current_price - structure_event.break_price) / current_price
        return price_distance < 0.02  # Within 2% of break price
    
    def _calculate_sl_tp(self, entry_price: float, structure_event, current_price: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        # Simple ATR-based calculation
        atr_estimate = entry_price * 0.02  # 2% ATR estimate
        
        if 'bullish' in structure_event.structure_type.value:
            stop_loss = entry_price - (2 * atr_estimate)
            take_profit = entry_price + (3 * atr_estimate)  # 1.5:1 R:R
        else:
            stop_loss = entry_price + (2 * atr_estimate)
            take_profit = entry_price - (3 * atr_estimate)  # 1.5:1 R:R
        
        return stop_loss, take_profit
    
    def _calculate_unrealized_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate unrealized P&L for open position"""
        entry_price = position['actual_entry_price']
        position_size = position['position_size']
        signal_type = position['signal_type']
        
        if signal_type == 'BUY':
            return (current_price - entry_price) * position_size
        else:
            return (entry_price - current_price) * position_size
    
    def _force_close_position(
        self, position: Dict, final_candle: pd.Series, 
        final_time: datetime, config: TradeSimulatorConfig
    ) -> TradeResult:
        """Force close position at end of backtest"""
        exit_price = final_candle['close']
        
        # Apply slippage
        if position['signal_type'] == 'BUY':
            exit_price *= (1 - config.slippage_pct)
        else:
            exit_price *= (1 + config.slippage_pct)
        
        return self._create_trade_result(position, exit_price, final_time, "End of Data", config)
    
    def _calculate_period_metrics(self, trades: List[TradeResult], equity_curve: List[Dict]) -> Dict[str, float]:
        """Calculate metrics for a single walk-forward period"""
        if not trades:
            return {
                'total_return_pct': 0.0,
                'max_drawdown_pct': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Calculate basic metrics
        net_profit = sum(t.net_pnl for t in trades)
        initial_capital = 10000.0  # Normalized
        total_return_pct = (net_profit / initial_capital) * 100
        
        # Drawdown
        equity_values = [point['equity'] for point in equity_curve]
        max_drawdown_pct = self._calculate_max_drawdown_from_curve(equity_values)
        
        # Profit factor
        gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0)
        gross_loss = abs(sum(t.net_pnl for t in trades if t.net_pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio
        returns = [t.pnl_percent for t in trades]
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        
        return {
            'total_return_pct': total_return_pct,
            'max_drawdown_pct': max_drawdown_pct,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio
        }
    
    def _calculate_walk_forward_overall_metrics(self, periods: List[WalkForwardPeriod]) -> Dict[str, float]:
        """Calculate overall metrics across all walk-forward periods"""
        if not periods:
            return {}
        
        # Aggregate metrics
        total_trades = sum(p.total_trades for p in periods)
        total_winning = sum(p.winning_trades for p in periods)
        
        # Average metrics
        avg_return = np.mean([p.total_return_pct for p in periods])
        avg_drawdown = np.mean([p.max_drawdown_pct for p in periods])
        avg_profit_factor = np.mean([p.profit_factor for p in periods if p.profit_factor != float('inf')])
        avg_sharpe = np.mean([p.sharpe_ratio for p in periods])
        
        return {
            'total_trades': total_trades,
            'overall_win_rate': (total_winning / total_trades * 100) if total_trades > 0 else 0,
            'avg_return_pct': avg_return,
            'avg_max_drawdown_pct': avg_drawdown,
            'avg_profit_factor': avg_profit_factor,
            'avg_sharpe_ratio': avg_sharpe
        }
    
    def _calculate_consistency_score(self, periods: List[WalkForwardPeriod]) -> float:
        """Calculate consistency score across periods"""
        if len(periods) < 2:
            return 0.0
        
        returns = [p.total_return_pct for p in periods]
        
        # Calculate coefficient of variation (lower is more consistent)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if mean_return == 0:
            return 0.0
        
        cv = std_return / abs(mean_return)
        
        # Convert to consistency score (0-100, higher is better)
        consistency_score = max(0, 100 - (cv * 100))
        return consistency_score
    
    def _calculate_degradation_factor(self, periods: List[WalkForwardPeriod]) -> float:
        """Calculate performance degradation over time"""
        if len(periods) < 2:
            return 0.0
        
        returns = [p.total_return_pct for p in periods]
        
        # Calculate linear regression slope
        x = np.arange(len(returns))
        slope, _, _, _, _ = stats.linregress(x, returns)
        
        # Negative slope indicates degradation
        return slope
    
    def _calculate_monthly_returns(self, equity_curve: List[Dict]) -> Dict[str, float]:
        """Calculate monthly returns from equity curve"""
        monthly_returns = {}
        
        if not equity_curve:
            return monthly_returns
        
        # Group by month and calculate returns
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Resample to monthly
        monthly_equity = df['equity'].resample('M').last()
        
        for i in range(1, len(monthly_equity)):
            month_key = monthly_equity.index[i].strftime('%Y-%m')
            prev_equity = monthly_equity.iloc[i-1]
            curr_equity = monthly_equity.iloc[i]
            
            monthly_return = ((curr_equity - prev_equity) / prev_equity) * 100
            monthly_returns[month_key] = monthly_return
        
        return monthly_returns
    
    def _calculate_yearly_returns(self, equity_curve: List[Dict]) -> Dict[str, float]:
        """Calculate yearly returns from equity curve"""
        yearly_returns = {}
        
        if not equity_curve:
            return yearly_returns
        
        # Group by year and calculate returns
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Resample to yearly
        yearly_equity = df['equity'].resample('Y').last()
        
        for i in range(1, len(yearly_equity)):
            year_key = str(yearly_equity.index[i].year)
            prev_equity = yearly_equity.iloc[i-1]
            curr_equity = yearly_equity.iloc[i]
            
            yearly_return = ((curr_equity - prev_equity) / prev_equity) * 100
            yearly_returns[year_key] = yearly_return
        
        return yearly_returns
    
    def _calculate_drawdown_periods(self, equity_curve: List[Dict]) -> List[Dict]:
        """Calculate drawdown periods"""
        drawdown_periods = []
        
        if not equity_curve:
            return drawdown_periods
        
        equity_values = [point['equity'] for point in equity_curve]
        timestamps = [point['timestamp'] for point in equity_curve]
        
        peak = equity_values[0]
        peak_time = timestamps[0]
        in_drawdown = False
        drawdown_start = None
        
        for i, (equity, timestamp) in enumerate(zip(equity_values, timestamps)):
            if equity > peak:
                # New peak
                if in_drawdown:
                    # End of drawdown period
                    drawdown_periods.append({
                        'start': drawdown_start,
                        'end': timestamps[i-1],
                        'peak_before': peak,
                        'trough': min(equity_values[equity_values.index(peak):i]),
                        'recovery': timestamp,
                        'duration_days': (timestamp - drawdown_start).days if drawdown_start else 0
                    })
                    in_drawdown = False
                
                peak = equity
                peak_time = timestamp
            
            elif equity < peak and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                drawdown_start = timestamp
        
        return drawdown_periods