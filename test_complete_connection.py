#!/usr/bin/env python3
"""
Complete Connection Test
Tests backend health, authentication, data, and WebSocket
"""

import asyncio
import aiohttp
import websockets
import json
import sys

BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def test_health():
    """Test backend health endpoint"""
    print("🏥 Testing backend health...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Backend healthy: {data['status']}")
                    print(f"   Environment: {data['environment']}")
                    print(f"   WebSocket connections: {data.get('websocket_connections', 0)}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def test_auth():
    """Test authentication"""
    print("🔑 Testing authentication...")
    
    try:
        async with aiohttp.ClientSession() as session:
            login_data = {
                "username": "admin",
                "password": "smc_admin_2024"
            }
            
            async with session.post(f"{BACKEND_URL}/api/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'access_token' in data:
                        print("✅ Authentication successful")
                        return data['access_token']
                    else:
                        print("❌ No access token in response")
                        return None
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

async def test_data(token):
    """Test data endpoint"""
    print("📊 Testing data endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        async with aiohttp.ClientSession() as session:
            params = {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "limit": 5
            }
            
            async with session.get(f"{BACKEND_URL}/api/data/ohlcv", params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        latest = data[-1]
                        print(f"✅ Data retrieved: {len(data)} candles")
                        print(f"   Latest BTC price: ${latest['close']}")
                        print(f"   Timestamp: {latest['timestamp']}")
                        return True
                    else:
                        print("❌ No data returned")
                        return False
                else:
                    print(f"❌ Data request failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Data error: {e}")
        return False

async def test_websocket():
    """Test WebSocket connection"""
    print("🔌 Testing WebSocket connection...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket connected")
            
            # Wait for initial messages
            messages_received = 0
            
            try:
                for i in range(3):  # Wait for 3 messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=8.0)
                    data = json.loads(message)
                    messages_received += 1
                    
                    print(f"📨 Message {messages_received}: {data['type']}")
                    
                    if data['type'] == 'price_update' and 'data' in data:
                        for symbol, info in data['data'].items():
                            print(f"   💰 {symbol}: ${info['price']}")
                
                print(f"✅ WebSocket working: {messages_received} messages received")
                return True
                
            except asyncio.TimeoutError:
                print(f"⚠️ WebSocket timeout (received {messages_received} messages)")
                return messages_received > 0
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Complete SMC Trading System Connection Test")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Health
    results['health'] = await test_health()
    
    # Test 2: Authentication
    token = await test_auth()
    results['auth'] = token is not None
    
    # Test 3: Data (if auth worked)
    if token:
        results['data'] = await test_data(token)
    else:
        results['data'] = False
        print("⏭️ Skipping data test (no auth token)")
    
    # Test 4: WebSocket
    results['websocket'] = await test_websocket()
    
    # Summary
    print("\n📋 Test Results Summary:")
    print("=" * 30)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.capitalize():12} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("💡 Frontend should now work in LIVE MODE")
        print("🚀 Start frontend with: cd frontend && npm start")
    else:
        print("\n❌ Some tests failed")
        print("💡 Check backend is running: python start_system_main.py")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)