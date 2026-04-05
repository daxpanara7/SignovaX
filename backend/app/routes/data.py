"""
Enhanced Data Management API Routes
Provides endpoints for data validation, caching, export, and quality monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import io
import json

from app.auth.auth import get_current_user, UserInfo
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter
from app.services.data_manager import (
    data_manager, DataQuality, ValidationResult, CacheStats,
    ValidationIssue, DataUnavailableError
)

logger = get_logger(__name__)
router = APIRouter()

# Request/Response Models
class DataRequest(BaseModel):
    """Request model for OHLCV data"""
    symbol: str
    timeframe: str
    start: str  # ISO format datetime
    end: str    # ISO format datetime
    validate: bool = True

class ValidationIssueResponse(BaseModel):
    """Response model for validation issues"""
    type: str
    timestamp: str
    description: str
    severity: str
    fixed: bool

class ValidationResultResponse(BaseModel):
    """Response model for validation results"""
    valid: bool
    issues: List[ValidationIssueResponse]
    original_count: int
    cleaned_count: int
    issues_fixed: int

class DataQualityResponse(BaseModel):
    """Response model for data quality metrics"""
    symbol: str
    timeframe: str
    total_candles: int
    missing_candles: int
    bad_ticks: int
    anomalies: int
    zero_volume_candles: int
    duplicate_timestamps: int
    quality_score: float
    source: str
    last_updated: str

class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    total_entries: int
    total_size_mb: float
    hit_rate: float
    miss_rate: float
    evictions: int
    oldest_entry: Optional[str]
    newest_entry: Optional[str]

class ExportRequest(BaseModel):
    """Request model for data export"""
    symbol: str
    timeframe: str
    start: str
    end: str
    format: str = "csv"  # csv or json
    include_smc: bool = False

class BatchValidationRequest(BaseModel):
    """Request model for batch validation"""
    requests: List[DataRequest]

class CachePreloadRequest(BaseModel):
    """Request model for cache preloading"""
    symbols: List[str]
    timeframes: List[str]
    days_back: int = 30

@router.get("/ohlcv", response_model=Dict[str, Any])
@limiter.limit("60/minute")
async def get_ohlcv_data(
    request: Request,
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    timeframe: str = Query(..., description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)"),
    start: str = Query(..., description="Start datetime in ISO format"),
    end: str = Query(..., description="End datetime in ISO format"),
    validate: bool = Query(True, description="Whether to validate and clean data"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get OHLCV data with validation and caching
    
    Parameters:
    - symbol: Trading symbol (e.g., BTCUSDT, EURUSD)
    - timeframe: Data timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
    - start: Start datetime in ISO format (e.g., 2024-01-01T00:00:00)
    - end: End datetime in ISO format (e.g., 2024-01-02T00:00:00)
    - validate: Whether to validate and clean the data
    
    Returns:
    - OHLCV data with metadata
    - Validation results if validation is enabled
    - Cache information
    """
    try:
        # Parse datetime strings
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None)
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
        
        # Validate timeframe
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timeframe. Must be one of: {valid_timeframes}"
            )
        
        # Validate date range
        if start_dt >= end_dt:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        max_days = 365
        if (end_dt - start_dt).days > max_days:
            raise HTTPException(
                status_code=400, 
                detail=f"Date range too large. Maximum {max_days} days allowed"
            )
        
        # Get data
        df = await data_manager.get_ohlcv(symbol, timeframe, start_dt, end_dt, validate)
        
        if df.empty:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "start": start,
                "end": end,
                "data": [],
                "count": 0,
                "message": "No data available for the specified period"
            }
        
        # Convert DataFrame to records
        data_records = df.to_dict('records')
        
        # Convert timestamps to ISO format
        for record in data_records:
            if 'timestamp' in record:
                record['timestamp'] = record['timestamp'].isoformat()
        
        # Get cache stats
        cache_stats = data_manager.get_cache_stats()
        
        response = {
            "symbol": symbol,
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "data": data_records,
            "count": len(data_records),
            "validated": validate,
            "cache_stats": {
                "hit_rate": cache_stats.hit_rate,
                "total_entries": cache_stats.total_entries,
                "total_size_mb": cache_stats.total_size_mb
            }
        }
        
        logger.info(f"OHLCV data requested by {current_user.username}: {symbol} {timeframe} ({len(data_records)} records)")
        return response
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Data unavailable: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OHLCV data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get OHLCV data: {str(e)}")

