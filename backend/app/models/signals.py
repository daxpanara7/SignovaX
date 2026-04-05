from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

class TradingSignal(BaseModel):
    id: Optional[str] = None
    symbol: str
    timeframe: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float  # 0-100
    reasoning: str
    timestamp: datetime
    status: SignalStatus = SignalStatus.ACTIVE
    
class BacktestResult(BaseModel):
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    trade_logs: list