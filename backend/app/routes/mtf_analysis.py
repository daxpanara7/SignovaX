"""
Multi-Timeframe Analysis API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.strategies.mtf_confluence import ConfluenceEngine, TimeframeHierarchy

router = APIRouter()
logger = logging.getLogger(__name__)


class MTFAnalysisRequest(BaseModel):
    """Request model for MTF analysis"""
    symbol: str
    entry_tf: Optional[str] = "5m"
    htf: Optional[str] = "4h"
    mtf: Optional[str] = "1h"


class MTFAnalysisResponse(BaseModel):
    """Response model for MTF analysis"""
    confluence_score: int
    bias: str
    entry: Optional[float]
    sl: Optional[float]
    tp: Optional[float]
    reasons: list
    htf_analysis: dict
    mtf_analysis: dict
    ltf_analysis: dict
    signal_valid: bool
    analysis_timestamp: str


@router.post("/mtf-analyze", response_model=MTFAnalysisResponse)
async def analyze_mtf_confluence(request: MTFAnalysisRequest):
    """
    Analyze Multi-Timeframe confluence for trading signals
    
    This endpoint performs comprehensive MTF analysis:
    1. Analyzes HTF bias and key levels
    2. Finds MTF confirmation aligned with HTF
    3. Identifies precise LTF entry points
    4. Calculates confluence score (0-100)
    5. Only generates signals with score >= 60
    
    Rules:
    - Never generates BUY signal if HTF bias is bearish
    - Never generates SELL signal if HTF bias is bullish
    - Logs each confluence check with reasoning
    """
    try:
        logger.info(f"MTF Analysis request: {request.symbol} - HTF:{request.htf}, MTF:{request.mtf}, LTF:{request.entry_tf}")
        
        # Validate timeframes
        try:
            TimeframeHierarchy.get_timeframe_type(request.htf)
            TimeframeHierarchy.get_timeframe_type(request.mtf)
            TimeframeHierarchy.get_timeframe_type(request.entry_tf)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid timeframe: {str(e)}")
        
        # Initialize confluence engine
        confluence_engine = ConfluenceEngine()
        
        # Perform MTF confluence analysis
        result = await confluence_engine.analyze_mtf_confluence(
            symbol=request.symbol,
            entry_tf=request.entry_tf,
            htf=request.htf,
            mtf=request.mtf
        )
        
        # Prepare response
        response = MTFAnalysisResponse(
            confluence_score=result.confluence_score,
            bias=result.bias,
            entry=result.entry,
            sl=result.stop_loss,
            tp=result.take_profit,
            reasons=result.reasons,
            htf_analysis=result.htf_analysis,
            mtf_analysis=result.mtf_analysis,
            ltf_analysis=result.ltf_analysis,
            signal_valid=result.entry is not None and result.confluence_score >= 60,
            analysis_timestamp=result.htf_analysis.get("analysis_time", "")
        )
        
        logger.info(f"MTF Analysis complete: Score {result.confluence_score}, Valid: {response.signal_valid}")
        return response
        
    except Exception as e:
        logger.error(f"Error in MTF analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"MTF analysis failed: {str(e)}")


@router.get("/mtf-timeframes")
async def get_available_mtf_timeframes():
    """Get available timeframes for MTF analysis"""
    return {
        "htf_timeframes": TimeframeHierarchy.HTF_TIMEFRAMES,
        "mtf_timeframes": TimeframeHierarchy.MTF_TIMEFRAMES,
        "ltf_timeframes": TimeframeHierarchy.LTF_TIMEFRAMES,
        "recommended_combinations": [
            {"htf": "4h", "mtf": "1h", "ltf": "5m"},
            {"htf": "1d", "mtf": "4h", "ltf": "15m"},
            {"htf": "4h", "mtf": "15m", "ltf": "1m"}
        ]
    }


@router.get("/mtf-status/{symbol}")
async def get_mtf_status(symbol: str, htf: str = "4h"):
    """Get quick MTF status for a symbol"""
    try:
        confluence_engine = ConfluenceEngine()
        htf_analysis = await confluence_engine.analyze_htf_bias(symbol, htf)
        
        return {
            "symbol": symbol,
            "htf_bias": htf_analysis.get("bias", "neutral"),
            "htf_ob_count": len(htf_analysis.get("htf_ob", [])),
            "htf_liquidity_count": len(htf_analysis.get("htf_liquidity", [])),
            "analysis_time": htf_analysis.get("analysis_time"),
            "status": "active" if htf_analysis.get("bias") != "neutral" else "neutral"
        }
        
    except Exception as e:
        logger.error(f"Error getting MTF status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get MTF status: {str(e)}")