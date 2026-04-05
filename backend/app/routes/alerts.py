"""
Alert Management API Routes
Provides endpoints for alert preferences, history, and testing
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.auth.auth import get_current_user, UserInfo
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter
from app.services.alert_manager import alert_manager, AlertPreferences

logger = get_logger(__name__)
router = APIRouter()

# Request/Response Models
class AlertPreferencesRequest(BaseModel):
    """Request model for updating alert preferences"""
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    email_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    min_confluence_to_alert: Optional[int] = None
    sessions_to_alert: Optional[List[str]] = None
    signal_types_to_alert: Optional[List[str]] = None

class AlertPreferencesResponse(BaseModel):
    """Response model for alert preferences"""
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    telegram_bot_token: Optional[str]  # Masked in response
    email_enabled: bool
    email_address: Optional[str]
    webhook_enabled: bool
    webhook_url: Optional[str]
    webhook_secret: Optional[str]  # Masked in response
    min_confluence_to_alert: int
    sessions_to_alert: List[str]
    signal_types_to_alert: List[str]

class AlertHistoryResponse(BaseModel):
    """Response model for alert history"""
    id: int
    type: str
    channel: str
    title: str
    message: str
    payload: Dict[str, Any]
    timestamp: str
    severity: str
    status: str
    error_message: Optional[str]
    retry_count: int

class AlertStatsResponse(BaseModel):
    """Response model for alert statistics"""
    total_alerts: int
    sent_count: int
    failed_count: int
    pending_count: int
    channel_counts: Dict[str, int]
    type_counts: Dict[str, int]
    recent_24h: int
    success_rate: float

class TestAlertResponse(BaseModel):
    """Response model for test alerts"""
    success: bool
    message: str
    error: Optional[str] = None

@router.get("/preferences", response_model=AlertPreferencesResponse)
@limiter.limit("30/minute")
async def get_alert_preferences(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get current alert preferences
    
    Returns:
    - Current alert configuration for all channels
    - Sensitive data (tokens, passwords) are masked
    """
    try:
        preferences = alert_manager.get_preferences()
        
        # Mask sensitive data
        if preferences.get('telegram_bot_token'):
            preferences['telegram_bot_token'] = f"***{preferences['telegram_bot_token'][-4:]}"
        
        if preferences.get('webhook_secret'):
            preferences['webhook_secret'] = f"***{preferences['webhook_secret'][-4:]}"
        
        logger.debug(f"Alert preferences requested by user {current_user.username}")
        return AlertPreferencesResponse(**preferences)
        
    except Exception as e:
        logger.error(f"Error getting alert preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert preferences: {str(e)}")

