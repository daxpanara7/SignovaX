"""
Advanced Backtesting API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.services.backtester import AdvancedBacktester
from app.models.backtest_models import (
    BacktestConfig, AdvancedBacktestResult, WalkForwardResult,
    MonteCarloResult, BacktestSummary, TradeSimulatorConfig
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize advanced backtester
backtester = AdvancedBacktester()


class AdvancedBacktestRequest(BaseModel):
    """Request model for advanced backtesting"""
    config: BacktestConfig


class WalkForwardRequest(BaseModel):
    """Request model for walk-forward testing"""
    config: BacktestConfig
    n_splits: int = 5


class MonteCarloRequest(BaseModel):
    """Request model for Monte Carlo simulation"""
    backtest_id: str  # ID of existing backtest result
    n_simulations: int = 1000


@router.post("/run", response_model=AdvancedBacktestResult)
async def run_advanced_backtest(request: AdvancedBacktestRequest):
    """
    Run advanced backtest with professional-grade features
    
    Features:
    - Realistic trade simulation with slippage and commissions
    - Professional metrics (Sharpe, Sortino, Calmar ratios)
    - R-multiple analysis and expectancy calculations
    - Comprehensive risk analysis (VaR, CVaR, Ulcer Index)
    - Benchmark comparison and drawdown analysis
    - Monthly/yearly return breakdowns
    
    Args:
        request: Advanced backtesting configuration
        
    Returns:
        Complete backtesting result with professional metrics
    """
    try:
        logger.info(f"Advanced backtest request: {request.config.symbol} {request.config.timeframe}")
        
        # Validate configuration
        if request.config.initial_capital <= 0:
            raise HTTPException(status_code=400, detail="Initial capital must be positive")
        
        if request.config.risk_per_trade <= 0 or request.config.risk_per_trade > 0.1:
            raise HTTPException(status_code=400, detail="Risk per trade must be between 0 and 10%")
        
        # Run advanced backtest
        result = await backtester.run_backtest(request.config)
        
        logger.info(f"Advanced backtest complete: {result.metrics.total_trades} trades, {result.metrics.total_return_pct:.2f}% return")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in advanced backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Advanced backtest failed: {str(e)}")


@router.post("/walkforward", response_model=WalkForwardResult)
async def run_walk_forward_test(request: WalkForwardRequest):
    """
    Run walk-forward testing for strategy validation
    
    Walk-forward testing:
    - Splits data into n equal periods
    - For each split: trains on 70%, tests on 30%
    - Runs strategy on each test period independently
    - Aggregates results across all splits
    - Provides consistency and degradation analysis
    
    Args:
        request: Walk-forward testing configuration
        
    Returns:
        Walk-forward results with per-period and overall metrics
    """
    try:
        logger.info(f"Walk-forward test request: {request.config.symbol}, {request.n_splits} splits")
        
        if request.n_splits < 2 or request.n_splits > 20:
            raise HTTPException(status_code=400, detail="Number of splits must be between 2 and 20")
        
        # Run walk-forward test
        result = await backtester.walk_forward_test(request.config, request.n_splits)
        
        logger.info(f"Walk-forward test complete: {len(result.per_period_results)} periods analyzed")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in walk-forward test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Walk-forward test failed: {str(e)}")


@router.post("/montecarlo", response_model=MonteCarloResult)
async def run_monte_carlo_simulation(request: MonteCarloRequest):
    """
    Run Monte Carlo simulation on historical trade results
    
    Monte Carlo simulation:
    - Takes historical trade results (W/L, R multiples)
    - Randomly shuffles trade order n times
    - Calculates equity curve for each simulation
    - Provides statistical analysis of possible outcomes
    - Calculates ruin probability and confidence intervals
    
    Args:
        request: Monte Carlo simulation configuration
        
    Returns:
        Monte Carlo results with statistical analysis
    """
    try:
        logger.info(f"Monte Carlo simulation request: {request.backtest_id}, {request.n_simulations} simulations")
        
        if request.n_simulations < 100 or request.n_simulations > 10000:
            raise HTTPException(status_code=400, detail="Number of simulations must be between 100 and 10,000")
        
        # Get saved backtest result
        saved_result = backtester.get_saved_result(request.backtest_id)
        if not saved_result:
            raise HTTPException(status_code=404, detail="Backtest result not found")
        
        # Parse trade log
        import json
        trade_data = json.loads(saved_result.trade_log_json)
        
        # Convert to TradeResult objects (simplified)
        from app.models.backtest_models import TradeResult
        trades = []
        for trade_dict in trade_data:
            # Create simplified TradeResult for Monte Carlo
            trade = TradeResult(
                entry_time=trade_dict['entry_time'],
                exit_time=trade_dict['exit_time'],
                signal_type=trade_dict['signal_type'],
                entry_price=trade_dict['entry_price'],
                exit_price=trade_dict['exit_price'],
                signal_entry_price=trade_dict.get('signal_entry_price', trade_dict['entry_price']),
                signal_exit_price=trade_dict.get('signal_exit_price', trade_dict['exit_price']),
                position_size=trade_dict.get('position_size', 1.0),
                gross_pnl=trade_dict.get('gross_pnl', trade_dict.get('net_pnl', 0)),
                slippage_cost=trade_dict.get('slippage_cost', 0),
                commission_cost=trade_dict.get('commission_cost', 0),
                net_pnl=trade_dict.get('net_pnl', 0),
                pnl_percent=trade_dict.get('pnl_percent', 0),
                r_multiple=trade_dict.get('r_multiple', trade_dict.get('pnl_percent', 0) / 100),
                exit_reason=trade_dict.get('exit_reason', 'Unknown'),
                confidence=trade_dict.get('confidence', 75.0),
                reasoning=trade_dict.get('reasoning', ''),
                trade_duration_hours=trade_dict.get('trade_duration_hours', 24.0)
            )
            trades.append(trade)
        
        # Run Monte Carlo simulation
        result = backtester.monte_carlo(trades, request.n_simulations)
        
        logger.info(f"Monte Carlo simulation complete: {request.n_simulations} simulations on {len(trades)} trades")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in Monte Carlo simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Monte Carlo simulation failed: {str(e)}")


@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """
    Fetch saved backtest result by ID
    
    Args:
        backtest_id: Unique identifier of the backtest
        
    Returns:
        Saved backtest result with all data
    """
    try:
        result = backtester.get_saved_result(backtest_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Backtest result not found")
        
        # Parse JSON data for response
        import json
        
        return {
            "id": result.id,
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "timestamp": result.timestamp,
            "config": json.loads(result.config_json),
            "metrics": json.loads(result.metrics_json),
            "trade_log": json.loads(result.trade_log_json),
            "equity_curve": json.loads(result.equity_curve_json),
            "summary": {
                "total_return_pct": result.total_return_pct,
                "max_drawdown_pct": result.max_drawdown_pct
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving backtest result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve result: {str(e)}")


@router.get("/results")
async def list_backtest_results(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    limit: int = Query(20, description="Maximum number of results")
):
    """
    List saved backtest results with optional filtering
    
    Args:
        symbol: Optional symbol filter
        timeframe: Optional timeframe filter
        limit: Maximum number of results to return
        
    Returns:
        List of backtest summaries
    """
    try:
        # This would require additional database query methods
        # For now, return a placeholder response
        return {
            "message": "Backtest results listing",
            "filters": {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit
            },
            "note": "Full implementation requires additional database queries"
        }
        
    except Exception as e:
        logger.error(f"Error listing backtest results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list results: {str(e)}")


@router.get("/config/default")
async def get_default_config():
    """Get default backtesting configuration"""
    return {
        "default_config": BacktestConfig(
            symbol="BTCUSDT",
            timeframe="1h",
            initial_capital=10000.0,
            trade_simulator=TradeSimulatorConfig(),
            min_confidence=75.0,
            risk_per_trade=0.01,
            enable_compounding=True,
            max_concurrent_trades=1
        ).dict(),
        "description": "Default configuration for advanced backtesting",
        "trade_simulator_explanation": {
            "slippage_pct": "0.05% slippage applied to entry and exit prices",
            "commission_pct": "0.1% commission deducted from P&L on open and close",
            "spread_pips": "2 pip spread for forex pairs (not currently used)"
        }
    }


@router.post("/config/validate")
async def validate_backtest_config(config: BacktestConfig):
    """Validate backtesting configuration"""
    try:
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Validate basic parameters
        if config.initial_capital <= 0:
            validation_results["errors"].append("Initial capital must be positive")
            validation_results["valid"] = False
        
        if config.risk_per_trade <= 0 or config.risk_per_trade > 0.1:
            validation_results["errors"].append("Risk per trade must be between 0 and 10%")
            validation_results["valid"] = False
        
        if config.min_confidence < 0 or config.min_confidence > 100:
            validation_results["errors"].append("Minimum confidence must be between 0 and 100")
            validation_results["valid"] = False
        
        # Validate trade simulator config
        if config.trade_simulator.slippage_pct < 0 or config.trade_simulator.slippage_pct > 0.01:
            validation_results["warnings"].append("Slippage percentage seems unusually high (>1%)")
        
        if config.trade_simulator.commission_pct < 0 or config.trade_simulator.commission_pct > 0.01:
            validation_results["warnings"].append("Commission percentage seems unusually high (>1%)")
        
        # Additional validations
        if config.max_concurrent_trades > 10:
            validation_results["warnings"].append("High number of concurrent trades may affect results")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Config validation failed: {str(e)}")