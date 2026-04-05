#!/usr/bin/env python3
"""
Multi-Timeframe Confluence Engine - Usage Example
This demonstrates how to use the MTF Confluence Engine
"""

# Example API Usage (when backend is running)
"""
import requests
import json

# 1. Complete MTF Analysis
mtf_request = {
    "symbol": "BTCUSDT",
    "entry_tf": "5m",
    "htf": "4h", 
    "mtf": "1h"
}

response = requests.post(
    "http://localhost:8000/api/mtf/mtf-analyze",
    json=mtf_request
)

result = response.json()
print(f"Confluence Score: {result['confluence_score']}/100")
print(f"Signal Valid: {result['signal_valid']}")
if result['entry']:
    print(f"Entry: {result['entry']}")
    print(f"Stop Loss: {result['sl']}")
    print(f"Take Profit: {result['tp']}")

# 2. Get Available Timeframes
timeframes = requests.get("http://localhost:8000/api/mtf/mtf-timeframes")
print("Available timeframes:", timeframes.json())

# 3. Quick Status Check
status = requests.get("http://localhost:8000/api/mtf/mtf-status/BTCUSDT?htf=4h")
print("MTF Status:", status.json())
"""

# Example Direct Usage (with dependencies installed)
"""
import asyncio
from backend.app.strategies.mtf_confluence import ConfluenceEngine

async def analyze_symbol():
    engine = ConfluenceEngine()
    
    # Complete MTF analysis
    result = await engine.analyze_mtf_confluence(
        symbol="BTCUSDT",
        entry_tf="5m",
        htf="4h",
        mtf="1h"
    )
    
    print(f"Confluence Score: {result.confluence_score}/100")
    print(f"Bias: {result.bias}")
    print(f"Entry: {result.entry}")
    print("Reasons:", result.reasons)
    
    return result

# Run analysis
# asyncio.run(analyze_symbol())
"""

print("📋 Multi-Timeframe Confluence Engine Usage Examples")
print("=" * 60)
print("✅ Module 1 Implementation Complete!")
print()
print("🔧 To use the MTF Confluence Engine:")
print("1. Install dependencies: pip install -r backend/requirements.txt")
print("2. Start backend: python backend/run.py")
print("3. Use API endpoints or import classes directly")
print()
print("🎯 Key Features:")
print("• Multi-timeframe analysis (HTF → MTF → LTF)")
print("• Confluence scoring (0-100 points)")
print("• Signal validation with bias alignment")
print("• Risk management (SL/TP calculation)")
print("• RESTful API endpoints")
print()
print("🚀 Ready for Module 2!")