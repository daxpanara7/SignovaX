"""
Authentication API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
import logging

from app.auth.auth import (
    LoginRequest, TokenResponse, RefreshTokenRequest, UserInfo,
    login_user, refresh_access_token, get_current_user, security
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User login endpoint
    
    Authenticates user credentials and returns JWT access token.
    Token expires in 24 hours.
    
    Default demo credentials:
    - Username: admin
    - Password: smc_admin_2024
    
    Args:
        request: Login credentials (username and password)
        
    Returns:
        JWT access token with expiration info
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")
        
        # Validate input
        if not request.username or not request.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        if len(request.username) < 3 or len(request.username) > 50:
            raise HTTPException(status_code=400, detail="Username must be between 3 and 50 characters")
        
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Authenticate and return token
        token_response = login_user(request.username, request.password)
        
        logger.info(f"Successful login for user: {request.username}")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token
    
    Uses a valid refresh token to generate a new access token.
    Refresh tokens are valid for 7 days.
    
    Args:
        request: Refresh token request
        
    Returns:
        New JWT access token
    """
    try:
        logger.info("Token refresh attempt")
        
        if not request.refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")
        
        # Refresh the token
        token_response = refresh_access_token(request.refresh_token)
        
        logger.info("Token refreshed successfully")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: UserInfo = Depends(get_current_user)):
    """
    Get current user information
    
    Returns information about the currently authenticated user.
    Requires valid JWT token in Authorization header.
    
    Returns:
        Current user information including permissions
    """
    try:
        logger.debug(f"User info requested for: {current_user.username}")
        return current_user
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve user information")


@router.post("/logout")
async def logout(current_user: UserInfo = Depends(get_current_user)):
    """
    User logout endpoint
    
    Logs out the current user. In a stateless JWT system, this mainly
    serves as a confirmation endpoint. Client should discard the token.
    
    Returns:
        Logout confirmation message
    """
    try:
        logger.info(f"User logout: {current_user.username}")
        
        return {
            "message": "Successfully logged out",
            "username": current_user.username,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/validate")
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate JWT token
    
    Validates the provided JWT token and returns validation status.
    Useful for client-side token validation.
    
    Returns:
        Token validation status and user info
    """
    try:
        from app.auth.auth import verify_token
        
        payload = verify_token(credentials.credentials)
        username = payload.get("sub")
        
        logger.debug(f"Token validation successful for user: {username}")
        
        return {
            "valid": True,
            "username": username,
            "expires_at": payload.get("exp"),
            "permissions": payload.get("permissions", [])
        }
        
    except HTTPException as e:
        logger.warning(f"Token validation failed: {e.detail}")
        return {
            "valid": False,
            "error": e.detail
        }
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token validation failed")


@router.get("/permissions")
async def get_user_permissions(current_user: UserInfo = Depends(get_current_user)):
    """
    Get current user permissions
    
    Returns the list of permissions for the currently authenticated user.
    
    Returns:
        User permissions list
    """
    try:
        logger.debug(f"Permissions requested for user: {current_user.username}")
        
        return {
            "username": current_user.username,
            "permissions": current_user.permissions,
            "is_admin": "admin" in current_user.permissions,
            "can_read": "read" in current_user.permissions,
            "can_write": "write" in current_user.permissions
        }
        
    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve permissions")