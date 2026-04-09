from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.market_data_service import MarketDataService
from app.services.smc_strategy import SMCStrategy
from app.models.market_data import SMCAnalysis

router = APIRouter()
market_data_service = MarketDataService()
smc_strategy = SMCStrategy()

class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    limit: int = 500

@router.post("/smc", response_model=SMCAnalysis)
async def analyze_smc_patterns(request: AnalysisRequest):
    """Run Smart Money Concepts analysis on market data"""
    try:
        # Fetch market data
        market_data = await market_data_service.fetch_ohlcv(
            request.symbol, 
            request.timeframe, 
            request.limit
        )
        
        # Convert to DataFrame for analysis
        df = market_data_service.to_dataframe(market_data)
        
        # Run SMC analysis
        smc_analysis = smc_strategy.analyze(df, request.symbol, request.timeframe)
        
        return smc_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/patterns/{symbol}")
async def get_pattern_summary(symbol: str, timeframe: str = "1h"):
    """Get a summary of detected SMC patterns"""
    try:
        # Fetch and analyze data
        market_data = await market_data_service.fetch_ohlcv(symbol, timeframe, 200)
        df = market_data_service.to_dataframe(market_data)
        smc_analysis = smc_strategy.analyze(df, symbol, timeframe)
        
        # Create summary
        summary = {
            "symbol": symbol,
            "timeframe": timeframe,
            "analysis_time": smc_analysis.analysis_timestamp,
            "pattern_counts": {
                "liquidity_zones": len(smc_analysis.liquidity_zones),
                "order_blocks": len(smc_analysis.order_blocks),
                "fair_value_gaps": len(smc_analysis.fair_value_gaps),
                "bos_signals": len(smc_analysis.bos_signals),
                "choch_signals": len(smc_analysis.choch_signals)
            },
            "latest_patterns": {
                "recent_liquidity_zones": smc_analysis.liquidity_zones[-3:] if smc_analysis.liquidity_zones else [],
                "recent_order_blocks": smc_analysis.order_blocks[-3:] if smc_analysis.order_blocks else [],
                "recent_fvg": smc_analysis.fair_value_gaps[-3:] if smc_analysis.fair_value_gaps else []
            }
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")