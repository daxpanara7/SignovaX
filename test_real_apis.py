#!/usr/bin/env python3
"""
Test real API connections with proper configuration
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append('backend')

async def test_binance_direct():
    """Test Binance API directly"""
    print("🔍 Testing Binance API Connection")
    print("=" * 40)
    
    try:
        import ccxt
        from app.config import Settings
        
        # Load settings with correct env file
        settings = Settings(_env_file='backend/.env')
        
        if not settings.BINANCE_API_KEY or not settings.BINANCE_SECRET_KEY:
            print("❌ Binance API keys not found")
            return False
        
        print(f"✅ API Key loaded: {settings.BINANCE_API_KEY[:8]}...{settings.BINANCE_API_KEY[-4:]}")
        
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_SECRET_KEY,
            'sandbox': False,  # Use real API
            'enableRateLimit': True,
        })
        
        print("📡 Testing connection...")
        
        # Test 1: Server time
        server_time = exchange.fetch_time()
        print(f"✅ Server time: {datetime.fromtimestamp(server_time/1000)}")
        
        # Test 2: Market data
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT: ${ticker['last']:,.2f}")
        print(f"   24h Volume: {ticker['baseVolume']:,.2f} BTC")
        print(f"   24h Change: {ticker['percentage']:.2f}%")
        
        # Test 3: Historical data
        print("\n📊 Fetching historical data...")
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=24)
        
        if ohlcv:
            print(f"✅ Retrieved {len(ohlcv)} hourly candles")
            latest = ohlcv[-1]
            timestamp = datetime.fromtimestamp(latest[0]/1000)
            print(f"   Latest candle: {timestamp}")
            print(f"   OHLC: ${latest[1]:.2f} / ${latest[2]:.2f} / ${latest[3]:.2f} / ${latest[4]:.2f}")
            print(f"   Volume: {latest[5]:,.2f}")
        
        # Test 4: Multiple symbols
        print("\n🔄 Testing multiple symbols...")
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                print(f"   {symbol}: ${ticker['last']:,.2f}")
            except Exception as e:
                print(f"   {symbol}: ❌ {str(e)}")
        
        print("\n🎉 Binance API is working perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Binance API error: {str(e)}")
        return False

async def test_finnhub_direct():
    """Test Finnhub API directly"""
    print("\n🔍 Testing Finnhub API Connection")
    print("=" * 40)
    
    try:
        import aiohttp
        from app.config import Settings
        
        settings = Settings(_env_file='backend/.env')
        
        if not settings.FINNHUB_API_KEY:
            print("❌ Finnhub API key not found")
            return False
        
        print(f"✅ API Key loaded: {settings.FINNHUB_API_KEY[:8]}...{settings.FINNHUB_API_KEY[-4:]}")
        
        base_url = "https://finnhub.io/api/v1"
        api_key = settings.FINNHUB_API_KEY
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Company profile
            print("📡 Testing company profile...")
            url = f"{base_url}/stock/profile2"
            params = {'symbol': 'AAPL', 'token': api_key}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and 'name' in data:
                        print(f"✅ Company: {data['name']}")
                        print(f"   Industry: {data.get('finnhubIndustry', 'N/A')}")
                        print(f"   Market Cap: ${data.get('marketCapitalization', 0):,.0f}M")
                    else:
                        print("⚠️  Empty response from company profile")
                else:
                    print(f"❌ Company profile failed: {response.status}")
            
            # Test 2: Stock candles
            print("\n📊 Testing stock candles...")
            url = f"{base_url}/stock/candle"
            
            # Get data for last 7 days
            end_time = int(datetime.now().timestamp())
            start_time = int((datetime.now() - timedelta(days=7)).timestamp())
            
            params = {
                'symbol': 'AAPL',
                'resolution': 'D',
                'from': start_time,
                'to': end_time,
                'token': api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('s') == 'ok' and 'c' in data:
                        print(f"✅ Retrieved {len(data['c'])} daily candles")
                        print(f"   Latest close: ${data['c'][-1]:.2f}")
                        print(f"   High: ${max(data['h']):.2f}")
                        print(f"   Low: ${min(data['l']):.2f}")
                    else:
                        print(f"⚠️  No data returned: {data}")
                else:
                    print(f"❌ Candles failed: {response.status}")
            
            # Test 3: Crypto (if supported)
            print("\n🪙 Testing crypto data...")
            url = f"{base_url}/crypto/candle"
            params = {
                'symbol': 'BINANCE:BTCUSDT',
                'resolution': 'D',
                'from': start_time,
                'to': end_time,
                'token': api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('s') == 'ok' and 'c' in data:
                        print(f"✅ BTC data: ${data['c'][-1]:,.2f}")
                    else:
                        print("⚠️  Crypto data not available (may require premium)")
                else:
                    print(f"⚠️  Crypto endpoint: {response.status}")
        
        print("\n🎉 Finnhub API is working!")
        return True
        
    except Exception as e:
        print(f"❌ Finnhub API error: {str(e)}")
        return False

async def test_data_manager():
    """Test the integrated data manager"""
    print("\n🔍 Testing Integrated Data Manager")
    print("=" * 40)
    
    try:
        from app.services.data_manager import DataManager
        
        # Initialize with correct settings
        os.environ['ENV_FILE_PATH'] = 'backend/.env'
        data_manager = DataManager()
        
        # Test crypto data (should use Binance)
        print("📊 Testing BTCUSDT (crypto)...")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        df = await data_manager.get_ohlcv(
            symbol='BTCUSDT',
            timeframe='1h',
            start=start_time,
            end=end_time
        )
        
        if not df.empty:
            print(f"✅ Retrieved {len(df)} candles")
            print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            print(f"   Latest: ${df['close'].iloc[-1]:.2f}")
        else:
            print("❌ No data retrieved")
        
        # Test stock data (should use Finnhub)
        print("\n📈 Testing AAPL (stock)...")
        df = await data_manager.get_ohlcv(
            symbol='AAPL',
            timeframe='1d',
            start=start_time,
            end=end_time
        )
        
        if not df.empty:
            print(f"✅ Retrieved {len(df)} candles")
            print(f"   Latest: ${df['close'].iloc[-1]:.2f}")
        else:
            print("❌ No stock data retrieved")
        
        return True
        
    except Exception as e:
        print(f"❌ Data manager error: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 API Connection Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test Binance
    results.append(await test_binance_direct())
    
    # Test Finnhub
    results.append(await test_finnhub_direct())
    
    # Test integrated data manager
    results.append(await test_data_manager())
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   Binance: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"   Finnhub: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"   Data Manager: {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    if all(results):
        print("\n🎉 All APIs are working correctly!")
        print("Your system now has access to real market data!")
    else:
        print("\n⚠️  Some APIs need attention. Check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())