"""
Multi-Channel Alert System for SMC Trading Platform
Handles Telegram, Webhook, Email, and In-App notifications
"""

import asyncio
import json
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import time
import logging

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class AlertType(Enum):
    """Alert type enumeration"""
    SIGNAL = "signal"
    CIRCUIT_BREAKER = "circuit_breaker"
    DAILY_PNL = "daily_pnl"
    SYSTEM = "system"
    ERROR = "error"

class AlertChannel(Enum):
    """Alert channel enumeration"""
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    EMAIL = "email"
    IN_APP = "in_app"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertPreferences:
    """User alert preferences"""
    telegram_enabled: bool = False
    telegram_chat_id: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    email_enabled: bool = False
    email_address: Optional[str] = None
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    min_confluence_to_alert: int = 70
    sessions_to_alert: List[str] = None
    signal_types_to_alert: List[str] = None
    
    def __post_init__(self):
        if self.sessions_to_alert is None:
            self.sessions_to_alert = ["london", "new_york", "overlap"]
        if self.signal_types_to_alert is None:
            self.signal_types_to_alert = ["BOS", "CHOCH", "OB", "FVG"]

@dataclass
class Alert:
    """Alert data structure"""
    id: Optional[int] = None
    type: AlertType = AlertType.SIGNAL
    channel: AlertChannel = AlertChannel.IN_APP
    title: str = ""
    message: str = ""
    payload: Dict[str, Any] = None
    timestamp: datetime = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    status: str = "pending"  # pending, sent, failed
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.payload is None:
            self.payload = {}

