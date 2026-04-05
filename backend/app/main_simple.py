from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import os
import aiohttp
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SMC Trading System",
    description="Smart Money Concepts Algorithmic Trading Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global variable to store real prices
real_prices = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def fetch_real_crypto_prices():
    """Fetch real crypto prices from Binance API"""
    global real_prices
    
    try:
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT", "LINKUSDT"]
        
        async with aiohttp.ClientSession() as session:
            # Get 24hr ticker statistics from Binance
            url = "https://api.binance.com/api/v3/ticker/24hr"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for ticker in data:
                        if ticker['symbol'] in symbols:
                            real_prices[ticker['symbol']] = {
                                'price': float(ticker['lastPrice']),
                                'change_24h': float(ticker['priceChangePercent']),
                                'volume_24h': float(ticker['volume']),
                                'high_24h': float(ticker['highPrice']),
                                'low_24h': float(ticker['lowPrice'])
                            }
                    
                    print(f"✅ Updated real prices for {len(real_prices)} symbols")
                else:
                    print(f"⚠️ Failed to fetch prices: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error fetching real prices: {e}")
        # Fallback to mock prices if API fails
        real_prices = {
            "BTCUSDT": {"price": 43250.50, "change_24h": 2.34, "volume_24h": 28543.21},
            "ETHUSDT": {"price": 2634.80, "change_24h": -1.12, "volume_24h": 156432.45},
            "ADAUSDT": {"price": 0.4523, "change_24h": 0.89, "volume_24h": 89234.67},
            "SOLUSDT": {"price": 94.67, "change_24h": 3.45, "volume_24h": 45123.89},
            "DOTUSDT": {"price": 7.23, "change_24h": -0.67, "volume_24h": 23456.78},
            "LINKUSDT": {"price": 15.84, "change_24h": 1.23, "volume_24h": 34567.89}
        }

