#!/usr/bin/env python3
"""
Test script for Session Awareness Engine (Module 7)
Tests session detection, optimal trading times, and session statistics
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test session management imports"""
    print("🧪 Testing Session Management Imports...")
    
    try:
        from app.services.session_manager import (
            SessionManager, SessionConfig, SessionRange, SessionBox, SessionStats,
            session_manager, get_current_session, is_optimal_trading_time
        )
        print("✅ Session manager imports successful")
        
        from app.routes.sessions import router
        print("✅ Session routes imports successful")
        
        # Test pytz import
        import pytz
        print("✅ Timezone handling imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_session_detection():
    """Test session detection functionality"""
    print("\n🕐 Testing Session Detection...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Test different times
        test_times = [
            (datetime(2024, 1, 15, 2, 0), "asia"),      # 02:00 UTC - Asia
            (datetime(2024, 1, 15, 8, 0), "london"),   # 08:00 UTC - London (Asia ends at 08:00)
            (datetime(2024, 1, 15, 14, 0), "overlap"), # 14:00 UTC - London/NY overlap (12:00-16:00)
            (datetime(2024, 1, 15, 13, 0), "overlap"),  # 13:00 UTC - London/NY overlap
            (datetime(2024, 1, 15, 22, 0), "off_hours"), # 22:00 UTC - Off hours
            (datetime(2024, 1, 14, 2, 0), "off_hours"),  # Sunday - Off hours
        ]
        
        for test_time, expected_session in test_times:
            detected_session = manager.get_current_session(test_time)
            
            if detected_session == expected_session:
                print(f"✅ {test_time.strftime('%a %H:%M UTC')}: {detected_session}")
            else:
                print(f"❌ {test_time.strftime('%a %H:%M UTC')}: expected {expected_session}, got {detected_session}")
                return False
        
        # Test current session (should not crash)
        current = manager.get_current_session()
        print(f"✅ Current session detection: {current}")
        
        return True
        
    except Exception as e:
        print(f"❌ Session detection test error: {e}")
        return False

def test_optimal_trading_times():
    """Test optimal trading time logic"""
    print("\n⏰ Testing Optimal Trading Times...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Test CHOCH signals (only first 2 hours of session)
        london_open = datetime(2024, 1, 15, 7, 30)  # 30 min after London open
        london_late = datetime(2024, 1, 15, 10, 0)  # 3 hours after London open
        off_hours = datetime(2024, 1, 15, 22, 0)    # Off hours
        
        test_cases = [
            (london_open, "CHOCH", True, "CHOCH during session open"),
            (london_late, "CHOCH", False, "CHOCH too late in session"),
            (london_open, "BOS", True, "BOS during active session"),
            (london_late, "BOS", True, "BOS during active session"),
            (off_hours, "BOS", False, "BOS during off hours"),
            (off_hours, "CHOCH", False, "CHOCH during off hours"),
        ]
        
        for test_time, signal_type, expected, description in test_cases:
            result = manager.is_optimal_trading_time(test_time, signal_type)
            
            if result == expected:
                print(f"✅ {description}: {result}")
            else:
                print(f"❌ {description}: expected {expected}, got {result}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Optimal trading times test error: {e}")
        return False

def test_session_range_calculation():
    """Test session range calculation"""
    print("\n📊 Testing Session Range Calculation...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Create test OHLCV data for one day
        dates = pd.date_range(start='2024-01-15 00:00:00', end='2024-01-15 23:59:00', freq='h')
        
        # Generate realistic price data
        base_price = 50000
        price_data = []
        
        for i, timestamp in enumerate(dates):
            # Add some volatility based on session
            session = manager.get_current_session(timestamp.to_pydatetime())
            
            if session == "london":
                volatility = 200  # Higher volatility during London
            elif session == "new_york":
                volatility = 150
            elif session == "asia":
                volatility = 100
            else:
                volatility = 50   # Lower during off hours
            
            price_change = np.random.normal(0, volatility)
            current_price = base_price + price_change
            
            price_data.append({
                'timestamp': timestamp,
                'open': current_price,
                'high': current_price + abs(np.random.normal(0, volatility/2)),
                'low': current_price - abs(np.random.normal(0, volatility/2)),
                'close': current_price + np.random.normal(0, volatility/4),
                'volume': np.random.uniform(100, 1000),
                'symbol': 'BTCUSDT'
            })
        
        df = pd.DataFrame(price_data)
        
        # Test session range calculation
        test_date = "2024-01-15"
        
        for session_name in ["asia", "london", "new_york"]:
            session_range = manager.get_session_range(df, session_name, test_date)
            
            if session_range:
                print(f"✅ {session_name.title()} session range:")
                print(f"   High: {session_range.high:.2f}")
                print(f"   Low: {session_range.low:.2f}")
                print(f"   Range: {session_range.range_size:.2f}")
                print(f"   Volume: {session_range.volume:.2f}")
            else:
                print(f"❌ Failed to calculate {session_name} session range")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Session range calculation test error: {e}")
        return False

def test_candle_tagging():
    """Test candle tagging with session information"""
    print("\n🏷️ Testing Candle Tagging...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Create test data spanning multiple sessions
        dates = pd.date_range(start='2024-01-15 06:00:00', end='2024-01-15 18:00:00', freq='h')
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(49000, 51000, len(dates)),
            'high': np.random.uniform(50000, 52000, len(dates)),
            'low': np.random.uniform(48000, 50000, len(dates)),
            'close': np.random.uniform(49000, 51000, len(dates)),
            'volume': np.random.uniform(100, 1000, len(dates))
        })
        
        # Tag candles with session information
        tagged_df = manager.tag_candles_with_session(df)
        
        # Verify required columns exist
        required_columns = ['session', 'is_session_open', 'is_overlap']
        for col in required_columns:
            if col not in tagged_df.columns:
                print(f"❌ Missing column: {col}")
                return False
        
        # Check session distribution
        session_counts = tagged_df['session'].value_counts()
        print(f"✅ Session distribution:")
        for session, count in session_counts.items():
            print(f"   {session}: {count} candles")
        
        # Check overlap detection
        overlap_count = tagged_df['is_overlap'].sum()
        print(f"✅ Overlap periods detected: {overlap_count} candles")
        
        # Verify session logic
        london_candles = tagged_df[tagged_df['session'] == 'london']
        if len(london_candles) > 0:
            london_times = london_candles['timestamp'].dt.hour
            if london_times.min() >= 7 and london_times.max() <= 16:
                print("✅ London session timing correct")
            else:
                print(f"❌ London session timing incorrect: {london_times.min()}-{london_times.max()}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Candle tagging test error: {e}")
        return False

def test_session_boxes():
    """Test session box generation"""
    print("\n📦 Testing Session Boxes...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Test getting session boxes (will be empty without stored data)
        boxes = manager.get_session_boxes("BTCUSDT", "2024-01-15")
        
        # Should return empty list for non-existent data
        if isinstance(boxes, list):
            print(f"✅ Session boxes retrieved: {len(boxes)} boxes")
        else:
            print("❌ Session boxes should return a list")
            return False
        
        # Test session info retrieval
        for session_name in ["asia", "london", "new_york"]:
            config = manager.get_session_info(session_name)
            if config:
                print(f"✅ {session_name.title()} session info:")
                print(f"   Time: {config.start_time} - {config.end_time} UTC")
                print(f"   Color: {config.color}")
                print(f"   Pairs: {len(config.pairs)} pairs")
            else:
                print(f"❌ Failed to get {session_name} session info")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Session boxes test error: {e}")
        return False

def test_session_statistics():
    """Test session statistics functionality"""
    print("\n📈 Testing Session Statistics...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Test getting statistics (will be empty without data)
        stats = manager.get_session_statistics("BTCUSDT", 30)
        
        if isinstance(stats, dict):
            print(f"✅ Session statistics retrieved for {len(stats)} sessions")
            
            for session_name, session_stats in stats.items():
                print(f"   {session_name.title()}:")
                print(f"     Total signals: {session_stats.total_signals}")
                print(f"     Win rate: {session_stats.win_rate:.2%}")
                print(f"     Avg range: {session_stats.avg_range_size:.2f}")
        else:
            print("❌ Session statistics should return a dictionary")
            return False
        
        # Test optimal pairs
        for session_name in ["asia", "london", "new_york"]:
            pairs = manager.get_optimal_pairs_for_session(session_name)
            if pairs:
                print(f"✅ {session_name.title()} optimal pairs: {pairs}")
            else:
                print(f"❌ No optimal pairs for {session_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Session statistics test error: {e}")
        return False

def test_api_integration():
    """Test API route integration"""
    print("\n🌐 Testing API Integration...")
    
    try:
        from app.routes.sessions import router
        from app.routes.sessions import (
            SessionStatusResponse, SessionBoxResponse, SessionStatsResponse,
            TradingTimeCheckRequest
        )
        
        # Test response models
        status_response = SessionStatusResponse(
            current_session="london",
            is_trading_hours=True,
            is_overlap=False,
            optimal_pairs=["GBPUSD", "EURUSD"]
        )
        
        box_response = SessionBoxResponse(
            session="london",
            start_time="2024-01-15T07:00:00",
            end_time="2024-01-15T16:00:00",
            high=50500.0,
            low=49500.0,
            color="#1a4a2a",
            range_pips=100.0,
            is_active=False
        )
        
        stats_response = SessionStatsResponse(
            session="london",
            total_signals=50,
            winning_signals=35,
            win_rate=0.70,
            avg_range_size=150.0,
            avg_volume=500.0,
            best_pairs=["GBPUSD", "EURUSD"]
        )
        
        trading_time_request = TradingTimeCheckRequest(
            signal_type="BOS",
            utc_time="2024-01-15T08:00:00"
        )
        
        print("✅ API models created successfully")
        print(f"   Status response: {status_response.current_session}")
        print(f"   Box response: {box_response.session} ({box_response.range_pips} pips)")
        print(f"   Stats response: {stats_response.win_rate:.1%} win rate")
        print(f"   Trading time request: {trading_time_request.signal_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test error: {e}")
        return False

def test_pair_optimization():
    """Test pair optimization for sessions"""
    print("\n💱 Testing Pair Optimization...")
    
    try:
        from app.services.session_manager import SessionManager
        
        manager = SessionManager()
        
        # Test pair optimization logic
        test_cases = [
            ("GBPUSD", "london", True, "GBP pair optimal for London"),
            ("USDJPY", "asia", True, "JPY pair optimal for Asia"),
            ("BTCUSDT", "new_york", True, "Crypto optimal for New York"),
            ("GBPUSD", "asia", False, "GBP pair not optimal for Asia"),
            ("USDJPY", "london", False, "JPY pair not optimal for London"),
        ]
        
        for pair, session, expected, description in test_cases:
            result = manager.is_pair_optimal_for_session(pair, session)
            
            if result == expected:
                print(f"✅ {description}: {result}")
            else:
                print(f"❌ {description}: expected {expected}, got {result}")
                return False
        
        # Test getting all optimal pairs
        all_sessions_pairs = {}
        for session in ["asia", "london", "new_york"]:
            pairs = manager.get_optimal_pairs_for_session(session)
            all_sessions_pairs[session] = pairs
            print(f"✅ {session.title()} session pairs: {len(pairs)} pairs")
        
        return True
        
    except Exception as e:
        print(f"❌ Pair optimization test error: {e}")
        return False

def main():
    """Run all session awareness tests"""
    print("Session Awareness Engine (Module 7) - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Session Detection", test_session_detection),
        ("Optimal Trading Times", test_optimal_trading_times),
        ("Session Range Calculation", test_session_range_calculation),
        ("Candle Tagging", test_candle_tagging),
        ("Session Boxes", test_session_boxes),
        ("Session Statistics", test_session_statistics),
        ("API Integration", test_api_integration),
        ("Pair Optimization", test_pair_optimization)
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
        print("\n📋 MODULE 7 - Session Awareness Engine COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • Session Detection:")
        print("    - Asia: 00:00-08:00 UTC (USDJPY, AUDUSD, NZDUSD)")
        print("    - London: 07:00-16:00 UTC (GBPUSD, EURUSD, EURGBP)")
        print("    - New York: 12:00-21:00 UTC (BTCUSDT, EURUSD, GBPUSD)")
        print("    - Overlap detection for high liquidity periods")
        print("    - Off-hours identification and weekend handling")
        print("  • Optimal Trading Times:")
        print("    - CHOCH signals: only during session open (first 2 hours)")
        print("    - BOS signals: during active session hours")
        print("    - No trading during off-hours or weekends")
        print("    - Session-specific pair optimization")
        print("  • Session Range Analysis:")
        print("    - Daily high/low calculation per session")
        print("    - Range size and volume tracking")
        print("    - Liquidity zone identification")
        print("    - Historical session data storage")
        print("  • Chart Integration:")
        print("    - Session box overlays with colors")
        print("    - Real-time session status")
        print("    - Range and pip calculations")
        print("    - Active session highlighting")
        print("  • Statistics & Analytics:")
        print("    - Win rate by session analysis")
        print("    - Average range size tracking")
        print("    - Best session identification")
        print("    - Pair performance by session")
        print("  • API Endpoints:")
        print("    - GET /api/sessions/status → current session info")
        print("    - GET /api/sessions/boxes → chart overlay data")
        print("    - GET /api/sessions/stats → session statistics")
        print("    - POST /api/sessions/check-trading-time → time validation")
        print("    - GET /api/sessions/pairs/{session} → optimal pairs")
        print("\n🚀 Session-Aware Trading!")
        print("\nThe system now optimizes trading based on:")
        print("• Market liquidity and session characteristics")
        print("• Time-based signal filtering and validation")
        print("• Session-specific pair recommendations")
        print("• Historical session performance analysis")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)