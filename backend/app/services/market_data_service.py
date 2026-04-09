import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import aiohttp
from app.models.market_data import OHLCV, MarketData

class MarketDataService:
    def __init__(self):
        self.exchange = ccxt.binance({
            'sandbox': True,  # Use testnet for demo
            'enableRateLimit': True,
        })
    
    async def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1h', 
        limit: int = 500
    ) -> MarketData:
        """Fetch OHLCV data from Binance"""
        try:
            # Fetch data from exchange
            ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to our model format
            ohlcv_list = []
            for candle in ohlcv_data:
                ohlcv = OHLCV(
                    timestamp=datetime.fromtimestamp(candle[0] / 1000),
                    open=float(candle[1]),
                    high=float(candle[2]),
                    low=float(candle[3]),
                    close=float(candle[4]),
                    volume=float(candle[5])
                )
                ohlcv_list.append(ohlcv)
            
            return MarketData(
                symbol=symbol,
                timeframe=timeframe,
                data=ohlcv_list
            )
        
        except Exception as e:
            # Fallback to mock data for demo
            return self._generate_mock_data(symbol, timeframe, limit)
    
    def _generate_mock_data(self, symbol: str, timeframe: str, limit: int) -> MarketData:
        """Generate realistic mock OHLCV data for demo purposes"""
        import random
        import numpy as np
        
        # Start with a base price
        base_price = 50000 if 'BTC' in symbol else 2000 if 'ETH' in symbol else 1.0
        
        ohlcv_list = []
        current_time = datetime.now() - timedelta(hours=limit)
        current_price = base_price
        
        for i in range(limit):
            # Generate realistic price movement
            volatility = 0.02  # 2% volatility
            price_change = np.random.normal(0, volatility)
            
            open_price = current_price
            close_price = open_price * (1 + price_change)
            
            # Generate high and low with realistic wicks
            high_wick = random.uniform(0, 0.01)  # Up to 1% wick
            low_wick = random.uniform(0, 0.01)   # Up to 1% wick
            
            high_price = max(open_price, close_price) * (1 + high_wick)
            low_price = min(open_price, close_price) * (1 - low_wick)
            
            volume = random.uniform(100, 1000)
            
            ohlcv = OHLCV(
                timestamp=current_time + timedelta(hours=i),
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=round(volume, 2)
            )
            ohlcv_list.append(ohlcv)
            current_price = close_price
        
        return MarketData(
            symbol=symbol,
            timeframe=timeframe,
            data=ohlcv_list
        )
    
    def to_dataframe(self, market_data: MarketData) -> pd.DataFrame:
        """Convert MarketData to pandas DataFrame for analysis"""
        data = []
        for ohlcv in market_data.data:
            data.append({
                'timestamp': ohlcv.timestamp,
                'open': ohlcv.open,
                'high': ohlcv.high,
                'low': ohlcv.low,
                'close': ohlcv.close,
                'volume': ohlcv.volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df