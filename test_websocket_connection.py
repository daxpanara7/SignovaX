#!/usr/bin/env python3
"""
Test WebSocket Connection
Quick test to verify WebSocket functionality
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test WebSocket connection to backend"""
    uri = "ws://localhost:8000/ws"
    
    try:
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Listen for messages for 10 seconds
            print("📡 Listening for messages...")
            
            try:
                for i in range(5):  # Listen for 5 messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 Message {i+1}: {data['type']} - {data.get('message', 'No message')}")
                    
                    if data['type'] == 'price_update' and 'data' in data:
                        for symbol, info in data['data'].items():
                            print(f"   💰 {symbol}: ${info['price']} ({info['change']:+.2f}%)")
                
                print("✅ WebSocket test completed successfully!")
                return True
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for messages")
                return False
                
    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend running?")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 WebSocket Connection Test")
    print("=" * 40)
    
    success = await test_websocket()
    
    if success:
        print("\n🎉 WebSocket is working correctly!")
        print("💡 Frontend should now connect and exit demo mode")
    else:
        print("\n❌ WebSocket test failed")
        print("💡 Make sure backend is running: python start_system_main.py")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)