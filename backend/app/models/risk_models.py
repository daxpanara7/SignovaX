"""
Risk Management Data Models
"""

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, date
from enum import Enum


class RiskValidationResult(BaseModel):
    """Result of signal risk validation"""
    approved: bool
    reason: str
    position_size: Optional[float] = None
    risk_amount: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status information"""
    active: bool
    triggered_at: Optional[datetime] = None
    daily_loss_pct: float
    max_allowed_loss_pct: float
    reason: str


class RiskMetrics(BaseModel):
    """Current risk metrics"""
    account_balance: float
    daily_pnl: float
    daily_loss_pct: float
    trades_today: int
    concurrent_trades: int
    max_concurrent_trades: int
    circuit_breaker_active: bool
    risk_per_trade: float
    max_daily_loss: float


class PositionSizeRequest(BaseModel):
    """Request for position size calculation"""
    entry: float
    stop_loss: float
    account_balance: Optional[float] = None
    risk_pct: Optional[float] = None


class PositionSizeResponse(BaseModel):
    """Response for position size calculation"""
    position_size: float
    risk_amount: float
    pip_risk: float
    risk_pct: float


class SignalValidationRequest(BaseModel):
    """Request for signal validation"""
    symbol: str
    signal_type: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: str


class DailyRiskLog(BaseModel):
    """Daily risk log entry"""
    date: date
    starting_balance: float
    current_balance: float
    trades_taken: int
    daily_pnl: float
    circuit_breaker_triggered: bool
    max_drawdown: float
    created_at: datetime


class CorrelationGroup(str, Enum):
    """Asset correlation groups"""
    CRYPTO = "crypto"
    FOREX_USD = "forex_usd"
    FOREX_EUR = "forex_eur"
    COMMODITIES = "commodities"
    INDICES = "indices"


class OpenTrade(BaseModel):
    """Open trade information for correlation checking"""
    symbol: str
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    unrealized_pnl: float
    correlation_group: CorrelationGroup