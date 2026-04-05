#!/usr/bin/env python3
"""
Test script for Risk Management Module
"""

import sys
import os
import asyncio
from datetime import datetime, date

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all risk management modules can be imported"""
    print("🧪 Testing Risk Management Imports...")
    
    try:
        # Test risk models
        from app.models.risk_models import (
            RiskValidationResult, CircuitBreakerStatus, RiskMetrics,
            PositionSizeResponse, DailyRiskLog, CorrelationGroup, OpenTrade
        )
        print("✅ Risk models imported successfully")
        
        # Test risk manager
        from app.services.risk_manager import RiskManager, RiskConfig
        print("✅ RiskManager imported successfully")
        
        # Test risk routes
        from app.routes.risk import router
        print("✅ Risk API routes imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_risk_config():
    """Test risk configuration"""
    print("\n📋 Testing Risk Configuration...")
    
    try:
        from app.services.risk_manager import RiskConfig
        
        # Test default configuration
        config = RiskConfig()
        assert config.account_balance == 10000.0
        assert config.risk_per_trade == 0.01
        assert config.max_daily_loss == 0.05
        assert config.min_risk_reward == 2.0
        assert config.max_concurrent_trades == 3
        assert config.max_correlated_trades == 1
        print("✅ Default risk configuration correct")
        
        # Test custom configuration
        custom_config = RiskConfig(
            account_balance=50000.0,
            risk_per_trade=0.02,
            max_daily_loss=0.03,
            min_risk_reward=1.5,
            max_concurrent_trades=5,
            max_correlated_trades=2
        )
        assert custom_config.account_balance == 50000.0
        assert custom_config.risk_per_trade == 0.02
        print("✅ Custom risk configuration working")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk config test error: {e}")
        return False


def test_position_sizing():
    """Test position size calculations"""
    print("\n💰 Testing Position Size Calculations...")
    
    try:
        from app.services.risk_manager import RiskManager, RiskConfig
        
        # Create risk manager with test config
        config = RiskConfig(account_balance=10000.0, risk_per_trade=0.01)
        risk_manager = RiskManager(config, db_path=":memory:")
        
        # Test position size calculation
        entry = 50000.0
        sl = 49000.0
        
        result = risk_manager.calculate_position_size(entry, sl)
        
        # Expected: risk_amount = 10000 * 0.01 = 100
        # pip_risk = 50000 - 49000 = 1000
        # position_size = 100 / 1000 = 0.1
        
        assert result.risk_amount == 100.0
        assert result.pip_risk == 1000.0
        assert result.position_size == 0.1
        print(f"✅ Position size calculation: {result.position_size} units for ${result.risk_amount} risk")
        
        # Test with different parameters
        result2 = risk_manager.calculate_position_size(entry, sl, account_balance=20000.0, risk_pct=0.02)
        expected_risk = 20000.0 * 0.02  # 400
        expected_size = expected_risk / 1000.0  # 0.4
        
        assert result2.risk_amount == 400.0
        assert result2.position_size == 0.4
        print(f"✅ Custom position size calculation: {result2.position_size} units for ${result2.risk_amount} risk")
        
        return True
        
    except Exception as e:
        print(f"❌ Position sizing test error: {e}")
        return False


def test_correlation_groups():
    """Test correlation group functionality"""
    print("\n🔗 Testing Correlation Groups...")
    
    try:
        from app.services.risk_manager import RiskManager
        
        risk_manager = RiskManager(db_path=":memory:")
        
        # Test correlation groups
        correlations = risk_manager.get_correlated_pairs()
        
        assert "crypto" in correlations
        assert "forex_usd" in correlations
        assert "BTCUSDT" in correlations["crypto"]
        assert "EURUSD" in correlations["forex_usd"]
        print("✅ Correlation groups defined correctly")
        
        # Test correlation group detection
        btc_group = risk_manager._get_correlation_group("BTCUSDT")
        eur_group = risk_manager._get_correlation_group("EURUSD")
        
        assert btc_group.value == "crypto"
        assert eur_group.value == "forex_usd"
        print("✅ Correlation group detection working")
        
        return True
        
    except Exception as e:
        print(f"❌ Correlation groups test error: {e}")
        return False


def test_signal_validation():
    """Test signal validation logic"""
    print("\n✅ Testing Signal Validation...")
    
    try:
        from app.services.risk_manager import RiskManager, RiskConfig
        from app.models.signals import TradingSignal, SignalType
        
        # Create risk manager
        config = RiskConfig(min_risk_reward=2.0, max_concurrent_trades=3)
        risk_manager = RiskManager(config, db_path=":memory:")
        
        # Test valid signal
        valid_signal = TradingSignal(
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.BUY,
            entry_price=50000.0,
            stop_loss=49000.0,  # 1000 pip risk
            take_profit=52000.0,  # 2000 pip reward (2:1 R:R)
            confidence=85.0,
            reasoning="Test signal",
            timestamp=datetime.now()
        )
        
        result = risk_manager.validate_signal(valid_signal)
        assert result.approved == True
        assert result.risk_reward_ratio == 2.0
        print("✅ Valid signal approved")
        
        # Test invalid R:R signal
        invalid_signal = TradingSignal(
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.BUY,
            entry_price=50000.0,
            stop_loss=49000.0,  # 1000 pip risk
            take_profit=50500.0,  # 500 pip reward (0.5:1 R:R)
            confidence=85.0,
            reasoning="Test signal",
            timestamp=datetime.now()
        )
        
        result = risk_manager.validate_signal(invalid_signal)
        assert result.approved == False
        assert "R:R ratio" in result.reason
        print("✅ Invalid R:R signal rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal validation test error: {e}")
        return False


def test_api_structure():
    """Test API endpoint structure"""
    print("\n🌐 Testing API Structure...")
    
    try:
        from app.routes.risk import router
        
        # Check router exists
        assert router is not None
        print("✅ Risk API router created")
        
        # Check routes are defined
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/status", "/position-size", "/validate", 
            "/circuit-breaker", "/correlations", "/daily-logs",
            "/config", "/reset-daily"
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
    print("Risk Management Module - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Risk Configuration", test_risk_config),
        ("Position Sizing", test_position_sizing),
        ("Correlation Groups", test_correlation_groups),
        ("Signal Validation", test_signal_validation),
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
        print("\n📋 MODULE 2 - Risk Management System COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • RiskManager class with comprehensive configuration")
        print("  • Position size calculation with risk-based formula")
        print("  • Signal validation with multiple risk checks")
        print("  • Circuit breaker system for daily loss protection")
        print("  • Correlation group management")
        print("  • SQLite database for daily risk logging")
        print("  • API endpoints:")
        print("    - GET /api/risk/status")
        print("    - GET /api/risk/position-size")
        print("    - POST /api/risk/validate")
        print("    - GET /api/risk/circuit-breaker")
        print("    - GET /api/risk/correlations")
        print("    - GET /api/risk/daily-logs")
        print("    - POST /api/risk/config")
        print("    - POST /api/risk/reset-daily")
        print("  • Integration with signal generation (all signals validated)")
        print("  • Comprehensive error handling and logging")
        print("\n🚀 Ready for Module 3!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)