#!/usr/bin/env python3
"""
Precise SMC Logic Definitions - Usage Examples
This demonstrates how to use the Precise SMC Engine
"""

# Example API Usage (when backend is running)
"""
import requests
import json

# 1. Complete Precise SMC Analysis
smc_request = {
    "symbol": "BTCUSDT",
    "timeframe": "1h"
}

response = requests.post("http://localhost:8000/api/smc/analyze", json=smc_request)
analysis = response.json()

print(f"Symbol: {analysis['symbol']}")
print(f"Current Trend: {analysis['current_trend']}")
print(f"Order Blocks: {len(analysis['order_blocks'])}")
print(f"Fair Value Gaps: {len(analysis['fair_value_gaps'])}")
print(f"Liquidity Zones: {len(analysis['liquidity_zones'])}")
print(f"Structure Events: {len(analysis['structure_events'])}")
print(f"High Confidence Patterns: {analysis['high_confidence_patterns']}")

# 2. Get Pattern Summary
response = requests.get("http://localhost:8000/api/smc/summary/BTCUSDT?timeframe=1h")
summary = response.json()
print(f"Active Order Blocks: {summary['active_order_blocks']}")
print(f"Active FVGs: {summary['active_fvgs']}")
print(f"Unswept Liquidity: {summary['unswept_liquidity_zones']}")

# 3. Get Order Blocks (Active Only)
response = requests.get("http://localhost:8000/api/smc/order-blocks/BTCUSDT?timeframe=1h&active_only=true")
order_blocks = response.json()
for ob in order_blocks['order_blocks']:
    print(f"OB: {ob['ob_type']} at {ob['top']}-{ob['bottom']}, Confidence: {ob['confidence']}")
    print(f"    Mitigated: {ob['mitigated']}, ATR Multiple: {ob['atr_multiple']:.2f}")

# 4. Get Fair Value Gaps (Unfilled Only)
response = requests.get("http://localhost:8000/api/smc/fair-value-gaps/BTCUSDT?timeframe=1h&unfilled_only=true")
fvgs = response.json()
for fvg in fvgs['fair_value_gaps']:
    print(f"FVG: {fvg['fvg_type']} at {fvg['top']}-{fvg['bottom']}")
    print(f"     Fill %: {fvg['fill_percentage']:.1f}%, Gap Size: {fvg['gap_size']}")

# 5. Get Liquidity Zones (Unswept Only)
response = requests.get("http://localhost:8000/api/smc/liquidity-zones/BTCUSDT?timeframe=1h&unswept_only=true")
liquidity = response.json()
for lz in liquidity['liquidity_zones']:
    print(f"Liquidity: {lz['zone_type']} at {lz['price']}")
    print(f"          Levels: {lz['level_count']}, Swept: {lz['swept']}")

# 6. Get Structure Events (BOS Only)
response = requests.get("http://localhost:8000/api/smc/structure-events/BTCUSDT?timeframe=1h&event_type=BOS")
structure = response.json()
for se in structure['structure_events']:
    print(f"Structure: {se['structure_type']} at {se['break_price']}")
    print(f"          Signal: {se['signal_type']}, Position Size: {se['position_size_multiplier']}x")

# 7. Get SMC Configuration
response = requests.get("http://localhost:8000/api/smc/config")
config = response.json()
print("SMC Configuration:", json.dumps(config['config'], indent=2))
"""

