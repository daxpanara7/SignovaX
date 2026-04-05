#!/usr/bin/env python3
"""
Test WebSocket Price Data
Check what prices are actually being broadcast
"""

import asyncio
import websockets
import json

async def listen_to_prices():
    """Listen to WebSocket and show actual price data"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket")
            print("📡 Listening for price updates...\n")
            
            message_count = 0
            while message_count < 3:  # Listen for 3 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    data = json.loads(message)
                    
                    print(f"📨 Message {message_count + 1}: {data.get('type', 'Unknown')}")
                    
                    if data.get('type') == 'price_update':
                        price_data = data.get('data', {})
                        print(f"   Source: {data.get('source', 'Unknown')}")
                        print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
                        
                        if price_data:
                            for symbol, info in price_data.items():
                                price = info.get('price', 'Unknown')
                                change = info.get('change', 0)
                                volume = info.get('volume', 'Unknown')
                                print(f"   💰 {symbol}: ${price} ({change:+.2f}%) Vol: {volume}")
                        else:
                            print("   ⚠️ No price data in message")
                    
                    print()
                    message_count += 1
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                    
    except Exception as e:
        print(f"❌ WebSocket Error: {e}")

if __name__ == "__main__":
    asyncio.run(listen_to_prices())