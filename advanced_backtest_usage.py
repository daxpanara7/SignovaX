#!/usr/bin/env python3
"""
Advanced Backtesting Engine - Usage Examples
This demonstrates how to use the Advanced Backtesting Engine
"""

# Example API Usage (when backend is running)
"""
import requests
import json

# 1. Run Advanced Backtest with Realistic Trade Simulation
backtest_config = {
    "config": {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "initial_capital": 10000.0,
        "trade_simulator": {
            "slippage_pct": 0.0005,    # 0.05% slippage
            "commission_pct": 0.001,   # 0.1% commission
            "spread_pips": 2.0
        },
        "risk_per_trade": 0.01,        # 1% risk per trade
        "min_confidence": 75.0,
        "enable_compounding": True,
        "max_concurrent_trades": 1
    }
}

response = requests.post("http://localhost:8000/api/advanced-backtest/run", json=backtest_config)
result = response.json()

print(f"Backtest Results for {result['symbol']}:")
print(f"Total Return: {result['metrics']['total_return_pct']:.2f}%")
print(f"Win Rate: {result['metrics']['win_rate']:.2f}%")
print(f"Profit Factor: {result['metrics']['profit_factor']:.2f}")
print(f"Sharpe Ratio: {result['metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result['metrics']['max_drawdown_pct']:.2f}%")
print(f"Total Trades: {result['metrics']['total_trades']}")
print(f"Expectancy: {result['metrics']['expectancy']:.3f} R")

# 2. Run Walk-Forward Testing
walkforward_config = {
    "config": backtest_config["config"],
    "n_splits": 5
}

response = requests.post("http://localhost:8000/api/advanced-backtest/walkforward", json=walkforward_config)
wf_result = response.json()

print(f"\\nWalk-Forward Test Results:")
print(f"Number of Periods: {wf_result['n_splits']}")
print(f"Consistency Score: {wf_result['consistency_score']:.2f}/100")
print(f"Degradation Factor: {wf_result['degradation_factor']:.4f}")

for i, period in enumerate(wf_result['per_period_results']):
    print(f"Period {i+1}: {period['total_return_pct']:.2f}% return, {period['win_rate']:.1f}% win rate")

# 3. Run Monte Carlo Simulation
# First, get a backtest ID from a previous run
backtest_id = "your-backtest-id-here"  # From previous backtest

montecarlo_config = {
    "backtest_id": backtest_id,
    "n_simulations": 1000
}

response = requests.post("http://localhost:8000/api/advanced-backtest/montecarlo", json=montecarlo_config)
mc_result = response.json()

print(f"\\nMonte Carlo Simulation Results:")
print(f"Simulations: {mc_result['n_simulations']}")
print(f"Median Return: {mc_result['median_return']:.2f}%")
print(f"Best Return (95%): {mc_result['best_return_95pct']:.2f}%")
print(f"Worst Drawdown (95%): {mc_result['worst_drawdown_95pct']:.2f}%")
print(f"Ruin Probability: {mc_result['ruin_probability']:.2f}%")

# 4. Get Saved Backtest Result
response = requests.get(f"http://localhost:8000/api/advanced-backtest/results/{backtest_id}")
saved_result = response.json()

print(f"\\nSaved Backtest Result:")
print(f"ID: {saved_result['id']}")
print(f"Symbol: {saved_result['symbol']}")
print(f"Timestamp: {saved_result['timestamp']}")
print(f"Total Trades: {len(saved_result['trade_log'])}")

# 5. Get Default Configuration
response = requests.get("http://localhost:8000/api/advanced-backtest/config/default")
default_config = response.json()

print(f"\\nDefault Configuration:")
print(json.dumps(default_config['default_config'], indent=2))

# 6. Validate Configuration
response = requests.post("http://localhost:8000/api/advanced-backtest/config/validate", json=backtest_config["config"])
validation = response.json()

print(f"\\nConfiguration Validation:")
print(f"Valid: {validation['valid']}")
if validation['warnings']:
    print(f"Warnings: {validation['warnings']}")
if validation['errors']:
    print(f"Errors: {validation['errors']}")
"""

