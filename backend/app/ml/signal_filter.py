"""
ML Signal Filter using Random Forest Classifier
Filters trading signals based on historical performance patterns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pickle
import os
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
import sqlite3
import json

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class SignalFilter:
    """Random Forest-based signal filtering system"""
    
    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.feature_names = [
            'atr_14', 'volume_ratio', 'session', 'day_of_week',
            'distance_to_htf_ob', 'fvg_present', 'fvg_fill_pct',
            'liquidity_swept', 'confluence_score', 'rsi_14',
            'bb_position', 'time_since_last_bos', 'signal_type'
        ]
        self.model_path = "backend/models/signal_filter.pkl"
        self.db_path = settings.database_url_sync.replace("sqlite:///", "")
        self.win_threshold = 0.65  # 65% probability threshold
        self.model_metadata = {}
        
        # Load existing model if available
        self.load_model()
    
    def extract_features(self, signal: Dict[str, Any], df: pd.DataFrame, market_context: Dict[str, Any]) -> np.ndarray:
        """
        Extract features for ML model from signal and market data
        
        Args:
            signal: Signal dictionary with entry, sl, tp, etc.
            df: OHLCV dataframe
            market_context: Additional market context data
            
        Returns:
            Feature array for ML model
        """
        try:
            features = {}
            
            # Get signal timestamp and find corresponding candle
            signal_time = pd.to_datetime(signal.get('timestamp', datetime.now()))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            signal_idx = df[df['timestamp'] <= signal_time].index[-1] if len(df) > 0 else 0
            
            # 1. ATR (Average True Range) - Volatility
            features['atr_14'] = self._calculate_atr(df, signal_idx, period=14)
            
            # 2. Volume Ratio - Signal candle volume vs average
            features['volume_ratio'] = self._calculate_volume_ratio(df, signal_idx, period=20)
            
            # 3. Trading Session (0=Asia, 1=London, 2=NewYork)
            features['session'] = self._get_trading_session(signal_time)
            
            # 4. Day of Week (0=Monday ... 4=Friday)
            features['day_of_week'] = signal_time.weekday()
            
            # 5. Distance to HTF Order Block
            features['distance_to_htf_ob'] = self._calculate_distance_to_htf_ob(
                signal, market_context.get('htf_order_blocks', [])
            )
            
            # 6. FVG Present at signal level
            features['fvg_present'] = self._check_fvg_present(
                signal, market_context.get('fvgs', [])
            )
            
            # 7. FVG Fill Percentage
            features['fvg_fill_pct'] = self._calculate_fvg_fill_pct(
                signal, market_context.get('fvgs', [])
            )
            
            # 8. Liquidity Swept before signal
            features['liquidity_swept'] = self._check_liquidity_swept(
                signal, market_context.get('liquidity_zones', [])
            )
            
            # 9. Confluence Score from Module 1
            features['confluence_score'] = signal.get('confluence_score', 0.0)
            
            # 10. RSI (Relative Strength Index)
            features['rsi_14'] = self._calculate_rsi(df, signal_idx, period=14)
            
            # 11. Bollinger Band Position
            features['bb_position'] = self._calculate_bb_position(df, signal_idx, period=20)
            
            # 12. Time since last BOS (Break of Structure)
            features['time_since_last_bos'] = self._calculate_time_since_last_bos(
                signal, market_context.get('structure_events', [])
            )
            
            # 13. Signal Type (0=BOS, 1=CHOCH, 2=OB, 3=FVG)
            signal_type_map = {'BOS': 0, 'CHOCH': 1, 'OB': 2, 'FVG': 3}
            features['signal_type'] = signal_type_map.get(signal.get('type', 'BOS'), 0)
            
            # Convert to numpy array in correct order
            feature_array = np.array([features[name] for name in self.feature_names])
            
            logger.debug(f"Extracted features for signal: {dict(zip(self.feature_names, feature_array))}")
            return feature_array
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            # Return default features if extraction fails
            return np.zeros(len(self.feature_names))
    
    def _calculate_atr(self, df: pd.DataFrame, idx: int, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if idx < period:
                return 0.0
            
            high = df['high'].iloc[max(0, idx-period+1):idx+1]
            low = df['low'].iloc[max(0, idx-period+1):idx+1]
            close = df['close'].iloc[max(0, idx-period):idx]
            
            if len(high) < 2 or len(low) < 2 or len(close) < 1:
                return 0.0
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1).iloc[1:])
            tr3 = abs(low - close.shift(1).iloc[1:])
            
            tr = pd.concat([tr1.iloc[1:], tr2, tr3], axis=1).max(axis=1)
            return tr.mean()
            
        except Exception:
            return 0.0
    
    def _calculate_volume_ratio(self, df: pd.DataFrame, idx: int, period: int = 20) -> float:
        """Calculate volume ratio vs average"""
        try:
            if idx < period or 'volume' not in df.columns:
                return 1.0
            
            current_volume = df['volume'].iloc[idx]
            avg_volume = df['volume'].iloc[max(0, idx-period):idx].mean()
            
            return current_volume / avg_volume if avg_volume > 0 else 1.0
            
        except Exception:
            return 1.0
    
    def _get_trading_session(self, timestamp: pd.Timestamp) -> int:
        """Get trading session (0=Asia, 1=London, 2=NewYork)"""
        try:
            hour = timestamp.hour
            
            # Asia: 21:00-06:00 UTC
            if hour >= 21 or hour < 6:
                return 0
            # London: 06:00-15:00 UTC
            elif 6 <= hour < 15:
                return 1
            # New York: 15:00-21:00 UTC
            else:
                return 2
                
        except Exception:
            return 1  # Default to London
    
    def _calculate_distance_to_htf_ob(self, signal: Dict[str, Any], htf_obs: List[Dict]) -> float:
        """Calculate percentage distance to nearest HTF Order Block"""
        try:
            if not htf_obs:
                return 100.0  # No HTF OB available
            
            signal_price = signal.get('entry_price', 0)
            if signal_price == 0:
                return 100.0
            
            min_distance = float('inf')
            
            for ob in htf_obs:
                if not ob.get('mitigated', True):  # Only consider unmitigated OBs
                    ob_top = ob.get('top', 0)
                    ob_bottom = ob.get('bottom', 0)
                    
                    # Distance to closest edge of OB
                    distance_to_top = abs(signal_price - ob_top) / signal_price * 100
                    distance_to_bottom = abs(signal_price - ob_bottom) / signal_price * 100
                    
                    min_distance = min(min_distance, distance_to_top, distance_to_bottom)
            
            return min_distance if min_distance != float('inf') else 100.0
            
        except Exception:
            return 100.0
    
    def _check_fvg_present(self, signal: Dict[str, Any], fvgs: List[Dict]) -> bool:
        """Check if FVG is present at signal level"""
        try:
            signal_price = signal.get('entry_price', 0)
            if signal_price == 0:
                return False
            
            for fvg in fvgs:
                if not fvg.get('filled', True):  # Only unfilled FVGs
                    fvg_top = fvg.get('top', 0)
                    fvg_bottom = fvg.get('bottom', 0)
                    
                    # Check if signal price is within FVG
                    if fvg_bottom <= signal_price <= fvg_top:
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_fvg_fill_pct(self, signal: Dict[str, Any], fvgs: List[Dict]) -> float:
        """Calculate FVG fill percentage"""
        try:
            signal_price = signal.get('entry_price', 0)
            if signal_price == 0:
                return 0.0
            
            for fvg in fvgs:
                fvg_top = fvg.get('top', 0)
                fvg_bottom = fvg.get('bottom', 0)
                
                # Check if signal price is within FVG
                if fvg_bottom <= signal_price <= fvg_top:
                    return fvg.get('fill_pct', 0.0)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _check_liquidity_swept(self, signal: Dict[str, Any], liquidity_zones: List[Dict]) -> bool:
        """Check if liquidity was swept before signal"""
        try:
            signal_time = pd.to_datetime(signal.get('timestamp', datetime.now()))
            
            for zone in liquidity_zones:
                if zone.get('swept', False):
                    swept_time = pd.to_datetime(zone.get('swept_time', datetime.min))
                    
                    # Check if liquidity was swept within last 10 candles before signal
                    if (signal_time - swept_time).total_seconds() / 3600 <= 10:  # 10 hours
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_rsi(self, df: pd.DataFrame, idx: int, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if idx < period:
                return 50.0  # Neutral RSI
            
            closes = df['close'].iloc[max(0, idx-period):idx+1]
            delta = closes.diff()
            
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
            
        except Exception:
            return 50.0
    
    def _calculate_bb_position(self, df: pd.DataFrame, idx: int, period: int = 20) -> float:
        """Calculate position within Bollinger Bands (0-1)"""
        try:
            if idx < period:
                return 0.5  # Middle position
            
            closes = df['close'].iloc[max(0, idx-period):idx+1]
            sma = closes.rolling(window=period).mean()
            std = closes.rolling(window=period).std()
            
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            
            current_price = closes.iloc[-1]
            upper = upper_band.iloc[-1]
            lower = lower_band.iloc[-1]
            
            if upper == lower:
                return 0.5
            
            position = (current_price - lower) / (upper - lower)
            return max(0, min(1, position))  # Clamp between 0 and 1
            
        except Exception:
            return 0.5
    
    def _calculate_time_since_last_bos(self, signal: Dict[str, Any], structure_events: List[Dict]) -> int:
        """Calculate candles since last Break of Structure"""
        try:
            signal_time = pd.to_datetime(signal.get('timestamp', datetime.now()))
            
            last_bos_time = None
            for event in structure_events:
                if event.get('type') == 'BOS':
                    event_time = pd.to_datetime(event.get('timestamp', datetime.min))
                    if event_time <= signal_time:
                        if last_bos_time is None or event_time > last_bos_time:
                            last_bos_time = event_time
            
            if last_bos_time is None:
                return 100  # No recent BOS
            
            # Approximate candles (assuming 1H timeframe)
            hours_diff = (signal_time - last_bos_time).total_seconds() / 3600
            return int(hours_diff)
            
        except Exception:
            return 100
    
    def train_model(self, historical_signals: List[Dict], outcomes: List[int]) -> Dict[str, Any]:
        """
        Train Random Forest model on historical signals
        
        Args:
            historical_signals: List of signal dictionaries with features
            outcomes: List of outcomes (1=win, 0=loss)
            
        Returns:
            Training results dictionary
        """
        try:
            if len(historical_signals) < 50:
                logger.warning(f"Insufficient training data: {len(historical_signals)} samples")
                return {"error": "Insufficient training data (minimum 50 samples required)"}
            
            logger.info(f"Training model with {len(historical_signals)} samples")
            
            # Extract features for all signals
            X = []
            for signal in historical_signals:
                # For training, we assume features are already extracted
                if 'features' in signal:
                    X.append(signal['features'])
                else:
                    # Extract features if not present
                    features = self.extract_features(
                        signal, 
                        signal.get('df', pd.DataFrame()), 
                        signal.get('market_context', {})
                    )
                    X.append(features)
            
            X = np.array(X)
            y = np.array(outcomes)
            
            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train Random Forest model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42,
                class_weight='balanced'  # Handle imbalanced data
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            
            # Feature importances
            feature_importances = dict(zip(self.feature_names, self.model.feature_importances_))
            
            # Save model
            self.save_model()
            
            # Update metadata
            self.model_metadata = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'n_samples': len(historical_signals),
                'last_trained': datetime.now().isoformat(),
                'feature_importances': feature_importances
            }
            
            results = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'n_samples': len(historical_signals),
                'n_train': len(X_train),
                'n_test': len(X_test),
                'feature_importances': feature_importances,
                'classification_report': classification_report(y_test, y_pred, output_dict=True)
            }
            
            logger.info(f"Model trained successfully - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return {"error": str(e)}
    
    def filter_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter signal using trained ML model
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Dictionary with approval status and win probability
        """
        try:
            # If no model is trained, approve all signals (fallback)
            if self.model is None:
                logger.warning("No trained model available, approving signal by default")
                return {
                    'approved': True,
                    'win_probability': 0.5,
                    'reason': 'No trained model available'
                }
            
            # Extract features
            features = self.extract_features(
                signal,
                signal.get('df', pd.DataFrame()),
                signal.get('market_context', {})
            )
            
            # Predict probability
            features_reshaped = features.reshape(1, -1)
            win_probability = self.model.predict_proba(features_reshaped)[0, 1]
            
            # Apply threshold
            approved = win_probability >= self.win_threshold
            
            result = {
                'approved': approved,
                'win_probability': float(win_probability),
                'threshold': self.win_threshold,
                'reason': f"ML prediction: {win_probability:.3f} {'≥' if approved else '<'} {self.win_threshold}"
            }
            
            logger.info(f"Signal filtered - Approved: {approved}, Probability: {win_probability:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error filtering signal: {str(e)}")
            # Fallback to approval on error
            return {
                'approved': True,
                'win_probability': 0.5,
                'reason': f'Error in ML filter: {str(e)}'
            }
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'win_threshold': self.win_threshold,
                'metadata': self.model_metadata
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.model = model_data.get('model')
                self.feature_names = model_data.get('feature_names', self.feature_names)
                self.win_threshold = model_data.get('win_threshold', self.win_threshold)
                self.model_metadata = model_data.get('metadata', {})
                
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.info("No existing model found")
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get model status and metadata"""
        return {
            'model_trained': self.model is not None,
            'model_path': self.model_path,
            'win_threshold': self.win_threshold,
            'feature_count': len(self.feature_names),
            'metadata': self.model_metadata
        }
    
    def get_feature_importances(self) -> Dict[str, float]:
        """Get feature importances from trained model"""
        if self.model is None:
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_))


# Global instance
signal_filter = SignalFilter()


def extract_features(signal: Dict[str, Any], df: pd.DataFrame, market_context: Dict[str, Any]) -> np.ndarray:
    """Convenience function for feature extraction"""
    return signal_filter.extract_features(signal, df, market_context)


def train_model(historical_signals: List[Dict], outcomes: List[int]) -> Dict[str, Any]:
    """Convenience function for model training"""
    return signal_filter.train_model(historical_signals, outcomes)


def filter_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for signal filtering"""
    return signal_filter.filter_signal(signal)