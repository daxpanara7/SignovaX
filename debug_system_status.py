#!/usr/bin/env python3
"""
Debug System Status
Comprehensive test to check backend, authentication, and data flow
"""

import requests
import json
import time
import asyncio
import websockets

def test_backend_health():
    """Test backend health and basic endpoints"""
    print("🔍 Testing Backend Health...")
    
    try:
        # Health check
        health = requests.get('http://localhost:8000/health', timeout=5)
        print(f"Health endpoint: {health.status_code}")
        if health.status_code == 200:
            print(f"Health data: {health.json()}")
        
        # Test authentication
        login_data = {"username": "admin", "password": "smc_admin_2024"}
        login = requests.post('http://localhost:8000/api/auth/login', json=login_data, timeout=5)
        print(f"Login endpoint: {login.status_code}")
        
        if login.status_code == 200:
            token_data = login.json()
            token = token_data.get('access_token')
            print(f"✅ Login successful, token: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test data endpoint
            data_response = requests.get('http://localhost:8000/api/data/ohlcv?symbol=BTCUSDT&timeframe=15m&limit=10', headers=headers, timeout=10)
            print(f"Data endpoint: {data_response.status_code}")
            if data_response.status_code == 200:
                data = data_response.json()
                print(f"✅ Got {len(data)} candles")
                if data:
                    latest = data[-1]
                    print(f"Latest BTC price: ${latest.get('close', 'N/A')}")
            else:
                print(f"❌ Data error: {data_response.text}")
            
            # Test signals endpoint (no auth required)
            signals = requests.get('http://localhost:8000/api/signals/current?limit=5', timeout=5)
            print(f"Signals endpoint: {signals.status_code}")
            
            # Test sessions endpoint (auth required)
            sessions = requests.get('http://localhost:8000/api/sessions/data', headers=headers, timeout=5)
            print(f"Sessions endpoint: {sessions.status_code}")
            
            return True
        else:
            print(f"❌ Login failed: {login.text}")
            return False
            
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

async def test_websocket():
    """Test WebSocket connection"""
    print("\n🔌 Testing WebSocket...")
    
    try:
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Wait for initial messages
            try:
                for i in range(3):  # Wait for up to 3 messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 Message {i+1}: {data.get('type', 'unknown')} - {data.get('message', '')[:50]}...")
                    
                    if data.get('type') == 'price_update':
                        print(f"💰 Price update received: {list(data.get('data', {}).keys())}")
                        
            except asyncio.TimeoutError:
                print("⏰ No more messages received (timeout)")
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔥 System Status Debug")
    print("=" * 40)
    
    # Test backend
    backend_ok = test_backend_health()
    
    # Test WebSocket
    if backend_ok:
        websocket_ok = asyncio.run(test_websocket())
    else:
        print("⏭️ Skipping WebSocket test (backend not ready)")
        websocket_ok = False
    
    print("\n📊 Summary:")
    print(f"Backend: {'✅ OK' if backend_ok else '❌ FAILED'}")
    print(f"WebSocket: {'✅ OK' if websocket_ok else '❌ FAILED'}")
    
    if backend_ok and websocket_ok:
        print("\n🎉 System should be working in LIVE MODE")
        print("💡 If you still see demo mode, check browser console for errors")
    else:
        print("\n⚠️ System has issues - will show DEMO MODE")
        print("💡 Make sure backend is running: python start_system_main.py")

if __name__ == "__main__":
    main()