# Example Direct Usage (with dependencies installed)
"""
import asyncio
from backend.app.services.backtester import AdvancedBacktester
from backend.app.models.backtest_models import BacktestConfig, TradeSimulatorConfig

async def run_advanced_backtest():
    # Configure realistic trade simulation
    trade_simulator = TradeSimulatorConfig(
        slippage_pct=0.0005,      # 0.05% slippage
        commission_pct=0.001,     # 0.1% commission per trade
        spread_pips=2.0           # for forex pairs
    )
    
    # Configure backtest
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframe="1h",
        initial_capital=10000.0,
        trade_simulator=trade_simulator,
        risk_per_trade=0.01,      # 1% risk per trade
        min_confidence=75.0,
        enable_compounding=True,
        max_concurrent_trades=1
    )
    
    # Initialize backtester
    backtester = AdvancedBacktester()
    
    # Run advanced backtest
    result = await backtester.run_backtest(config)
    
    print(f"Advanced Backtest Results:")
    print(f"Symbol: {result.symbol}")
    print(f"Period: {result.start_date} to {result.end_date}")
    print(f"Total Return: {result.metrics.total_return_pct:.2f}%")
    print(f"Win Rate: {result.metrics.win_rate:.2f}%")
    print(f"Profit Factor: {result.metrics.profit_factor:.2f}")
    print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
    print(f"Sortino Ratio: {result.metrics.sortino_ratio:.2f}")
    print(f"Calmar Ratio: {result.metrics.calmar_ratio:.2f}")
    print(f"Max Drawdown: {result.metrics.max_drawdown_pct:.2f}%")
    print(f"Expectancy: {result.metrics.expectancy:.3f} R")
    print(f"Average Win: {result.metrics.avg_win_r:.2f} R")
    print(f"Average Loss: {result.metrics.avg_loss_r:.2f} R")
    print(f"Best Trade: ${result.metrics.best_trade:.2f}")
    print(f"Worst Trade: ${result.metrics.worst_trade:.2f}")
    print(f"Benchmark Comparison: {result.metrics.benchmark_comparison:.2f}%")
    
    # Run walk-forward test
    wf_result = await backtester.walk_forward_test(config, n_splits=5)
    
    print(f"\\nWalk-Forward Test:")
    print(f"Consistency Score: {wf_result.consistency_score:.2f}/100")
    print(f"Degradation Factor: {wf_result.degradation_factor:.4f}")
    
    # Run Monte Carlo simulation
    mc_result = backtester.monte_carlo(result.trades, n_simulations=1000)
    
    print(f"\\nMonte Carlo Simulation:")
    print(f"Median Return: {mc_result.median_return:.2f}%")
    print(f"Ruin Probability: {mc_result.ruin_probability:.2f}%")
    print(f"95% Confidence Interval: {mc_result.confidence_intervals['95%']}")

# Run the backtest
# asyncio.run(run_advanced_backtest())
"""

print("📋 Advanced Backtesting Engine Usage Examples")
print("=" * 60)
print("✅ Module 4 Implementation Complete!")
print()
print("🔧 To use the Advanced Backtesting Engine:")
print("1. Install dependencies: pip install -r backend/requirements.txt")
print("2. Start backend: python backend/run.py")
print("3. Use API endpoints or import classes directly")
print()
print("🎯 Professional-Grade Features:")
print()
print("💰 Realistic Trade Simulation:")
print("• BUY entry = signal_entry * (1 + 0.05% slippage)")
print("• SELL entry = signal_entry * (1 - 0.05% slippage)")
print("• Commission: 0.1% deducted on open and close")
print("• Spread handling for forex pairs")
print()
print("🔄 Walk-Forward Testing:")
print("• Split data into n equal periods")
print("• Train on 70%, test on 30% for each split")
print("• Consistency and degradation analysis")
print("• Aggregate results across all periods")
print()
print("🎲 Monte Carlo Simulation:")
print("• Randomly shuffle historical trade order")
print("• 1000+ simulations for statistical analysis")
print("• Ruin probability calculation")
print("• 95% and 99% confidence intervals")
print("• Sample equity curves for visualization")
print()
print("📊 Professional Metrics:")
print("• Sharpe Ratio (annualized risk-adjusted return)")
print("• Sortino Ratio (downside deviation only)")
print("• Calmar Ratio (return / max drawdown)")
print("• R-multiple analysis (avg win/loss in R)")
print("• Expectancy (average R per trade)")
print("• VaR and CVaR (Value at Risk)")
print("• Ulcer Index (downside volatility)")
print("• Recovery Factor, Payoff Ratio, Sterling Ratio")
print("• Benchmark comparison vs buy & hold")
print()
print("🗄️ Database Storage:")
print("• SQLite storage for all backtest results")
print("• JSON serialization of configs and metrics")
print("• Retrieve saved results by ID")
print("• Historical backtest tracking")
print()
print("🌐 API Endpoints:")
print("• POST /api/advanced-backtest/run")
print("• POST /api/advanced-backtest/walkforward")
print("• POST /api/advanced-backtest/montecarlo")
print("• GET /api/advanced-backtest/results/{id}")
print("• GET /api/advanced-backtest/config/default")
print("• POST /api/advanced-backtest/config/validate")
print()
print("🚀 Ready for Module 5!")