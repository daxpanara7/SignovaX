"""
Session Awareness Engine for Market Session Detection and Filtering
Manages trading sessions, liquidity zones, and optimal trading times
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
import pytz
from dataclasses import dataclass
import sqlite3
import json

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

@dataclass
class SessionConfig:
    """Configuration for a trading session"""
    name: str
    start_time: str  # UTC time in HH:MM format
    end_time: str    # UTC time in HH:MM format
    color: str       # Hex color for chart display
    pairs: List[str] # Preferred trading pairs
    timezone: str = "UTC"

@dataclass
class SessionRange:
    """Session high/low range data"""
    session: str
    date: str
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    open_price: float
    close_price: float
    range_size: float
    volume: float = 0.0

@dataclass
class SessionBox:
    """Session box for chart overlay"""
    session: str
    start_time: str
    end_time: str
    high: float
    low: float
    color: str
    range_pips: float
    is_active: bool = False

@dataclass
class SessionStats:
    """Session trading statistics"""
    session: str
    total_signals: int
    winning_signals: int
    win_rate: float
    avg_range_size: float
    avg_volume: float
    best_pairs: List[str]

class SessionManager:
    """Market session detection and management system"""
    
    def __init__(self):
        self.db_path = settings.database_url_sync.replace("sqlite:///", "")
        
        # Define trading sessions (all times in UTC)
        self.sessions = {
            "asia": SessionConfig(
                name="asia",
                start_time="00:00",  # UTC
                end_time="08:00",
                color="#1a3a5c",
                pairs=["USDJPY", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY"]
            ),
            "london": SessionConfig(
                name="london", 
                start_time="07:00",  # UTC (overlaps Asia close)
                end_time="16:00",
                color="#1a4a2a",
                pairs=["GBPUSD", "EURUSD", "EURGBP", "GBPJPY", "EURCHF"]
            ),
            "new_york": SessionConfig(
                name="new_york",
                start_time="12:00",  # UTC (overlaps London)
                end_time="21:00",
                color="#4a1a1a", 
                pairs=["BTCUSDT", "EURUSD", "GBPUSD", "USDCAD", "USDCHF"]
            )
        }
        
        # Initialize database
        self._init_database()
        
        logger.info("Session Manager initialized with 3 trading sessions")
    
    def _init_database(self):
        """Initialize session tracking database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Session ranges table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_ranges (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        session TEXT NOT NULL,
                        date TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        open_price REAL NOT NULL,
                        close_price REAL NOT NULL,
                        range_size REAL NOT NULL,
                        volume REAL DEFAULT 0.0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, session, date)
                    )
                """)
                
                # Session statistics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        session TEXT NOT NULL,
                        date TEXT NOT NULL,
                        total_signals INTEGER DEFAULT 0,
                        winning_signals INTEGER DEFAULT 0,
                        win_rate REAL DEFAULT 0.0,
                        avg_range_size REAL DEFAULT 0.0,
                        avg_volume REAL DEFAULT 0.0,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, session, date)
                    )
                """)
                
                # Indexes for performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_ranges_symbol_date 
                    ON session_ranges(symbol, date)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_stats_symbol_session 
                    ON session_stats(symbol, session)
                """)
                
                conn.commit()
                logger.info("Session database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing session database: {str(e)}")
    
    def get_current_session(self, utc_time: datetime = None) -> str:
        """
        Get the currently active trading session
        
        Args:
            utc_time: UTC datetime, defaults to current time
            
        Returns:
            Session name: 'asia', 'london', 'new_york', 'overlap', or 'off_hours'
        """
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        # Convert to UTC if timezone-aware
        if utc_time.tzinfo is not None:
            utc_time = utc_time.astimezone(pytz.UTC).replace(tzinfo=None)
        
        current_time = utc_time.time()
        weekday = utc_time.weekday()  # 0=Monday, 6=Sunday
        
        # Check for weekend (no trading Sunday 00:00 - Monday 00:00 UTC)
        if weekday == 6:  # Sunday - no trading all day
            return "off_hours"
        
        active_sessions = []
        
        # Check each session
        for session_name, config in self.sessions.items():
            if self._is_time_in_session(current_time, config):
                active_sessions.append(session_name)
        
        # Return session status
        if len(active_sessions) == 0:
            return "off_hours"
        elif len(active_sessions) == 1:
            return active_sessions[0]
        else:
            # Multiple sessions active = overlap (highest liquidity)
            return "overlap"
    
    def _is_time_in_session(self, current_time: time, config: SessionConfig) -> bool:
        """Check if current time falls within session hours"""
        start = time(*map(int, config.start_time.split(':')))
        end = time(*map(int, config.end_time.split(':')))
        
        # Handle sessions that cross midnight
        if start <= end:
            # Normal session (e.g., 07:00 - 16:00)
            return start <= current_time < end  # Changed to < end to avoid overlap
        else:
            # Session crosses midnight (e.g., 21:00 - 08:00)
            return current_time >= start or current_time < end
    
    def get_session_range(self, df: pd.DataFrame, session: str, date: str) -> Optional[SessionRange]:
        """
        Calculate session's high, low, open for a given date
        
        Args:
            df: OHLCV dataframe
            session: Session name ('asia', 'london', 'new_york')
            date: Date string in YYYY-MM-DD format
            
        Returns:
            SessionRange object or None if no data
        """
        try:
            if session not in self.sessions:
                logger.warning(f"Unknown session: {session}")
                return None
            
            config = self.sessions[session]
            
            # Parse date and create session time range
            target_date = pd.to_datetime(date).date()
            start_datetime = datetime.combine(target_date, time(*map(int, config.start_time.split(':'))))
            end_datetime = datetime.combine(target_date, time(*map(int, config.end_time.split(':'))))
            
            # Handle sessions that cross midnight
            if config.start_time > config.end_time:
                end_datetime += timedelta(days=1)
            
            # Filter dataframe for session period
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            session_data = df[
                (df['timestamp'] >= start_datetime) & 
                (df['timestamp'] <= end_datetime)
            ]
            
            if session_data.empty:
                logger.debug(f"No data found for {session} session on {date}")
                return None
            
            # Calculate session metrics
            high = session_data['high'].max()
            low = session_data['low'].min()
            open_price = session_data.iloc[0]['open']
            close_price = session_data.iloc[-1]['close']
            range_size = high - low
            volume = session_data['volume'].sum() if 'volume' in session_data.columns else 0.0
            
            session_range = SessionRange(
                session=session,
                date=date,
                start_time=start_datetime,
                end_time=end_datetime,
                high=high,
                low=low,
                open_price=open_price,
                close_price=close_price,
                range_size=range_size,
                volume=volume
            )
            
            # Store in database
            self._store_session_range(session_range, df.iloc[0].get('symbol', 'UNKNOWN'))
            
            return session_range
            
        except Exception as e:
            logger.error(f"Error calculating session range: {str(e)}")
            return None
    
    def _store_session_range(self, session_range: SessionRange, symbol: str):
        """Store session range data in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO session_ranges 
                    (symbol, session, date, start_time, end_time, high, low, 
                     open_price, close_price, range_size, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    session_range.session,
                    session_range.date,
                    session_range.start_time.isoformat(),
                    session_range.end_time.isoformat(),
                    session_range.high,
                    session_range.low,
                    session_range.open_price,
                    session_range.close_price,
                    session_range.range_size,
                    session_range.volume
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing session range: {str(e)}")
    
    def is_optimal_trading_time(self, utc_time: datetime, signal_type: str) -> bool:
        """
        Check if current time is optimal for trading based on signal type
        
        Args:
            utc_time: UTC datetime
            signal_type: 'CHOCH', 'BOS', 'OB', 'FVG', etc.
            
        Returns:
            True if optimal trading time, False otherwise
        """
        try:
            current_session = self.get_current_session(utc_time)
            
            # Never trade during off hours
            if current_session == "off_hours":
                return False
            
            # Get session start time for timing rules
            session_start_time = self._get_session_start_time(utc_time, current_session)
            
            if signal_type == "CHOCH":
                # CHOCH signals: only during session open (first 2 hours)
                if session_start_time is None:
                    return False
                
                time_since_open = utc_time - session_start_time
                return time_since_open <= timedelta(hours=2)
            
            elif signal_type in ["BOS", "OB", "FVG"]:
                # BOS, OB, FVG signals: during any active session hours
                return current_session in ["asia", "london", "new_york", "overlap"]
            
            else:
                # Default: allow during active sessions
                return current_session in ["asia", "london", "new_york", "overlap"]
                
        except Exception as e:
            logger.error(f"Error checking optimal trading time: {str(e)}")
            return False
    
    def _get_session_start_time(self, utc_time: datetime, session: str) -> Optional[datetime]:
        """Get the start time of the current session"""
        try:
            if session == "overlap":
                # For overlap, use the later starting session (New York starts at 12:00, London at 07:00)
                # At overlap time, we want to use the most recent session start
                current_hour = utc_time.hour
                if 12 <= current_hour < 16:  # NY-London overlap (12:00-16:00)
                    start_time = time(12, 0)  # Use NY start time
                elif 7 <= current_hour < 8:   # London-Asia overlap (07:00-08:00)
                    start_time = time(7, 0)   # Use London start time
                else:
                    return None
            elif session in self.sessions:
                start_time = time(*map(int, self.sessions[session].start_time.split(':')))
            else:
                return None
            
            # Create datetime for session start on the same date
            session_date = utc_time.date()
            session_start = datetime.combine(session_date, start_time)
            
            # If the session start is in the future, it must have started yesterday
            if session_start > utc_time:
                session_start -= timedelta(days=1)
            
            return session_start
            
        except Exception as e:
            logger.error(f"Error getting session start time: {str(e)}")
            return None
    
    def tag_candles_with_session(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add session information to OHLCV dataframe
        
        Args:
            df: OHLCV dataframe with timestamp column
            
        Returns:
            Enhanced dataframe with session columns
        """
        try:
            df = df.copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Initialize session columns
            df['session'] = 'off_hours'
            df['is_session_open'] = False
            df['is_overlap'] = False
            
            # Process each candle
            for idx, row in df.iterrows():
                candle_time = row['timestamp']
                
                # Convert to UTC if timezone-aware
                if candle_time.tzinfo is not None:
                    candle_time = candle_time.astimezone(pytz.UTC).replace(tzinfo=None)
                
                current_session = self.get_current_session(candle_time)
                
                df.at[idx, 'session'] = current_session
                df.at[idx, 'is_session_open'] = current_session != 'off_hours'
                df.at[idx, 'is_overlap'] = current_session == 'overlap'
            
            # Calculate daily session ranges
            df = self._add_daily_session_ranges(df)
            
            logger.debug(f"Tagged {len(df)} candles with session information")
            return df
            
        except Exception as e:
            logger.error(f"Error tagging candles with session: {str(e)}")
            return df
    
    def _add_daily_session_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add daily session range sizes to dataframe"""
        try:
            df['asia_range_size'] = 0.0
            df['london_range_size'] = 0.0
            df['new_york_range_size'] = 0.0
            
            # Group by date
            df['date'] = df['timestamp'].dt.date
            
            for date, group in df.groupby('date'):
                date_str = date.strftime('%Y-%m-%d')
                
                # Calculate ranges for each session
                for session_name in ['asia', 'london', 'new_york']:
                    session_range = self.get_session_range(group, session_name, date_str)
                    
                    if session_range:
                        range_column = f"{session_name}_range_size"
                        df.loc[df['date'] == date, range_column] = session_range.range_size
            
            # Remove temporary date column
            df = df.drop('date', axis=1)
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding daily session ranges: {str(e)}")
            return df
    
    def get_session_boxes(self, symbol: str, date: str) -> List[SessionBox]:
        """
        Get session boxes for chart overlay
        
        Args:
            symbol: Trading symbol
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of SessionBox objects for chart display
        """
        try:
            boxes = []
            
            # Get stored session ranges from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT session, start_time, end_time, high, low, range_size
                    FROM session_ranges 
                    WHERE symbol = ? AND date = ?
                    ORDER BY start_time
                """, (symbol, date))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    session, start_time, end_time, high, low, range_size = row
                    
                    if session in self.sessions:
                        config = self.sessions[session]
                        
                        # Calculate range in pips (approximate)
                        range_pips = range_size * 10000 if 'JPY' not in symbol else range_size * 100
                        
                        box = SessionBox(
                            session=session,
                            start_time=start_time,
                            end_time=end_time,
                            high=high,
                            low=low,
                            color=config.color,
                            range_pips=range_pips,
                            is_active=False  # Historical boxes are not active
                        )
                        
                        boxes.append(box)
            
            # Add current session box if it's today
            today = datetime.utcnow().date().strftime('%Y-%m-%d')
            if date == today:
                current_session = self.get_current_session()
                if current_session in self.sessions:
                    # This would need real-time data to calculate current high/low
                    # For now, we'll skip adding the current session box
                    pass
            
            logger.debug(f"Retrieved {len(boxes)} session boxes for {symbol} on {date}")
            return boxes
            
        except Exception as e:
            logger.error(f"Error getting session boxes: {str(e)}")
            return []
    
    def get_session_statistics(self, symbol: str, days: int = 30) -> Dict[str, SessionStats]:
        """
        Get session trading statistics
        
        Args:
            symbol: Trading symbol
            days: Number of days to analyze
            
        Returns:
            Dictionary of session statistics
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            stats = {}
            
            with sqlite3.connect(self.db_path) as conn:
                for session_name in self.sessions.keys():
                    # Get session range statistics
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_days,
                            AVG(range_size) as avg_range_size,
                            AVG(volume) as avg_volume
                        FROM session_ranges 
                        WHERE symbol = ? AND session = ? 
                        AND date BETWEEN ? AND ?
                    """, (symbol, session_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                    
                    range_data = cursor.fetchone()
                    
                    # Get signal statistics (if available)
                    cursor = conn.execute("""
                        SELECT 
                            COALESCE(SUM(total_signals), 0) as total_signals,
                            COALESCE(SUM(winning_signals), 0) as winning_signals,
                            COALESCE(AVG(win_rate), 0.0) as avg_win_rate
                        FROM session_stats 
                        WHERE symbol = ? AND session = ? 
                        AND date BETWEEN ? AND ?
                    """, (symbol, session_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                    
                    signal_data = cursor.fetchone()
                    
                    # Calculate win rate
                    total_signals = signal_data[0] if signal_data[0] else 0
                    winning_signals = signal_data[1] if signal_data[1] else 0
                    win_rate = winning_signals / total_signals if total_signals > 0 else 0.0
                    
                    # Get preferred pairs for this session
                    config = self.sessions[session_name]
                    
                    stats[session_name] = SessionStats(
                        session=session_name,
                        total_signals=total_signals,
                        winning_signals=winning_signals,
                        win_rate=win_rate,
                        avg_range_size=range_data[1] if range_data[1] else 0.0,
                        avg_volume=range_data[2] if range_data[2] else 0.0,
                        best_pairs=config.pairs
                    )
            
            # Find best session by win rate
            best_session = max(stats.values(), key=lambda x: x.win_rate) if stats else None
            
            logger.info(f"Generated session statistics for {symbol} over {days} days")
            if best_session:
                logger.info(f"Best session: {best_session.session} with {best_session.win_rate:.2%} win rate")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}")
            return {}
    
    def update_session_stats(self, symbol: str, session: str, date: str, signal_won: bool):
        """Update session statistics with new signal result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current stats
                cursor = conn.execute("""
                    SELECT total_signals, winning_signals 
                    FROM session_stats 
                    WHERE symbol = ? AND session = ? AND date = ?
                """, (symbol, session, date))
                
                result = cursor.fetchone()
                
                if result:
                    total_signals, winning_signals = result
                    total_signals += 1
                    if signal_won:
                        winning_signals += 1
                else:
                    total_signals = 1
                    winning_signals = 1 if signal_won else 0
                
                win_rate = winning_signals / total_signals if total_signals > 0 else 0.0
                
                # Update stats
                conn.execute("""
                    INSERT OR REPLACE INTO session_stats 
                    (symbol, session, date, total_signals, winning_signals, win_rate, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, session, date, total_signals, winning_signals, 
                    win_rate, datetime.utcnow().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating session stats: {str(e)}")
    
    def get_optimal_pairs_for_session(self, session: str) -> List[str]:
        """Get optimal trading pairs for a specific session"""
        if session in self.sessions:
            return self.sessions[session].pairs
        return []
    
    def get_session_info(self, session: str) -> Optional[SessionConfig]:
        """Get configuration information for a session"""
        return self.sessions.get(session)
    
    def is_pair_optimal_for_session(self, pair: str, session: str) -> bool:
        """Check if a trading pair is optimal for a specific session"""
        if session in self.sessions:
            return pair in self.sessions[session].pairs
        return False


# Global instance
session_manager = SessionManager()


# Convenience functions
def get_current_session(utc_time: datetime = None) -> str:
    """Get current trading session"""
    return session_manager.get_current_session(utc_time)


def is_optimal_trading_time(utc_time: datetime, signal_type: str) -> bool:
    """Check if time is optimal for trading"""
    return session_manager.is_optimal_trading_time(utc_time, signal_type)


def get_session_range(df: pd.DataFrame, session: str, date: str) -> Optional[SessionRange]:
    """Get session range data"""
    return session_manager.get_session_range(df, session, date)