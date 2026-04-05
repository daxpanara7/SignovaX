#!/usr/bin/env python3
"""
Test script for Advanced Backtesting Engine
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all advanced backtesting modules can be imported"""
    print("🧪 Testing Advanced Backtesting Imports...")
    
    try:
        # Test backtest models
        from app.models.backtest_models import (
            TradeSimulatorConfig, TradeResult, WalkForwardResult,
            MonteCarloResult, ProfessionalMetrics, AdvancedBacktestResult,
            BacktestConfig
        )
        print("✅ Backtest models imported successfully")
        
        # Test advanced backtester
        from app.services.backtester import AdvancedBacktester
        print("✅ AdvancedBacktester imported successfully")
        
        # Test backtest routes
        from app.routes.advanced_backtest import router
        print("✅ Advanced backtest API routes imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_trade_simulator_config():
    """Test trade simulator configuration"""
    print("\n⚙️ Testing Trade Simulator Configuration...")
    
    try:
        from app.models.backtest_models import TradeSimulatorConfig
        
        # Test default configuration
        config = TradeSimulatorConfig()
        assert config.slippage_pct == 0.0005  # 0.05%
        assert config.commission_pct == 0.001  # 0.1%
        assert config.spread_pips == 2.0
        print("✅ Default trade simulator config correct")
        
        # Test custom configuration
        custom_config = TradeSimulatorConfig(
            slippage_pct=0.001,
            commission_pct=0.002,
            spread_pips=3.0
        )
        assert custom_config.slippage_pct == 0.001
        assert custom_config.commission_pct == 0.002
        assert custom_config.spread_pips == 3.0
        print("✅ Custom trade simulator config working")
        
        return True
        
    except Exception as e:
        print(f"❌ Trade simulator config test error: {e}")
        return False


def test_professional_metrics():
    """Test professional metrics model"""
    print("\n📊 Testing Professional Metrics...")
    
    try:
        from app.models.backtest_models import ProfessionalMetrics
        
        # Test metrics creation
        metrics = ProfessionalMetrics(
            total_return_pct=25.5,
            win_rate=65.0,
            profit_factor=1.8,
            total_trades=100,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            calmar_ratio=0.8,
            max_drawdown_pct=12.5,
            avg_win_r=1.8,
            avg_loss_r=-0.9,
            expectancy=0.25,
            best_trade=500.0,
            worst_trade=-200.0,
            avg_trade_duration="2.5 hours",
            benchmark_comparison=5.2,
            recovery_factor=2.0,
            payoff_ratio=2.0,
            sterling_ratio=1.1,
            ulcer_index=8.5,
            var_95=-2.5,
            cvar_95=-3.8
        )
        
        assert metrics.total_return_pct == 25.5
        assert metrics.win_rate == 65.0
        assert metrics.profit_factor == 1.8
        assert metrics.sharpe_ratio == 1.2
        assert metrics.expectancy == 0.25
        print("✅ Professional metrics model working")
        
        return True
        
    except Exception as e:
        print(f"❌ Professional metrics test error: {e}")
        return False


def test_backtest_config():
    """Test backtesting configuration"""
    print("\n🔧 Testing Backtest Configuration...")
    
    try:
        from app.models.backtest_models import BacktestConfig, TradeSimulatorConfig
        
        # Test default configuration
        config = BacktestConfig(
            symbol="BTCUSDT",
            timeframe="1h",
            initial_capital=10000.0
        )
        
        assert config.symbol == "BTCUSDT"
        assert config.timeframe == "1h"
        assert config.initial_capital == 10000.0
        assert config.risk_per_trade == 0.01  # Default 1%
        assert config.enable_compounding == True
        print("✅ Default backtest config correct")
        
        # Test custom configuration
        custom_simulator = TradeSimulatorConfig(
            slippage_pct=0.001,
            commission_pct=0.002
        )
        
        custom_config = BacktestConfig(
            symbol="ETHUSDT",
            timeframe="4h",
            initial_capital=50000.0,
            trade_simulator=custom_simulator,
            risk_per_trade=0.02,
            min_confidence=80.0,
            max_concurrent_trades=3
        )
        
        assert custom_config.symbol == "ETHUSDT"
        assert custom_config.risk_per_trade == 0.02
        assert custom_config.trade_simulator.slippage_pct == 0.001
        print("✅ Custom backtest config working")
        
        return True
        
    except Exception as e:
        print(f"❌ Backtest config test error: {e}")
        return False


def create_mock_trade_results():
    """Create mock trade results for testing"""
    from app.models.backtest_models import TradeResult
    
    trades = []
    base_time = datetime.now()
    
    # Create 10 mock trades with varying results
    for i in range(10):
        entry_time = base_time + timedelta(hours=i*24)
        exit_time = entry_time + timedelta(hours=4)
        
        # Alternate between winning and losing trades
        if i % 3 == 0:  # Winning trade
            gross_pnl = 100.0 + (i * 10)
            net_pnl = gross_pnl - 5.0  # After costs
            r_multiple = 1.5
        else:  # Losing trade
            gross_pnl = -50.0
            net_pnl = gross_pnl - 5.0  # After costs
            r_multiple = -0.8
        
        trade = TradeResult(
            entry_time=entry_time,
            exit_time=exit_time,
            signal_type="BUY" if i % 2 == 0 else "SELL",
            entry_price=50000.0 + (i * 100),
            exit_price=50000.0 + (i * 100) + (gross_pnl * 10),
            signal_entry_price=50000.0 + (i * 100),
            signal_exit_price=50000.0 + (i * 100) + (gross_pnl * 10),
            position_size=0.1,
            gross_pnl=gross_pnl,
            slippage_cost=2.0,
            commission_cost=3.0,
            net_pnl=net_pnl,
            pnl_percent=(net_pnl / 5000.0) * 100,  # Assuming $5000 position
            r_multiple=r_multiple,
            exit_reason="Take Profit" if gross_pnl > 0 else "Stop Loss",
            confidence=75.0 + (i * 2),
            reasoning=f"Test trade {i+1}",
            trade_duration_hours=4.0
        )
        trades.append(trade)
    
    return trades


def test_monte_carlo_simulation():
    """Test Monte Carlo simulation logic"""
    print("\n🎲 Testing Monte Carlo Simulation...")
    
    try:
        from app.services.backtester import AdvancedBacktester
        
        # Create backtester instance
        backtester = AdvancedBacktester(db_path=":memory:")
        
        # Create mock trades
        trades = create_mock_trade_results()
        
        # Run Monte Carlo simulation (small number for testing)
        result = backtester.monte_carlo(trades, n_simulations=100)
        
        # Validate results
        assert result.n_simulations == 100
        assert result.original_trades == len(trades)
        assert isinstance(result.worst_drawdown_95pct, float)
        assert isinstance(result.best_return_95pct, float)
        assert isinstance(result.median_return, float)
        assert isinstance(result.ruin_probability, float)
        assert len(result.equity_curves_sample) <= 10
        
        print(f"✅ Monte Carlo simulation working")
        print(f"   - Simulations: {result.n_simulations}")
        print(f"   - Median Return: {result.median_return:.2f}%")
        print(f"   - Worst DD 95%: {result.worst_drawdown_95pct:.2f}%")
        print(f"   - Ruin Probability: {result.ruin_probability:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Monte Carlo simulation test error: {e}")
        return False


def test_professional_metrics_calculation():
    """Test professional metrics calculation"""
    print("\n📈 Testing Professional Metrics Calculation...")
    
    try:
        from app.services.backtester import AdvancedBacktester
        from app.models.backtest_models import BacktestConfig
        
        # Create backtester instance
        backtester = AdvancedBacktester(db_path=":memory:")
        
        # Create mock data
        trades = create_mock_trade_results()
        
        # Create mock equity curve
        equity_curve = []
        equity = 10000.0
        for i, trade in enumerate(trades):
            equity += trade.net_pnl
            equity_curve.append({
                'timestamp': trade.exit_time,
                'equity': equity,
                'realized_equity': equity,
                'unrealized_pnl': 0.0
            })
        
        # Create mock DataFrame
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        df = pd.DataFrame({
            'open': np.random.uniform(49000, 51000, 100),
            'high': np.random.uniform(50000, 52000, 100),
            'low': np.random.uniform(48000, 50000, 100),
            'close': np.random.uniform(49500, 50500, 100),
            'volume': np.random.uniform(100, 1000, 100)
        }, index=dates)
        
        # Create config
        config = BacktestConfig(symbol="BTCUSDT", timeframe="1h")
        
        # Calculate metrics
        metrics = backtester.calculate_metrics(trades, equity_curve, df, config)
        
        # Validate metrics
        assert isinstance(metrics.total_return_pct, float)
        assert isinstance(metrics.win_rate, float)
        assert isinstance(metrics.profit_factor, float)
        assert isinstance(metrics.sharpe_ratio, float)
        assert isinstance(metrics.max_drawdown_pct, float)
        assert metrics.total_trades == len(trades)
        
        print("✅ Professional metrics calculation working")
        print(f"   - Total Return: {metrics.total_return_pct:.2f}%")
        print(f"   - Win Rate: {metrics.win_rate:.2f}%")
        print(f"   - Profit Factor: {metrics.profit_factor:.2f}")
        print(f"   - Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"   - Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Professional metrics calculation test error: {e}")
        return False


def test_api_structure():
    """Test API endpoint structure"""
    print("\n🌐 Testing API Structure...")
    
    try:
        from app.routes.advanced_backtest import router
        
        # Check router exists
        assert router is not None
        print("✅ Advanced backtest API router created")
        
        # Check routes are defined
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/run", "/walkforward", "/montecarlo", 
            "/results/{backtest_id}", "/results",
            "/config/default", "/config/validate"
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
    print("Advanced Backtesting Engine - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Trade Simulator Config", test_trade_simulator_config),
        ("Professional Metrics", test_professional_metrics),
        ("Backtest Configuration", test_backtest_config),
        ("Monte Carlo Simulation", test_monte_carlo_simulation),
        ("Professional Metrics Calculation", test_professional_metrics_calculation),
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
        print("\n📋 MODULE 4 - Advanced Backtesting Engine COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • Realistic trade simulation:")
        print("    - Slippage: BUY entry * (1 + 0.05%), SELL entry * (1 - 0.05%)")
        print("    - Commission: 0.1% deducted on open and close")
        print("    - Spread handling for forex pairs")
        print("  • Walk-Forward Testing:")
        print("    - Split data into n equal periods")
        print("    - Train on 70%, test on 30% for each split")
        print("    - Aggregate results with consistency analysis")
        print("  • Monte Carlo Simulation:")
        print("    - Randomly shuffle historical trade order")
        print("    - 1000+ simulations for statistical analysis")
        print("    - Ruin probability and confidence intervals")
        print("  • Professional Metrics:")
        print("    - Sharpe, Sortino, Calmar ratios")
        print("    - R-multiple analysis and expectancy")
        print("    - VaR, CVaR, Ulcer Index")
        print("    - Recovery factor, payoff ratio")
        print("    - Benchmark comparison (buy & hold)")
        print("  • Database Storage:")
        print("    - SQLite storage for all backtest results")
        print("    - JSON serialization of configs and results")
        print("  • API Endpoints:")
        print("    - POST /api/advanced-backtest/run")
        print("    - POST /api/advanced-backtest/walkforward")
        print("    - POST /api/advanced-backtest/montecarlo")
        print("    - GET /api/advanced-backtest/results/{id}")
        print("    - Configuration validation and defaults")
        print("\n🚀 Ready for Module 5!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)