@router.put("/preferences")
@limiter.limit("10/minute")
async def update_alert_preferences(
    request: Request,
    preferences: AlertPreferencesRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Update alert preferences
    
    Parameters:
    - telegram_enabled: Enable/disable Telegram alerts
    - telegram_chat_id: Telegram chat ID for alerts
    - telegram_bot_token: Telegram bot token
    - email_enabled: Enable/disable email alerts
    - email_address: Email address for alerts
    - webhook_enabled: Enable/disable webhook alerts
    - webhook_url: Webhook URL for alerts
    - webhook_secret: Optional webhook secret
    - min_confluence_to_alert: Minimum confluence score to trigger alerts
    - sessions_to_alert: List of sessions to alert for
    - signal_types_to_alert: List of signal types to alert for
    
    Returns:
    - Success confirmation
    - Updated preferences
    """
    try:
        # Convert to dict and filter None values
        update_data = {k: v for k, v in preferences.dict().items() if v is not None}
        
        # Validate sessions
        if 'sessions_to_alert' in update_data:
            valid_sessions = ['asia', 'london', 'new_york', 'overlap']
            invalid_sessions = [s for s in update_data['sessions_to_alert'] if s not in valid_sessions]
            if invalid_sessions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid sessions: {invalid_sessions}. Valid sessions: {valid_sessions}"
                )
        
        # Validate signal types
        if 'signal_types_to_alert' in update_data:
            valid_types = ['BOS', 'CHOCH', 'OB', 'FVG']
            invalid_types = [t for t in update_data['signal_types_to_alert'] if t not in valid_types]
            if invalid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid signal types: {invalid_types}. Valid types: {valid_types}"
                )
        
        # Validate confluence score
        if 'min_confluence_to_alert' in update_data:
            score = update_data['min_confluence_to_alert']
            if not 0 <= score <= 100:
                raise HTTPException(
                    status_code=400,
                    detail="min_confluence_to_alert must be between 0 and 100"
                )
        
        # Update preferences
        success = alert_manager.update_preferences(update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update preferences")
        
        # Get updated preferences (masked)
        updated_preferences = alert_manager.get_preferences()
        if updated_preferences.get('telegram_bot_token'):
            updated_preferences['telegram_bot_token'] = f"***{updated_preferences['telegram_bot_token'][-4:]}"
        if updated_preferences.get('webhook_secret'):
            updated_preferences['webhook_secret'] = f"***{updated_preferences['webhook_secret'][-4:]}"
        
        logger.info(f"Alert preferences updated by user {current_user.username}")
        
        return {
            "status": "success",
            "message": "Alert preferences updated successfully",
            "preferences": updated_preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update alert preferences: {str(e)}")

@router.get("/history", response_model=List[AlertHistoryResponse])
@limiter.limit("60/minute")
async def get_alert_history(
    request: Request,
    limit: int = Query(50, description="Number of alerts to return", ge=1, le=200),
    offset: int = Query(0, description="Number of alerts to skip", ge=0),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get alert history
    
    Parameters:
    - limit: Number of alerts to return (1-200)
    - offset: Number of alerts to skip for pagination
    
    Returns:
    - List of recent alerts with details
    - Ordered by timestamp (newest first)
    """
    try:
        alerts = alert_manager.get_alert_history(limit=limit, offset=offset)
        
        response_alerts = []
        for alert in alerts:
            response_alerts.append(AlertHistoryResponse(
                id=alert['id'],
                type=alert['type'],
                channel=alert['channel'],
                title=alert['title'],
                message=alert['message'],
                payload=alert['payload'],
                timestamp=alert['timestamp'],
                severity=alert['severity'],
                status=alert['status'],
                error_message=alert['error_message'],
                retry_count=alert['retry_count']
            ))
        
        logger.debug(f"Alert history requested by user {current_user.username}: {len(response_alerts)} alerts")
        return response_alerts
        
    except Exception as e:
        logger.error(f"Error getting alert history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert history: {str(e)}")

@router.get("/stats", response_model=AlertStatsResponse)
@limiter.limit("30/minute")
async def get_alert_statistics(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get alert statistics
    
    Returns:
    - Total alert counts by status
    - Alert counts by channel and type
    - Recent activity metrics
    - Success rate percentage
    """
    try:
        stats = alert_manager.get_alert_statistics()
        
        response = AlertStatsResponse(
            total_alerts=stats.get('total_alerts', 0),
            sent_count=stats.get('sent_count', 0),
            failed_count=stats.get('failed_count', 0),
            pending_count=stats.get('pending_count', 0),
            channel_counts=stats.get('channel_counts', {}),
            type_counts=stats.get('type_counts', {}),
            recent_24h=stats.get('recent_24h', 0),
            success_rate=stats.get('success_rate', 0.0)
        )
        
        logger.debug(f"Alert statistics requested by user {current_user.username}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert statistics: {str(e)}")

@router.post("/test/telegram", response_model=TestAlertResponse)
@limiter.limit("5/minute")
async def test_telegram_alert(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Send test Telegram alert
    
    Tests the Telegram alert configuration by sending a test message.
    Requires Telegram to be enabled and configured.
    
    Returns:
    - Success status
    - Error details if failed
    """
    try:
        if not alert_manager.preferences.telegram_enabled:
            raise HTTPException(status_code=400, detail="Telegram alerts are not enabled")
        
        if not alert_manager.preferences.telegram_bot_token or not alert_manager.preferences.telegram_chat_id:
            raise HTTPException(status_code=400, detail="Telegram credentials not configured")
        
        result = await alert_manager.test_telegram()
        
        logger.info(f"Telegram test requested by user {current_user.username}: {'success' if result['success'] else 'failed'}")
        
        return TestAlertResponse(
            success=result['success'],
            message=result['message'],
            error=result.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Telegram alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test Telegram alert: {str(e)}")

@router.post("/test/webhook", response_model=TestAlertResponse)
@limiter.limit("5/minute")
async def test_webhook_alert(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Send test webhook alert
    
    Tests the webhook alert configuration by sending a test payload.
    Requires webhook to be enabled and URL configured.
    
    Returns:
    - Success status
    - Error details if failed
    """
    try:
        if not alert_manager.preferences.webhook_enabled:
            raise HTTPException(status_code=400, detail="Webhook alerts are not enabled")
        
        if not alert_manager.preferences.webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL not configured")
        
        result = await alert_manager.test_webhook()
        
        logger.info(f"Webhook test requested by user {current_user.username}: {'success' if result['success'] else 'failed'}")
        
        return TestAlertResponse(
            success=result['success'],
            message=result['message'],
            error=result.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test webhook alert: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications
    
    Provides real-time in-app notifications for alerts.
    Clients connect to receive immediate alert updates.
    """
    await websocket.accept()
    alert_manager.add_websocket_connection(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        alert_manager.remove_websocket_connection(websocket)
        logger.debug("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        alert_manager.remove_websocket_connection(websocket)

@router.post("/send-test-signal")
@limiter.limit("3/minute")
async def send_test_signal_alert(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Send a test signal alert through all enabled channels
    
    This endpoint is for testing the complete alert workflow
    with a realistic signal payload.
    """
    try:
        # Create test signal data
        test_signal = {
            "symbol": "BTCUSDT",
            "direction": "BUY",
            "signal_type": "Order Block",
            "entry_price": 43250.00,
            "stop_loss": 42800.00,
            "take_profit": 44150.00,
            "confluence_score": 85,
            "ml_probability": 0.71,
            "session": "london",
            "timeframes": ["4H", "1H", "15M"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        success = await alert_manager.send_signal_alert(test_signal)
        
        logger.info(f"Test signal alert sent by user {current_user.username}: {'success' if success else 'failed'}")
        
        return {
            "success": success,
            "message": "Test signal alert sent through all enabled channels" if success else "Test signal alert failed",
            "signal_data": test_signal
        }
        
    except Exception as e:
        logger.error(f"Error sending test signal alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test signal alert: {str(e)}")

@router.get("/health")
async def alert_health_check():
    """Health check for alert management service"""
    try:
        preferences = alert_manager.get_preferences()
        stats = alert_manager.get_alert_statistics()
        
        return {
            "status": "healthy",
            "service": "alert-manager",
            "channels_enabled": {
                "telegram": preferences.get('telegram_enabled', False),
                "email": preferences.get('email_enabled', False),
                "webhook": preferences.get('webhook_enabled', False),
                "in_app": True
            },
            "websocket_connections": len(alert_manager.websocket_connections),
            "total_alerts": stats.get('total_alerts', 0),
            "success_rate": f"{stats.get('success_rate', 0):.1f}%",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alert health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "alert-manager",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }