"""
Comprehensive Logging System for SMC Trading Platform
Handles application logging with rotation, formatting, and multiple outputs
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
import json

from app.config import get_settings

# Get settings
settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'symbol'):
            log_entry["symbol"] = record.symbol
        if hasattr(record, 'trade_id'):
            log_entry["trade_id"] = record.trade_id
        
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = f"{color}[{timestamp}] [{record.levelname}] [{record.name}] {record.getMessage()}{reset}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging():
    """Setup comprehensive logging system"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # Use JSON formatter for file output
    if settings.is_production:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    
    # Console handler (only in development)
    if settings.is_development:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized - Level: {settings.LOG_LEVEL}, File: {settings.LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with proper configuration"""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(self.__class__.__name__)


def log_api_request(method: str, path: str, user: Optional[str] = None, 
                   status_code: Optional[int] = None, duration: Optional[float] = None):
    """Log API request with details"""
    logger = logging.getLogger("api")
    
    message = f"{method} {path}"
    if user:
        message += f" - User: {user}"
    if status_code:
        message += f" - Status: {status_code}"
    if duration:
        message += f" - Duration: {duration:.3f}s"
    
    if status_code and status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)


def log_signal_generated(symbol: str, signal_type: str, confidence: float, 
                        entry: float, sl: float, tp: float, reasoning: str):
    """Log signal generation"""
    logger = logging.getLogger("signals")
    
    message = f"Signal generated: {symbol} {signal_type} - Entry: {entry}, SL: {sl}, TP: {tp}, Confidence: {confidence}%, Reason: {reasoning}"
    
    # Add structured data
    extra = {
        'symbol': symbol,
        'signal_type': signal_type,
        'confidence': confidence,
        'entry': entry,
        'sl': sl,
        'tp': tp
    }
    
    logger.info(message, extra=extra)


def log_trade_executed(trade_id: str, symbol: str, action: str, price: float, 
                      quantity: float, pnl: Optional[float] = None):
    """Log trade execution"""
    logger = logging.getLogger("trades")
    
    message = f"Trade executed: {trade_id} - {symbol} {action} {quantity} @ {price}"
    if pnl is not None:
        message += f" - P&L: {pnl}"
    
    # Add structured data
    extra = {
        'trade_id': trade_id,
        'symbol': symbol,
        'action': action,
        'price': price,
        'quantity': quantity
    }
    
    if pnl is not None:
        extra['pnl'] = pnl
    
    logger.info(message, extra=extra)


def log_circuit_breaker_trigger(reason: str, loss_pct: float, max_loss_pct: float):
    """Log circuit breaker trigger"""
    logger = logging.getLogger("risk")
    
    message = f"CIRCUIT BREAKER TRIGGERED: {reason} - Loss: {loss_pct:.2%}, Max: {max_loss_pct:.2%}"
    
    # Add structured data
    extra = {
        'circuit_breaker': True,
        'loss_pct': loss_pct,
        'max_loss_pct': max_loss_pct,
        'reason': reason
    }
    
    logger.critical(message, extra=extra)


def log_error(error: Exception, context: Optional[str] = None, **kwargs):
    """Log error with context"""
    logger = logging.getLogger("errors")
    
    message = f"Error occurred: {str(error)}"
    if context:
        message = f"{context}: {message}"
    
    # Add structured data
    extra = {
        'error_type': type(error).__name__,
        'error_message': str(error)
    }
    extra.update(kwargs)
    
    logger.error(message, extra=extra, exc_info=True)


def log_performance_metric(metric_name: str, value: float, symbol: Optional[str] = None, 
                          timeframe: Optional[str] = None):
    """Log performance metric"""
    logger = logging.getLogger("performance")
    
    message = f"Performance metric: {metric_name} = {value}"
    if symbol:
        message += f" ({symbol}"
        if timeframe:
            message += f" {timeframe}"
        message += ")"
    
    # Add structured data
    extra = {
        'metric_name': metric_name,
        'metric_value': value
    }
    
    if symbol:
        extra['symbol'] = symbol
    if timeframe:
        extra['timeframe'] = timeframe
    
    logger.info(message, extra=extra)


def log_system_event(event_type: str, message: str, **kwargs):
    """Log system event"""
    logger = logging.getLogger("system")
    
    full_message = f"System event [{event_type}]: {message}"
    
    # Add structured data
    extra = {
        'event_type': event_type
    }
    extra.update(kwargs)
    
    logger.info(full_message, extra=extra)


# Initialize logging on import
if not logging.getLogger().handlers:
    setup_logging()