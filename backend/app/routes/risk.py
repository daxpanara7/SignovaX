"""
Risk Management API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.services.risk_manager import RiskManager, RiskConfig
from app.models.risk_models import (
    RiskMetrics, PositionSizeRequest, PositionSizeResponse,
    SignalValidationRequest, RiskValidationResult, CircuitBreakerStatus,
    DailyRiskLog
)
from app.models.signals import TradingSignal, SignalType

router = APIRouter()
logger = logging.getLogger(__name__)

# Global risk manager instance
risk_manager = RiskManager()


class RiskConfigUpdate(BaseModel):
    """Request model for updating risk configuration"""
    account_balance: Optional[float] = None
    risk_per_trade: Optional[float] = None
    max_daily_loss: Optional[float] = None
    min_risk_reward: Optional[float] = None
    max_concurrent_trades: Optional[int] = None
    max_correlated_trades: Optional[int] = None


@router.get("/status", response_model=RiskMetrics)
async def get_risk_status():
    """
    Get current risk management status and metrics
    
    Returns comprehensive risk metrics including:
    - Account balance and daily P&L
    - Trade counts and limits
    - Circuit breaker status
    - Risk configuration
    """
    try:
        logger.info("Getting risk status")
        metrics = risk_manager.get_risk_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting risk status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk status: {str(e)}")


@router.get("/position-size", response_model=PositionSizeResponse)
async def calculate_position_size(
    entry: float = Query(..., description="Entry price"),
    sl: float = Query(..., description="Stop loss price"),
    account_balance: Optional[float] = Query(None, description="Account balance (uses config if not provided)"),
    risk_pct: Optional[float] = Query(None, description="Risk percentage (uses config if not provided)")
):
    """
    Calculate position size based on entry, stop loss, and risk parameters
    
    Formula:
    - risk_amount = balance * risk_pct
    - pip_risk = abs(entry - sl)
    - position_size = risk_amount / pip_risk
    
    Args:
        entry: Entry price
        sl: Stop loss price
        account_balance: Optional account balance override
        risk_pct: Optional risk percentage override
        
    Returns:
        PositionSizeResponse with calculated position size and risk metrics
    """
    try:
        logger.info(f"Calculating position size: Entry {entry}, SL {sl}")
        
        if entry <= 0 or sl <= 0:
            raise HTTPException(status_code=400, detail="Entry and stop loss must be positive")
        
        if entry == sl:
            raise HTTPException(status_code=400, detail="Entry price cannot equal stop loss")
        
        result = risk_manager.calculate_position_size(entry, sl, account_balance, risk_pct)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating position size: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Position size calculation failed: {str(e)}")


@router.post("/validate", response_model=RiskValidationResult)
async def validate_signal(request: SignalValidationRequest):
    """
    Validate a trading signal against all risk management rules
    
    Validation checks:
    - Risk-reward ratio meets minimum requirement
    - Daily loss limits not exceeded
    - Concurrent trade limits not exceeded
    - Correlation limits not violated
    - Circuit breaker not active
    
    Args:
        request: Signal validation request with trade details
        
    Returns:
        RiskValidationResult with approval status and detailed reasoning
    """
    try:
        logger.info(f"Validating signal: {request.symbol} {request.signal_type}")
        
        # Convert request to TradingSignal
        signal = TradingSignal(
            symbol=request.symbol,
            timeframe=request.timeframe,
            signal_type=SignalType(request.signal_type.upper()),
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            confidence=100.0,  # Default confidence
            reasoning="Risk validation check",
            timestamp=datetime.now()
        )
        
        # Validate signal
        result = risk_manager.validate_signal(signal)
        
        logger.info(f"Signal validation result: {result.approved} - {result.reason}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signal validation failed: {str(e)}")


@router.get("/circuit-breaker", response_model=CircuitBreakerStatus)
async def check_circuit_breaker():
    """
    Check current circuit breaker status
    
    Circuit breaker triggers when daily loss exceeds maximum allowed percentage.
    When active, all new trading is halted until the next trading day.
    
    Returns:
        CircuitBreakerStatus with current status and trigger details
    """
    try:
        logger.info("Checking circuit breaker status")
        status = risk_manager.check_circuit_breaker()
        return status
        
    except Exception as e:
        logger.error(f"Error checking circuit breaker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Circuit breaker check failed: {str(e)}")


@router.get("/correlations")
async def get_correlation_groups():
    """
    Get asset correlation groups used for risk management
    
    Returns correlation groups to prevent over-exposure to correlated assets.
    Maximum correlated trades per group is enforced by risk manager.
    
    Returns:
        Dict mapping correlation group names to symbol lists
    """
    try:
        correlations = risk_manager.get_correlated_pairs()
        return {
            "correlation_groups": correlations,
            "max_correlated_trades": risk_manager.config.max_correlated_trades,
            "description": "Asset correlation groups for risk management"
        }
        
    except Exception as e:
        logger.error(f"Error getting correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get correlations: {str(e)}")


@router.get("/daily-logs", response_model=List[DailyRiskLog])
async def get_daily_risk_logs(days: int = Query(30, ge=1, le=365, description="Number of days to retrieve")):
    """
    Get daily risk management logs
    
    Returns historical daily risk data including:
    - Daily P&L and balance changes
    - Trade counts
    - Circuit breaker triggers
    - Maximum drawdown
    
    Args:
        days: Number of days to retrieve (1-365)
        
    Returns:
        List of DailyRiskLog entries
    """
    try:
        logger.info(f"Getting daily risk logs for {days} days")
        logs = risk_manager.get_daily_logs(days)
        return logs
        
    except Exception as e:
        logger.error(f"Error getting daily logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily logs: {str(e)}")


@router.post("/config")
async def update_risk_config(config_update: RiskConfigUpdate):
    """
    Update risk management configuration
    
    Allows updating risk parameters such as:
    - Account balance
    - Risk per trade percentage
    - Maximum daily loss percentage
    - Minimum risk-reward ratio
    - Trade limits
    
    Args:
        config_update: Risk configuration updates
        
    Returns:
        Updated risk configuration
    """
    try:
        logger.info("Updating risk configuration")
        
        # Update configuration
        if config_update.account_balance is not None:
            risk_manager.config.account_balance = config_update.account_balance
        if config_update.risk_per_trade is not None:
            risk_manager.config.risk_per_trade = config_update.risk_per_trade
        if config_update.max_daily_loss is not None:
            risk_manager.config.max_daily_loss = config_update.max_daily_loss
        if config_update.min_risk_reward is not None:
            risk_manager.config.min_risk_reward = config_update.min_risk_reward
        if config_update.max_concurrent_trades is not None:
            risk_manager.config.max_concurrent_trades = config_update.max_concurrent_trades
        if config_update.max_correlated_trades is not None:
            risk_manager.config.max_correlated_trades = config_update.max_correlated_trades
        
        # Return updated configuration
        return {
            "account_balance": risk_manager.config.account_balance,
            "risk_per_trade": risk_manager.config.risk_per_trade,
            "max_daily_loss": risk_manager.config.max_daily_loss,
            "min_risk_reward": risk_manager.config.min_risk_reward,
            "max_concurrent_trades": risk_manager.config.max_concurrent_trades,
            "max_correlated_trades": risk_manager.config.max_correlated_trades,
            "message": "Risk configuration updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating risk config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update risk config: {str(e)}")


@router.post("/reset-daily")
async def reset_daily_state():
    """
    Reset daily risk state (for new trading day)
    
    Resets:
    - Circuit breaker status
    - Daily P&L tracking
    - Trade counters
    
    This should be called at the start of each trading day.
    
    Returns:
        Confirmation message
    """
    try:
        logger.info("Resetting daily risk state")
        risk_manager.reset_daily_state()
        
        return {
            "message": "Daily risk state reset successfully",
            "timestamp": datetime.now().isoformat(),
            "circuit_breaker_active": False
        }
        
    except Exception as e:
        logger.error(f"Error resetting daily state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset daily state: {str(e)}")


# Import datetime for timestamp
from datetime import datetime