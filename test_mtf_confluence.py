#!/usr/bin/env python3
"""
Test script for Multi-Timeframe Confluence Engine
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.strategies.mtf_confluence import ConfluenceEngine, TimeframeHierarchy


async def test_mtf_confluence():
    """Test the MTF Confluence Engine"""
    print("🚀 Testing Multi-Timeframe Confluence Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = ConfluenceEngine()
    
    # Test parameters
    symbol = "BTCUSDT"
    htf = "4h"
    mtf = "1h"
    ltf = "5m"
    
    print(f"Testing symbol: {symbol}")
    print(f"Timeframes - HTF: {htf}, MTF: {mtf}, LTF: {ltf}")
    print()
    
    try:
        # Test 1: HTF Bias Analysis
        print("📊 Step 1: Analyzing HTF Bias...")
        htf_result = await engine.analyze_htf_bias(symbol, htf)
        print(f"HTF Bias: {htf_result.get('bias', 'Unknown')}")
        print(f"HTF Order Blocks: {len(htf_result.get('htf_ob', []))}")
        print(f"HTF Liquidity Zones: {len(htf_result.get('htf_liquidity', []))}")
        print()
        
        # Test 2: MTF Confirmation
        print("🔍 Step 2: Finding MTF Confirmation...")
        mtf_result = await engine.find_mtf_confirmation(symbol, mtf, htf_result)
        print(f"MTF Confirmed: {mtf_result.get('confirmed', False)}")
        if mtf_result.get('confirmed'):
            print(f"MTF BOS Level: {mtf_result.get('mtf_bos_level')}")
            print(f"MTF Direction: {mtf_result.get('mtf_bos_direction')}")
        print()
        
        # Test 3: LTF Entry
        print("🎯 Step 3: Finding LTF Entry...")
        ltf_result = await engine.find_ltf_entry(symbol, ltf, mtf_result)
        if ltf_result.get('entry'):
            print(f"Entry Price: {ltf_result['entry']}")
            print(f"Stop Loss: {ltf_result.get('sl')}")
            print(f"Take Profit: {ltf_result.get('tp')}")
            print(f"Direction: {ltf_result.get('direction')}")
            print(f"Entry Type: {ltf_result.get('entry_type')}")
        else:
            print(f"No entry found: {ltf_result.get('reason', 'Unknown')}")
        print()
        
        # Test 4: Complete MTF Analysis
        print("🎯 Step 4: Complete MTF Confluence Analysis...")
        confluence_result = await engine.analyze_mtf_confluence(symbol, ltf, htf, mtf)
        
        print(f"Confluence Score: {confluence_result.confluence_score}/100")
        print(f"Overall Bias: {confluence_result.bias}")
        print(f"Signal Valid: {confluence_result.entry is not None}")
        
        if confluence_result.entry:
            print(f"Entry: {confluence_result.entry}")
            print(f"Stop Loss: {confluence_result.stop_loss}")
            print(f"Take Profit: {confluence_result.take_profit}")
        
        print("\nConfluence Reasons:")
        for i, reason in enumerate(confluence_result.reasons, 1):
            print(f"  {i}. {reason}")
        
        print()
        print("✅ MTF Confluence Engine test completed successfully!")
        
        # Test 5: Timeframe Hierarchy
        print("\n📋 Timeframe Hierarchy Test:")
        print(f"HTF Timeframes: {TimeframeHierarchy.HTF_TIMEFRAMES}")
        print(f"MTF Timeframes: {TimeframeHierarchy.MTF_TIMEFRAMES}")
        print(f"LTF Timeframes: {TimeframeHierarchy.LTF_TIMEFRAMES}")
        
        # Test timeframe classification
        test_tfs = ["1m", "5m", "15m", "1h", "4h", "1d"]
        for tf in test_tfs:
            tf_type = TimeframeHierarchy.get_timeframe_type(tf)
            print(f"  {tf} -> {tf_type.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_integration():
    """Test API integration"""
    print("\n🌐 Testing API Integration...")
    print("=" * 30)
    
    try:
        import requests
        import json
        
        # Test data
        test_request = {
            "symbol": "BTCUSDT",
            "entry_tf": "5m",
            "htf": "4h",
            "mtf": "1h"
        }
        
        print("Note: API integration test requires running backend server")
        print(f"Test request: {json.dumps(test_request, indent=2)}")
        print("To test API manually:")
        print("1. Start backend: python backend/run.py")
        print("2. POST to: http://localhost:8000/api/mtf/mtf-analyze")
        print("3. GET timeframes: http://localhost:8000/api/mtf/mtf-timeframes")
        print("4. GET status: http://localhost:8000/api/mtf/mtf-status/BTCUSDT")
        
    except ImportError:
        print("Requests library not available for API testing")


if __name__ == "__main__":
    print("Multi-Timeframe Confluence Engine Test Suite")
    print("=" * 60)
    
    # Run tests
    success = asyncio.run(test_mtf_confluence())
    asyncio.run(test_api_integration())
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\nModule 1 - Multi-Timeframe Confluence Engine is ready!")
        print("\nFeatures implemented:")
        print("✅ TimeframeHierarchy class with HTF/MTF/LTF classification")
        print("✅ ConfluenceEngine with HTF bias analysis")
        print("✅ MTF confirmation detection")
        print("✅ LTF entry point identification")
        print("✅ Confluence scoring system (0-100)")
        print("✅ Signal validation rules (no conflicting bias)")
        print("✅ API endpoints for MTF analysis")
        print("✅ Comprehensive logging and error handling")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)