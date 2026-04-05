#!/usr/bin/env python3
"""
Test script to verify the chart API is working
"""

import requests
import json
from datetime import datetime

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend is not running: {e}")
        return False

def test_ohlcv_api():
    """Test OHLCV API endpoint"""
    try:
        url = "http://localhost:8000/api/data/ohlcv"
        params = {
            "symbol": "BTCUSDT",
            "timeframe": "15m"
        }
        
        print(f"🔍 Testing OHLCV API: {url}")
        print(f"   Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ OHLCV API is working")
            print(f"   Symbol: {data.get('symbol')}")
            print(f"   Timeframe: {data.get('timeframe')}")
            print(f"   Data points: {len(data.get('data', []))}")
            print(f"   Source: {data.get('source')}")
            
            # Show first data point
            if data.get('data'):
                first_candle = data['data'][0]
                print(f"   First candle: {first_candle}")
            
            return True
        else:
            print(f"❌ OHLCV API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OHLCV API error: {e}")
        return False

def test_watchlist_api():
    """Test watchlist prices API"""
    try:
        url = "http://localhost:8000/api/watchlist/prices"
        
        print(f"🔍 Testing Watchlist API: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Watchlist API is working")
            print(f"   Source: {data.get('source')}")
            print(f"   Symbols: {list(data.get('data', {}).keys())}")
            
            # Show BTCUSDT price
            btc_data = data.get('data', {}).get('BTCUSDT')
            if btc_data:
                print(f"   BTCUSDT: ${btc_data.get('price'):.2f} ({btc_data.get('change_24h'):+.2f}%)")
            
            return True
        else:
            print(f"❌ Watchlist API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Watchlist API error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing SMC Trading System APIs")
    print("=" * 50)
    
    # Test backend health
    if not test_backend_health():
        print("\n❌ Backend is not running. Please start it first:")
        print("   cd backend && python main_simple.py")
        return
    
    print()
    
    # Test OHLCV API
    test_ohlcv_api()
    
    print()
    
    # Test watchlist API
    test_watchlist_api()
    
    print("\n" + "=" * 50)
    print("🏁 API testing completed")

if __name__ == "__main__":
    main()