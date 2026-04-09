from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from app.services.market_data_service import MarketDataService
from app.services.backtest_engine import BacktestEngine
from app.models.signals import BacktestResult

router = APIRouter()
market_data_service = MarketDataService()

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 10000.0

@router.post("/run", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    """Run backtest on historical data"""
    try:
        # Fetch historical data (more data for backtesting)
        market_data = await market_data_service.fetch_ohlcv(
            request.symbol, 
            request.timeframe, 
            1000  # More data for comprehensive backtest
        )
        
        # Convert to DataFrame
        df = market_data_service.to_dataframe(market_data)
        
        # Initialize backtest engine
        backtest_engine = BacktestEngine(request.initial_capital)
        
        # Set default date range if not provided
        start_date = request.start_date or df.index[0]
        end_date = request.end_date or df.index[-1]
        
        # Run backtest
        result = backtest_engine.run_backtest(
            df, 
            request.symbol, 
            request.timeframe,
            start_date,
            end_date
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@router.get("/quick/{symbol}")
async def quick_backtest(symbol: str, timeframe: str = "1h", days: int = 30):
    """Run a quick backtest for the last N days"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        request = BacktestRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0
        )
        
        result = await run_backtest(request)
        
        # Add some additional quick stats
        return {
            "backtest_result": result,
            "quick_stats": {
                "period_days": days,
                "avg_trades_per_day": result.total_trades / days if days > 0 else 0,
                "profit_factor": _calculate_profit_factor(result.trade_logs),
                "best_trade": max(result.trade_logs, key=lambda x: x['pnl_percent'])['pnl_percent'] if result.trade_logs else 0,
                "worst_trade": min(result.trade_logs, key=lambda x: x['pnl_percent'])['pnl_percent'] if result.trade_logs else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick backtest failed: {str(e)}")

@router.get("/performance/{symbol}")
async def get_performance_metrics(symbol: str, timeframe: str = "1h"):
    """Get detailed performance metrics for a symbol"""
    try:
        # Run backtest for last 60 days
        result = await quick_backtest(symbol, timeframe, 60)
        
        backtest_result = result["backtest_result"]
        
        # Calculate additional metrics
        trades = backtest_result.trade_logs
        
        performance_metrics = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_return_percent": backtest_result.total_pnl,
            "annualized_return": (backtest_result.total_pnl / 60) * 365,  # Rough annualization
            "win_rate": backtest_result.win_rate,
            "profit_factor": _calculate_profit_factor(trades),
            "max_drawdown": backtest_result.max_drawdown,
            "sharpe_ratio": backtest_result.sharpe_ratio,
            "total_trades": backtest_result.total_trades,
            "avg_trade_duration": _calculate_avg_trade_duration(trades),
            "consecutive_wins": _calculate_max_consecutive_wins(trades),
            "consecutive_losses": _calculate_max_consecutive_losses(trades)
        }
        
        return performance_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

def _calculate_profit_factor(trades):
    """Calculate profit factor (gross profit / gross loss)"""
    if not trades:
        return 0
    
    gross_profit = sum(t['pnl_percent'] for t in trades if t['pnl_percent'] > 0)
    gross_loss = abs(sum(t['pnl_percent'] for t in trades if t['pnl_percent'] < 0))
    
    return gross_profit / gross_loss if gross_loss > 0 else float('inf')

def _calculate_avg_trade_duration(trades):
    """Calculate average trade duration in hours"""
    if not trades:
        return 0
    
    durations = []
    for trade in trades:
        entry_time = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00'))
        exit_time = datetime.fromisoformat(trade['exit_time'].replace('Z', '+00:00'))
        duration = (exit_time - entry_time).total_seconds() / 3600  # Convert to hours
        durations.append(duration)
    
    return sum(durations) / len(durations)

def _calculate_max_consecutive_wins(trades):
    """Calculate maximum consecutive winning trades"""
    if not trades:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for trade in trades:
        if trade['pnl_percent'] > 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive

def _calculate_max_consecutive_losses(trades):
    """Calculate maximum consecutive losing trades"""
    if not trades:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for trade in trades:
        if trade['pnl_percent'] <= 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive