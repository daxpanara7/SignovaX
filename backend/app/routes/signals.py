from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.market_data_service import MarketDataService
from app.services.smc_strategy import SMCStrategy
from app.services.signal_generator import SignalGenerator
from app.services.risk_manager import RiskManager
from app.models.signals import TradingSignal

router = APIRouter()
market_data_service = MarketDataService()
smc_strategy = SMCStrategy()
signal_generator = SignalGenerator()
risk_manager = RiskManager()  # Add risk manager

class SignalRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    min_confidence: float = 70.0

@router.post("/generate", response_model=List[TradingSignal])
async def generate_trading_signals(request: SignalRequest):
    """Generate trading signals based on SMC analysis with risk management validation"""
    try:
        # Fetch market data
        market_data = await market_data_service.fetch_ohlcv(
            request.symbol, 
            request.timeframe, 
            500
        )
        
        # Convert to DataFrame and get current price
        df = market_data_service.to_dataframe(market_data)
        current_price = df['close'].iloc[-1]
        
        # Run SMC analysis
        smc_analysis = smc_strategy.analyze(df, request.symbol, request.timeframe)
        
        # Generate signals
        signals = signal_generator.generate_signals(smc_analysis, current_price)
        
        # Filter by confidence
        filtered_signals = signal_generator.filter_signals(signals, request.min_confidence)
        
        # IMPORTANT: Validate each signal through risk management
        validated_signals = []
        for signal in filtered_signals:
            validation_result = risk_manager.validate_signal(signal)
            
            if validation_result.approved:
                # Add risk management data to signal
                signal.reasoning += f" | Risk validated: {validation_result.reason}"
                if validation_result.position_size:
                    signal.reasoning += f" | Position size: {validation_result.position_size}"
                validated_signals.append(signal)
            else:
                # Log rejected signal
                print(f"Signal rejected by risk manager: {signal.symbol} {signal.signal_type} - {validation_result.reason}")
        
        return validated_signals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")

@router.get("/current")
async def get_current_signals(
    symbol: Optional[str] = Query(None, description="Symbol filter"),
    limit: int = Query(50, description="Maximum number of signals to return")
):
    """Get current/recent trading signals"""
    try:
        # Default symbols if none specified
        symbols = [symbol] if symbol else ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        all_signals = []
        
        for sym in symbols:
            try:
                request = SignalRequest(symbol=sym, timeframe="1h", min_confidence=70.0)
                signals = await generate_trading_signals(request)
                all_signals.extend(signals)
            except Exception as e:
                print(f"Failed to get signals for {sym}: {e}")
                continue
        
        # Sort by confidence and return limited results
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        return all_signals[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current signals: {str(e)}")

@router.get("/active/{symbol}")
async def get_active_signals(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe"),
    limit: int = Query(10, description="Maximum number of signals to return")
):
    """Get active trading signals for a symbol"""
    try:
        # Generate fresh signals
        request = SignalRequest(symbol=symbol, timeframe=timeframe)
        signals = await generate_trading_signals(request)
        
        # Return limited number of signals
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal_count": len(signals),
            "signals": signals[:limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active signals: {str(e)}")

@router.get("/summary")
async def get_signals_summary():
    """Get summary of signals across multiple symbols"""
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    timeframes = ["1h", "4h"]
    
    summary = {
        "timestamp": market_data_service.exchange.milliseconds(),
        "signals_by_symbol": {}
    }
    
    try:
        for symbol in symbols:
            symbol_signals = {}
            for timeframe in timeframes:
                try:
                    request = SignalRequest(symbol=symbol, timeframe=timeframe, min_confidence=75.0)
                    signals = await generate_trading_signals(request)
                    
                    symbol_signals[timeframe] = {
                        "count": len(signals),
                        "buy_signals": len([s for s in signals if s.signal_type.value == "BUY"]),
                        "sell_signals": len([s for s in signals if s.signal_type.value == "SELL"]),
                        "avg_confidence": sum(s.confidence for s in signals) / len(signals) if signals else 0
                    }
                except:
                    symbol_signals[timeframe] = {"count": 0, "buy_signals": 0, "sell_signals": 0, "avg_confidence": 0}
            
            summary["signals_by_symbol"][symbol] = symbol_signals
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signals summary: {str(e)}")