"""
ML API Routes for Signal Filtering
Provides endpoints for model training, status, and feature analysis
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from app.auth.auth import get_current_user, UserInfo
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter
from app.ml.signal_filter import signal_filter, train_model, filter_signal
from app.ml.training_data_generator import training_data_generator

logger = get_logger(__name__)
router = APIRouter()

# Request/Response Models
class TrainModelRequest(BaseModel):
    """Request model for training ML model"""
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    months_back: int = 6
    force_regenerate: bool = False

class FilterSignalRequest(BaseModel):
    """Request model for filtering signals"""
    signal: Dict[str, Any]
    market_context: Optional[Dict[str, Any]] = {}

class ModelStatusResponse(BaseModel):
    """Response model for model status"""
    model_trained: bool
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    n_samples: Optional[int] = None
    last_trained: Optional[str] = None
    win_threshold: float
    feature_count: int

class FeatureImportanceResponse(BaseModel):
    """Response model for feature importances"""
    features: Dict[str, float]
    total_features: int

class TrainingStatsResponse(BaseModel):
    """Response model for training statistics"""
    total_samples: int
    overall_win_rate: float
    by_symbol: List[Dict[str, Any]]
    by_signal_type: List[Dict[str, Any]]

@router.post("/train")
@limiter.limit("2/minute")  # Limited to prevent abuse
async def train_ml_model(
    request: Request,
    train_request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Trigger ML model training on historical data
    
    This endpoint:
    1. Generates training data from historical backtests
    2. Trains Random Forest classifier
    3. Saves model for future use
    """
    try:
        logger.info(f"ML model training requested by user {current_user.username}")
        
        # Check if user has admin permissions
        if "admin" not in current_user.permissions:
            raise HTTPException(status_code=403, detail="Admin permissions required for model training")
        
        # Start training in background
        background_tasks.add_task(
            _train_model_background,
            train_request.symbol,
            train_request.timeframe,
            train_request.months_back,
            train_request.force_regenerate
        )
        
        return {
            "status": "training_started",
            "message": f"Model training started for {train_request.symbol} {train_request.timeframe}",
            "symbol": train_request.symbol,
            "timeframe": train_request.timeframe,
            "months_back": train_request.months_back,
            "estimated_duration": "5-15 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training initiation failed: {str(e)}")

async def _train_model_background(
    symbol: str,
    timeframe: str,
    months_back: int,
    force_regenerate: bool
):
    """Background task for model training"""
    try:
        logger.info(f"Starting background model training for {symbol} {timeframe}")
        
        # Step 1: Generate training data
        logger.info("Generating training data...")
        training_result = await training_data_generator.generate_training_data(
            symbol=symbol,
            timeframe=timeframe,
            months_back=months_back,
            force_regenerate=force_regenerate
        )
        
        if 'error' in training_result:
            logger.error(f"Training data generation failed: {training_result['error']}")
            return
        
        logger.info(f"Training data generated: {training_result.get('stored_samples', 0)} samples")
        
        # Step 2: Load training data
        training_data = training_data_generator.get_training_data(symbol=symbol, timeframe=timeframe)
        
        if len(training_data) < 50:
            logger.error(f"Insufficient training data: {len(training_data)} samples")
            return
        
        # Step 3: Prepare data for training
        historical_signals = []
        outcomes = []
        
        for data in training_data:
            signal = {
                'id': data['signal_id'],
                'symbol': data['symbol'],
                'timeframe': data['timeframe'],
                'timestamp': data['timestamp'],
                'type': data['signal_type'],
                'entry_price': data['entry_price'],
                'stop_loss': data['stop_loss'],
                'take_profit': data['take_profit'],
                'confluence_score': data['confluence_score'],
                'features': list(data['features'].values()) if data['features'] else [0] * 13
            }
            
            historical_signals.append(signal)
            outcomes.append(data['outcome'])
        
        # Step 4: Train model
        logger.info(f"Training model with {len(historical_signals)} samples...")
        training_results = train_model(historical_signals, outcomes)
        
        if 'error' in training_results:
            logger.error(f"Model training failed: {training_results['error']}")
            return
        
        logger.info(f"Model training completed - Accuracy: {training_results.get('accuracy', 0):.3f}")
        
        # Log training completion
        logger.info(f"ML model training completed successfully for {symbol} {timeframe}")
        
    except Exception as e:
        logger.error(f"Background model training failed: {str(e)}")

@router.get("/status", response_model=ModelStatusResponse)
@limiter.limit("30/minute")
async def get_model_status(request: Request, current_user: UserInfo = Depends(get_current_user)):
    """
    Get ML model status and performance metrics
    
    Returns information about:
    - Whether model is trained
    - Model accuracy, precision, recall
    - Number of training samples
    - Last training date
    - Feature count and threshold
    """
    try:
        status = signal_filter.get_model_status()
        metadata = status.get('metadata', {})
        
        return ModelStatusResponse(
            model_trained=status['model_trained'],
            accuracy=metadata.get('accuracy'),
            precision=metadata.get('precision'),
            recall=metadata.get('recall'),
            n_samples=metadata.get('n_samples'),
            last_trained=metadata.get('last_trained'),
            win_threshold=status['win_threshold'],
            feature_count=status['feature_count']
        )
        
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")

