#!/usr/bin/env python3
"""
Complete system test to verify everything is working
"""

import requests
import time
import json
from datetime import datetime

def test_backend():
    """Test backend health and API"""
    print("🔧 Testing Backend...")
    
    try:
        # Health check
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("   ❌ Backend health check failed")
            return False
        print("   ✅ Backend is healthy")
        
        # OHLCV API
        response = requests.get("http://localhost:8000/api/data/ohlcv?symbol=BTCUSDT&timeframe=15m", timeout=10)
        if response.status_code != 200:
            print("   ❌ OHLCV API failed")
            return False
        
        data = response.json()
        if not data.get('data') or len(data['data']) == 0:
            print("   ❌ No OHLCV data returned")
            return False
        
        print(f"   ✅ OHLCV API working ({len(data['data'])} candles)")
        
        # Watchlist API
        response = requests.get("http://localhost:8000/api/watchlist/prices", timeout=10)
        if response.status_code != 200:
            print("   ❌ Watchlist API failed")
            return False
        
        data = response.json()
        if not data.get('data'):
            print("   ❌ No watchlist data returned")
            return False
        
        print(f"   ✅ Watchlist API working ({len(data['data'])} symbols)")
        return True
        
    except Exception as e:
        print(f"   ❌ Backend test error: {e}")
        return False

def test_frontend():
    """Test frontend accessibility"""
    print("🎨 Testing Frontend...")
    
    try:
        # Frontend health
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code != 200:
            print("   ❌ Frontend not accessible")
            return False
        
        if "SMC Trading System" not in response.text:
            print("   ❌ Frontend content incorrect")
            return False
        
        print("   ✅ Frontend is accessible")
        
        # API proxy test
        response = requests.get("http://localhost:3000/api/data/ohlcv?symbol=BTCUSDT&timeframe=15m", timeout=10)
        if response.status_code != 200:
            print("   ❌ API proxy not working")
            return False
        
        data = response.json()
        if not data.get('data') or len(data['data']) == 0:
            print("   ❌ No data through proxy")
            return False
        
        print(f"   ✅ API proxy working ({len(data['data'])} candles)")
        return True
        
    except Exception as e:
        print(f"   ❌ Frontend test error: {e}")
        return False

def test_chart_data_format():
    """Test chart data format compatibility"""
    print("📊 Testing Chart Data Format...")
    
    try:
        response = requests.get("http://localhost:3000/api/data/ohlcv?symbol=BTCUSDT&timeframe=15m", timeout=10)
        if response.status_code != 200:
            print("   ❌ Failed to get data")
            return False
        
        data = response.json()
        candles = data.get('data', [])
        
        if not candles:
            print("   ❌ No candles data")
            return False
        
        # Test first candle format
        first_candle = candles[0]
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        for field in required_fields:
            if field not in first_candle:
                print(f"   ❌ Missing field: {field}")
                return False
        
        # Test data conversion (simulate frontend)
        try:
            converted_candle = {
                "time": int(datetime.fromisoformat(first_candle['timestamp']).timestamp()),
                "open": float(first_candle['open']),
                "high": float(first_candle['high']),
                "low": float(first_candle['low']),
                "close": float(first_candle['close']),
                "volume": float(first_candle.get('volume', 0))
            }
            
            # Validate converted data
            if converted_candle['high'] < converted_candle['low']:
                print("   ❌ Invalid OHLC data (high < low)")
                return False
            
            if converted_candle['open'] < 0 or converted_candle['close'] < 0:
                print("   ❌ Invalid price data (negative prices)")
                return False
            
            print("   ✅ Chart data format is valid")
            print(f"   📅 Sample: {first_candle['timestamp']}")
            print(f"   💰 OHLC: {converted_candle['open']:.2f} / {converted_candle['high']:.2f} / {converted_candle['low']:.2f} / {converted_candle['close']:.2f}")
            return True
            
        except Exception as e:
            print(f"   ❌ Data conversion failed: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Chart data test error: {e}")
        return False

def test_multiple_symbols():
    """Test multiple symbols and timeframes"""
    print("🔄 Testing Multiple Symbols/Timeframes...")
    
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    timeframes = ["15m", "1h", "4h"]
    
    success_count = 0
    total_tests = len(symbols) * len(timeframes)
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                response = requests.get(
                    f"http://localhost:3000/api/data/ohlcv?symbol={symbol}&timeframe={timeframe}", 
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        success_count += 1
                        print(f"   ✅ {symbol} {timeframe}: {len(data['data'])} candles")
                    else:
                        print(f"   ⚠️ {symbol} {timeframe}: No data")
                else:
                    print(f"   ❌ {symbol} {timeframe}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {symbol} {timeframe}: {e}")
            
            time.sleep(0.1)  # Small delay
    
    success_rate = (success_count / total_tests) * 100
    print(f"   📊 Success rate: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    return success_rate >= 80  # 80% success rate is acceptable

def main():
    """Run complete system test"""
    print("🎯 SMC Trading System - Complete System Test")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Backend", test_backend),
        ("Frontend", test_frontend),
        ("Chart Data Format", test_chart_data_format),
        ("Multiple Symbols", test_multiple_symbols)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print("=" * 60)
    print("📋 Test Results Summary")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The system should work correctly.")
        print("🌐 Open http://localhost:3000 to see the trading dashboard")
        print("📊 Charts should load with real-time data from Binance")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()