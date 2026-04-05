#!/usr/bin/env python3
"""
Test the chart functionality specifically
"""

import requests
import json
import time
from datetime import datetime

def test_chart_data_flow():
    """Test the complete chart data flow"""
    print("🧪 Testing Chart Data Flow")
    print("=" * 50)
    
    # 1. Test backend health
    print("1️⃣ Testing backend health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is healthy")
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend is not running: {e}")
        return False
    
    # 2. Test OHLCV endpoint
    print("\n2️⃣ Testing OHLCV endpoint...")
    try:
        url = "http://localhost:8000/api/data/ohlcv"
        params = {"symbol": "BTCUSDT", "timeframe": "15m"}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ OHLCV data received")
            print(f"   📊 Symbol: {data.get('symbol')}")
            print(f"   ⏰ Timeframe: {data.get('timeframe')}")
            print(f"   📈 Data points: {len(data.get('data', []))}")
            print(f"   🔗 Source: {data.get('source')}")
            
            # Validate data structure
            if data.get('data') and len(data['data']) > 0:
                first_candle = data['data'][0]
                required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                
                missing_fields = [field for field in required_fields if field not in first_candle]
                if missing_fields:
                    print(f"   ⚠️ Missing fields in data: {missing_fields}")
                else:
                    print("   ✅ Data structure is valid")
                    print(f"   📅 First candle: {first_candle['timestamp']}")
                    print(f"   💰 Price range: ${first_candle['low']:.2f} - ${first_candle['high']:.2f}")
            
            return True
        else:
            print(f"   ❌ OHLCV request failed: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ OHLCV request error: {e}")
        return False

def test_multiple_symbols():
    """Test multiple symbols to ensure API works for all"""
    print("\n3️⃣ Testing multiple symbols...")
    
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
    timeframes = ["15m", "1h", "4h"]
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                url = "http://localhost:8000/api/data/ohlcv"
                params = {"symbol": symbol, "timeframe": timeframe}
                
                response = requests.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    data_count = len(data.get('data', []))
                    print(f"   ✅ {symbol} {timeframe}: {data_count} candles")
                else:
                    print(f"   ❌ {symbol} {timeframe}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {symbol} {timeframe}: {e}")
            
            time.sleep(0.1)  # Small delay to avoid rate limiting

def test_data_conversion():
    """Test data conversion for TradingView format"""
    print("\n4️⃣ Testing data conversion...")
    
    try:
        url = "http://localhost:8000/api/data/ohlcv"
        params = {"symbol": "BTCUSDT", "timeframe": "15m"}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                # Simulate frontend conversion
                chart_data = []
                for candle in data['data']:
                    try:
                        converted = {
                            "time": int(datetime.fromisoformat(candle['timestamp']).timestamp()),
                            "open": float(candle['open']),
                            "high": float(candle['high']),
                            "low": float(candle['low']),
                            "close": float(candle['close']),
                            "volume": float(candle.get('volume', 0))
                        }
                        chart_data.append(converted)
                    except Exception as e:
                        print(f"   ❌ Conversion error for candle: {e}")
                        return False
                
                # Sort by time
                chart_data.sort(key=lambda x: x['time'])
                
                print(f"   ✅ Converted {len(chart_data)} candles successfully")
                print(f"   📅 Time range: {chart_data[0]['time']} - {chart_data[-1]['time']}")
                print(f"   💰 Price range: ${min(c['low'] for c in chart_data):.2f} - ${max(c['high'] for c in chart_data):.2f}")
                
                return True
            else:
                print("   ❌ No data to convert")
                return False
        else:
            print(f"   ❌ Failed to get data for conversion test")
            return False
            
    except Exception as e:
        print(f"   ❌ Data conversion test error: {e}")
        return False

def main():
    """Run all chart tests"""
    print("🎯 SMC Trading System - Chart Functionality Test")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    # Test basic data flow
    if not test_chart_data_flow():
        success = False
    
    # Test multiple symbols
    test_multiple_symbols()
    
    # Test data conversion
    if not test_data_conversion():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All chart tests passed!")
        print("💡 The chart should work properly in the frontend")
    else:
        print("❌ Some chart tests failed")
        print("🔧 Please check the backend and fix any issues")
    
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()