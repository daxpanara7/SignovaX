from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.market_data_service import MarketDataService
from app.models.market_data import MarketData

router = APIRouter()
market_data_service = MarketDataService()

@router.get("/ohlcv", response_model=MarketData)
async def get_ohlcv_data(
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    timeframe: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(500, description="Number of candles to fetch")
):
    """Fetch OHLCV market data"""
    try:
        market_data = await market_data_service.fetch_ohlcv(symbol, timeframe, limit)
        return market_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")

@router.get("/symbols")
async def get_available_symbols():
    """Get list of available trading symbols"""
    return {
        "crypto": [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
            "BNBUSDT", "XRPUSDT", "LTCUSDT", "BCHUSDT", "EOSUSDT"
        ],
        "forex": [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
            "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"
        ]
    }

@router.get("/timeframes")
async def get_available_timeframes():
    """Get list of supported timeframes"""
    return {
        "timeframes": [
            {"value": "1m", "label": "1 Minute"},
            {"value": "5m", "label": "5 Minutes"},
            {"value": "15m", "label": "15 Minutes"},
            {"value": "1h", "label": "1 Hour"},
            {"value": "4h", "label": "4 Hours"},
            {"value": "1d", "label": "1 Day"}
        ]
    }