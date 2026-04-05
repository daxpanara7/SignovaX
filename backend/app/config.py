"""
Application Configuration using Pydantic BaseSettings
Loads configuration from environment variables and .env file
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    APP_ENV: str = "development"
    APP_NAME: str = "SMC Trading System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./smc_trading.db"
    
    # SMTP Configuration for Email Alerts
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    
    # External API settings
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    
    # Additional data sources
    FINNHUB_API_KEY: Optional[str] = None
    COINMARKETCAP_API_KEY: Optional[str] = None
    
    # Telegram settings (for notifications)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Trading settings
    MAX_DAILY_LOSS_PCT: float = 0.05  # 5% maximum daily loss
    DEFAULT_RISK_PCT: float = 0.01    # 1% default risk per trade
    
    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = True
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v):
        """Validate application environment"""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"APP_ENV must be one of: {allowed_envs}")
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v, info):
        """Validate secret key in production"""
        if info.data.get("APP_ENV") == "production" and v == "your-secret-key-here-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production environment")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("MAX_DAILY_LOSS_PCT")
    @classmethod
    def validate_max_daily_loss(cls, v):
        """Validate maximum daily loss percentage"""
        if v <= 0 or v > 1:
            raise ValueError("MAX_DAILY_LOSS_PCT must be between 0 and 1 (0-100%)")
        return v
    
    @field_validator("DEFAULT_RISK_PCT")
    @classmethod
    def validate_default_risk(cls, v):
        """Validate default risk percentage"""
        if v <= 0 or v > 0.1:
            raise ValueError("DEFAULT_RISK_PCT must be between 0 and 0.1 (0-10%)")
        return v
    

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {allowed_levels}")
        return v.upper()
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.APP_ENV == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL"""
        return self.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite:///")
    
    class Config:
        env_file = "backend/.env" if os.path.exists("backend/.env") else ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create settings instance
settings = get_settings()


def create_env_file():
    """Create .env file with default values if it doesn't exist"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        env_content = """# SMC Trading System Environment Configuration

# Application Environment (development, staging, production)
APP_ENV=development

# Security Settings
SECRET_KEY=your-secret-key-here-change-in-production-must-be-32-chars-minimum

# Database Configuration
DATABASE_URL=sqlite:///./smc_trading.db

# External API Keys (Optional)
BINANCE_API_KEY=
BINANCE_SECRET_KEY=

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Trading Configuration
MAX_DAILY_LOSS_PCT=0.05
DEFAULT_RISK_PCT=0.01

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1
"""
        
        with open(env_path, "w") as f:
            f.write(env_content)
        
        print(f"Created {env_path} with default configuration")
        print("Please update the SECRET_KEY and other settings as needed")


# Validation function for startup
def validate_configuration():
    """Validate configuration on startup"""
    try:
        settings = get_settings()
        
        # Check critical settings
        if settings.is_production and settings.SECRET_KEY == "your-secret-key-here-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production")
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        print(f"Configuration validated successfully")
        print(f"Environment: {settings.APP_ENV}")
        print(f"Debug mode: {settings.DEBUG}")
        print(f"Database: {settings.DATABASE_URL}")
        print(f"Log level: {settings.LOG_LEVEL}")
        
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Validate configuration
    validate_configuration()