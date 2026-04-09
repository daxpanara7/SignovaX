#!/usr/bin/env python3
"""
SMC Trading System - Quick Test Script
Tests core functionality without starting the full server
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.market_data_service import MarketDataService
from app.services.smc_strategy import SMCStrategy
from app.services.signal_generator import SignalGenerator
from app.services.backtest_engine import BacktestEngine
import asyncio

async def test_system():
    """Test core system functionality"""
    print("🧪 Testing SMC Trading System Components...\n")
    
    # Test 1: Market Data Service
    print("1️⃣ Testing Market Data Service...")
    try:
        market_service = MarketDataService()
        market_data = await market_service.fetch_ohlcv("BTCUSDT", "1h", 100)
        print(f"   ✅ Fetched {len(market_data.data)} candles for {market_data.symbol}")
        print(f"   📊 Price range: ${market_data.data[0].close:.2f} - ${market_data.data[-1].close:.2f}")
    except Exception as e:
        print(f"   ❌ Market data test failed: {e}")
        return False
    
    # Test 2: SMC Strategy
    print("\n2️⃣ Testing SMC Strategy Engine...")
    try:
        smc_strategy = SMCStrategy()
        df = market_service.to_dataframe(market_data)
        analysis = smc_strategy.analyze(df, "BTCUSDT", "1h")
        
        print(f"   ✅ SMC Analysis completed")
        print(f"   🎯 Liquidity Zones: {len(analysis.liquidity_zones)}")
        print(f"   📦 Order Blocks: {len(analysis.order_blocks)}")
        print(f"   🕳️  Fair Value Gaps: {len(analysis.fair_value_gaps)}")
        print(f"   📈 BOS Signals: {len(analysis.bos_signals)}")
        print(f"   🔄 CHOCH Signals: {len(analysis.choch_signals)}")
    except Exception as e:
        print(f"   ❌ SMC strategy test failed: {e}")
        return False
    
    # Test 3: Signal Generator
    print("\n3️⃣ Testing Signal Generator...")
    try:
        signal_generator = SignalGenerator()
        current_price = df['close'].iloc[-1]
        signals = signal_generator.generate_signals(analysis, current_price)
        filtered_signals = signal_generator.filter_signals(signals, 70.0)
        
        print(f"   ✅ Signal generation completed")
        print(f"   📡 Raw signals: {len(signals)}")
        print(f"   🎯 Filtered signals (>70% confidence): {len(filtered_signals)}")
        
        if filtered_signals:
            best_signal = max(filtered_signals, key=lambda s: s.confidence)
            print(f"   🏆 Best signal: {best_signal.signal_type} at ${best_signal.entry_price:.2f} ({best_signal.confidence:.1f}% confidence)")
    except Exception as e:
        print(f"   ❌ Signal generator test failed: {e}")
        return False
    
    # Test 4: Backtest Engine
    print("\n4️⃣ Testing Backtest Engine...")
    try:
        backtest_engine = BacktestEngine(10000)
        result = backtest_engine.run_backtest(df, "BTCUSDT", "1h")
        
        print(f"   ✅ Backtest completed")
        print(f"   📊 Total trades: {result.total_trades}")
        print(f"   🎯 Win rate: {result.win_rate:.1f}%")
        print(f"   💰 Total P&L: {result.total_pnl:.2f}%")
        print(f"   📉 Max drawdown: {result.max_drawdown:.2f}%")
    except Exception as e:
        print(f"   ❌ Backtest engine test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! System is working correctly.")
    print("\n📋 Next steps:")
    print("   1. Run './start_backend.sh' to start the API server")
    print("   2. Run './start_frontend.sh' to start the web interface")
    print("   3. Open http://localhost:3000 in your browser")
    
    return True

def test_imports():
    """Test that all required packages are installed"""
    print("📦 Testing package imports...")
    
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('requests', 'Requests'),
        ('ccxt', 'CCXT'),
        ('pydantic', 'Pydantic'),
        ('uvicorn', 'Uvicorn')
    ]
    
    missing_packages = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r backend/requirements.txt")
        return False
    
    print("   ✅ All packages installed correctly")
    return True

if __name__ == "__main__":
    print("🚀 SMC Trading System - Quick Test\n")
    
    # Test imports first
    if not test_imports():
        sys.exit(1)
    
    print()
    
    # Test system functionality
    try:
        success = asyncio.run(test_system())
        if success:
            print("\n🎯 System test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ System test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)