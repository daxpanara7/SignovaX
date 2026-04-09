from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OHLCV(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketData(BaseModel):
    symbol: str
    timeframe: str
    data: List[OHLCV]

class LiquidityZone(BaseModel):
    level: float
    zone_type: str  # "support" or "resistance"
    strength: int  # 1-5 scale
    timestamp: datetime

class OrderBlock(BaseModel):
    high: float
    low: float
    timestamp: datetime
    block_type: str  # "bullish" or "bearish"
    mitigation_level: float

class FairValueGap(BaseModel):
    top: float
    bottom: float
    timestamp: datetime
    gap_type: str  # "bullish" or "bearish"
    filled: bool = False

class SMCAnalysis(BaseModel):
    symbol: str
    timeframe: str
    liquidity_zones: List[LiquidityZone]
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    bos_signals: List[dict]
    choch_signals: List[dict]
    analysis_timestamp: datetime