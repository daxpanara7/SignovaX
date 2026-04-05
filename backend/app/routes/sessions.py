"""
Session Management API Routes
Provides endpoints for market session analysis and chart overlays
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from app.auth.auth import get_current_user, UserInfo
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter
from app.services.session_manager import session_manager, SessionBox, SessionStats
from app.services.market_data_service import MarketDataService

logger = get_logger(__name__)
router = APIRouter()

# Request/Response Models
class SessionStatusResponse(BaseModel):
    """Response model for current session status"""
    current_session: str
    is_trading_hours: bool
    is_overlap: bool
    session_info: Optional[Dict[str, Any]] = None
    optimal_pairs: List[str] = []
    next_session: Optional[str] = None
    time_to_next_session: Optional[str] = None

class SessionBoxResponse(BaseModel):
    """Response model for session boxes"""
    session: str
    start_time: str
    end_time: str
    high: float
    low: float
    color: str
    range_pips: float
    is_active: bool

class SessionStatsResponse(BaseModel):
    """Response model for session statistics"""
    session: str
    total_signals: int
    winning_signals: int
    win_rate: float
    avg_range_size: float
    avg_volume: float
    best_pairs: List[str]

class TradingTimeCheckRequest(BaseModel):
    """Request model for trading time validation"""
    signal_type: str
    utc_time: Optional[str] = None  # ISO format, defaults to current time

@router.get("/data")
@limiter.limit("60/minute")
async def get_session_data(
    request: Request,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get session data for a specific date or current session
    
    Returns session information, trading hours, and market activity
    """
    try:
        current_time = datetime.utcnow()
        current_session = session_manager.get_current_session(current_time)
        
        # Basic session data
        session_data = {
            "date": date or current_time.strftime("%Y-%m-%d"),
            "current_session": current_session.name if current_session else "None",
            "is_trading_hours": current_session is not None,
            "session_overlap": False,  # Simplified for now
            "optimal_pairs": ["BTCUSDT", "ETHUSDT", "EURUSD", "GBPUSD"],
            "session_times": {
                "sydney": {"open": "22:00", "close": "07:00", "timezone": "UTC"},
                "tokyo": {"open": "00:00", "close": "09:00", "timezone": "UTC"},
                "london": {"open": "08:00", "close": "17:00", "timezone": "UTC"},
                "new_york": {"open": "13:00", "close": "22:00", "timezone": "UTC"}
            },
            "market_activity": "high" if current_session else "low",
            "timestamp": current_time.isoformat()
        }
        
        return session_data
        
    except Exception as e:
        logger.error(f"Failed to get session data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session data: {str(e)}")

