"""
JWT Authentication System for SMC Trading Platform
Handles user authentication, token generation, and security middleware
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

from app.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Settings
settings = get_settings()

# Algorithm for JWT
ALGORITHM = "HS256"

# Demo user database (in production, use proper database)
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": bcrypt.hashpw("smc_admin_2024".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "is_active": True,
        "permissions": ["read", "write", "admin"]
    }
}


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class UserInfo(BaseModel):
    """User information model"""
    username: str
    is_active: bool
    permissions: list


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user credentials"""
    user = DEMO_USERS.get(username)
    if not user:
        logger.warning(f"Authentication attempt for non-existent user: {username}")
        return None
    
    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"Failed password attempt for user: {username}")
        return None
    
    if not user["is_active"]:
        logger.warning(f"Authentication attempt for inactive user: {username}")
        return None
    
    logger.info(f"Successful authentication for user: {username}")
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)  # 24 hours default
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Created access token for user: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token (longer expiry)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    to_encode.update({"exp": expire, "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Created refresh token for user: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create refresh token"
        )


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            logger.warning("Token verification failed: no username in payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user still exists and is active
        user = DEMO_USERS.get(username)
        if not user or not user["is_active"]:
            logger.warning(f"Token verification failed: user {username} not found or inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Token verified successfully for user: {username}")
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication verification failed"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """Get current authenticated user from token"""
    try:
        payload = verify_token(credentials.credentials)
        username = payload.get("sub")
        
        user = DEMO_USERS.get(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return UserInfo(
            username=user["username"],
            is_active=user["is_active"],
            permissions=user["permissions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not validate credentials"
        )


def require_permission(required_permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if required_permission not in current_user.permissions:
            logger.warning(f"Permission denied for user {current_user.username}: requires {required_permission}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        return current_user
    
    return permission_checker


def login_user(username: str, password: str) -> TokenResponse:
    """Login user and return tokens"""
    user = authenticate_user(username, password)
    if not user:
        logger.warning(f"Login failed for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user["username"], "permissions": user["permissions"]},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {username} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )


def refresh_access_token(refresh_token: str) -> TokenResponse:
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if user still exists and is active
        user = DEMO_USERS.get(username)
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(hours=24)
        access_token = create_access_token(
            data={"sub": user["username"], "permissions": user["permissions"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Access token refreshed for user: {username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not refresh token"
        )


# Optional: Admin user creation function for production setup
def create_admin_user(username: str, password: str) -> bool:
    """Create admin user (for production setup)"""
    try:
        if username in DEMO_USERS:
            logger.warning(f"Attempt to create existing user: {username}")
            return False
        
        hashed_password = get_password_hash(password)
        DEMO_USERS[username] = {
            "username": username,
            "hashed_password": hashed_password,
            "is_active": True,
            "permissions": ["read", "write", "admin"]
        }
        
        logger.info(f"Admin user created: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return False