# Example Direct Usage (with dependencies installed)
"""
import asyncio
import pandas as pd
from backend.app.strategies.smc_engine import PreciseSMCEngine
from backend.app.models.smc_models import SMCDetectionConfig

async def analyze_precise_smc():
    # Custom configuration
    config = SMCDetectionConfig(
        min_displacement_atr_multiple=1.5,  # Order Block displacement
        min_fvg_atr_multiple=0.3,          # FVG minimum size
        liquidity_price_tolerance=0.001,    # 0.1% tolerance for equal levels
        min_candles_between_levels=5        # Minimum distance between levels
    )
    
    # Initialize engine
    engine = PreciseSMCEngine(config)
    
    # Create or load your OHLCV DataFrame
    # df = your_data_loading_function()
    
    # Perform complete analysis
    analysis = engine.analyze(df, "BTCUSDT", "1h")
    
    print(f"Analysis Results for {analysis.symbol} {analysis.timeframe}:")
    print(f"Current Trend: {analysis.current_trend}")
    print(f"ATR(14): {analysis.atr_14:.2f}")
    
    # Order Blocks
    active_obs = [ob for ob in analysis.order_blocks if not ob.mitigated]
    print(f"Active Order Blocks: {len(active_obs)}")
    for ob in active_obs:
        print(f"  {ob.ob_type.value} OB: {ob.bottom:.2f}-{ob.top:.2f}")
        print(f"    Confidence: {ob.confidence.value}, ATR Multiple: {ob.atr_multiple:.2f}")
    
    # Fair Value Gaps
    active_fvgs = [fvg for fvg in analysis.fair_value_gaps if not fvg.filled]
    print(f"Active Fair Value Gaps: {len(active_fvgs)}")
    for fvg in active_fvgs:
        print(f"  {fvg.fvg_type.value} FVG: {fvg.bottom:.2f}-{fvg.top:.2f}")
        print(f"    Fill: {fvg.fill_percentage:.1f}%, Size: {fvg.gap_size:.2f}")
    
    # Liquidity Zones
    unswept_lz = [lz for lz in analysis.liquidity_zones if not lz.swept]
    print(f"Unswept Liquidity Zones: {len(unswept_lz)}")
    for lz in unswept_lz:
        print(f"  {lz.zone_type.value} at {lz.price:.2f}")
        print(f"    Levels: {lz.level_count}, Confidence: {lz.confidence.value}")
    
    # Structure Events
    recent_structure = analysis.structure_events[-5:]  # Last 5 events
    print(f"Recent Structure Events: {len(recent_structure)}")
    for se in recent_structure:
        print(f"  {se.structure_type.value}: {se.break_price:.2f}")
        print(f"    Signal: {se.signal_type.value}, Position: {se.position_size_multiplier}x")
    
    return analysis

# Run the analysis
# asyncio.run(analyze_precise_smc())
"""

print("📋 Precise SMC Logic Definitions Usage Examples")
print("=" * 60)
print("✅ Module 3 Implementation Complete!")
print()
print("🔧 To use the Precise SMC Engine:")
print("1. Install dependencies: pip install -r backend/requirements.txt")
print("2. Start backend: python backend/run.py")
print("3. Use API endpoints or import classes directly")
print()
print("🎯 Mathematical Precision Features:")
print()
print("📦 Order Blocks:")
print("• Last RED candle before strong bullish impulse")
print("• Last GREEN candle before strong bearish impulse")
print("• Strong impulse: closes beyond last 3 candles' high/low")
print("• Displacement required: impulse body > 1.5x ATR(14)")
print("• Mitigation: price closes inside OB zone")
print()
print("📊 Fair Value Gaps:")
print("• Bullish FVG: candle[i+1].low > candle[i-1].high")
print("• Bearish FVG: candle[i+1].high < candle[i-1].low")
print("• Minimum size filter: gap_size > 0.3 * ATR(14)")
print("• Partial and complete fill tracking")
print()
print("💧 Liquidity Zones:")
print("• Equal highs/lows within 0.1% price tolerance")
print("• Minimum 5 candles between equal levels")
print("• Swept when price closes beyond the level")
print("• Swept liquidity = potential reversal zone")
print()
print("🏗️ Structure Events (BOS vs CHOCH):")
print("• BOS: Continuation signals, 100% position size")
print("  - Uptrend: break above previous HH")
print("  - Downtrend: break below previous LL")
print("• CHOCH: Reversal signals, 50% position size")
print("  - Uptrend: break below recent HL")
print("  - Downtrend: break above recent LH")
print()
print("📈 Enhanced Tracking:")
print("• Timestamps for all detections")
print("• Confidence levels (high/medium/low)")
print("• Invalidation price levels")
print("• Timeframe specification")
print("• ATR-based validation")
print()
print("🚀 Ready for Module 4!")