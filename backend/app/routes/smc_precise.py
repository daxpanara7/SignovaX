"""
Precise SMC Analysis API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.strategies.smc_engine import PreciseSMCEngine
from app.models.smc_models import SMCAnalysis, SMCDetectionConfig
from app.services.market_data_service import MarketDataService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
market_data_service = MarketDataService()
smc_engine = PreciseSMCEngine()


class PreciseSMCRequest(BaseModel):
    """Request model for precise SMC analysis"""
    symbol: str
    timeframe: str = "1h"
    config: Optional[SMCDetectionConfig] = None


class SMCPatternSummary(BaseModel):
    """Summary of SMC patterns"""
    symbol: str
    timeframe: str
    analysis_timestamp: str
    
    # Pattern counts
    total_order_blocks: int
    active_order_blocks: int
    total_fvgs: int
    active_fvgs: int
    total_liquidity_zones: int
    unswept_liquidity_zones: int
    total_structure_events: int
    
    # Quality metrics
    high_confidence_patterns: int
    current_trend: str
    atr_14: float
    
    # Recent patterns (last 10)
    recent_order_blocks: List[dict]
    recent_fvgs: List[dict]
    recent_liquidity_zones: List[dict]
    recent_structure_events: List[dict]


@router.post("/analyze", response_model=SMCAnalysis)
async def analyze_precise_smc(request: PreciseSMCRequest):
    """
    Perform precise SMC analysis with mathematical precision
    
    This endpoint implements exact SMC rules:
    - Order Blocks: Last opposite-color candle before strong impulse (1.5x ATR)
    - Fair Value Gaps: Gaps > 0.3x ATR with precise fill tracking
    - Liquidity Zones: Equal highs/lows within 0.1% tolerance, min 5 candles apart
    - Structure Events: BOS (continuation) vs CHOCH (reversal) with position sizing
    
    Args:
        request: SMC analysis request with symbol, timeframe, and optional config
        
    Returns:
        Complete SMC analysis with all detected patterns and metadata
    """
    try:
        logger.info(f"Precise SMC analysis request: {request.symbol} {request.timeframe}")
        
        # Initialize engine with custom config if provided
        if request.config:
            engine = PreciseSMCEngine(request.config)
        else:
            engine = smc_engine
        
        # Fetch market data
        market_data = await market_data_service.fetch_ohlcv(
            symbol=request.symbol,
            timeframe=request.timeframe,
            limit=500
        )
        
        # Convert to DataFrame
        df = market_data_service.to_dataframe(market_data)
        
        if len(df) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient data for SMC analysis (minimum 50 candles required)"
            )
        
        # Perform precise SMC analysis
        analysis = engine.analyze(df, request.symbol, request.timeframe)
        
        logger.info(f"SMC analysis complete: {analysis.detection_summary}")
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in precise SMC analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SMC analysis failed: {str(e)}")


@router.get("/summary/{symbol}", response_model=SMCPatternSummary)
async def get_smc_pattern_summary(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    limit: int = Query(10, description="Number of recent patterns to include")
):
    """
    Get SMC pattern summary with recent patterns
    
    Provides a condensed view of SMC analysis including:
    - Pattern counts (total and active)
    - Quality metrics and confidence levels
    - Recent patterns for quick review
    - Current market trend
    
    Args:
        symbol: Trading pair symbol
        timeframe: Analysis timeframe
        limit: Number of recent patterns to include
        
    Returns:
        SMC pattern summary with counts and recent patterns
    """
    try:
        logger.info(f"SMC pattern summary request: {symbol} {timeframe}")
        
        # Perform analysis
        request = PreciseSMCRequest(symbol=symbol, timeframe=timeframe)
        analysis = await analyze_precise_smc(request)
        
        # Create summary
        summary = SMCPatternSummary(
            symbol=analysis.symbol,
            timeframe=analysis.timeframe,
            analysis_timestamp=analysis.analysis_timestamp.isoformat(),
            
            # Pattern counts
            total_order_blocks=len(analysis.order_blocks),
            active_order_blocks=len([ob for ob in analysis.order_blocks if not ob.mitigated]),
            total_fvgs=len(analysis.fair_value_gaps),
            active_fvgs=len([fvg for fvg in analysis.fair_value_gaps if not fvg.filled]),
            total_liquidity_zones=len(analysis.liquidity_zones),
            unswept_liquidity_zones=len([lz for lz in analysis.liquidity_zones if not lz.swept]),
            total_structure_events=len(analysis.structure_events),
            
            # Quality metrics
            high_confidence_patterns=analysis.high_confidence_patterns,
            current_trend=analysis.current_trend,
            atr_14=analysis.atr_14,
            
            # Recent patterns (convert to dict for JSON serialization)
            recent_order_blocks=[ob.dict() for ob in analysis.order_blocks[-limit:]],
            recent_fvgs=[fvg.dict() for fvg in analysis.fair_value_gaps[-limit:]],
            recent_liquidity_zones=[lz.dict() for lz in analysis.liquidity_zones[-limit:]],
            recent_structure_events=[se.dict() for se in analysis.structure_events[-limit:]]
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting SMC summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get SMC summary: {str(e)}")


@router.get("/order-blocks/{symbol}")
async def get_order_blocks(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    active_only: bool = Query(False, description="Return only non-mitigated order blocks")
):
    """
    Get Order Blocks with precise detection rules
    
    Order Block Rules:
    - Bullish OB: Last RED candle before strong bullish impulse
    - Bearish OB: Last GREEN candle before strong bearish impulse
    - Strong impulse: Next candle closes beyond last 3 candles' high/low
    - Displacement required: Impulse candle body > 1.5x ATR(14)
    - Mitigation: Price closes inside OB zone
    
    Args:
        symbol: Trading pair symbol
        timeframe: Analysis timeframe
        active_only: Filter to only non-mitigated order blocks
        
    Returns:
        List of Order Blocks with mitigation status
    """
    try:
        # Perform analysis
        request = PreciseSMCRequest(symbol=symbol, timeframe=timeframe)
        analysis = await analyze_precise_smc(request)
        
        order_blocks = analysis.order_blocks
        
        if active_only:
            order_blocks = [ob for ob in order_blocks if not ob.mitigated]
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_order_blocks": len(analysis.order_blocks),
            "returned_order_blocks": len(order_blocks),
            "active_only": active_only,
            "order_blocks": [ob.dict() for ob in order_blocks]
        }
        
    except Exception as e:
        logger.error(f"Error getting order blocks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get order blocks: {str(e)}")


@router.get("/fair-value-gaps/{symbol}")
async def get_fair_value_gaps(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    unfilled_only: bool = Query(False, description="Return only unfilled FVGs")
):
    """
    Get Fair Value Gaps with precise detection rules
    
    FVG Rules:
    - Bullish FVG: candle[i+1].low > candle[i-1].high
    - Bearish FVG: candle[i+1].high < candle[i-1].low
    - Minimum size: gap_size > 0.3 * ATR(14)
    - Fill tracking: Partial and complete fill percentages
    - Valid until 100% filled
    
    Args:
        symbol: Trading pair symbol
        timeframe: Analysis timeframe
        unfilled_only: Filter to only unfilled FVGs
        
    Returns:
        List of Fair Value Gaps with fill status
    """
    try:
        # Perform analysis
        request = PreciseSMCRequest(symbol=symbol, timeframe=timeframe)
        analysis = await analyze_precise_smc(request)
        
        fvgs = analysis.fair_value_gaps
        
        if unfilled_only:
            fvgs = [fvg for fvg in fvgs if not fvg.filled]
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_fvgs": len(analysis.fair_value_gaps),
            "returned_fvgs": len(fvgs),
            "unfilled_only": unfilled_only,
            "fair_value_gaps": [fvg.dict() for fvg in fvgs]
        }
        
    except Exception as e:
        logger.error(f"Error getting FVGs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get FVGs: {str(e)}")


@router.get("/liquidity-zones/{symbol}")
async def get_liquidity_zones(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    unswept_only: bool = Query(False, description="Return only unswept liquidity zones")
):
    """
    Get Liquidity Zones with precise detection rules
    
    Liquidity Rules:
    - Equal Highs/Lows: Within 0.1% price tolerance
    - Minimum 5 candles between equal levels
    - Swept when price closes beyond the level
    - Swept liquidity = potential reversal zone
    
    Args:
        symbol: Trading pair symbol
        timeframe: Analysis timeframe
        unswept_only: Filter to only unswept liquidity zones
        
    Returns:
        List of Liquidity Zones with sweep status
    """
    try:
        # Perform analysis
        request = PreciseSMCRequest(symbol=symbol, timeframe=timeframe)
        analysis = await analyze_precise_smc(request)
        
        liquidity_zones = analysis.liquidity_zones
        
        if unswept_only:
            liquidity_zones = [lz for lz in liquidity_zones if not lz.swept]
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_liquidity_zones": len(analysis.liquidity_zones),
            "returned_liquidity_zones": len(liquidity_zones),
            "unswept_only": unswept_only,
            "liquidity_zones": [lz.dict() for lz in liquidity_zones]
        }
        
    except Exception as e:
        logger.error(f"Error getting liquidity zones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get liquidity zones: {str(e)}")


@router.get("/structure-events/{symbol}")
async def get_structure_events(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    event_type: Optional[str] = Query(None, description="Filter by BOS or CHOCH")
):
    """
    Get Structure Events (BOS vs CHOCH) with precise distinction
    
    BOS (Break of Structure) Rules:
    - Uptrend: Price breaks above previous Higher High → BOS bullish
    - Downtrend: Price breaks below previous Lower Low → BOS bearish
    - Signal type: CONTINUATION, Position size: 100%
    
    CHOCH (Change of Character) Rules:
    - Uptrend: Price breaks below most recent Higher Low → CHOCH bearish
    - Downtrend: Price breaks above most recent Lower High → CHOCH bullish
    - Signal type: REVERSAL, Position size: 50%
    
    Args:
        symbol: Trading pair symbol
        timeframe: Analysis timeframe
        event_type: Filter by "BOS" or "CHOCH"
        
    Returns:
        List of Structure Events with signal type and position sizing
    """
    try:
        # Perform analysis
        request = PreciseSMCRequest(symbol=symbol, timeframe=timeframe)
        analysis = await analyze_precise_smc(request)
        
        structure_events = analysis.structure_events
        
        if event_type:
            if event_type.upper() == "BOS":
                structure_events = [se for se in structure_events if "bos" in se.structure_type.value]
            elif event_type.upper() == "CHOCH":
                structure_events = [se for se in structure_events if "choch" in se.structure_type.value]
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_structure_events": len(analysis.structure_events),
            "returned_structure_events": len(structure_events),
            "event_type_filter": event_type,
            "current_trend": analysis.current_trend,
            "structure_events": [se.dict() for se in structure_events]
        }
        
    except Exception as e:
        logger.error(f"Error getting structure events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get structure events: {str(e)}")


@router.get("/config")
async def get_smc_config():
    """Get current SMC detection configuration"""
    return {
        "config": smc_engine.config.dict(),
        "description": "SMC detection configuration parameters",
        "order_block_rules": {
            "min_displacement_atr_multiple": "Minimum ATR multiple for displacement validation",
            "confidence_thresholds": "ATR multiples for confidence levels"
        },
        "fvg_rules": {
            "min_fvg_atr_multiple": "Minimum ATR multiple for gap size validation",
            "confidence_thresholds": "ATR multiples for confidence levels"
        },
        "liquidity_rules": {
            "price_tolerance": "Price tolerance for equal levels (0.1%)",
            "min_candles_between_levels": "Minimum candles between equal levels",
            "confidence_thresholds": "Number of equal levels for confidence"
        }
    }


@router.post("/config")
async def update_smc_config(config: SMCDetectionConfig):
    """Update SMC detection configuration"""
    try:
        global smc_engine
        smc_engine = PreciseSMCEngine(config)
        
        return {
            "message": "SMC configuration updated successfully",
            "new_config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating SMC config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")