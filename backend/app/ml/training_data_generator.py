"""
Training Data Generator for ML Signal Filter
Generates labeled training data from historical backtests
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import sqlite3
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings
from app.utils.logger import get_logger
from app.services.market_data_service import MarketDataService
from app.strategies.smc_engine import PreciseSMCEngine
from app.strategies.mtf_confluence import ConfluenceEngine
from app.services.backtester import AdvancedBacktester
from app.ml.signal_filter import extract_features

logger = get_logger(__name__)
settings = get_settings()

class TrainingDataGenerator:
    """Generates labeled training data for ML model"""
    
    def __init__(self):
        self.db_path = settings.database_url_sync.replace("sqlite:///", "")
        self.market_data_service = MarketDataService()
        self.smc_engine = PreciseSMCEngine()
        self.confluence_engine = ConfluenceEngine()
        self.backtester = AdvancedBacktester()
        
        # Initialize database table
        self._init_database()
    
    def _init_database(self):
        """Initialize ML training data table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ml_training_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signal_id TEXT UNIQUE,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        take_profit REAL NOT NULL,
                        confluence_score REAL,
                        features TEXT NOT NULL,  -- JSON string of features
                        outcome INTEGER NOT NULL,  -- 1=win, 0=loss
                        pnl_pct REAL,
                        duration_hours REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Index for faster queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ml_training_symbol_timeframe 
                    ON ml_training_data(symbol, timeframe)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ml_training_timestamp 
                    ON ml_training_data(timestamp)
                """)
                
                conn.commit()
                logger.info("ML training data table initialized")
                
        except Exception as e:
            logger.error(f"Error initializing ML training database: {str(e)}")
    
    async def generate_training_data(
        self, 
        symbol: str = "BTCUSDT", 
        timeframe: str = "1h",
        months_back: int = 6,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate training data by running backtests on historical data
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            months_back: How many months of historical data to use
            force_regenerate: Whether to regenerate existing data
            
        Returns:
            Generation results
        """
        try:
            logger.info(f"Generating training data for {symbol} {timeframe} - {months_back} months")
            
            # Check if data already exists
            if not force_regenerate:
                existing_count = self._count_existing_data(symbol, timeframe)
                if existing_count > 100:
                    logger.info(f"Training data already exists: {existing_count} samples")
                    return {
                        'status': 'exists',
                        'samples': existing_count,
                        'message': 'Training data already exists'
                    }
            
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            logger.info(f"Fetching historical data from {start_date} to {end_date}")
            df = await self.market_data_service.get_historical_data(
                symbol, timeframe, start_date, end_date
            )
            
            if df.empty:
                return {'error': 'No historical data available'}
            
            logger.info(f"Retrieved {len(df)} candles of historical data")
            
            # Generate signals using SMC and MTF engines
            signals = await self._generate_historical_signals(df, symbol, timeframe)
            
            if not signals:
                return {'error': 'No signals generated from historical data'}
            
            logger.info(f"Generated {len(signals)} historical signals")
            
            # Label signals with outcomes
            labeled_signals = await self._label_signals_with_outcomes(signals, df)
            
            # Extract features and store in database
            stored_count = await self._store_training_data(labeled_signals, symbol, timeframe)
            
            result = {
                'status': 'success',
                'symbol': symbol,
                'timeframe': timeframe,
                'total_signals': len(signals),
                'labeled_signals': len(labeled_signals),
                'stored_samples': stored_count,
                'win_rate': sum(1 for s in labeled_signals if s['outcome'] == 1) / len(labeled_signals) if labeled_signals else 0,
                'date_range': f"{start_date.date()} to {end_date.date()}"
            }
            
            logger.info(f"Training data generation completed: {stored_count} samples stored")
            return result
            
        except Exception as e:
            logger.error(f"Error generating training data: {str(e)}")
            return {'error': str(e)}
    
    def _count_existing_data(self, symbol: str, timeframe: str) -> int:
        """Count existing training data samples"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM ml_training_data WHERE symbol = ? AND timeframe = ?",
                    (symbol, timeframe)
                )
                return cursor.fetchone()[0]
        except Exception:
            return 0
    
    async def _generate_historical_signals(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Generate signals from historical data using SMC and MTF engines"""
        try:
            signals = []
            
            # Process data in chunks to avoid memory issues
            chunk_size = 500
            for i in range(100, len(df), chunk_size):  # Start from candle 100 for indicators
                chunk_end = min(i + chunk_size, len(df))
                chunk_df = df.iloc[max(0, i-100):chunk_end].copy()  # Include lookback
                
                if len(chunk_df) < 100:
                    continue
                
                # Generate SMC signals
                smc_signals = await self._generate_smc_signals(chunk_df, symbol, timeframe)
                signals.extend(smc_signals)
                
                # Generate MTF confluence signals
                mtf_signals = await self._generate_mtf_signals(chunk_df, symbol, timeframe)
                signals.extend(mtf_signals)
            
            # Remove duplicates and sort by timestamp
            unique_signals = {}
            for signal in signals:
                key = f"{signal['timestamp']}_{signal['type']}_{signal['entry_price']}"
                if key not in unique_signals:
                    unique_signals[key] = signal
            
            sorted_signals = sorted(unique_signals.values(), key=lambda x: x['timestamp'])
            return sorted_signals
            
        except Exception as e:
            logger.error(f"Error generating historical signals: {str(e)}")
            return []
    
    async def _generate_smc_signals(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Generate SMC-based signals"""
        try:
            signals = []
            
            # Detect SMC patterns
            order_blocks = self.smc_engine.detect_order_blocks(df)
            fvgs = self.smc_engine.detect_fvg(df)
            structure_events = self.smc_engine.detect_structure(df)
            
            # Generate signals from Order Blocks
            for ob in order_blocks:
                if not ob.get('mitigated', True):  # Only unmitigated OBs
                    signal = {
                        'id': f"OB_{symbol}_{timeframe}_{ob['timestamp']}",
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': ob['timestamp'],
                        'type': 'OB',
                        'direction': ob['type'],
                        'entry_price': ob['top'] if ob['type'] == 'bearish' else ob['bottom'],
                        'stop_loss': ob['bottom'] if ob['type'] == 'bearish' else ob['top'],
                        'take_profit': self._calculate_take_profit(ob, df),
                        'confluence_score': 60.0,  # Base score for OB
                        'market_context': {
                            'order_blocks': order_blocks,
                            'fvgs': fvgs,
                            'structure_events': structure_events
                        }
                    }
                    signals.append(signal)
            
            # Generate signals from Structure Breaks
            for event in structure_events:
                if event['type'] in ['BOS', 'CHOCH']:
                    signal = {
                        'id': f"{event['type']}_{symbol}_{timeframe}_{event['timestamp']}",
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': event['timestamp'],
                        'type': event['type'],
                        'direction': event['direction'],
                        'entry_price': event['price'],
                        'stop_loss': self._calculate_stop_loss(event, df),
                        'take_profit': self._calculate_take_profit(event, df),
                        'confluence_score': 70.0 if event['type'] == 'BOS' else 50.0,
                        'market_context': {
                            'order_blocks': order_blocks,
                            'fvgs': fvgs,
                            'structure_events': structure_events
                        }
                    }
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating SMC signals: {str(e)}")
            return []
    
    async def _generate_mtf_signals(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Generate MTF confluence signals"""
        try:
            signals = []
            
            # For simplicity, we'll generate some MTF signals based on confluence
            # In a real implementation, you'd analyze multiple timeframes
            
            for i in range(50, len(df) - 10):  # Leave room for TP/SL calculation
                current_candle = df.iloc[i]
                
                # Simple confluence check (this would be more sophisticated in practice)
                confluence_score = self._calculate_simple_confluence(df, i)
                
                if confluence_score >= 65:  # Minimum confluence threshold
                    direction = 'BUY' if current_candle['close'] > current_candle['open'] else 'SELL'
                    
                    signal = {
                        'id': f"MTF_{symbol}_{timeframe}_{current_candle['timestamp']}",
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': current_candle['timestamp'],
                        'type': 'MTF',
                        'direction': direction,
                        'entry_price': current_candle['close'],
                        'stop_loss': self._calculate_mtf_stop_loss(df, i, direction),
                        'take_profit': self._calculate_mtf_take_profit(df, i, direction),
                        'confluence_score': confluence_score,
                        'market_context': {}
                    }
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating MTF signals: {str(e)}")
            return []
    
    def _calculate_simple_confluence(self, df: pd.DataFrame, idx: int) -> float:
        """Calculate simple confluence score"""
        try:
            score = 0.0
            
            # RSI confluence
            rsi = self._calculate_rsi(df, idx)
            if 30 <= rsi <= 70:  # Not oversold/overbought
                score += 20
            
            # Volume confluence
            current_volume = df.iloc[idx]['volume'] if 'volume' in df.columns else 1
            avg_volume = df['volume'].iloc[max(0, idx-20):idx].mean() if 'volume' in df.columns else 1
            if current_volume > avg_volume * 1.2:  # Above average volume
                score += 25
            
            # Trend confluence (simple moving average)
            if idx >= 20:
                sma_20 = df['close'].iloc[idx-20:idx].mean()
                if df.iloc[idx]['close'] > sma_20:  # Above trend
                    score += 20
            
            # Volatility confluence (ATR)
            atr = self._calculate_atr(df, idx)
            avg_atr = df['close'].iloc[max(0, idx-14):idx].std() if idx >= 14 else 0
            if atr > avg_atr * 0.8:  # Sufficient volatility
                score += 15
            
            return min(100, score)
            
        except Exception:
            return 0.0
    
    def _calculate_rsi(self, df: pd.DataFrame, idx: int, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            if idx < period:
                return 50.0
            
            closes = df['close'].iloc[idx-period:idx+1]
            delta = closes.diff()
            
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
            
        except Exception:
            return 50.0
    
    def _calculate_atr(self, df: pd.DataFrame, idx: int, period: int = 14) -> float:
        """Calculate ATR"""
        try:
            if idx < period:
                return 0.0
            
            high = df['high'].iloc[idx-period+1:idx+1]
            low = df['low'].iloc[idx-period+1:idx+1]
            close = df['close'].iloc[idx-period:idx]
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1).iloc[1:])
            tr3 = abs(low - close.shift(1).iloc[1:])
            
            tr = pd.concat([tr1.iloc[1:], tr2, tr3], axis=1).max(axis=1)
            return tr.mean()
            
        except Exception:
            return 0.0
    
    def _calculate_stop_loss(self, signal: Dict[str, Any], df: pd.DataFrame) -> float:
        """Calculate stop loss for signal"""
        try:
            entry_price = signal['entry_price']
            direction = signal['direction']
            
            # Use 2x ATR for stop loss
            signal_time = pd.to_datetime(signal['timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            signal_idx = df[df['timestamp'] <= signal_time].index[-1]
            
            atr = self._calculate_atr(df, signal_idx)
            atr_multiplier = 2.0
            
            if direction == 'BUY':
                return entry_price - (atr * atr_multiplier)
            else:
                return entry_price + (atr * atr_multiplier)
                
        except Exception:
            # Fallback: 2% stop loss
            return signal['entry_price'] * (0.98 if signal['direction'] == 'BUY' else 1.02)
    
    def _calculate_take_profit(self, signal: Dict[str, Any], df: pd.DataFrame) -> float:
        """Calculate take profit for signal"""
        try:
            entry_price = signal['entry_price']
            direction = signal['direction']
            
            # Use 3x ATR for take profit (1.5 R:R ratio)
            signal_time = pd.to_datetime(signal['timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            signal_idx = df[df['timestamp'] <= signal_time].index[-1]
            
            atr = self._calculate_atr(df, signal_idx)
            atr_multiplier = 3.0
            
            if direction == 'BUY':
                return entry_price + (atr * atr_multiplier)
            else:
                return entry_price - (atr * atr_multiplier)
                
        except Exception:
            # Fallback: 3% take profit
            return signal['entry_price'] * (1.03 if signal['direction'] == 'BUY' else 0.97)
    
    def _calculate_mtf_stop_loss(self, df: pd.DataFrame, idx: int, direction: str) -> float:
        """Calculate MTF stop loss"""
        entry_price = df.iloc[idx]['close']
        atr = self._calculate_atr(df, idx)
        
        if direction == 'BUY':
            return entry_price - (atr * 1.5)
        else:
            return entry_price + (atr * 1.5)
    
    def _calculate_mtf_take_profit(self, df: pd.DataFrame, idx: int, direction: str) -> float:
        """Calculate MTF take profit"""
        entry_price = df.iloc[idx]['close']
        atr = self._calculate_atr(df, idx)
        
        if direction == 'BUY':
            return entry_price + (atr * 2.5)
        else:
            return entry_price - (atr * 2.5)
    
    async def _label_signals_with_outcomes(
        self, 
        signals: List[Dict[str, Any]], 
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Label signals with win/loss outcomes"""
        try:
            labeled_signals = []
            
            for signal in signals:
                try:
                    outcome = self._determine_signal_outcome(signal, df)
                    if outcome is not None:
                        signal['outcome'] = outcome['result']
                        signal['pnl_pct'] = outcome['pnl_pct']
                        signal['duration_hours'] = outcome['duration_hours']
                        labeled_signals.append(signal)
                        
                except Exception as e:
                    logger.warning(f"Error labeling signal {signal.get('id', 'unknown')}: {str(e)}")
                    continue
            
            return labeled_signals
            
        except Exception as e:
            logger.error(f"Error labeling signals: {str(e)}")
            return []
    
    def _determine_signal_outcome(self, signal: Dict[str, Any], df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Determine if signal was a win or loss"""
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            direction = signal['direction']
            signal_time = pd.to_datetime(signal['timestamp'])
            
            # Find signal candle and subsequent candles
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            signal_idx = df[df['timestamp'] >= signal_time].index[0] if len(df[df['timestamp'] >= signal_time]) > 0 else len(df) - 1
            
            # Look at next 100 candles or until end of data
            end_idx = min(signal_idx + 100, len(df))
            future_candles = df.iloc[signal_idx:end_idx]
            
            if len(future_candles) < 2:
                return None
            
            # Check each candle for TP or SL hit
            for i, candle in future_candles.iterrows():
                high = candle['high']
                low = candle['low']
                
                if direction == 'BUY':
                    # Check if TP hit first
                    if high >= take_profit:
                        pnl_pct = (take_profit - entry_price) / entry_price * 100
                        duration = (pd.to_datetime(candle['timestamp']) - signal_time).total_seconds() / 3600
                        return {'result': 1, 'pnl_pct': pnl_pct, 'duration_hours': duration}
                    
                    # Check if SL hit
                    if low <= stop_loss:
                        pnl_pct = (stop_loss - entry_price) / entry_price * 100
                        duration = (pd.to_datetime(candle['timestamp']) - signal_time).total_seconds() / 3600
                        return {'result': 0, 'pnl_pct': pnl_pct, 'duration_hours': duration}
                
                else:  # SELL
                    # Check if TP hit first
                    if low <= take_profit:
                        pnl_pct = (entry_price - take_profit) / entry_price * 100
                        duration = (pd.to_datetime(candle['timestamp']) - signal_time).total_seconds() / 3600
                        return {'result': 1, 'pnl_pct': pnl_pct, 'duration_hours': duration}
                    
                    # Check if SL hit
                    if high >= stop_loss:
                        pnl_pct = (entry_price - stop_loss) / entry_price * 100
                        duration = (pd.to_datetime(candle['timestamp']) - signal_time).total_seconds() / 3600
                        return {'result': 0, 'pnl_pct': pnl_pct, 'duration_hours': duration}
            
            # If neither TP nor SL hit, consider it a loss (timeout)
            last_candle = future_candles.iloc[-1]
            final_price = last_candle['close']
            
            if direction == 'BUY':
                pnl_pct = (final_price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - final_price) / entry_price * 100
            
            duration = (pd.to_datetime(last_candle['timestamp']) - signal_time).total_seconds() / 3600
            result = 1 if pnl_pct > 0 else 0
            
            return {'result': result, 'pnl_pct': pnl_pct, 'duration_hours': duration}
            
        except Exception as e:
            logger.warning(f"Error determining signal outcome: {str(e)}")
            return None
    
    async def _store_training_data(
        self, 
        labeled_signals: List[Dict[str, Any]], 
        symbol: str, 
        timeframe: str
    ) -> int:
        """Store labeled signals as training data"""
        try:
            stored_count = 0
            
            with sqlite3.connect(self.db_path) as conn:
                for signal in labeled_signals:
                    try:
                        # Extract features (simplified for storage)
                        features = {
                            'atr_14': 0.0,  # Would be calculated from market data
                            'volume_ratio': 1.0,
                            'session': 1,
                            'day_of_week': pd.to_datetime(signal['timestamp']).weekday(),
                            'distance_to_htf_ob': 50.0,
                            'fvg_present': False,
                            'fvg_fill_pct': 0.0,
                            'liquidity_swept': False,
                            'confluence_score': signal.get('confluence_score', 50.0),
                            'rsi_14': 50.0,
                            'bb_position': 0.5,
                            'time_since_last_bos': 10,
                            'signal_type': {'BOS': 0, 'CHOCH': 1, 'OB': 2, 'FVG': 3, 'MTF': 2}.get(signal['type'], 0)
                        }
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO ml_training_data 
                            (signal_id, symbol, timeframe, timestamp, signal_type, 
                             entry_price, stop_loss, take_profit, confluence_score,
                             features, outcome, pnl_pct, duration_hours)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            signal['id'],
                            symbol,
                            timeframe,
                            signal['timestamp'],
                            signal['type'],
                            signal['entry_price'],
                            signal['stop_loss'],
                            signal['take_profit'],
                            signal.get('confluence_score', 50.0),
                            json.dumps(features),
                            signal['outcome'],
                            signal.get('pnl_pct', 0.0),
                            signal.get('duration_hours', 0.0)
                        ))
                        
                        stored_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error storing signal {signal.get('id', 'unknown')}: {str(e)}")
                        continue
                
                conn.commit()
            
            logger.info(f"Stored {stored_count} training samples")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing training data: {str(e)}")
            return 0
    
    def get_training_data(self, symbol: str = None, timeframe: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve training data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM ml_training_data"
                params = []
                
                conditions = []
                if symbol:
                    conditions.append("symbol = ?")
                    params.append(symbol)
                
                if timeframe:
                    conditions.append("timeframe = ?")
                    params.append(timeframe)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to dictionaries
                columns = [desc[0] for desc in cursor.description]
                training_data = []
                
                for row in rows:
                    data = dict(zip(columns, row))
                    # Parse features JSON
                    if data['features']:
                        data['features'] = json.loads(data['features'])
                    training_data.append(data)
                
                return training_data
                
        except Exception as e:
            logger.error(f"Error retrieving training data: {str(e)}")
            return []
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training data statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total samples
                cursor = conn.execute("SELECT COUNT(*) FROM ml_training_data")
                total_samples = cursor.fetchone()[0]
                
                # Win rate
                cursor = conn.execute("SELECT AVG(outcome) FROM ml_training_data")
                win_rate = cursor.fetchone()[0] or 0.0
                
                # By symbol
                cursor = conn.execute("""
                    SELECT symbol, COUNT(*) as count, AVG(outcome) as win_rate 
                    FROM ml_training_data 
                    GROUP BY symbol
                """)
                by_symbol = [dict(zip(['symbol', 'count', 'win_rate'], row)) for row in cursor.fetchall()]
                
                # By signal type
                cursor = conn.execute("""
                    SELECT signal_type, COUNT(*) as count, AVG(outcome) as win_rate 
                    FROM ml_training_data 
                    GROUP BY signal_type
                """)
                by_signal_type = [dict(zip(['signal_type', 'count', 'win_rate'], row)) for row in cursor.fetchall()]
                
                return {
                    'total_samples': total_samples,
                    'overall_win_rate': win_rate,
                    'by_symbol': by_symbol,
                    'by_signal_type': by_signal_type
                }
                
        except Exception as e:
            logger.error(f"Error getting training stats: {str(e)}")
            return {'total_samples': 0, 'overall_win_rate': 0.0}


# Global instance
training_data_generator = TrainingDataGenerator()