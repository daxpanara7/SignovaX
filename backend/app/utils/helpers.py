import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    return true_range.rolling(period).mean()

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period).mean()

def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return series.rolling(window=period).mean()

def find_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict:
    """Find support and resistance levels"""
    highs = df['high'].rolling(window=window, center=True).max()
    lows = df['low'].rolling(window=window, center=True).min()
    
    resistance_levels = df[df['high'] == highs]['high'].dropna().unique()
    support_levels = df[df['low'] == lows]['low'].dropna().unique()
    
    return {
        'resistance': sorted(resistance_levels, reverse=True)[:5],
        'support': sorted(support_levels)[:5]
    }

def calculate_volatility(df: pd.DataFrame, period: int = 20) -> float:
    """Calculate price volatility"""
    returns = df['close'].pct_change()
    return returns.rolling(window=period).std().iloc[-1] * np.sqrt(252)  # Annualized

def format_currency(amount: float, symbol: str = "USD") -> str:
    """Format currency amount"""
    if symbol == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {symbol}"

def calculate_position_size(
    account_balance: float, 
    risk_percent: float, 
    entry_price: float, 
    stop_loss: float
) -> float:
    """Calculate position size based on risk management"""
    risk_amount = account_balance * (risk_percent / 100)
    price_risk = abs(entry_price - stop_loss)
    
    if price_risk == 0:
        return 0
    
    position_size = risk_amount / price_risk
    return position_size

def validate_timeframe(timeframe: str) -> bool:
    """Validate if timeframe is supported"""
    valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    return timeframe in valid_timeframes

def convert_timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes"""
    timeframe_map = {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '2h': 120, '4h': 240, '6h': 360,
        '8h': 480, '12h': 720, '1d': 1440,
        '3d': 4320, '1w': 10080, '1M': 43200
    }
    return timeframe_map.get(timeframe, 60)

def generate_trade_id() -> str:
    """Generate unique trade ID"""
    return f"SMC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def calculate_drawdown_series(equity_curve: List[float]) -> List[float]:
    """Calculate drawdown series from equity curve"""
    if not equity_curve:
        return []
    
    drawdowns = []
    peak = equity_curve[0]
    
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        
        drawdown = (peak - equity) / peak * 100
        drawdowns.append(drawdown)
    
    return drawdowns

def is_market_hours(symbol: str) -> bool:
    """Check if market is open for given symbol"""
    now = datetime.now()
    
    # Crypto markets are always open
    if any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']):
        return True
    
    # Forex markets (simplified - Monday to Friday)
    if now.weekday() < 5:  # Monday = 0, Friday = 4
        return True
    
    return False