class AlertManager:
    """Multi-channel alert management system"""
    
    def __init__(self):
        self.db_path = settings.database_url_sync.replace("sqlite:///", "")
        self.preferences = AlertPreferences()
        self.websocket_connections = set()
        
        # Initialize database
        self._init_database()
        
        # Load preferences
        self._load_preferences()
        
        logger.info("Alert Manager initialized with multi-channel support")
    
    def _init_database(self):
        """Initialize alert database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Alerts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Alert preferences table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alert_preferences (
                        id INTEGER PRIMARY KEY,
                        user_id TEXT DEFAULT 'default',
                        telegram_enabled BOOLEAN DEFAULT 0,
                        telegram_chat_id TEXT,
                        telegram_bot_token TEXT,
                        email_enabled BOOLEAN DEFAULT 0,
                        email_address TEXT,
                        webhook_enabled BOOLEAN DEFAULT 0,
                        webhook_url TEXT,
                        webhook_secret TEXT,
                        min_confluence_to_alert INTEGER DEFAULT 70,
                        sessions_to_alert TEXT DEFAULT '["london","new_york","overlap"]',
                        signal_types_to_alert TEXT DEFAULT '["BOS","CHOCH","OB","FVG"]',
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Indexes for performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                    ON alerts(timestamp DESC)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_alerts_type_status 
                    ON alerts(type, status)
                """)
                
                conn.commit()
                logger.info("Alert database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing alert database: {str(e)}")
    
    def _load_preferences(self):
        """Load alert preferences from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM alert_preferences WHERE user_id = 'default'
                """)
                
                row = cursor.fetchone()
                
                if row:
                    # Map database row to preferences
                    self.preferences = AlertPreferences(
                        telegram_enabled=bool(row[2]),
                        telegram_chat_id=row[3],
                        telegram_bot_token=row[4],
                        email_enabled=bool(row[5]),
                        email_address=row[6],
                        webhook_enabled=bool(row[7]),
                        webhook_url=row[8],
                        webhook_secret=row[9],
                        min_confluence_to_alert=row[10],
                        sessions_to_alert=json.loads(row[11]) if row[11] else ["london", "new_york", "overlap"],
                        signal_types_to_alert=json.loads(row[12]) if row[12] else ["BOS", "CHOCH", "OB", "FVG"]
                    )
                else:
                    # Create default preferences
                    self._save_preferences()
                    
        except Exception as e:
            logger.error(f"Error loading alert preferences: {str(e)}")
    
    def _save_preferences(self):
        """Save alert preferences to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_preferences 
                    (user_id, telegram_enabled, telegram_chat_id, telegram_bot_token,
                     email_enabled, email_address, webhook_enabled, webhook_url, webhook_secret,
                     min_confluence_to_alert, sessions_to_alert, signal_types_to_alert, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'default',
                    self.preferences.telegram_enabled,
                    self.preferences.telegram_chat_id,
                    self.preferences.telegram_bot_token,
                    self.preferences.email_enabled,
                    self.preferences.email_address,
                    self.preferences.webhook_enabled,
                    self.preferences.webhook_url,
                    self.preferences.webhook_secret,
                    self.preferences.min_confluence_to_alert,
                    json.dumps(self.preferences.sessions_to_alert),
                    json.dumps(self.preferences.signal_types_to_alert),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving alert preferences: {str(e)}")
    
    def update_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update alert preferences"""
        try:
            # Update preferences object
            for key, value in preferences.items():
                if hasattr(self.preferences, key):
                    setattr(self.preferences, key, value)
            
            # Save to database
            self._save_preferences()
            
            logger.info("Alert preferences updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert preferences: {str(e)}")
            return False
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get current alert preferences"""
        return asdict(self.preferences)
    
    async def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """Send signal alert through all enabled channels"""
        try:
            # Check if signal meets alert criteria
            if not self._should_alert_for_signal(signal_data):
                logger.debug(f"Signal does not meet alert criteria: {signal_data.get('symbol', 'Unknown')}")
                return False
            
            # Format signal message
            message = self._format_signal_message(signal_data)
            title = f"🚨 SMC Signal: {signal_data.get('symbol', 'Unknown')} {signal_data.get('direction', 'Unknown')}"
            
            # Create alert record
            alert = Alert(
                type=AlertType.SIGNAL,
                title=title,
                message=message,
                payload=signal_data,
                severity=AlertSeverity.HIGH
            )
            
            # Send through all enabled channels
            success = True
            
            if self.preferences.telegram_enabled:
                success &= await self._send_telegram_alert(alert)
            
            if self.preferences.webhook_enabled:
                success &= await self._send_webhook_alert(alert)
            
            if self.preferences.email_enabled:
                success &= await self._send_email_alert(alert)
            
            # Always send in-app notification
            await self._send_in_app_alert(alert)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending signal alert: {str(e)}")
            return False
    
    def _should_alert_for_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Check if signal meets alert criteria"""
        try:
            # Check confluence score
            confluence_score = signal_data.get('confluence_score', 0)
            if confluence_score < self.preferences.min_confluence_to_alert:
                return False
            
            # Check session
            session = signal_data.get('session', '').lower()
            if session not in self.preferences.sessions_to_alert:
                return False
            
            # Check signal type
            signal_type = signal_data.get('signal_type', '').upper()
            if signal_type not in self.preferences.signal_types_to_alert:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert criteria: {str(e)}")
            return False
    
    def _format_signal_message(self, signal_data: Dict[str, Any]) -> str:
        """Format signal data into alert message"""
        try:
            symbol = signal_data.get('symbol', 'Unknown')
            direction = signal_data.get('direction', 'Unknown')
            signal_type = signal_data.get('signal_type', 'Unknown')
            entry_price = signal_data.get('entry_price', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            take_profit = signal_data.get('take_profit', 0)
            confluence_score = signal_data.get('confluence_score', 0)
            ml_probability = signal_data.get('ml_probability', 0)
            session = signal_data.get('session', 'Unknown')
            timeframes = signal_data.get('timeframes', ['4H', '1H', '15M'])
            
            # Calculate R:R ratio
            risk = abs(entry_price - stop_loss) if entry_price and stop_loss else 0
            reward = abs(take_profit - entry_price) if take_profit and entry_price else 0
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Direction emoji
            direction_emoji = "🟢" if direction.upper() == "BUY" else "🔴"
            
            # ML approval
            ml_approval = "✅" if ml_probability >= 0.65 else "❌"
            
            # Format timeframes
            tf_display = " → ".join(timeframes[:3])
            
            message = f"""🚨 SMC SIGNAL ALERT
━━━━━━━━━━━━━━━━
📊 Symbol: {symbol}
⏰ Timeframe: {tf_display}
{direction_emoji} Direction: {direction.upper()}
💡 Type: {signal_type}
━━━━━━━━━━━━━━━━
📍 Entry: ${entry_price:,.2f}
🛑 Stop Loss: ${stop_loss:,.2f}
🎯 Take Profit: ${take_profit:,.2f}
📐 R:R Ratio: 1:{rr_ratio:.1f}
💯 Confluence: {confluence_score}/100
🤖 ML Approval: {ml_approval} {ml_probability:.0%}
━━━━━━━━━━━━━━━━
⏱ Session: {session.title()}
🕐 Time: {datetime.utcnow().strftime('%H:%M UTC')}"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting signal message: {str(e)}")
            return f"Signal Alert: {signal_data.get('symbol', 'Unknown')} - {signal_data.get('direction', 'Unknown')}"
    
    async def _send_telegram_alert(self, alert: Alert) -> bool:
        """Send alert via Telegram"""
        try:
            if not self.preferences.telegram_bot_token or not self.preferences.telegram_chat_id:
                logger.warning("Telegram credentials not configured")
                return False
            
            url = f"https://api.telegram.org/bot{self.preferences.telegram_bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.preferences.telegram_chat_id,
                "text": alert.message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        alert.status = "sent"
                        alert.channel = AlertChannel.TELEGRAM
                        self._store_alert(alert)
                        logger.info(f"Telegram alert sent successfully: {alert.title}")
                        return True
                    else:
                        error_text = await response.text()
                        alert.status = "failed"
                        alert.error_message = f"HTTP {response.status}: {error_text}"
                        alert.channel = AlertChannel.TELEGRAM
                        self._store_alert(alert)
                        logger.error(f"Telegram alert failed: {alert.error_message}")
                        return False
                        
        except Exception as e:
            alert.status = "failed"
            alert.error_message = str(e)
            alert.channel = AlertChannel.TELEGRAM
            self._store_alert(alert)
            logger.error(f"Error sending Telegram alert: {str(e)}")
            return False
    
    async def _send_webhook_alert(self, alert: Alert) -> bool:
        """Send alert via webhook with retry logic"""
        try:
            if not self.preferences.webhook_url:
                logger.warning("Webhook URL not configured")
                return False
            
            payload = {
                "type": alert.type.value,
                "title": alert.title,
                "message": alert.message,
                "data": alert.payload,
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity.value
            }
            
            # Add webhook secret if configured
            headers = {"Content-Type": "application/json"}
            if self.preferences.webhook_secret:
                headers["X-Webhook-Secret"] = self.preferences.webhook_secret
            
            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            self.preferences.webhook_url,
                            json=payload,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status in [200, 201, 202]:
                                alert.status = "sent"
                                alert.channel = AlertChannel.WEBHOOK
                                alert.retry_count = attempt
                                self._store_alert(alert)
                                logger.info(f"Webhook alert sent successfully: {alert.title}")
                                return True
                            else:
                                error_text = await response.text()
                                raise Exception(f"HTTP {response.status}: {error_text}")
                                
                except Exception as retry_error:
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        alert.status = "failed"
                        alert.error_message = str(retry_error)
                        alert.channel = AlertChannel.WEBHOOK
                        alert.retry_count = attempt + 1
                        self._store_alert(alert)
                        logger.error(f"Webhook alert failed after {max_retries} attempts: {retry_error}")
                        return False
                    else:
                        # Wait before retry (exponential backoff)
                        wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                        await asyncio.sleep(wait_time)
                        logger.warning(f"Webhook attempt {attempt + 1} failed, retrying in {wait_time}s: {retry_error}")
            
            return False
            
        except Exception as e:
            alert.status = "failed"
            alert.error_message = str(e)
            alert.channel = AlertChannel.WEBHOOK
            self._store_alert(alert)
            logger.error(f"Error sending webhook alert: {str(e)}")
            return False
    
    async def _send_email_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            if not self.preferences.email_address:
                logger.warning("Email address not configured")
                return False
            
            # Get SMTP configuration from environment
            smtp_host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_user = getattr(settings, 'SMTP_USER', None)
            smtp_pass = getattr(settings, 'SMTP_PASS', None)
            
            if not smtp_user or not smtp_pass:
                logger.warning("SMTP credentials not configured")
                return False
            
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = alert.title
            msg['From'] = smtp_user
            msg['To'] = self.preferences.email_address
            
            # Create HTML content
            html_content = self._format_email_html(alert)
            
            # Create plain text version
            text_content = alert.message
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            alert.status = "sent"
            alert.channel = AlertChannel.EMAIL
            self._store_alert(alert)
            logger.info(f"Email alert sent successfully: {alert.title}")
            return True
            
        except Exception as e:
            alert.status = "failed"
            alert.error_message = str(e)
            alert.channel = AlertChannel.EMAIL
            self._store_alert(alert)
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def _format_email_html(self, alert: Alert) -> str:
        """Format alert as HTML email"""
        try:
            if alert.type == AlertType.SIGNAL:
                signal_data = alert.payload
                symbol = signal_data.get('symbol', 'Unknown')
                direction = signal_data.get('direction', 'Unknown')
                signal_type = signal_data.get('signal_type', 'Unknown')
                entry_price = signal_data.get('entry_price', 0)
                stop_loss = signal_data.get('stop_loss', 0)
                take_profit = signal_data.get('take_profit', 0)
                confluence_score = signal_data.get('confluence_score', 0)
                ml_probability = signal_data.get('ml_probability', 0)
                session = signal_data.get('session', 'Unknown')
                
                # Calculate R:R ratio
                risk = abs(entry_price - stop_loss) if entry_price and stop_loss else 0
                reward = abs(take_profit - entry_price) if take_profit and entry_price else 0
                rr_ratio = reward / risk if risk > 0 else 0
                
                direction_color = "#28a745" if direction.upper() == "BUY" else "#dc3545"
                
                html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                        .content {{ padding: 20px; }}
                        .signal-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                        .direction {{ color: {direction_color}; font-weight: bold; font-size: 18px; }}
                        .price {{ font-family: monospace; font-size: 16px; }}
                        .footer {{ background-color: #6c757d; color: white; padding: 10px; text-align: center; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚨 SMC Signal Alert</h1>
                            <p>{symbol} - {signal_type}</p>
                        </div>
                        <div class="content">
                            <div class="signal-info">
                                <h3>Signal Details</h3>
                                <p><strong>Symbol:</strong> {symbol}</p>
                                <p><strong>Direction:</strong> <span class="direction">{direction.upper()}</span></p>
                                <p><strong>Type:</strong> {signal_type}</p>
                                <p><strong>Session:</strong> {session.title()}</p>
                            </div>
                            <div class="signal-info">
                                <h3>Price Levels</h3>
                                <p><strong>Entry:</strong> <span class="price">${entry_price:,.2f}</span></p>
                                <p><strong>Stop Loss:</strong> <span class="price">${stop_loss:,.2f}</span></p>
                                <p><strong>Take Profit:</strong> <span class="price">${take_profit:,.2f}</span></p>
                                <p><strong>R:R Ratio:</strong> 1:{rr_ratio:.1f}</p>
                            </div>
                            <div class="signal-info">
                                <h3>Analysis</h3>
                                <p><strong>Confluence Score:</strong> {confluence_score}/100</p>
                                <p><strong>ML Probability:</strong> {ml_probability:.1%}</p>
                                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</p>
                            </div>
                        </div>
                        <div class="footer">
                            <p>SMC Trading System - Automated Alert</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                return html
            else:
                # Generic HTML template for other alert types
                return f"""
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2>{alert.title}</h2>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                        <pre>{alert.message}</pre>
                    </div>
                    <p><small>Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</small></p>
                </body>
                </html>
                """
                
        except Exception as e:
            logger.error(f"Error formatting email HTML: {str(e)}")
            return f"<html><body><h2>{alert.title}</h2><p>{alert.message}</p></body></html>"
    
    async def _send_in_app_alert(self, alert: Alert) -> bool:
        """Send in-app notification via WebSocket"""
        try:
            alert.channel = AlertChannel.IN_APP
            alert.status = "sent"
            
            # Store alert in database
            alert_id = self._store_alert(alert)
            alert.id = alert_id
            
            # Send WebSocket notification
            if self.websocket_connections:
                websocket_payload = {
                    "event": "new_alert",
                    "data": {
                        "id": alert.id,
                        "type": alert.type.value,
                        "title": alert.title,
                        "message": alert.message,
                        "payload": alert.payload,
                        "timestamp": alert.timestamp.isoformat(),
                        "severity": alert.severity.value
                    }
                }
                
                # Send to all connected clients
                disconnected = set()
                for websocket in self.websocket_connections:
                    try:
                        await websocket.send_text(json.dumps(websocket_payload))
                    except Exception as ws_error:
                        logger.warning(f"WebSocket send failed: {ws_error}")
                        disconnected.add(websocket)
                
                # Remove disconnected clients
                self.websocket_connections -= disconnected
                
                logger.info(f"In-app alert sent to {len(self.websocket_connections)} clients: {alert.title}")
            else:
                logger.debug("No WebSocket connections for in-app alert")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending in-app alert: {str(e)}")
            return False
    
    def _store_alert(self, alert: Alert) -> Optional[int]:
        """Store alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO alerts 
                    (type, channel, title, message, payload, timestamp, severity, status, error_message, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.type.value,
                    alert.channel.value,
                    alert.title,
                    alert.message,
                    json.dumps(alert.payload),
                    alert.timestamp.isoformat(),
                    alert.severity.value,
                    alert.status,
                    alert.error_message,
                    alert.retry_count
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
            return None
    
    async def send_circuit_breaker_alert(self, reason: str, details: Dict[str, Any]) -> bool:
        """Send circuit breaker alert"""
        try:
            message = f"""🚨 CIRCUIT BREAKER TRIGGERED
━━━━━━━━━━━━━━━━
⚠️ Reason: {reason}
🛑 Trading Halted
⏰ Time: {datetime.utcnow().strftime('%H:%M UTC')}
━━━━━━━━━━━━━━━━
Details: {json.dumps(details, indent=2)}"""
            
            alert = Alert(
                type=AlertType.CIRCUIT_BREAKER,
                title="🚨 Circuit Breaker Triggered",
                message=message,
                payload={"reason": reason, "details": details},
                severity=AlertSeverity.CRITICAL
            )
            
            # Send through all channels (circuit breaker is critical)
            success = True
            
            if self.preferences.telegram_enabled:
                success &= await self._send_telegram_alert(alert)
            
            if self.preferences.webhook_enabled:
                success &= await self._send_webhook_alert(alert)
            
            if self.preferences.email_enabled:
                success &= await self._send_email_alert(alert)
            
            await self._send_in_app_alert(alert)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending circuit breaker alert: {str(e)}")
            return False
    
    async def send_daily_pnl_alert(self, pnl_data: Dict[str, Any]) -> bool:
        """Send daily P&L summary alert"""
        try:
            total_pnl = pnl_data.get('total_pnl', 0)
            total_trades = pnl_data.get('total_trades', 0)
            winning_trades = pnl_data.get('winning_trades', 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            pnl_emoji = "📈" if total_pnl >= 0 else "📉"
            pnl_color = "green" if total_pnl >= 0 else "red"
            
            message = f"""📊 DAILY P&L SUMMARY
━━━━━━━━━━━━━━━━
{pnl_emoji} Total P&L: ${total_pnl:,.2f}
📈 Total Trades: {total_trades}
✅ Winning Trades: {winning_trades}
📊 Win Rate: {win_rate:.1f}%
━━━━━━━━━━━━━━━━
📅 Date: {datetime.utcnow().strftime('%Y-%m-%d')}
🕘 Time: 21:00 UTC"""
            
            alert = Alert(
                type=AlertType.DAILY_PNL,
                title=f"📊 Daily P&L: ${total_pnl:,.2f}",
                message=message,
                payload=pnl_data,
                severity=AlertSeverity.MEDIUM
            )
            
            # Send through enabled channels
            success = True
            
            if self.preferences.telegram_enabled:
                success &= await self._send_telegram_alert(alert)
            
            if self.preferences.webhook_enabled:
                success &= await self._send_webhook_alert(alert)
            
            if self.preferences.email_enabled:
                success &= await self._send_email_alert(alert)
            
            await self._send_in_app_alert(alert)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending daily P&L alert: {str(e)}")
            return False
    
    def get_alert_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get alert history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, type, channel, title, message, payload, timestamp, 
                           severity, status, error_message, retry_count
                    FROM alerts 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'id': row[0],
                        'type': row[1],
                        'channel': row[2],
                        'title': row[3],
                        'message': row[4],
                        'payload': json.loads(row[5]) if row[5] else {},
                        'timestamp': row[6],
                        'severity': row[7],
                        'status': row[8],
                        'error_message': row[9],
                        'retry_count': row[10]
                    })
                
                return alerts
                
        except Exception as e:
            logger.error(f"Error getting alert history: {str(e)}")
            return []
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total counts
                cursor = conn.execute("SELECT COUNT(*) FROM alerts")
                total_alerts = cursor.fetchone()[0]
                
                # Status counts
                cursor = conn.execute("""
                    SELECT status, COUNT(*) 
                    FROM alerts 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Channel counts
                cursor = conn.execute("""
                    SELECT channel, COUNT(*) 
                    FROM alerts 
                    GROUP BY channel
                """)
                channel_counts = dict(cursor.fetchall())
                
                # Type counts
                cursor = conn.execute("""
                    SELECT type, COUNT(*) 
                    FROM alerts 
                    GROUP BY type
                """)
                type_counts = dict(cursor.fetchall())
                
                # Recent activity (last 24 hours)
                yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM alerts 
                    WHERE timestamp >= ?
                """, (yesterday,))
                recent_alerts = cursor.fetchone()[0]
                
                return {
                    'total_alerts': total_alerts,
                    'sent_count': status_counts.get('sent', 0),
                    'failed_count': status_counts.get('failed', 0),
                    'pending_count': status_counts.get('pending', 0),
                    'channel_counts': channel_counts,
                    'type_counts': type_counts,
                    'recent_24h': recent_alerts,
                    'success_rate': (status_counts.get('sent', 0) / total_alerts * 100) if total_alerts > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting alert statistics: {str(e)}")
            return {}
    
    async def test_telegram(self) -> Dict[str, Any]:
        """Test Telegram alert"""
        try:
            test_alert = Alert(
                type=AlertType.SYSTEM,
                title="🧪 Telegram Test Alert",
                message="This is a test message from SMC Trading System. If you receive this, Telegram alerts are working correctly!",
                payload={"test": True},
                severity=AlertSeverity.LOW
            )
            
            success = await self._send_telegram_alert(test_alert)
            
            return {
                "success": success,
                "message": "Test alert sent successfully" if success else "Test alert failed",
                "error": test_alert.error_message if not success else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "Test failed",
                "error": str(e)
            }
    
    async def test_webhook(self) -> Dict[str, Any]:
        """Test webhook alert"""
        try:
            test_alert = Alert(
                type=AlertType.SYSTEM,
                title="🧪 Webhook Test Alert",
                message="This is a test webhook from SMC Trading System.",
                payload={"test": True, "timestamp": datetime.utcnow().isoformat()},
                severity=AlertSeverity.LOW
            )
            
            success = await self._send_webhook_alert(test_alert)
            
            return {
                "success": success,
                "message": "Test webhook sent successfully" if success else "Test webhook failed",
                "error": test_alert.error_message if not success else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "Test failed",
                "error": str(e)
            }
    
    def add_websocket_connection(self, websocket):
        """Add WebSocket connection for in-app notifications"""
        self.websocket_connections.add(websocket)
        logger.debug(f"WebSocket connection added. Total: {len(self.websocket_connections)}")
    
    def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
        logger.debug(f"WebSocket connection removed. Total: {len(self.websocket_connections)}")


# Global instance
alert_manager = AlertManager()


# Convenience functions
async def send_signal_alert(signal_data: Dict[str, Any]) -> bool:
    """Send signal alert through all enabled channels"""
    return await alert_manager.send_signal_alert(signal_data)


async def send_circuit_breaker_alert(reason: str, details: Dict[str, Any]) -> bool:
    """Send circuit breaker alert"""
    return await alert_manager.send_circuit_breaker_alert(reason, details)


async def send_daily_pnl_alert(pnl_data: Dict[str, Any]) -> bool:
    """Send daily P&L summary alert"""
    return await alert_manager.send_daily_pnl_alert(pnl_data)