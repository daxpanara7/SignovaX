"""
Advanced Backtesting Data Models
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class TradeSimulatorConfig(BaseModel):
    """Configuration for realistic trade simulation"""
    slippage_pct: float = 0.0005      # 0.05% slippage
    commission_pct: float = 0.001     # 0.1% commission per trade
    spread_pips: float = 2.0          # for forex pairs


class TradeResult(BaseModel):
    """Individual trade result with realistic costs"""
    entry_time: datetime
    exit_time: datetime
    signal_type: str  # BUY/SELL
    entry_price: float
    exit_price: float
    signal_entry_price: float  # Original signal price
    signal_exit_price: float   # Original signal price
    position_size: float
    gross_pnl: float
    slippage_cost: float
    commission_cost: float
    net_pnl: float
    pnl_percent: float
    r_multiple: float  # Risk multiple (net P&L / risk amount)
    exit_reason: str
    confidence: float
    reasoning: str
    trade_duration_hours: float


class WalkForwardPeriod(BaseModel):
    """Single period result in walk-forward testing"""
    period_number: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    total_trades: int
    winning_trades: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    sharpe_ratio: float
    trades: List[TradeResult]


class WalkForwardResult(BaseModel):
    """Complete walk-forward testing result"""
    n_splits: int
    per_period_results: List[WalkForwardPeriod]
    overall_metrics: Dict[str, float]
    consistency_score: float  # How consistent results are across periods
    degradation_factor: float  # Performance degradation over time


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation result"""
    n_simulations: int
    original_trades: int
    worst_drawdown_95pct: float    # 95th percentile worst DD
    best_return_95pct: float       # 95th percentile best return
    median_return: float
    ruin_probability: float        # % sims that hit -50% balance
    confidence_intervals: Dict[str, Dict[str, float]]  # 95%, 99% intervals
    equity_curves_sample: List[List[float]]  # Sample of 10 curves for chart


class ProfessionalMetrics(BaseModel):
    """Professional-grade backtesting metrics"""
    # Basic metrics
    total_return_pct: float
    win_rate: float
    profit_factor: float           # gross_profit / gross_loss
    total_trades: int
    
    # Risk-adjusted metrics
    sharpe_ratio: float            # annualized
    sortino_ratio: float           # downside deviation only
    calmar_ratio: float            # return / max_drawdown
    max_drawdown_pct: float
    
    # R-multiple analysis
    avg_win_r: float               # average win in R multiples
    avg_loss_r: float              # average loss in R multiples
    expectancy: float              # avg R per trade
    
    # Trade analysis
    best_trade: float
    worst_trade: float
    avg_trade_duration: str
    
    # Benchmark comparison
    benchmark_comparison: float     # vs buy and hold return
    
    # Additional professional metrics
    recovery_factor: float         # net profit / max drawdown
    payoff_ratio: float           # avg win / avg loss
    sterling_ratio: float         # return / avg drawdown
    ulcer_index: float            # measure of downside volatility
    var_95: float                 # Value at Risk 95%
    cvar_95: float                # Conditional VaR 95%


class BacktestConfig(BaseModel):
    """Complete backtesting configuration"""
    symbol: str
    timeframe: str = "1h"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 10000.0
    
    # Trade simulation
    trade_simulator: TradeSimulatorConfig = TradeSimulatorConfig()
    
    # Strategy parameters
    min_confidence: float = 75.0
    risk_per_trade: float = 0.01  # 1% risk per trade
    
    # Advanced options
    enable_compounding: bool = True
    max_concurrent_trades: int = 1
    benchmark_symbol: Optional[str] = None


class AdvancedBacktestResult(BaseModel):
    """Complete advanced backtesting result"""
    # Basic info
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    config: BacktestConfig
    
    # Trade results
    trades: List[TradeResult]
    equity_curve: List[Dict[str, Any]]
    
    # Professional metrics
    metrics: ProfessionalMetrics
    
    # Analysis timestamp
    analysis_timestamp: datetime
    
    # Additional data
    monthly_returns: Dict[str, float]
    yearly_returns: Dict[str, float]
    drawdown_periods: List[Dict[str, Any]]


class BacktestSummary(BaseModel):
    """Summary of backtest for quick overview"""
    backtest_id: str
    symbol: str
    timeframe: str
    period_days: int
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    created_at: datetime


class SavedBacktestResult(BaseModel):
    """Saved backtest result in database"""
    id: str
    config_json: str
    metrics_json: str
    trade_log_json: str
    equity_curve_json: str
    timestamp: datetime
    symbol: str
    timeframe: str
    total_return_pct: float
    max_drawdown_pct: float