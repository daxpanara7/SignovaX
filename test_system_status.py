#!/usr/bin/env python3
"""
Test System Status
Quick verification that everything is working
"""

import requests
import json
import asyncio
import websockets

def test_backend_health():
    """Test backend health"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data['status']}")
            print(f"   WebSocket Connections: {data.get('websocket_connections', 0)}")
            return True
        else:
            print(f"❌ Backend Health Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Health Error: {e}")
        return False

def test_signals_endpoint():
    """Test signals endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/signals/current?limit=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                signal = data[0]
                print(f"✅ Signals Working: {signal.get('symbol', 'Unknown')} {signal.get('signal_type', 'Unknown')}")
                print(f"   Price: ${signal.get('entry_price', 'Unknown')}")
                return True
            else:
                print("⚠️ Signals endpoint working but no signals returned")
                return True
        else:
            print(f"❌ Signals Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Signals Error: {e}")
        return False

async def test_websocket():
    """Test WebSocket connection"""
    try:
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket Connected")
            
            # Wait for a message
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            print(f"✅ WebSocket Message: {data.get('type', 'Unknown')}")
            
            if data.get('type') == 'price_update':
                price_data = data.get('data', {})
                if price_data:
                    for symbol, info in price_data.items():
                        print(f"   💰 {symbol}: ${info.get('price', 'Unknown')}")
            
            return True
            
    except asyncio.TimeoutError:
        print("⚠️ WebSocket timeout (no messages received)")
        return False
    except Exception as e:
        print(f"❌ WebSocket Error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 SMC Trading System - Status Check")
    print("=" * 40)
    
    results = {}
    
    # Test backend health
    results['health'] = test_backend_health()
    
    # Test signals
    results['signals'] = test_signals_endpoint()
    
    # Test WebSocket
    results['websocket'] = asyncio.run(test_websocket())
    
    print("\n📋 System Status Summary:")
    print("=" * 30)
    
    for test, passed in results.items():
        status = "✅ WORKING" if passed else "❌ FAILED"
        print(f"{test.capitalize():12} {status}")
    
    all_working = all(results.values())
    
    if all_working:
        print("\n🎉 All systems operational!")
        print("💡 Frontend should be working at http://localhost:3000")
    else:
        print("\n⚠️ Some issues detected")
    
    return all_working

if __name__ == "__main__":
    main()