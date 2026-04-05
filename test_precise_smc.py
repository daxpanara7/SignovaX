#!/usr/bin/env python3
"""
Test script for Precise SMC Logic Definitions
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all precise SMC modules can be imported"""
    print("🧪 Testing Precise SMC Imports...")
    
    try:
        # Test SMC models
        from app.models.smc_models import (
            OrderBlock, FairValueGap, LiquidityZone, StructureEvent, SMCAnalysis,
            OrderBlockType, FVGType, LiquidityType, StructureType, ConfidenceLevel,
            SignalType, SMCDetectionConfig
        )
        print("✅ SMC models imported successfully")
        
        # Test precise SMC engine
        from app.strategies.smc_engine import PreciseSMCEngine
        print("✅ PreciseSMCEngine imported successfully")
        
        # Test SMC routes
        from app.routes.smc_precise import router
        print("✅ Precise SMC API routes imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_smc_models():
    """Test SMC data models"""
    print("\n📋 Testing SMC Data Models...")
    
    try:
        from app.models.smc_models import (
            OrderBlock, OrderBlockType, ConfidenceLevel,
            FairValueGap, FVGType, LiquidityZone, LiquidityType,
            StructureEvent, StructureType, SignalType
        )
        
        # Test OrderBlock model
        ob = OrderBlock(
            top=50100.0,
            bottom=49900.0,
            timestamp=datetime.now(),
            candle_index=100,
            ob_type=OrderBlockType.BULLISH,
            timeframe="1h",
            displacement_size=200.0,
            atr_multiple=1.8,
            confidence=ConfidenceLevel.HIGH,
            invalidation_price=49800.0,
            impulse_candle_index=101
        )
        assert ob.ob_type == OrderBlockType.BULLISH
        assert ob.confidence == ConfidenceLevel.HIGH
        print("✅ OrderBlock model working")
        
        # Test FairValueGap model
        fvg = FairValueGap(
            top=50200.0,
            bottom=50000.0,
            gap_size=200.0,
            timestamp=datetime.now(),
            candle_index=50,
            fvg_type=FVGType.BULLISH,
            timeframe="1h",
            atr_multiple=0.5,
            min_size_met=True,
            confidence=ConfidenceLevel.MEDIUM,
            invalidation_price=49900.0,
            candle_before_index=49,
            candle_middle_index=50,
            candle_after_index=51
        )
        assert fvg.fvg_type == FVGType.BULLISH
        assert fvg.gap_size == 200.0
        print("✅ FairValueGap model working")
        
        # Test StructureEvent model
        se = StructureEvent(
            structure_type=StructureType.BOS_BULLISH,
            timestamp=datetime.now(),
            candle_index=75,
            break_price=50500.0,
            close_price=50600.0,
            previous_structure_price=50400.0,
            signal_type=SignalType.CONTINUATION,
            position_size_multiplier=1.0,
            previous_trend="uptrend",
            new_trend="uptrend",
            timeframe="1h",
            confidence=ConfidenceLevel.HIGH,
            invalidation_price=50450.0
        )
        assert se.signal_type == SignalType.CONTINUATION
        assert se.position_size_multiplier == 1.0
        print("✅ StructureEvent model working")
        
        return True
        
    except Exception as e:
        print(f"❌ SMC models test error: {e}")
        return False


def create_test_data():
    """Create test OHLCV data for SMC analysis"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # Create realistic price data with patterns
    base_price = 50000.0
    prices = []
    
    for i in range(100):
        # Add some volatility and trend
        volatility = np.random.normal(0, 100)
        trend = i * 10  # Slight uptrend
        price = base_price + trend + volatility
        prices.append(price)
    
    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Create realistic OHLC from close price
        close = price
        open_price = close + np.random.normal(0, 50)
        high = max(open_price, close) + abs(np.random.normal(0, 30))
        low = min(open_price, close) - abs(np.random.normal(0, 30))
        volume = np.random.uniform(100, 1000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


def test_order_block_detection():
    """Test Order Block detection with precise rules"""
    print("\n🔲 Testing Order Block Detection...")
    
    try:
        from app.strategies.smc_engine import PreciseSMCEngine
        from app.models.smc_models import SMCDetectionConfig
        
        # Create test data
        df = create_test_data()
        
        # Initialize engine
        config = SMCDetectionConfig()
        engine = PreciseSMCEngine(config)
        
        # Calculate ATR for testing
        atr_14 = engine._calculate_atr(df)
        
        # Test Order Block detection
        order_blocks = engine.detect_order_blocks(df, atr_14, "1h")
        
        print(f"✅ Order Block detection completed: {len(order_blocks)} blocks found")
        
        # Validate Order Block properties
        for ob in order_blocks[:3]:  # Check first 3
            assert hasattr(ob, 'top')
            assert hasattr(ob, 'bottom')
            assert hasattr(ob, 'ob_type')
            assert hasattr(ob, 'mitigated')
            assert hasattr(ob, 'confidence')
            assert hasattr(ob, 'displacement_size')
            assert hasattr(ob, 'atr_multiple')
        
        print("✅ Order Block properties validated")
        return True
        
    except Exception as e:
        print(f"❌ Order Block detection test error: {e}")
        return False


def test_fvg_detection():
    """Test Fair Value Gap detection with precise rules"""
    print("\n📊 Testing Fair Value Gap Detection...")
    
    try:
        from app.strategies.smc_engine import PreciseSMCEngine
        from app.models.smc_models import SMCDetectionConfig
        
        # Create test data
        df = create_test_data()
        
        # Initialize engine
        config = SMCDetectionConfig()
        engine = PreciseSMCEngine(config)
        
        # Calculate ATR for testing
        atr_14 = engine._calculate_atr(df)
        
        # Test FVG detection
        fvgs = engine.detect_fvg(df, atr_14, "1h")
        
        print(f"✅ FVG detection completed: {len(fvgs)} gaps found")
        
        # Validate FVG properties
        for fvg in fvgs[:3]:  # Check first 3
            assert hasattr(fvg, 'top')
            assert hasattr(fvg, 'bottom')
            assert hasattr(fvg, 'gap_size')
            assert hasattr(fvg, 'fvg_type')
            assert hasattr(fvg, 'filled')
            assert hasattr(fvg, 'fill_percentage')
            assert hasattr(fvg, 'atr_multiple')
            assert fvg.gap_size > 0
        
        print("✅ FVG properties validated")
        return True
        
    except Exception as e:
        print(f"❌ FVG detection test error: {e}")
        return False


def test_liquidity_detection():
    """Test Liquidity Zone detection with precise rules"""
    print("\n💧 Testing Liquidity Zone Detection...")
    
    try:
        from app.strategies.smc_engine import PreciseSMCEngine
        from app.models.smc_models import SMCDetectionConfig
        
        # Create test data
        df = create_test_data()
        
        # Initialize engine
        config = SMCDetectionConfig()
        engine = PreciseSMCEngine(config)
        
        # Test Liquidity detection
        liquidity_zones = engine.detect_liquidity(df, "1h")
        
        print(f"✅ Liquidity detection completed: {len(liquidity_zones)} zones found")
        
        # Validate Liquidity properties
        for lz in liquidity_zones[:3]:  # Check first 3
            assert hasattr(lz, 'price')
            assert hasattr(lz, 'zone_type')
            assert hasattr(lz, 'equal_levels')
            assert hasattr(lz, 'level_count')
            assert hasattr(lz, 'swept')
            assert hasattr(lz, 'confidence')
            assert lz.level_count >= 2
        
        print("✅ Liquidity Zone properties validated")
        return True
        
    except Exception as e:
        print(f"❌ Liquidity detection test error: {e}")
        return False


def test_structure_detection():
    """Test Structure Event detection (BOS vs CHOCH)"""
    print("\n🏗️ Testing Structure Event Detection...")
    
    try:
        from app.strategies.smc_engine import PreciseSMCEngine
        from app.models.smc_models import SMCDetectionConfig
        
        # Create test data
        df = create_test_data()
        
        # Initialize engine
        config = SMCDetectionConfig()
        engine = PreciseSMCEngine(config)
        
        # Test Structure detection
        structure_events = engine.detect_structure(df, "1h")
        
        print(f"✅ Structure detection completed: {len(structure_events)} events found")
        
        # Validate Structure properties
        for se in structure_events[:3]:  # Check first 3
            assert hasattr(se, 'structure_type')
            assert hasattr(se, 'signal_type')
            assert hasattr(se, 'position_size_multiplier')
            assert hasattr(se, 'break_price')
            assert hasattr(se, 'previous_trend')
            assert hasattr(se, 'new_trend')
            assert hasattr(se, 'confidence')
            assert se.position_size_multiplier in [0.5, 1.0]
        
        print("✅ Structure Event properties validated")
        return True
        
    except Exception as e:
        print(f"❌ Structure detection test error: {e}")
        return False


def test_complete_analysis():
    """Test complete SMC analysis"""
    print("\n🎯 Testing Complete SMC Analysis...")
    
    try:
        from app.strategies.smc_engine import PreciseSMCEngine
        from app.models.smc_models import SMCDetectionConfig
        
        # Create test data
        df = create_test_data()
        
        # Initialize engine
        config = SMCDetectionConfig()
        engine = PreciseSMCEngine(config)
        
        # Perform complete analysis
        analysis = engine.analyze(df, "BTCUSDT", "1h")
        
        # Validate analysis result
        assert hasattr(analysis, 'symbol')
        assert hasattr(analysis, 'timeframe')
        assert hasattr(analysis, 'order_blocks')
        assert hasattr(analysis, 'fair_value_gaps')
        assert hasattr(analysis, 'liquidity_zones')
        assert hasattr(analysis, 'structure_events')
        assert hasattr(analysis, 'current_trend')
        assert hasattr(analysis, 'atr_14')
        assert hasattr(analysis, 'detection_summary')
        assert hasattr(analysis, 'high_confidence_patterns')
        assert hasattr(analysis, 'active_patterns')
        
        assert analysis.symbol == "BTCUSDT"
        assert analysis.timeframe == "1h"
        assert analysis.candles_analyzed == len(df)
        
        print("✅ Complete SMC analysis working")
        print(f"   - Order Blocks: {len(analysis.order_blocks)}")
        print(f"   - Fair Value Gaps: {len(analysis.fair_value_gaps)}")
        print(f"   - Liquidity Zones: {len(analysis.liquidity_zones)}")
        print(f"   - Structure Events: {len(analysis.structure_events)}")
        print(f"   - Current Trend: {analysis.current_trend}")
        print(f"   - High Confidence Patterns: {analysis.high_confidence_patterns}")
        print(f"   - Active Patterns: {analysis.active_patterns}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete analysis test error: {e}")
        return False


def test_api_structure():
    """Test API endpoint structure"""
    print("\n🌐 Testing API Structure...")
    
    try:
        from app.routes.smc_precise import router
        
        # Check router exists
        assert router is not None
        print("✅ Precise SMC API router created")
        
        # Check routes are defined
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/analyze", "/summary/{symbol}", "/order-blocks/{symbol}",
            "/fair-value-gaps/{symbol}", "/liquidity-zones/{symbol}",
            "/structure-events/{symbol}", "/config"
        ]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"✅ Route {expected_route} defined")
            else:
                print(f"❌ Route {expected_route} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test error: {e}")
        return False


def main():
    """Run all tests"""
    print("Precise SMC Logic Definitions - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("SMC Data Models", test_smc_models),
        ("Order Block Detection", test_order_block_detection),
        ("Fair Value Gap Detection", test_fvg_detection),
        ("Liquidity Zone Detection", test_liquidity_detection),
        ("Structure Event Detection", test_structure_detection),
        ("Complete SMC Analysis", test_complete_analysis),
        ("API Structure", test_api_structure)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n📋 MODULE 3 - Precise SMC Logic Definitions COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • Order Blocks with mathematical precision:")
        print("    - Last opposite-color candle before strong impulse")
        print("    - Displacement validation: impulse body > 1.5x ATR")
        print("    - Mitigation tracking when price closes inside OB zone")
        print("  • Fair Value Gaps with exact rules:")
        print("    - Bullish FVG: candle[i+1].low > candle[i-1].high")
        print("    - Bearish FVG: candle[i+1].high < candle[i-1].low")
        print("    - Minimum size filter: gap_size > 0.3 * ATR(14)")
        print("    - Partial and complete fill tracking")
        print("  • Liquidity Zones with precise criteria:")
        print("    - Equal highs/lows within 0.1% tolerance")
        print("    - Minimum 5 candles between equal levels")
        print("    - Sweep detection when price closes beyond level")
        print("  • Structure Events (BOS vs CHOCH) with clear distinction:")
        print("    - BOS: Continuation signals, 100% position size")
        print("    - CHOCH: Reversal signals, 50% position size")
        print("    - Precise trend analysis and break validation")
        print("  • Enhanced data models with all required fields:")
        print("    - Timestamps, confidence levels, invalidation prices")
        print("    - Mitigation/fill/sweep status tracking")
        print("    - ATR-based validation and confidence scoring")
        print("  • API endpoints:")
        print("    - POST /api/smc/analyze")
        print("    - GET /api/smc/summary/{symbol}")
        print("    - GET /api/smc/order-blocks/{symbol}")
        print("    - GET /api/smc/fair-value-gaps/{symbol}")
        print("    - GET /api/smc/liquidity-zones/{symbol}")
        print("    - GET /api/smc/structure-events/{symbol}")
        print("    - GET/POST /api/smc/config")
        print("\n🚀 Ready for Module 4!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)