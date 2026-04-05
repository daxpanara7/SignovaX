"""
Input Validation Models using Pydantic
Comprehensive validation for all API request bodies
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
import re


class SymbolValidator(BaseModel):
    """Symbol validation model"""
    symbol: str = Field(..., description="Trading pair symbol")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate symbol format"""
        if not v:
            raise ValueError("Symbol is required")
        
        # Symbol must match pattern: 3-10 uppercase letters + currency suffix
        pattern = r'^[A-Z]{3,10}(USDT|USD|EUR|GBP|JPY|AUD|CAD|CHF|NZD)$'
        if not re.match(pattern, v):
            raise ValueError(
                "Symbol must be 3-10 uppercase letters followed by USDT, USD, EUR, GBP, JPY, AUD, CAD, CHF, or NZD"
            )
        
        return v


class TimeframeValidator(BaseModel):
    """Timeframe validation model"""
    timeframe: str = Field(..., description="Chart timeframe")
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe"""
        if not v:
            raise ValueError("Timeframe is required")
        
        allowed_timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
        if v not in allowed_timeframes:
            raise ValueError(f"Timeframe must be one of: {', '.join(allowed_timeframes)}")
        
        return v


class DateRangeValidator(BaseModel):
    """Date range validation model"""
    start_date: Optional[datetime] = Field(None, description="Start date for analysis")
    end_date: Optional[datetime] = Field(None, description="End date for analysis")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date"""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError("End date must be after start date")
        
        return v
    
    @validator('start_date', 'end_date')
    def validate_date_not_future(cls, v):
        """Validate that dates are not in the future"""
        if v and v > datetime.now():
            raise ValueError("Date cannot be in the future")
        
        return v


class PriceValidator(BaseModel):
    """Price validation model"""
    entry: Optional[float] = Field(None, gt=0, description="Entry price")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    
    @validator('entry', 'stop_loss', 'take_profit')
    def validate_positive_prices(cls, v):
        """Validate that prices are positive"""
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        
        return v
    
    @validator('stop_loss')
    def validate_stop_loss(cls, v, values):
        """Validate stop loss relative to entry"""
        if v and 'entry' in values and values['entry']:
            # Allow both long and short positions
            # For validation, we just ensure they're different
            if v == values['entry']:
                raise ValueError("Stop loss cannot equal entry price")
        
        return v
    
    @validator('take_profit')
    def validate_take_profit(cls, v, values):
        """Validate take profit relative to entry"""
        if v and 'entry' in values and values['entry']:
            # Allow both long and short positions
            # For validation, we just ensure they're different
            if v == values['entry']:
                raise ValueError("Take profit cannot equal entry price")
        
        return v


class PercentageValidator(BaseModel):
    """Percentage validation model"""
    percentage: float = Field(..., ge=0, le=100, description="Percentage value (0-100)")
    
    @validator('percentage')
    def validate_percentage(cls, v):
        """Validate percentage range"""
        if v < 0 or v > 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        return v


class RiskValidator(BaseModel):
    """Risk parameter validation model"""
    risk_per_trade: Optional[float] = Field(None, gt=0, le=0.1, description="Risk per trade (0-10%)")
    max_daily_loss: Optional[float] = Field(None, gt=0, le=0.5, description="Maximum daily loss (0-50%)")
    
    @validator('risk_per_trade')
    def validate_risk_per_trade(cls, v):
        """Validate risk per trade"""
        if v is not None and (v <= 0 or v > 0.1):
            raise ValueError("Risk per trade must be between 0 and 10% (0.1)")
        
        return v
    
    @validator('max_daily_loss')
    def validate_max_daily_loss(cls, v):
        """Validate maximum daily loss"""
        if v is not None and (v <= 0 or v > 0.5):
            raise ValueError("Maximum daily loss must be between 0 and 50% (0.5)")
        
        return v


class StringValidator(BaseModel):
    """String input validation model"""
    text: str = Field(..., min_length=1, max_length=1000, description="Text input")
    
    @validator('text')
    def sanitize_string(cls, v):
        """Sanitize string input"""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
        for char in dangerous_chars:
            v = v.replace(char, '')
        
        # Limit length
        if len(v) > 1000:
            v = v[:1000]
        
        return v.strip()


class ConfidenceValidator(BaseModel):
    """Confidence level validation model"""
    confidence: float = Field(..., ge=0, le=100, description="Confidence level (0-100)")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence level"""
        if v < 0 or v > 100:
            raise ValueError("Confidence must be between 0 and 100")
        
        return v


class QuantityValidator(BaseModel):
    """Quantity validation model"""
    quantity: float = Field(..., gt=0, description="Trade quantity")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate trade quantity"""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        
        # Check for reasonable limits
        if v > 1000000:  # 1 million units max
            raise ValueError("Quantity exceeds maximum limit")
        
        return v


class PaginationValidator(BaseModel):
    """Pagination validation model"""
    page: int = Field(1, ge=1, le=1000, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    
    @validator('page')
    def validate_page(cls, v):
        """Validate page number"""
        if v < 1 or v > 1000:
            raise ValueError("Page must be between 1 and 1000")
        
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        """Validate items per page"""
        if v < 1 or v > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        return v


# Combined validation models for common use cases
class BasicTradingRequest(SymbolValidator, TimeframeValidator):
    """Basic trading request validation"""
    pass


class TradingSignalRequest(SymbolValidator, TimeframeValidator, PriceValidator, ConfidenceValidator):
    """Trading signal request validation"""
    pass


class BacktestRequest(SymbolValidator, TimeframeValidator, DateRangeValidator, RiskValidator):
    """Backtest request validation"""
    initial_capital: float = Field(1000.0, gt=0, le=10000000, description="Initial capital")
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        """Validate initial capital"""
        if v <= 0:
            raise ValueError("Initial capital must be positive")
        
        if v > 10000000:  # 10 million max
            raise ValueError("Initial capital exceeds maximum limit")
        
        return v


class AnalysisRequest(SymbolValidator, TimeframeValidator, DateRangeValidator):
    """Analysis request validation"""
    min_confidence: Optional[float] = Field(70.0, ge=0, le=100, description="Minimum confidence level")
    
    @validator('min_confidence')
    def validate_min_confidence(cls, v):
        """Validate minimum confidence"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Minimum confidence must be between 0 and 100")
        
        return v


# Validation helper functions
def validate_symbol_format(symbol: str) -> bool:
    """Validate symbol format"""
    try:
        SymbolValidator(symbol=symbol)
        return True
    except ValueError:
        return False


def validate_timeframe_format(timeframe: str) -> bool:
    """Validate timeframe format"""
    try:
        TimeframeValidator(timeframe=timeframe)
        return True
    except ValueError:
        return False


def sanitize_user_input(text: str) -> str:
    """Sanitize user input string"""
    try:
        validator = StringValidator(text=text)
        return validator.text
    except ValueError:
        return ""


def validate_price_levels(entry: float, stop_loss: float, take_profit: float, signal_type: str) -> bool:
    """Validate price levels for a trading signal"""
    try:
        # Basic price validation
        PriceValidator(entry=entry, stop_loss=stop_loss, take_profit=take_profit)
        
        # Signal-specific validation
        if signal_type.upper() == "BUY":
            # For buy signals: SL < Entry < TP
            if stop_loss >= entry:
                return False
            if take_profit <= entry:
                return False
        elif signal_type.upper() == "SELL":
            # For sell signals: TP < Entry < SL
            if take_profit >= entry:
                return False
            if stop_loss <= entry:
                return False
        
        return True
        
    except ValueError:
        return False