@router.get("/features", response_model=FeatureImportanceResponse)
@limiter.limit("30/minute")
async def get_feature_importances(request: Request, current_user: UserInfo = Depends(get_current_user)):
    """
    Get feature importance data for ML model
    
    Returns:
    - Feature names and their importance scores
    - Total number of features
    - Can be used to create charts showing which features matter most
    """
    try:
        importances = signal_filter.get_feature_importances()
        
        if not importances:
            raise HTTPException(status_code=404, detail="No trained model available")
        
        return FeatureImportanceResponse(
            features=importances,
            total_features=len(importances)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature importances: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get feature importances: {str(e)}")

@router.post("/filter")
@limiter.limit("60/minute")
async def filter_trading_signal(
    request: Request,
    filter_request: FilterSignalRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Filter a trading signal using the ML model
    
    Takes a signal and returns:
    - Whether the signal is approved (probability >= threshold)
    - Win probability prediction
    - Reasoning for the decision
    """
    try:
        # Add market context to signal
        signal_with_context = filter_request.signal.copy()
        signal_with_context['market_context'] = filter_request.market_context
        
        # Filter signal
        result = filter_signal(signal_with_context)
        
        logger.info(f"Signal filtered for user {current_user.username} - Approved: {result['approved']}")
        
        return {
            "signal_id": filter_request.signal.get('id', 'unknown'),
            "approved": result['approved'],
            "win_probability": result['win_probability'],
            "threshold": result.get('threshold', signal_filter.win_threshold),
            "reason": result['reason'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error filtering signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signal filtering failed: {str(e)}")

@router.get("/training-stats", response_model=TrainingStatsResponse)
@limiter.limit("30/minute")
async def get_training_statistics(request: Request, current_user: UserInfo = Depends(get_current_user)):
    """
    Get training data statistics
    
    Returns:
    - Total number of training samples
    - Overall win rate
    - Statistics by symbol
    - Statistics by signal type
    """
    try:
        stats = training_data_generator.get_training_stats()
        
        return TrainingStatsResponse(
            total_samples=stats['total_samples'],
            overall_win_rate=stats['overall_win_rate'],
            by_symbol=stats.get('by_symbol', []),
            by_signal_type=stats.get('by_signal_type', [])
        )
        
    except Exception as e:
        logger.error(f"Error getting training statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get training statistics: {str(e)}")

@router.post("/generate-data")
@limiter.limit("1/hour")  # Very limited to prevent abuse
async def generate_training_data(
    request: Request,
    data_request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Generate training data from historical backtests
    
    This is a resource-intensive operation that:
    1. Fetches historical market data
    2. Generates signals using SMC and MTF engines
    3. Labels signals with win/loss outcomes
    4. Stores labeled data for model training
    """
    try:
        # Check admin permissions
        if "admin" not in current_user.permissions:
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        logger.info(f"Training data generation requested by user {current_user.username}")
        
        # Start generation in background
        background_tasks.add_task(
            _generate_training_data_background,
            data_request.symbol,
            data_request.timeframe,
            data_request.months_back,
            data_request.force_regenerate
        )
        
        return {
            "status": "generation_started",
            "message": f"Training data generation started for {data_request.symbol} {data_request.timeframe}",
            "symbol": data_request.symbol,
            "timeframe": data_request.timeframe,
            "months_back": data_request.months_back,
            "estimated_duration": "10-30 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting training data generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data generation initiation failed: {str(e)}")

async def _generate_training_data_background(
    symbol: str,
    timeframe: str,
    months_back: int,
    force_regenerate: bool
):
    """Background task for training data generation"""
    try:
        logger.info(f"Starting background training data generation for {symbol} {timeframe}")
        
        result = await training_data_generator.generate_training_data(
            symbol=symbol,
            timeframe=timeframe,
            months_back=months_back,
            force_regenerate=force_regenerate
        )
        
        if 'error' in result:
            logger.error(f"Training data generation failed: {result['error']}")
        else:
            logger.info(f"Training data generation completed: {result.get('stored_samples', 0)} samples")
        
    except Exception as e:
        logger.error(f"Background training data generation failed: {str(e)}")

@router.delete("/model")
@limiter.limit("5/minute")
async def delete_model(request: Request, current_user: UserInfo = Depends(get_current_user)):
    """
    Delete the trained ML model
    
    Requires admin permissions. Use this to reset the model
    and force retraining with new data.
    """
    try:
        # Check admin permissions
        if "admin" not in current_user.permissions:
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        import os
        if os.path.exists(signal_filter.model_path):
            os.remove(signal_filter.model_path)
            signal_filter.model = None
            signal_filter.model_metadata = {}
            
            logger.info(f"ML model deleted by user {current_user.username}")
            
            return {
                "status": "success",
                "message": "ML model deleted successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "not_found",
                "message": "No model file found to delete"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model deletion failed: {str(e)}")

@router.get("/health")
async def ml_health_check():
    """Health check for ML service"""
    try:
        status = signal_filter.get_model_status()
        
        return {
            "status": "healthy",
            "service": "ml-signal-filter",
            "model_loaded": status['model_trained'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "ml-signal-filter",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }