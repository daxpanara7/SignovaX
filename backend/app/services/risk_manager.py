"""
Risk Management System for SMC Trading Platform
Handles position sizing, risk validation, circuit breakers, and correlation management
"""

import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
import json

from app.models.risk_models import (
    RiskValidationResult, CircuitBreakerStatus, RiskMetrics,
    PositionSizeResponse, DailyRiskLog, CorrelationGroup, OpenTrade
)
from app.models.signals import TradingSignal, SignalType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """Risk management configuration"""
    account_balance: float = 10000.0
    risk_per_trade: float = 0.01  # 1% default
    max_daily_loss: float = 0.05  # 5% circuit breaker
    min_risk_reward: float = 2.0  # minimum 1:2 R:R
    max_concurrent_trades: int = 3
    max_correlated_trades: int = 1  # same direction, same asset class


class RiskManager:
    """Complete Risk Management System"""
    
    def __init__(self, config: RiskConfig = None, db_path: str = "risk_management.db"):
        self.config = config or RiskConfig()
        self.db_path = db_path
        self.circuit_breaker_active = False
        self.circuit_breaker_triggered_at = None
        self.open_trades: List[OpenTrade] = []
        
        # Initialize database
        self._init_database()
        
        # Load today's risk state
        self._load_daily_state()
        
        logger.info(f"RiskManager initialized with balance: ${self.config.account_balance}")
    
    def _init_database(self):
        """Initialize SQLite database for risk management"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create daily_risk_log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_risk_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    starting_balance REAL NOT NULL,
                    current_balance REAL NOT NULL,
                    trades_taken INTEGER DEFAULT 0,
                    daily_pnl REAL DEFAULT 0.0,
                    circuit_breaker_triggered BOOLEAN DEFAULT FALSE,
                    max_drawdown REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create open_trades table for tracking active positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS open_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    position_size REAL NOT NULL,
                    unrealized_pnl REAL DEFAULT 0.0,
                    correlation_group TEXT,
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Risk management database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def _load_daily_state(self):
        """Load today's risk state from database"""
        try:
            today = date.today()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get today's risk log
            cursor.execute("""
                SELECT current_balance, trades_taken, daily_pnl, circuit_breaker_triggered
                FROM daily_risk_log 
                WHERE date = ?
            """, (today,))
            
            result = cursor.fetchone()
            if result:
                current_balance, trades_taken, daily_pnl, cb_triggered = result
                self.config.account_balance = current_balance
                self.circuit_breaker_active = bool(cb_triggered)
                if self.circuit_breaker_active:
                    self.circuit_breaker_triggered_at = datetime.now()
            else:
                # Create today's entry
                self._create_daily_log_entry(today)
            
            # Load open trades
            cursor.execute("SELECT * FROM open_trades")
            trades_data = cursor.fetchall()
            
            self.open_trades = []
            for trade_data in trades_data:
                trade = OpenTrade(
                    symbol=trade_data[1],
                    direction=trade_data[2],
                    entry_price=trade_data[3],
                    stop_loss=trade_data[4],
                    take_profit=trade_data[5],
                    position_size=trade_data[6],
                    unrealized_pnl=trade_data[7],
                    correlation_group=CorrelationGroup(trade_data[8]) if trade_data[8] else CorrelationGroup.CRYPTO
                )
                self.open_trades.append(trade)
            
            conn.close()
            logger.info(f"Daily state loaded: Balance ${self.config.account_balance}, Open trades: {len(self.open_trades)}")
            
        except Exception as e:
            logger.error(f"Error loading daily state: {str(e)}")
    
    def _create_daily_log_entry(self, log_date: date):
        """Create new daily log entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_risk_log 
                (date, starting_balance, current_balance, trades_taken, daily_pnl)
                VALUES (?, ?, ?, 0, 0.0)
            """, (log_date, self.config.account_balance, self.config.account_balance))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating daily log entry: {str(e)}")
    
    def calculate_position_size(
        self, 
        entry: float, 
        sl: float, 
        account_balance: Optional[float] = None, 
        risk_pct: Optional[float] = None
    ) -> PositionSizeResponse:
        """
        Calculate position size based on risk parameters
        
        Formula:
        - risk_amount = balance * risk_pct
        - pip_risk = abs(entry - sl)
        - position_size = risk_amount / pip_risk
        
        Args:
            entry: Entry price
            sl: Stop loss price
            account_balance: Account balance (uses config if None)
            risk_pct: Risk percentage (uses config if None)
            
        Returns:
            PositionSizeResponse with calculated values
        """
        balance = account_balance or self.config.account_balance
        risk_percentage = risk_pct or self.config.risk_per_trade
        
        # Calculate risk amount
        risk_amount = balance * risk_percentage
        
        # Calculate pip risk (distance to stop loss)
        pip_risk = abs(entry - sl)
        
        if pip_risk == 0:
            raise ValueError("Entry price cannot equal stop loss price")
        
        # Calculate position size
        position_size = risk_amount / pip_risk
        
        logger.info(f"Position size calculated: {position_size:.4f} units for ${risk_amount:.2f} risk")
        
        return PositionSizeResponse(
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            pip_risk=round(pip_risk, 4),
            risk_pct=risk_percentage
        )
    
    def validate_signal(self, signal: TradingSignal) -> RiskValidationResult:
        """
        Validate trading signal against all risk parameters
        
        Checks:
        - R:R ratio >= min_risk_reward
        - Daily loss not exceeded
        - Concurrent trade limit
        - Correlation with open trades
        
        Args:
            signal: Trading signal to validate
            
        Returns:
            RiskValidationResult with approval status and reason
        """
        logger.info(f"Validating signal: {signal.symbol} {signal.signal_type}")
        
        try:
            # Check circuit breaker first
            if self.circuit_breaker_active:
                return RiskValidationResult(
                    approved=False,
                    reason="Circuit breaker active - trading halted due to daily loss limit"
                )
            
            # Check R:R ratio
            pip_risk = abs(signal.entry_price - signal.stop_loss)
            pip_reward = abs(signal.take_profit - signal.entry_price)
            
            if pip_risk == 0:
                return RiskValidationResult(
                    approved=False,
                    reason="Invalid signal: Entry price equals stop loss"
                )
            
            risk_reward_ratio = pip_reward / pip_risk
            
            if risk_reward_ratio < self.config.min_risk_reward:
                return RiskValidationResult(
                    approved=False,
                    reason=f"R:R ratio {risk_reward_ratio:.2f} below minimum {self.config.min_risk_reward}"
                )
            
            # Check concurrent trades limit
            if len(self.open_trades) >= self.config.max_concurrent_trades:
                return RiskValidationResult(
                    approved=False,
                    reason=f"Maximum concurrent trades ({self.config.max_concurrent_trades}) reached"
                )
            
            # Check correlation limits
            correlation_check = self._check_correlation_limits(signal)
            if not correlation_check["allowed"]:
                return RiskValidationResult(
                    approved=False,
                    reason=correlation_check["reason"]
                )
            
            # Calculate position size
            position_calc = self.calculate_position_size(
                signal.entry_price, 
                signal.stop_loss
            )
            
            # All checks passed
            logger.info(f"Signal approved: {signal.symbol} with position size {position_calc.position_size}")
            
            return RiskValidationResult(
                approved=True,
                reason="Signal approved - all risk checks passed",
                position_size=position_calc.position_size,
                risk_amount=position_calc.risk_amount,
                risk_reward_ratio=risk_reward_ratio
            )
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return RiskValidationResult(
                approved=False,
                reason=f"Validation error: {str(e)}"
            )
    
    def check_circuit_breaker(self) -> CircuitBreakerStatus:
        """
        Check if circuit breaker should be triggered
        
        Calculates today's realized + unrealized P&L
        If loss > max_daily_loss * balance → halt all trading
        
        Returns:
            CircuitBreakerStatus with current status
        """
        try:
            # Calculate total daily P&L (realized + unrealized)
            daily_pnl = self._calculate_daily_pnl()
            daily_loss_pct = abs(daily_pnl) / self.config.account_balance
            
            # Check if circuit breaker should trigger
            should_trigger = (
                daily_pnl < 0 and 
                daily_loss_pct >= self.config.max_daily_loss and 
                not self.circuit_breaker_active
            )
            
            if should_trigger:
                self._trigger_circuit_breaker(daily_loss_pct)
                
                return CircuitBreakerStatus(
                    active=True,
                    triggered_at=self.circuit_breaker_triggered_at,
                    daily_loss_pct=daily_loss_pct,
                    max_allowed_loss_pct=self.config.max_daily_loss,
                    reason=f"Daily loss {daily_loss_pct:.2%} exceeded maximum {self.config.max_daily_loss:.2%}"
                )
            
            return CircuitBreakerStatus(
                active=self.circuit_breaker_active,
                triggered_at=self.circuit_breaker_triggered_at,
                daily_loss_pct=daily_loss_pct,
                max_allowed_loss_pct=self.config.max_daily_loss,
                reason="Circuit breaker not triggered" if not self.circuit_breaker_active else "Circuit breaker active"
            )
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {str(e)}")
            return CircuitBreakerStatus(
                active=False,
                triggered_at=None,
                daily_loss_pct=0.0,
                max_allowed_loss_pct=self.config.max_daily_loss,
                reason=f"Error checking circuit breaker: {str(e)}"
            )
    
    def get_correlated_pairs(self) -> Dict[str, List[str]]:
        """
        Get correlation groups for risk management
        
        Returns:
            Dict mapping correlation group names to symbol lists
        """
        correlation_groups = {
            "crypto": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT"],
            "forex_usd": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD"],
            "forex_eur": ["EURJPY", "EURGBP", "EURAUD", "EURCHF"],
            "commodities": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
            "indices": ["US30", "US500", "NAS100", "GER30", "UK100"]
        }
        
        return correlation_groups
    
    def _check_correlation_limits(self, signal: TradingSignal) -> Dict[str, any]:
        """Check if signal violates correlation limits"""
        try:
            # Get correlation group for the signal symbol
            signal_group = self._get_correlation_group(signal.symbol)
            
            if not signal_group:
                return {"allowed": True, "reason": "No correlation group found"}
            
            # Count same-direction trades in the same correlation group
            same_direction_count = 0
            for trade in self.open_trades:
                if (trade.correlation_group == signal_group and 
                    trade.direction == signal.signal_type.value):
                    same_direction_count += 1
            
            if same_direction_count >= self.config.max_correlated_trades:
                return {
                    "allowed": False,
                    "reason": f"Maximum correlated trades ({self.config.max_correlated_trades}) "
                             f"reached for {signal_group.value} group in {signal.signal_type.value} direction"
                }
            
            return {"allowed": True, "reason": "Correlation check passed"}
            
        except Exception as e:
            logger.error(f"Error checking correlation limits: {str(e)}")
            return {"allowed": False, "reason": f"Correlation check error: {str(e)}"}
    
    def _get_correlation_group(self, symbol: str) -> Optional[CorrelationGroup]:
        """Get correlation group for a symbol"""
        correlation_groups = self.get_correlated_pairs()
        
        for group_name, symbols in correlation_groups.items():
            if symbol in symbols:
                return CorrelationGroup(group_name)
        
        # Default to crypto for unknown symbols
        return CorrelationGroup.CRYPTO
    
    def _calculate_daily_pnl(self) -> float:
        """Calculate total daily P&L (realized + unrealized)"""
        try:
            # Get realized P&L from database
            today = date.today()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT daily_pnl FROM daily_risk_log WHERE date = ?
            """, (today,))
            
            result = cursor.fetchone()
            realized_pnl = result[0] if result else 0.0
            
            # Calculate unrealized P&L from open trades
            unrealized_pnl = sum(trade.unrealized_pnl for trade in self.open_trades)
            
            conn.close()
            
            total_pnl = realized_pnl + unrealized_pnl
            logger.info(f"Daily P&L: Realized ${realized_pnl:.2f}, Unrealized ${unrealized_pnl:.2f}, Total ${total_pnl:.2f}")
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"Error calculating daily P&L: {str(e)}")
            return 0.0
    
    def _trigger_circuit_breaker(self, loss_pct: float):
        """Trigger circuit breaker and log the event"""
        try:
            self.circuit_breaker_active = True
            self.circuit_breaker_triggered_at = datetime.now()
            
            # Update database
            today = date.today()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE daily_risk_log 
                SET circuit_breaker_triggered = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            """, (today,))
            
            conn.commit()
            conn.close()
            
            logger.critical(f"CIRCUIT BREAKER TRIGGERED! Daily loss: {loss_pct:.2%} at {self.circuit_breaker_triggered_at}")
            
            # TODO: Emit WebSocket event to frontend
            # self._emit_circuit_breaker_event()
            
        except Exception as e:
            logger.error(f"Error triggering circuit breaker: {str(e)}")
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        try:
            daily_pnl = self._calculate_daily_pnl()
            daily_loss_pct = abs(daily_pnl) / self.config.account_balance if daily_pnl < 0 else 0.0
            
            # Get today's trade count
            today = date.today()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT trades_taken FROM daily_risk_log WHERE date = ?
            """, (today,))
            
            result = cursor.fetchone()
            trades_today = result[0] if result else 0
            
            conn.close()
            
            return RiskMetrics(
                account_balance=self.config.account_balance,
                daily_pnl=daily_pnl,
                daily_loss_pct=daily_loss_pct,
                trades_today=trades_today,
                concurrent_trades=len(self.open_trades),
                max_concurrent_trades=self.config.max_concurrent_trades,
                circuit_breaker_active=self.circuit_breaker_active,
                risk_per_trade=self.config.risk_per_trade,
                max_daily_loss=self.config.max_daily_loss
            )
            
        except Exception as e:
            logger.error(f"Error getting risk metrics: {str(e)}")
            return RiskMetrics(
                account_balance=self.config.account_balance,
                daily_pnl=0.0,
                daily_loss_pct=0.0,
                trades_today=0,
                concurrent_trades=0,
                max_concurrent_trades=self.config.max_concurrent_trades,
                circuit_breaker_active=False,
                risk_per_trade=self.config.risk_per_trade,
                max_daily_loss=self.config.max_daily_loss
            )
    
    def add_open_trade(self, trade: OpenTrade):
        """Add a new open trade to tracking"""
        try:
            self.open_trades.append(trade)
            
            # Add to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO open_trades 
                (symbol, direction, entry_price, stop_loss, take_profit, position_size, correlation_group)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.symbol, trade.direction, trade.entry_price, trade.stop_loss,
                trade.take_profit, trade.position_size, trade.correlation_group.value
            ))
            
            # Update daily trade count
            today = date.today()
            cursor.execute("""
                UPDATE daily_risk_log 
                SET trades_taken = trades_taken + 1, updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            """, (today,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added open trade: {trade.symbol} {trade.direction}")
            
        except Exception as e:
            logger.error(f"Error adding open trade: {str(e)}")
    
    def remove_open_trade(self, symbol: str, direction: str):
        """Remove an open trade from tracking"""
        try:
            # Remove from memory
            self.open_trades = [
                trade for trade in self.open_trades 
                if not (trade.symbol == symbol and trade.direction == direction)
            ]
            
            # Remove from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM open_trades 
                WHERE symbol = ? AND direction = ?
            """, (symbol, direction))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Removed open trade: {symbol} {direction}")
            
        except Exception as e:
            logger.error(f"Error removing open trade: {str(e)}")
    
    def update_trade_pnl(self, symbol: str, direction: str, unrealized_pnl: float):
        """Update unrealized P&L for an open trade"""
        try:
            # Update in memory
            for trade in self.open_trades:
                if trade.symbol == symbol and trade.direction == direction:
                    trade.unrealized_pnl = unrealized_pnl
                    break
            
            # Update in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE open_trades 
                SET unrealized_pnl = ?
                WHERE symbol = ? AND direction = ?
            """, (unrealized_pnl, symbol, direction))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating trade P&L: {str(e)}")
    
    def close_trade(self, symbol: str, direction: str, realized_pnl: float):
        """Close a trade and update daily P&L"""
        try:
            # Remove from open trades
            self.remove_open_trade(symbol, direction)
            
            # Update daily P&L
            today = date.today()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE daily_risk_log 
                SET daily_pnl = daily_pnl + ?, 
                    current_balance = current_balance + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            """, (realized_pnl, realized_pnl, today))
            
            conn.commit()
            conn.close()
            
            # Update account balance
            self.config.account_balance += realized_pnl
            
            logger.info(f"Closed trade: {symbol} {direction} with P&L ${realized_pnl:.2f}")
            
            # Check circuit breaker after trade close
            self.check_circuit_breaker()
            
        except Exception as e:
            logger.error(f"Error closing trade: {str(e)}")
    
    def reset_daily_state(self):
        """Reset daily state (for new trading day)"""
        try:
            self.circuit_breaker_active = False
            self.circuit_breaker_triggered_at = None
            
            # Create new daily log entry
            today = date.today()
            self._create_daily_log_entry(today)
            
            logger.info("Daily risk state reset for new trading day")
            
        except Exception as e:
            logger.error(f"Error resetting daily state: {str(e)}")
    
    def get_daily_logs(self, days: int = 30) -> List[DailyRiskLog]:
        """Get daily risk logs for the past N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT date, starting_balance, current_balance, trades_taken, 
                       daily_pnl, circuit_breaker_triggered, max_drawdown, created_at
                FROM daily_risk_log 
                ORDER BY date DESC 
                LIMIT ?
            """, (days,))
            
            results = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in results:
                log = DailyRiskLog(
                    date=datetime.strptime(row[0], '%Y-%m-%d').date(),
                    starting_balance=row[1],
                    current_balance=row[2],
                    trades_taken=row[3],
                    daily_pnl=row[4],
                    circuit_breaker_triggered=bool(row[5]),
                    max_drawdown=row[6],
                    created_at=datetime.fromisoformat(row[7])
                )
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting daily logs: {str(e)}")
            return []