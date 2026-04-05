#!/usr/bin/env python3
"""
Test script to verify API connections and data fetching
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append('backend')

from app.services.data_manager import DataManager
from app.config import get_settings

async def test_api_connections():
    """Test all configured API connections"""
    print("🔍 Testing API Connections...")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataManager()
    settings = get_settings()
    
    # Test symbols
    test_cases = [
        ("BTCUSDT", "1h", "crypto"),
        ("ETHUSDT", "1h", "crypto"),
        ("AAPL", "1d", "stocks"),
        ("EURUSD", "1h", "forex")
    ]
    
    # Date range (last 7 days)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    print(f"📅 Testing period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    print()
    
    # Check API key configuration
    print("🔑 API Key Status:")
    print(f"  Binance: {'✅ Configured' if settings.BINANCE_API_KEY else '❌ Missing'}")
    print(f"  Finnhub: {'✅ Configured' if settings.FINNHUB_API_KEY else '❌ Missing'}")
    print(f"  CoinMarketCap: {'✅ Configured' if settings.COINMARKETCAP_API_KEY else '❌ Missing'}")
    print()
    
    # Test each symbol
    for symbol, timeframe, asset_type in test_cases:
        print(f"📊 Testing {symbol} ({asset_type}) - {timeframe}")
        
        try:
            df = await data_manager.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start=start_time,
                end=end_time
            )
            
            if not df.empty:
                print(f"  ✅ Success: {len(df)} candles retrieved")
                print(f"  📈 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                print(f"  📅 Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                
                # Show data quality
                quality = data_manager.get_data_quality(symbol, timeframe)
                if quality:
                    print(f"  📊 Quality score: {quality.quality_score:.2f}")
                    if quality.issues_count > 0:
                        print(f"  ⚠️  Issues found: {quality.issues_count}")
            else:
                print(f"  ❌ No data retrieved")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
    
    # Show cache statistics
    cache_stats = data_manager.get_cache_stats()
    print("💾 Cache Statistics:")
    print(f"  Entries: {cache_stats.entries}")
    print(f"  Hit rate: {cache_stats.hit_rate:.1%}")
    print(f"  Memory usage: {cache_stats.memory_usage_mb:.1f} MB")
    print()
    
    print("✅ API connection test completed!")

async def test_specific_binance():
    """Test Binance API specifically"""
    print("🔍 Testing Binance API specifically...")
    
    try:
        import ccxt
        from app.config import get_settings
        
        settings = get_settings()
        
        if not settings.BINANCE_API_KEY or not settings.BINANCE_SECRET_KEY:
            print("❌ Binance API keys not configured")
            return
        
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_SECRET_KEY,
            'sandbox': settings.is_development,
            'enableRateLimit': True,
        })
        
        # Test connection
        print("📡 Testing Binance connection...")
        
        # Fetch server time (simple test)
        server_time = exchange.fetch_time()
        print(f"✅ Binance server time: {datetime.fromtimestamp(server_time/1000)}")
        
        # Fetch ticker
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT price: ${ticker['last']:.2f}")
        
        # Fetch recent candles
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=10)
        print(f"✅ Retrieved {len(ohlcv)} recent candles")
        
        print("🎉 Binance API is working correctly!")
        
    except Exception as e:
        print(f"❌ Binance API error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting API Connection Tests")
    print()
    
    # Test Binance specifically first
    asyncio.run(test_specific_binance())
    print()
    
    # Test full data manager
    asyncio.run(test_api_connections())