async def fetch_real_ohlcv_data(symbol: str, interval: str = "15m", limit: int = 100):
    """Fetch real OHLCV data from Binance API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    ohlcv_data = []
                    for candle in data:
                        ohlcv_data.append({
                            "timestamp": datetime.fromtimestamp(candle[0] / 1000).isoformat(),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5])
                        })
                    
                    return ohlcv_data
                else:
                    print(f"⚠️ Failed to fetch OHLCV for {symbol}: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error fetching OHLCV for {symbol}: {e}")
        return None

# Background task to update prices every 30 seconds
async def price_updater():
    """Background task to update crypto prices"""
    while True:
        await fetch_real_crypto_prices()
        await asyncio.sleep(30)  # Update every 30 seconds

@app.on_event("startup")
async def startup_event():
    """Initialize real prices on startup"""
    await fetch_real_crypto_prices()
    # Start background price updater
    asyncio.create_task(price_updater())

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "SMC Trading System API", 
        "version": "1.0.0",
        "environment": "development",
        "docs_url": "/docs",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy", 
        "service": "smc-trading-system",
        "environment": "development"
    }

# Mock data endpoints for demo
@app.get("/api/data/ohlcv")
async def get_ohlcv_data(symbol: str = "BTCUSDT", timeframe: str = "15m"):
    """Get OHLCV data - tries real API first, falls back to mock data"""
    
    # Map frontend timeframes to Binance intervals
    interval_map = {
        "1m": "1m",
        "5m": "5m", 
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d"
    }
    
    binance_interval = interval_map.get(timeframe, "15m")
    
    # Try to get real data first
    real_data = await fetch_real_ohlcv_data(symbol, binance_interval, 100)
    
    if real_data:
        print(f"✅ Returning real OHLCV data for {symbol} {timeframe}")
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": real_data,
            "source": "binance_api"
        }
    
    # Fallback to mock data if real API fails
    print(f"⚠️ Using mock OHLCV data for {symbol} {timeframe}")
    
    # Generate mock OHLCV data based on real current price if available
    periods = 100
    start_time = datetime.now() - timedelta(hours=periods)
    
    # Use real price as base if available
    if symbol in real_prices:
        base_price = real_prices[symbol]['price']
    else:
        base_price = 45000 if symbol == "BTCUSDT" else 2800 if symbol == "ETHUSDT" else 0.45
    
    data = []
    current_price = base_price
    
    for i in range(periods):
        timestamp = start_time + timedelta(minutes=15 * i)
        
        # Generate realistic price movement
        change = np.random.normal(0, 0.008)  # 0.8% volatility
        current_price *= (1 + change)
        
        open_price = current_price
        high_price = open_price * (1 + abs(np.random.normal(0, 0.003)))
        low_price = open_price * (1 - abs(np.random.normal(0, 0.003)))
        close_price = low_price + np.random.random() * (high_price - low_price)
        volume = np.random.uniform(100, 1000)
        
        data.append({
            "timestamp": timestamp.isoformat(),
            "open": round(open_price, 4),
            "high": round(high_price, 4),
            "low": round(low_price, 4),
            "close": round(close_price, 4),
            "volume": round(volume, 2)
        })
        
        current_price = close_price
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": data,
        "source": "mock_data"
    }

@app.get("/api/signals/current")
async def get_current_signal():
    """Mock current signal endpoint"""
    import random
    
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
    directions = ["BUY", "SELL"]
    sessions = ["asia", "london", "new_york"]
    
    symbol = random.choice(symbols)
    direction = random.choice(directions)
    base_price = 45000 if symbol == "BTCUSDT" else 2800 if symbol == "ETHUSDT" else 0.45
    
    if direction == "BUY":
        entry_price = base_price * 0.999
        stop_loss = entry_price * 0.985
        take_profit = entry_price * 1.03
    else:
        entry_price = base_price * 1.001
        stop_loss = entry_price * 1.015
        take_profit = entry_price * 0.97
    
    return {
        "id": random.randint(1000, 9999),
        "symbol": symbol,
        "direction": direction,
        "entry_price": round(entry_price, 4),
        "stop_loss": round(stop_loss, 4),
        "take_profit": round(take_profit, 4),
        "confluence_score": random.randint(70, 95),
        "ml_probability": round(random.uniform(0.65, 0.85), 3),
        "session": random.choice(sessions),
        "timeframes": ["4h", "1h", "15m"],
        "timestamp": "2024-01-01T00:00:00Z",
        "type": random.choice(["Order Block + FVG", "Liquidity Sweep", "BOS Confirmation"])
    }

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Mock performance metrics endpoint"""
    import random
    
    return {
        "total_return_percent": round(random.uniform(10, 50), 2),
        "win_rate": round(random.uniform(55, 75), 1),
        "profit_factor": round(random.uniform(1.2, 2.5), 2),
        "sharpe_ratio": round(random.uniform(0.8, 1.8), 2),
        "max_drawdown": round(random.uniform(5, 15), 1),
        "expectancy": round(random.uniform(20, 80), 2),
        "total_trades": random.randint(100, 300),
        "calmar_ratio": round(random.uniform(0.8, 2.0), 2)
    }

@app.get("/api/watchlist/prices")
async def get_watchlist_prices():
    """Get real-time watchlist prices from Binance API"""
    global real_prices
    
    # If we don't have real prices yet, fetch them
    if not real_prices:
        await fetch_real_crypto_prices()
    
    # Return real prices with additional calculated data
    data = {}
    for symbol, price_data in real_prices.items():
        # Add some sparkline data (mock for now, but based on real price)
        sparkline = []
        base_price = price_data['price']
        for i in range(7):
            variation = np.random.uniform(-0.02, 0.02)  # ±2% variation
            sparkline.append(base_price * (1 + variation))
        
        data[symbol] = {
            "price": price_data['price'],
            "change_24h": price_data['change_24h'],
            "volume_24h": price_data.get('volume_24h', 0),
            "high_24h": price_data.get('high_24h', price_data['price']),
            "low_24h": price_data.get('low_24h', price_data['price']),
            "sparkline": sparkline,
            "last_updated": datetime.now().isoformat()
        }
    
    return {
        "data": data,
        "source": "binance_api" if real_prices else "mock_data",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting SMC Trading System Backend (Simplified)...")
    print("📡 Server will be available at: http://0.0.0.0:8000")
    print("📊 API Documentation: http://0.0.0.0:8000/docs")
    
    uvicorn.run(
        "main_simple:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )