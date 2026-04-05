#!/usr/bin/env python3
"""
Risk Management Module - Usage Examples
This demonstrates how to use the Risk Management System
"""

# Example API Usage (when backend is running)
"""
import requests
import json

# 1. Get Risk Status
response = requests.get("http://localhost:8000/api/risk/status")
risk_status = response.json()
print(f"Account Balance: ${risk_status['account_balance']}")
print(f"Daily P&L: ${risk_status['daily_pnl']}")
print(f"Circuit Breaker Active: {risk_status['circuit_breaker_active']}")

# 2. Calculate Position Size
params = {
    "entry": 50000.0,
    "sl": 49000.0,
    "risk_pct": 0.01
}
response = requests.get("http://localhost:8000/api/risk/position-size", params=params)
position_data = response.json()
print(f"Position Size: {position_data['position_size']} units")
print(f"Risk Amount: ${position_data['risk_amount']}")

# 3. Validate Signal
signal_data = {
    "symbol": "BTCUSDT",
    "signal_type": "BUY",
    "entry_price": 50000.0,
    "stop_loss": 49000.0,
    "take_profit": 52000.0,
    "timeframe": "1h"
}
response = requests.post("http://localhost:8000/api/risk/validate", json=signal_data)
validation = response.json()
print(f"Signal Approved: {validation['approved']}")
print(f"Reason: {validation['reason']}")

# 4. Check Circuit Breaker
response = requests.get("http://localhost:8000/api/risk/circuit-breaker")
cb_status = response.json()
print(f"Circuit Breaker Active: {cb_status['active']}")
print(f"Daily Loss %: {cb_status['daily_loss_pct']:.2%}")

# 5. Get Correlation Groups
response = requests.get("http://localhost:8000/api/risk/correlations")
correlations = response.json()
print("Correlation Groups:", correlations['correlation_groups'])

# 6. Get Daily Risk Logs
response = requests.get("http://localhost:8000/api/risk/daily-logs?days=7")
logs = response.json()
for log in logs:
    print(f"Date: {log['date']}, P&L: ${log['daily_pnl']}, Trades: {log['trades_taken']}")
"""

# Example Direct Usage (with dependencies installed)
"""
import asyncio
from backend.app.services.risk_manager import RiskManager, RiskConfig
from backend.app.models.signals import TradingSignal, SignalType
from datetime import datetime

async def test_risk_management():
    # Initialize risk manager
    config = RiskConfig(
        account_balance=10000.0,
        risk_per_trade=0.01,
        max_daily_loss=0.05,
        min_risk_reward=2.0,
        max_concurrent_trades=3,
        max_correlated_trades=1
    )
    
    risk_manager = RiskManager(config)
    
    # Calculate position size
    position_calc = risk_manager.calculate_position_size(
        entry=50000.0,
        sl=49000.0
    )
    print(f"Position Size: {position_calc.position_size} units")
    print(f"Risk Amount: ${position_calc.risk_amount}")
    
    # Validate a signal
    signal = TradingSignal(
        symbol="BTCUSDT",
        timeframe="1h",
        signal_type=SignalType.BUY,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        confidence=85.0,
        reasoning="SMC analysis",
        timestamp=datetime.now()
    )
    
    validation = risk_manager.validate_signal(signal)
    print(f"Signal Approved: {validation.approved}")
    print(f"Reason: {validation.reason}")
    
    # Check circuit breaker
    cb_status = risk_manager.check_circuit_breaker()
    print(f"Circuit Breaker Active: {cb_status.active}")
    
    # Get risk metrics
    metrics = risk_manager.get_risk_metrics()
    print(f"Account Balance: ${metrics.account_balance}")
    print(f"Concurrent Trades: {metrics.concurrent_trades}/{metrics.max_concurrent_trades}")

# Run the test
# asyncio.run(test_risk_management())
"""

print("📋 Risk Management Module Usage Examples")
print("=" * 60)
print("✅ Module 2 Implementation Complete!")
print()
print("🔧 To use the Risk Management System:")
print("1. Install dependencies: pip install -r backend/requirements.txt")
print("2. Start backend: python backend/run.py")
print("3. Use API endpoints or import classes directly")
print()
print("🎯 Key Features:")
print("• Position size calculation with risk-based formula")
print("• Signal validation with multiple risk checks:")
print("  - R:R ratio validation (minimum 2:1)")
print("  - Daily loss limit enforcement")
print("  - Concurrent trade limits")
print("  - Correlation group management")
print("• Circuit breaker system (5% daily loss limit)")
print("• SQLite database for daily risk logging")
print("• Integration with signal generation")
print("• RESTful API endpoints")
print()
print("🛡️ Risk Protection Rules:")
print("• Every signal must pass validate_signal() before execution")
print("• Circuit breaker halts trading at 5% daily loss")
print("• Maximum 3 concurrent trades")
print("• Maximum 1 correlated trade per asset group")
print("• Minimum 2:1 risk-reward ratio required")
print()
print("🚀 Ready for Module 3!")