#!/usr/bin/env python3
"""
Test script to verify the simplified backend works correctly
"""

import requests
import json
import time

def test_backend():
    """Test the simplified backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing SMC Trading System Backend...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: PASSED")
        else:
            print(f"❌ Health check: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health check: FAILED - {e}")
        return False
    
    # Test 2: Root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: PASSED - {data.get('message', 'No message')}")
        else:
            print(f"❌ Root endpoint: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Root endpoint: FAILED - {e}")
    
    # Test 3: Watchlist prices (real crypto data)
    try:
        response = requests.get(f"{base_url}/api/watchlist/prices", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print("✅ Watchlist prices: PASSED")
                # Show sample data
                for symbol, price_data in list(data['data'].items())[:3]:
                    print(f"   📊 {symbol}: ${price_data['price']:.4f} ({price_data['change_24h']:+.2f}%)")
            else:
                print("⚠️ Watchlist prices: No data returned")
        else:
            print(f"❌ Watchlist prices: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Watchlist prices: FAILED - {e}")
    
    # Test 4: OHLCV data (chart data)
    try:
        response = requests.get(f"{base_url}/api/data/ohlcv?symbol=BTCUSDT&timeframe=15m", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print("✅ OHLCV data: PASSED")
                print(f"   📈 {data['symbol']} {data['timeframe']}: {len(data['data'])} candles")
                print(f"   🔗 Source: {data.get('source', 'unknown')}")
            else:
                print("⚠️ OHLCV data: No data returned")
        else:
            print(f"❌ OHLCV data: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ OHLCV data: FAILED - {e}")
    
    # Test 5: Current signal
    try:
        response = requests.get(f"{base_url}/api/signals/current", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Current signal: PASSED")
            print(f"   🎯 {data.get('symbol', 'N/A')} {data.get('direction', 'N/A')} - Confidence: {data.get('confluence_score', 0)}%")
        else:
            print(f"❌ Current signal: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Current signal: FAILED - {e}")
    
    # Test 6: Performance metrics
    try:
        response = requests.get(f"{base_url}/api/performance/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Performance metrics: PASSED")
            print(f"   📊 Win Rate: {data.get('win_rate', 0)}% | Return: {data.get('total_return_percent', 0)}%")
        else:
            print(f"❌ Performance metrics: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Performance metrics: FAILED - {e}")
    
    print("=" * 50)
    print("🎉 Backend test completed!")
    print("\n💡 If all tests passed, your backend is working correctly!")
    print("💡 You can now start the frontend with: cd frontend && npm run dev")
    
    return True

if __name__ == "__main__":
    print("⏳ Waiting 2 seconds for backend to be ready...")
    time.sleep(2)
    test_backend()