@router.post("/validate", response_model=ValidationResultResponse)
@limiter.limit("30/minute")
async def validate_data(
    request: Request,
    data_request: DataRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Validate OHLCV data quality
    
    Parameters:
    - symbol: Trading symbol
    - timeframe: Data timeframe
    - start: Start datetime
    - end: End datetime
    
    Returns:
    - Validation results with issues found
    - Data quality metrics
    - Cleaned data statistics
    """
    try:
        # Parse datetime strings
        start_dt = datetime.fromisoformat(data_request.start.replace('Z', '+00:00')).replace(tzinfo=None)
        end_dt = datetime.fromisoformat(data_request.end.replace('Z', '+00:00')).replace(tzinfo=None)
        
        # Get raw data without validation
        df = await data_manager.get_ohlcv(
            data_request.symbol, data_request.timeframe, 
            start_dt, end_dt, validate=False
        )
        
        # Validate the data
        from app.services.data_manager import DataValidator
        validation_result = DataValidator.validate_ohlcv(df)
        
        # Convert issues to response format
        issues_response = []
        for issue in validation_result.issues:
            issues_response.append(ValidationIssueResponse(
                type=issue.type.value,
                timestamp=issue.timestamp,
                description=issue.description,
                severity=issue.severity,
                fixed=issue.fixed
            ))
        
        response = ValidationResultResponse(
            valid=validation_result.valid,
            issues=issues_response,
            original_count=validation_result.original_count,
            cleaned_count=validation_result.cleaned_count,
            issues_fixed=validation_result.issues_fixed
        )
        
        logger.info(f"Data validation requested by {current_user.username}: {data_request.symbol} {data_request.timeframe}")
        return response
        
    except Exception as e:
        logger.error(f"Error validating data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate data: {str(e)}")

@router.get("/quality", response_model=Optional[DataQualityResponse])
@limiter.limit("60/minute")
async def get_data_quality(
    request: Request,
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get data quality metrics for a symbol/timeframe
    
    Parameters:
    - symbol: Trading symbol
    - timeframe: Data timeframe
    
    Returns:
    - Data quality metrics including:
      - Total candles processed
      - Number of missing candles, bad ticks, anomalies
      - Quality score (0-100)
      - Last update timestamp
      - Data source information
    """
    try:
        quality = data_manager.get_data_quality(symbol, timeframe)
        
        if quality is None:
            return None
        
        response = DataQualityResponse(
            symbol=quality.symbol,
            timeframe=quality.timeframe,
            total_candles=quality.total_candles,
            missing_candles=quality.missing_candles,
            bad_ticks=quality.bad_ticks,
            anomalies=quality.anomalies,
            zero_volume_candles=quality.zero_volume_candles,
            duplicate_timestamps=quality.duplicate_timestamps,
            quality_score=quality.quality_score,
            source=quality.source,
            last_updated=quality.last_updated
        )
        
        logger.debug(f"Data quality requested by {current_user.username}: {symbol} {timeframe}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting data quality: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get data quality: {str(e)}")

@router.get("/export")
@limiter.limit("10/minute")
async def export_data(
    request: Request,
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    start: str = Query(..., description="Start datetime in ISO format"),
    end: str = Query(..., description="End datetime in ISO format"),
    format: str = Query("csv", description="Export format (csv or json)"),
    include_smc: bool = Query(False, description="Include SMC analysis levels"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Export OHLCV data with optional SMC levels
    
    Parameters:
    - symbol: Trading symbol
    - timeframe: Data timeframe
    - start: Start datetime
    - end: End datetime
    - format: Export format (csv or json)
    - include_smc: Whether to include SMC analysis levels
    
    Returns:
    - CSV file download or JSON response
    - Includes OHLCV data and optionally SMC levels
    """
    try:
        # Parse datetime strings
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None)
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
        
        # Validate format
        if format.lower() not in ['csv', 'json']:
            raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
        
        # Export data
        exported_data = await data_manager.export_data(
            symbol, timeframe, start_dt, end_dt, format, include_smc
        )
        
        if format.lower() == 'csv':
            # Return CSV as downloadable file
            filename = f"{symbol}_{timeframe}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.csv"
            
            return StreamingResponse(
                io.StringIO(exported_data),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Return JSON response
            logger.info(f"Data export requested by {current_user.username}: {symbol} {timeframe} ({format})")
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "start": start,
                "end": end,
                "format": format,
                "include_smc": include_smc,
                "data": exported_data,
                "count": len(exported_data) if isinstance(exported_data, list) else 0
            }
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")

@router.get("/cache/stats", response_model=CacheStatsResponse)
@limiter.limit("60/minute")
async def get_cache_statistics(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get cache performance statistics
    
    Returns:
    - Cache hit/miss rates
    - Memory usage statistics
    - Entry counts and eviction metrics
    - Oldest and newest cached entries
    """
    try:
        stats = data_manager.get_cache_stats()
        
        response = CacheStatsResponse(
            total_entries=stats.total_entries,
            total_size_mb=stats.total_size_mb,
            hit_rate=stats.hit_rate,
            miss_rate=stats.miss_rate,
            evictions=stats.evictions,
            oldest_entry=stats.oldest_entry,
            newest_entry=stats.newest_entry
        )
        
        logger.debug(f"Cache stats requested by {current_user.username}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/clear")
@limiter.limit("5/minute")
async def clear_cache(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Clear all cached data
    
    This will force fresh data fetching for all subsequent requests.
    Use with caution as it may impact performance temporarily.
    """
    try:
        data_manager.clear_cache()
        
        logger.info(f"Cache cleared by {current_user.username}")
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/cache/preload")
@limiter.limit("3/minute")
async def preload_cache(
    request: Request,
    preload_request: CachePreloadRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Preload cache with commonly used data
    
    Parameters:
    - symbols: List of symbols to preload
    - timeframes: List of timeframes to preload
    - days_back: Number of days of historical data to preload
    
    This endpoint helps warm up the cache for better performance.
    """
    try:
        # Validate input
        if not preload_request.symbols:
            raise HTTPException(status_code=400, detail="At least one symbol is required")
        
        if not preload_request.timeframes:
            raise HTTPException(status_code=400, detail="At least one timeframe is required")
        
        if preload_request.days_back < 1 or preload_request.days_back > 365:
            raise HTTPException(status_code=400, detail="days_back must be between 1 and 365")
        
        # Preload cache
        result = await data_manager.preload_cache(
            preload_request.symbols,
            preload_request.timeframes,
            preload_request.days_back
        )
        
        logger.info(f"Cache preload requested by {current_user.username}: {len(preload_request.symbols)} symbols, {len(preload_request.timeframes)} timeframes")
        
        return {
            "status": "success",
            "message": "Cache preload completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preloading cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preload cache: {str(e)}")

@router.post("/validate/batch", response_model=Dict[str, ValidationResultResponse])
@limiter.limit("10/minute")
async def validate_data_batch(
    request: Request,
    batch_request: BatchValidationRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Validate multiple data sets in batch
    
    Parameters:
    - requests: List of data validation requests
    
    Returns:
    - Dictionary of validation results keyed by symbol_timeframe
    - Allows efficient validation of multiple data sets
    """
    try:
        if not batch_request.requests:
            raise HTTPException(status_code=400, detail="At least one validation request is required")
        
        if len(batch_request.requests) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 validation requests allowed per batch")
        
        # Convert requests to the format expected by data_manager
        data_requests = []
        for req in batch_request.requests:
            data_requests.append({
                'symbol': req.symbol,
                'timeframe': req.timeframe,
                'start': datetime.fromisoformat(req.start.replace('Z', '+00:00')).replace(tzinfo=None),
                'end': datetime.fromisoformat(req.end.replace('Z', '+00:00')).replace(tzinfo=None)
            })
        
        # Perform batch validation
        results = await data_manager.validate_data_batch(data_requests)
        
        # Convert results to response format
        response_results = {}
        for key, validation_result in results.items():
            issues_response = []
            for issue in validation_result.issues:
                issues_response.append(ValidationIssueResponse(
                    type=issue.type.value,
                    timestamp=issue.timestamp,
                    description=issue.description,
                    severity=issue.severity,
                    fixed=issue.fixed
                ))
            
            response_results[key] = ValidationResultResponse(
                valid=validation_result.valid,
                issues=issues_response,
                original_count=validation_result.original_count,
                cleaned_count=validation_result.cleaned_count,
                issues_fixed=validation_result.issues_fixed
            )
        
        logger.info(f"Batch validation requested by {current_user.username}: {len(batch_request.requests)} requests")
        return response_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform batch validation: {str(e)}")

@router.get("/cache/info")
@limiter.limit("60/minute")
async def get_cache_info(
    request: Request,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get detailed cache information
    
    Parameters:
    - symbol: Optional symbol filter
    - timeframe: Optional timeframe filter
    
    Returns:
    - Detailed information about cached entries
    - Creation and access timestamps
    - Record counts and sources
    """
    try:
        cache_info = data_manager.get_cache_info(symbol, timeframe)
        
        logger.debug(f"Cache info requested by {current_user.username}")
        return {
            "cache_entries": cache_info,
            "total_entries": len(cache_info),
            "filters": {
                "symbol": symbol,
                "timeframe": timeframe
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache info: {str(e)}")

@router.get("/health")
async def data_health_check():
    """Health check for data management service"""
    try:
        cache_stats = data_manager.get_cache_stats()
        
        return {
            "status": "healthy",
            "service": "data-manager",
            "cache_entries": cache_stats.total_entries,
            "cache_size_mb": cache_stats.total_size_mb,
            "cache_hit_rate": f"{cache_stats.hit_rate:.1f}%",
            "data_sources": {
                "binance": "available" if hasattr(data_manager.source_manager.sources.get('binance'), 'apiKey') else "not_configured",
                "mock": "available"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "data-manager",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }