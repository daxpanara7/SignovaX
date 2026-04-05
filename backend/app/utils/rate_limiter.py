"""
Rate Limiting System using SlowAPI
Protects API endpoints from abuse and brute force attacks
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings

# Get settings
settings = get_settings()

# Configure logging
logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting
    Uses IP address by default, but can be extended to use user ID for authenticated requests
    """
    # Try to get user from JWT token if available
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you might decode the JWT to get user ID
            # For now, we'll use IP address
            pass
    except Exception:
        pass
    
    # Use IP address as identifier
    client_ip = get_remote_address(request)
    logger.debug(f"Rate limiting client identifier: {client_ip}")
    return client_ip


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    enabled=settings.RATE_LIMIT_ENABLED
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    client_id = get_client_identifier(request)
    logger.warning(f"Rate limit exceeded for client {client_id}: {exc.detail}")
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": exc.detail,
            "retry_after": exc.retry_after,
            "message": "Too many requests. Please try again later."
        }
    )
    
    # Add retry-after header
    if exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)
    
    return response


# Rate limiting decorators for different endpoint types
def auth_rate_limit():
    """Rate limit for authentication endpoints (5 requests/minute)"""
    return limiter.limit("5/minute")


def analysis_rate_limit():
    """Rate limit for analysis endpoints (10 requests/minute)"""
    return limiter.limit("10/minute")


def backtest_rate_limit():
    """Rate limit for backtest endpoints (5 requests/minute)"""
    return limiter.limit("5/minute")


def signals_rate_limit():
    """Rate limit for signals endpoints (30 requests/minute)"""
    return limiter.limit("30/minute")


def data_rate_limit():
    """Rate limit for data endpoints (60 requests/minute)"""
    return limiter.limit("60/minute")


def general_rate_limit():
    """General rate limit for other endpoints (100 requests/minute)"""
    return limiter.limit("100/minute")


# Rate limiting middleware
class RateLimitMiddleware:
    """Rate limiting middleware for additional protection"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request through rate limiting middleware"""
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Check for suspicious patterns
            if self._is_suspicious_request(request):
                logger.warning(f"Suspicious request detected from {get_client_identifier(request)}")
                
                # Return rate limit response
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "Request blocked",
                        "message": "Suspicious activity detected"
                    }
                )
                await response(scope, receive, send)
                return
        
        # Continue with normal processing
        await self.app(scope, receive, send)
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Check for suspicious request patterns"""
        # Check for common attack patterns
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Block requests without user agent
        if not user_agent:
            return True
        
        # Block common bot patterns
        suspicious_agents = [
            "bot", "crawler", "spider", "scraper", "scanner",
            "curl", "wget", "python-requests"
        ]
        
        for pattern in suspicious_agents:
            if pattern in user_agent:
                return True
        
        # Check for SQL injection patterns in query parameters
        query_string = str(request.url.query).lower()
        sql_patterns = ["union", "select", "drop", "insert", "delete", "update", "'", "\"", ";"]
        
        for pattern in sql_patterns:
            if pattern in query_string:
                return True
        
        return False


# Rate limit configuration for different endpoints
RATE_LIMITS = {
    # Authentication endpoints
    "/api/auth/login": "5/minute",
    "/api/auth/refresh": "10/minute",
    
    # Analysis endpoints
    "/api/analysis/*": "10/minute",
    "/api/smc/*": "10/minute",
    "/api/mtf/*": "10/minute",
    
    # Backtest endpoints
    "/api/backtest/*": "5/minute",
    "/api/advanced-backtest/*": "5/minute",
    
    # Signal endpoints
    "/api/signals/*": "30/minute",
    
    # Risk endpoints
    "/api/risk/*": "20/minute",
    
    # Data endpoints
    "/api/data/*": "60/minute",
    
    # Default for other endpoints
    "*": "100/minute"
}


def get_rate_limit_for_path(path: str) -> str:
    """Get rate limit configuration for a specific path"""
    # Check for exact match first
    if path in RATE_LIMITS:
        return RATE_LIMITS[path]
    
    # Check for wildcard matches
    for pattern, limit in RATE_LIMITS.items():
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            if path.startswith(prefix):
                return limit
    
    # Return default
    return RATE_LIMITS["*"]


def log_rate_limit_info():
    """Log rate limiting configuration"""
    if settings.RATE_LIMIT_ENABLED:
        logger.info("Rate limiting enabled with the following limits:")
        for path, limit in RATE_LIMITS.items():
            logger.info(f"  {path}: {limit}")
    else:
        logger.warning("Rate limiting is DISABLED")


# Initialize rate limiting logging
log_rate_limit_info()