@router.get("/status", response_model=SessionStatusResponse)
@limiter.limit("60/minute")
async def get_session_status(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get current market session status and information
    
    Returns:
    - Current active session
    - Whether it's trading hours
    - Session overlap status
    - Optimal pairs for current session
    - Next session information
    """
    try:
        current_time = datetime.utcnow()
        current_session = session_manager.get_current_session(current_time)
        
        # Get session info
        session_info = None
        optimal_pairs = []
        
        if current_session in session_manager.sessions:
            config = session_manager.sessions[current_session]
            session_info = {
                "name": config.name,
                "start_time": config.start_time,
                "end_time": config.end_time,
                "color": config.color,
                "timezone": config.timezone
            }
            optimal_pairs = config.pairs
        elif current_session == "overlap":
            # For overlap, combine pairs from active sessions
            optimal_pairs = []
            for session_name, config in session_manager.sessions.items():
                if session_manager._is_time_in_session(current_time.time(), config):
                    optimal_pairs.extend(config.pairs)
            optimal_pairs = list(set(optimal_pairs))  # Remove duplicates
        
        # Determine next session (simplified logic)
        next_session = None
        time_to_next = None
        
        if current_session == "off_hours":
            # Find next session
            current_hour = current_time.hour
            if current_hour < 7:
                next_session = "london"
                time_to_next = f"{7 - current_hour} hours"
            elif current_hour < 12:
                next_session = "new_york"
                time_to_next = f"{12 - current_hour} hours"
            else:
                next_session = "asia"
                time_to_next = f"{24 - current_hour} hours"
        
        response = SessionStatusResponse(
            current_session=current_session,
            is_trading_hours=current_session != "off_hours",
            is_overlap=current_session == "overlap",
            session_info=session_info,
            optimal_pairs=optimal_pairs,
            next_session=next_session,
            time_to_next_session=time_to_next
        )
        
        logger.debug(f"Session status requested by user {current_user.username}: {current_session}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.get("/boxes", response_model=List[SessionBoxResponse])
@limiter.limit("30/minute")
async def get_session_boxes(
    request: Request,
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get session boxes for chart overlay
    
    Parameters:
    - symbol: Trading symbol
    - date: Date for session boxes
    
    Returns:
    - List of session boxes with high/low ranges and colors
    - Used for drawing session rectangles on trading charts
    """
    try:
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get session boxes
        boxes = session_manager.get_session_boxes(symbol, date)
        
        # Convert to response format
        response_boxes = []
        for box in boxes:
            response_boxes.append(SessionBoxResponse(
                session=box.session,
                start_time=box.start_time,
                end_time=box.end_time,
                high=box.high,
                low=box.low,
                color=box.color,
                range_pips=box.range_pips,
                is_active=box.is_active
            ))
        
        logger.info(f"Session boxes requested for {symbol} on {date}: {len(response_boxes)} boxes")
        return response_boxes
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session boxes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session boxes: {str(e)}")

@router.get("/stats", response_model=Dict[str, SessionStatsResponse])
@limiter.limit("20/minute")
async def get_session_statistics(
    request: Request,
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get session trading statistics
    
    Parameters:
    - symbol: Trading symbol
    - days: Number of days to analyze (1-365)
    
    Returns:
    - Statistics for each session including win rates and average ranges
    - Best session identification
    - Optimal trading pairs per session
    """
    try:
        # Get session statistics
        stats = session_manager.get_session_statistics(symbol, days)
        
        # Convert to response format
        response_stats = {}
        for session_name, session_stats in stats.items():
            response_stats[session_name] = SessionStatsResponse(
                session=session_stats.session,
                total_signals=session_stats.total_signals,
                winning_signals=session_stats.winning_signals,
                win_rate=session_stats.win_rate,
                avg_range_size=session_stats.avg_range_size,
                avg_volume=session_stats.avg_volume,
                best_pairs=session_stats.best_pairs
            )
        
        logger.info(f"Session statistics requested for {symbol} over {days} days")
        return response_stats
        
    except Exception as e:
        logger.error(f"Error getting session statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session statistics: {str(e)}")

@router.post("/check-trading-time")
@limiter.limit("120/minute")
async def check_optimal_trading_time(
    request: Request,
    check_request: TradingTimeCheckRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Check if current time is optimal for trading based on signal type
    
    Parameters:
    - signal_type: Type of signal (CHOCH, BOS, OB, FVG)
    - utc_time: Optional UTC time (defaults to current time)
    
    Returns:
    - Whether the time is optimal for trading
    - Current session information
    - Reasoning for the decision
    """
    try:
        # Parse time or use current time
        if check_request.utc_time:
            try:
                utc_time = datetime.fromisoformat(check_request.utc_time.replace('Z', '+00:00'))
                if utc_time.tzinfo is not None:
                    utc_time = utc_time.replace(tzinfo=None)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UTC time format. Use ISO format")
        else:
            utc_time = datetime.utcnow()
        
        # Check if optimal trading time
        is_optimal = session_manager.is_optimal_trading_time(utc_time, check_request.signal_type)
        current_session = session_manager.get_current_session(utc_time)
        
        # Generate reasoning
        reasoning = []
        
        if current_session == "off_hours":
            reasoning.append("Market is in off-hours (no active sessions)")
        elif current_session == "overlap":
            reasoning.append("High liquidity overlap period between sessions")
        else:
            reasoning.append(f"Currently in {current_session} session")
        
        if check_request.signal_type == "CHOCH":
            if is_optimal:
                reasoning.append("CHOCH signals are optimal during session open (first 2 hours)")
            else:
                reasoning.append("CHOCH signals should only be taken during session open (first 2 hours)")
        elif check_request.signal_type in ["BOS", "OB", "FVG"]:
            if is_optimal:
                reasoning.append(f"{check_request.signal_type} signals are allowed during active sessions")
            else:
                reasoning.append(f"{check_request.signal_type} signals require active trading sessions")
        
        response = {
            "is_optimal": is_optimal,
            "signal_type": check_request.signal_type,
            "current_session": current_session,
            "utc_time": utc_time.isoformat(),
            "reasoning": reasoning,
            "session_info": session_manager.get_session_info(current_session).__dict__ if current_session in session_manager.sessions else None
        }
        
        logger.debug(f"Trading time check for {check_request.signal_type}: {is_optimal}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking trading time: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check trading time: {str(e)}")

@router.get("/pairs/{session}")
@limiter.limit("60/minute")
async def get_optimal_pairs_for_session(
    request: Request,
    session: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get optimal trading pairs for a specific session
    
    Parameters:
    - session: Session name (asia, london, new_york)
    
    Returns:
    - List of optimal trading pairs for the session
    - Session configuration details
    """
    try:
        if session not in session_manager.sessions:
            raise HTTPException(status_code=404, detail=f"Session '{session}' not found")
        
        config = session_manager.sessions[session]
        
        response = {
            "session": session,
            "optimal_pairs": config.pairs,
            "session_info": {
                "start_time": config.start_time,
                "end_time": config.end_time,
                "color": config.color,
                "timezone": config.timezone
            },
            "total_pairs": len(config.pairs)
        }
        
        logger.debug(f"Optimal pairs requested for {session} session")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimal pairs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimal pairs: {str(e)}")

@router.post("/update-stats")
@limiter.limit("300/minute")  # Higher limit for automated updates
async def update_session_statistics(
    request: Request,
    symbol: str,
    session: str,
    date: str,
    signal_won: bool,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Update session statistics with new signal result
    
    Parameters:
    - symbol: Trading symbol
    - session: Session name
    - date: Date in YYYY-MM-DD format
    - signal_won: Whether the signal was profitable
    
    This endpoint is typically called by the trading system
    to update session performance statistics.
    """
    try:
        # Validate inputs
        if session not in session_manager.sessions:
            raise HTTPException(status_code=400, detail=f"Invalid session: {session}")
        
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Update statistics
        session_manager.update_session_stats(symbol, session, date, signal_won)
        
        response = {
            "status": "success",
            "message": f"Session statistics updated for {symbol} in {session} session",
            "symbol": symbol,
            "session": session,
            "date": date,
            "signal_won": signal_won,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Session stats updated: {symbol} {session} {date} won={signal_won}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update session statistics: {str(e)}")

@router.get("/health")
async def session_health_check():
    """Health check for session management service"""
    try:
        current_session = session_manager.get_current_session()
        
        return {
            "status": "healthy",
            "service": "session-manager",
            "current_session": current_session,
            "total_sessions": len(session_manager.sessions),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "session-manager",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }