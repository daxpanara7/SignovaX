"""
Precise SMC Data Models with Mathematical Definitions
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for SMC patterns"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SignalType(str, Enum):
    """Signal types for structure events"""
    CONTINUATION = "continuation"
    REVERSAL = "reversal"


class OrderBlockType(str, Enum):
    """Order block types"""
    BULLISH = "bullish"
    BEARISH = "bearish"


class FVGType(str, Enum):
    """Fair Value Gap types"""
    BULLISH = "bullish"
    BEARISH = "bearish"


class LiquidityType(str, Enum):
    """Liquidity zone types"""
    EQUAL_HIGHS = "equal_highs"
    EQUAL_LOWS = "equal_lows"


class StructureType(str, Enum):
    """Structure event types"""
    BOS_BULLISH = "bos_bullish"
    BOS_BEARISH = "bos_bearish"
    CHOCH_BULLISH = "choch_bullish"
    CHOCH_BEARISH = "choch_bearish"


class OrderBlock(BaseModel):
    """Precise Order Block definition"""
    # Zone definition
    top: float
    bottom: float
    timestamp: datetime
    candle_index: int
    
    # Type and classification
    ob_type: OrderBlockType
    timeframe: str
    
    # Validation metrics
    displacement_size: float  # Size of the displacement candle
    atr_multiple: float      # Displacement size as multiple of ATR
    
    # Mitigation tracking
    mitigated: bool = False
    mitigation_time: Optional[datetime] = None
    mitigation_price: Optional[float] = None
    
    # Confidence and invalidation
    confidence: ConfidenceLevel
    invalidation_price: float  # Price level that invalidates this OB
    
    # Additional metadata
    impulse_candle_index: int  # Index of the impulse candle
    strength: int = 1  # 1-5 strength rating


class FairValueGap(BaseModel):
    """Precise Fair Value Gap definition"""
    # Gap definition
    top: float
    bottom: float
    gap_size: float
    timestamp: datetime
    candle_index: int
    
    # Type and classification
    fvg_type: FVGType
    timeframe: str
    
    # Size validation
    atr_multiple: float  # Gap size as multiple of ATR
    min_size_met: bool   # Whether gap meets minimum size requirement
    
    # Fill tracking
    filled: bool = False
    fill_percentage: float = 0.0
    fill_time: Optional[datetime] = None
    partial_fill_prices: List[float] = []
    
    # Confidence and invalidation
    confidence: ConfidenceLevel
    invalidation_price: float
    
    # Gap formation candles
    candle_before_index: int  # i-1
    candle_middle_index: int  # i
    candle_after_index: int   # i+1


class LiquidityZone(BaseModel):
    """Precise Liquidity Zone definition"""
    # Level definition
    price: float
    zone_type: LiquidityType
    timestamp: datetime
    
    # Equal level tracking
    equal_levels: List[Dict[str, Any]]  # List of equal high/low points
    level_count: int  # Number of equal levels found
    price_tolerance: float  # Tolerance used for equality
    
    # Sweep tracking
    swept: bool = False
    sweep_time: Optional[datetime] = None
    sweep_price: Optional[float] = None
    sweep_candle_index: Optional[int] = None
    
    # Validation
    min_candle_distance_met: bool  # Whether 5+ candles between levels
    timeframe: str
    
    # Confidence and strength
    confidence: ConfidenceLevel
    strength: int  # Based on number of equal levels and volume
    invalidation_price: float


class StructureEvent(BaseModel):
    """Precise Structure Event (BOS/CHOCH) definition"""
    # Event definition
    structure_type: StructureType
    timestamp: datetime
    candle_index: int
    
    # Price levels
    break_price: float  # Price that was broken
    close_price: float  # Close price of breaking candle
    previous_structure_price: float  # Previous HH/LL/HL/LH
    
    # Signal classification
    signal_type: SignalType  # CONTINUATION or REVERSAL
    position_size_multiplier: float  # 1.0 for BOS, 0.5 for CHOCH
    
    # Trend context
    previous_trend: str  # "uptrend" or "downtrend"
    new_trend: str      # Expected new trend direction
    
    # Validation and confidence
    timeframe: str
    confidence: ConfidenceLevel
    invalidation_price: float
    
    # Structure context
    swing_high_price: Optional[float] = None
    swing_low_price: Optional[float] = None
    structure_sequence: List[str] = []  # HH, HL, LH, LL sequence


class SMCAnalysis(BaseModel):
    """Complete SMC Analysis Result"""
    symbol: str
    timeframe: str
    analysis_timestamp: datetime
    
    # Pattern detections
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    liquidity_zones: List[LiquidityZone]
    structure_events: List[StructureEvent]
    
    # Market context
    current_trend: str
    atr_14: float
    current_price: float
    
    # Analysis metadata
    candles_analyzed: int
    detection_summary: Dict[str, int]  # Count of each pattern type
    
    # Quality metrics
    high_confidence_patterns: int
    active_patterns: int  # Non-mitigated/non-filled patterns


class SMCDetectionConfig(BaseModel):
    """Configuration for SMC detection parameters"""
    # Order Block parameters
    min_displacement_atr_multiple: float = 1.5
    ob_confidence_thresholds: Dict[str, float] = {
        "high": 2.0,    # 2x ATR displacement
        "medium": 1.5,  # 1.5x ATR displacement
        "low": 1.0      # 1x ATR displacement
    }
    
    # FVG parameters
    min_fvg_atr_multiple: float = 0.3
    fvg_confidence_thresholds: Dict[str, float] = {
        "high": 0.8,    # 0.8x ATR gap size
        "medium": 0.5,  # 0.5x ATR gap size
        "low": 0.3      # 0.3x ATR gap size
    }
    
    # Liquidity parameters
    liquidity_price_tolerance: float = 0.001  # 0.1% tolerance
    min_candles_between_levels: int = 5
    liquidity_confidence_thresholds: Dict[str, int] = {
        "high": 4,      # 4+ equal levels
        "medium": 3,    # 3 equal levels
        "low": 2        # 2 equal levels
    }
    
    # Structure parameters
    min_structure_break_pct: float = 0.001  # 0.1% minimum break
    structure_lookback_periods: int = 50
    
    # General parameters
    atr_period: int = 14
    swing_detection_period: int = 5