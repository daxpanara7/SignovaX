"""
Enhanced Data Layer with Validation, Caching, and Multi-Source Support
Provides robust data pipeline with quality checks and fallback mechanisms
"""

import pandas as pd
import numpy as np
import asyncio
import time
import sys
import aiohttp
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import lru_cache, wraps
import sqlite3
import json
import ccxt
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class DataSource(Enum):
    """Data source enumeration"""
    BINANCE = "binance"
    FINNHUB = "finnhub"
    COINMARKETCAP = "coinmarketcap"
    ALPHA_VANTAGE = "alpha_vantage"
    MOCK = "mock"

class ValidationIssueType(Enum):
    """Data validation issue types"""
    MISSING_CANDLES = "missing_candles"
    BAD_TICK = "bad_tick"
    ZERO_VOLUME = "zero_volume"
    DUPLICATE_TIMESTAMP = "duplicate_timestamp"
    PRICE_SPIKE = "price_spike"
    INVALID_OHLC = "invalid_ohlc"

@dataclass
class ValidationIssue:
    """Data validation issue"""
    type: ValidationIssueType
    timestamp: str
    description: str
    severity: str  # "warning", "error", "critical"
    fixed: bool = False

@dataclass
class ValidationResult:
    """Data validation result"""
    valid: bool
    issues: List[ValidationIssue]
    cleaned_df: pd.DataFrame
    original_count: int
    cleaned_count: int
    issues_fixed: int

@dataclass
class CacheStats:
    """Cache statistics"""
    total_entries: int
    total_size_mb: float
    hit_rate: float
    miss_rate: float
    evictions: int
    oldest_entry: Optional[str]
    newest_entry: Optional[str]

@dataclass
class DataQuality:
    """Data quality metrics"""
    symbol: str
    timeframe: str
    total_candles: int
    missing_candles: int
    bad_ticks: int
    anomalies: int
    zero_volume_candles: int
    duplicate_timestamps: int
    last_updated: str
    source: str
    quality_score: float  # 0-100

class DataUnavailableError(Exception):
    """Raised when data cannot be fetched from any source"""
    pass

class TTLCache:
    """Time-to-live cache with size tracking"""
    
    def __init__(self, maxsize: int = 1000, max_size_mb: float = 500.0):
        self.maxsize = maxsize
        self.max_size_mb = max_size_mb
        self.cache = {}
        self.timestamps = {}
        self.ttls = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.current_size_mb = 0.0
    
    def _get_size_mb(self, obj) -> float:
        """Estimate object size in MB"""
        try:
            if isinstance(obj, pd.DataFrame):
                return obj.memory_usage(deep=True).sum() / (1024 * 1024)
            else:
                return sys.getsizeof(obj) / (1024 * 1024)
        except:
            return 0.1  # Default estimate
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.timestamps.items():
            ttl = self.ttls.get(key, 3600)  # Default 1 hour
            if current_time - timestamp > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str):
        """Remove entry and update size tracking"""
        if key in self.cache:
            obj_size = self._get_size_mb(self.cache[key])
            self.current_size_mb -= obj_size
            del self.cache[key]
            del self.timestamps[key]
            del self.ttls[key]
    
    def _enforce_size_limit(self):
        """Enforce cache size limit by removing oldest entries"""
        while (self.current_size_mb > self.max_size_mb or 
               len(self.cache) > self.maxsize):
            if not self.cache:
                break
            
            # Remove oldest entry
            oldest_key = min(self.timestamps.keys(), 
                           key=lambda k: self.timestamps[k])
            self._remove_entry(oldest_key)
            self.evictions += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        self._cleanup_expired()
        
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value with TTL"""
        self._cleanup_expired()
        
        # Remove existing entry if present
        if key in self.cache:
            self._remove_entry(key)
        
        # Add new entry
        obj_size = self._get_size_mb(value)
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.ttls[key] = ttl
        self.current_size_mb += obj_size
        
        # Enforce limits
        self._enforce_size_limit()
    
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        self.timestamps.clear()
        self.ttls.clear()
        self.current_size_mb = 0.0
    
    def stats(self) -> CacheStats:
        """Get cache statistics"""
        self._cleanup_expired()
        
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        miss_rate = (self.misses / total_requests * 100) if total_requests > 0 else 0
        
        oldest_entry = None
        newest_entry = None
        
        if self.timestamps:
            oldest_key = min(self.timestamps.keys(), 
                           key=lambda k: self.timestamps[k])
            newest_key = max(self.timestamps.keys(), 
                           key=lambda k: self.timestamps[k])
            oldest_entry = datetime.fromtimestamp(self.timestamps[oldest_key]).isoformat()
            newest_entry = datetime.fromtimestamp(self.timestamps[newest_key]).isoformat()
        
        return CacheStats(
            total_entries=len(self.cache),
            total_size_mb=self.current_size_mb,
            hit_rate=hit_rate,
            miss_rate=miss_rate,
            evictions=self.evictions,
            oldest_entry=oldest_entry,
            newest_entry=newest_entry
        )

class DataSourceManager:
    """Manages multiple data sources with fallback"""
    
    def __init__(self):
        self.sources = {}
        self.priority_order = {
            'crypto': [DataSource.BINANCE, DataSource.COINMARKETCAP, DataSource.FINNHUB, DataSource.MOCK],
            'forex': [DataSource.FINNHUB, DataSource.ALPHA_VANTAGE, DataSource.MOCK],
            'stocks': [DataSource.FINNHUB, DataSource.ALPHA_VANTAGE, DataSource.MOCK]
        }
        self._init_sources()
    
    def _init_sources(self):
        """Initialize data sources"""
        try:
            # Initialize Binance
            if settings.BINANCE_API_KEY and settings.BINANCE_SECRET_KEY:
                self.sources[DataSource.BINANCE] = ccxt.binance({
                    'apiKey': settings.BINANCE_API_KEY,
                    'secret': settings.BINANCE_SECRET_KEY,
                    'sandbox': False,  # Use production API for real data
                    'enableRateLimit': True,
                })
                logger.info("Binance API initialized")
            else:
                logger.warning("Binance API credentials not configured")
            
            # Initialize Finnhub
            if settings.FINNHUB_API_KEY:
                self.sources[DataSource.FINNHUB] = {
                    'api_key': settings.FINNHUB_API_KEY,
                    'base_url': 'https://finnhub.io/api/v1'
                }
                logger.info("Finnhub API initialized")
            else:
                logger.warning("Finnhub API key not configured")
            
            # Initialize CoinMarketCap
            if settings.COINMARKETCAP_API_KEY:
                self.sources[DataSource.COINMARKETCAP] = {
                    'api_key': settings.COINMARKETCAP_API_KEY,
                    'base_url': 'https://pro-api.coinmarketcap.com/v1'
                }
                logger.info("CoinMarketCap API initialized")
            else:
                logger.warning("CoinMarketCap API key not configured")
            
            # Initialize Alpha Vantage (placeholder)
            alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
            if alpha_vantage_key:
                self.sources[DataSource.ALPHA_VANTAGE] = {
                    'api_key': alpha_vantage_key,
                    'base_url': 'https://www.alphavantage.co/query'
                }
                logger.info("Alpha Vantage API initialized")
            
            # Mock source is always available
            self.sources[DataSource.MOCK] = True
            logger.info("Mock data source initialized")
            
        except Exception as e:
            logger.error(f"Error initializing data sources: {str(e)}")
    
    def get_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol"""
        symbol_upper = symbol.upper()
        
        # Crypto patterns
        crypto_patterns = ['USDT', 'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'UNI', 'MATIC', 'SOL']
        if any(pattern in symbol_upper for pattern in crypto_patterns):
            return 'crypto'
        
        # Forex patterns
        forex_patterns = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
        if any(fx in symbol_upper for fx in forex_patterns) and len(symbol_upper) <= 7:
            return 'forex'
        
        # Stock patterns (typically 1-5 characters)
        if len(symbol_upper) <= 5 and symbol_upper.isalpha():
            return 'stocks'
            
        # Default to crypto for unknown patterns
        return 'crypto'
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str, 
                         start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch OHLCV data with fallback sources"""
        asset_type = self.get_asset_type(symbol)
        sources_to_try = self.priority_order.get(asset_type, [DataSource.MOCK])
        
        logger.info(f"Fetching {symbol} {timeframe} data, trying sources: {[s.value for s in sources_to_try]}")
        
        last_error = None
        
        for source in sources_to_try:
            try:
                logger.info(f"Trying {source.value} for {symbol} {timeframe}")
                
                if source == DataSource.BINANCE:
                    df = await self._fetch_binance(symbol, timeframe, start, end)
                elif source == DataSource.FINNHUB:
                    df = await self._fetch_finnhub(symbol, timeframe, start, end)
                elif source == DataSource.COINMARKETCAP:
                    df = await self._fetch_coinmarketcap(symbol, timeframe, start, end)
                elif source == DataSource.ALPHA_VANTAGE:
                    df = await self._fetch_alpha_vantage(symbol, timeframe, start, end)
                elif source == DataSource.MOCK:
                    df = await self._fetch_mock(symbol, timeframe, start, end)
                else:
                    continue
                
                if df is not None and not df.empty:
                    logger.info(f"✅ Successfully fetched {len(df)} candles from {source.value}")
                    return df
                else:
                    logger.warning(f"❌ {source.value} returned empty data for {symbol}")
                    
            except Exception as e:
                last_error = e
                logger.error(f"❌ Failed to fetch from {source.value}: {str(e)}")
                continue
        
        # All sources failed
        error_msg = f"Failed to fetch data for {symbol} {timeframe} from all sources"
        if last_error:
            error_msg += f". Last error: {str(last_error)}"
        
        raise DataUnavailableError(error_msg)
    
    async def _fetch_binance(self, symbol: str, timeframe: str, 
                           start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch data from Binance API"""
        if DataSource.BINANCE not in self.sources:
            raise Exception("Binance not configured")
        
        exchange = self.sources[DataSource.BINANCE]
        
        # Convert timeframe
        tf_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d'
        }
        
        binance_tf = tf_map.get(timeframe, '1h')
        
        # For recent data, just get the latest candles without strict date filtering
        limit = 100  # Get more recent candles
        
        logger.info(f"Binance fetch: {symbol} {binance_tf}, limit={limit} (recent data)")
        
        try:
            # Get recent data without specifying 'since' to get the latest
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: exchange.fetch_ohlcv(symbol, binance_tf, None, limit)
            )
            
            logger.info(f"Binance raw response: {len(ohlcv) if ohlcv else 0} candles")
            
            if not ohlcv:
                logger.warning("Binance returned no data")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            
            logger.info(f"Binance DataFrame created: {len(df)} rows, date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            # Return the most recent data (no strict filtering)
            df = df.sort_values('timestamp').tail(50)  # Keep last 50 candles
            
            logger.info(f"Returning {len(df)} recent candles")
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            logger.error(f"Binance fetch error: {str(e)}")
            raise
    
    async def _fetch_alpha_vantage(self, symbol: str, timeframe: str,
                                 start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch data from Alpha Vantage API (placeholder implementation)"""
        if DataSource.ALPHA_VANTAGE not in self.sources:
            raise Exception("Alpha Vantage not configured")
        
        # This is a placeholder - would need actual Alpha Vantage implementation
        logger.warning("Alpha Vantage implementation is placeholder")
        return await self._fetch_mock(symbol, timeframe, start, end)
    
    async def _fetch_finnhub(self, symbol: str, timeframe: str,
                           start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch data from Finnhub API"""
        if DataSource.FINNHUB not in self.sources:
            raise Exception("Finnhub not configured")
        
        source_config = self.sources[DataSource.FINNHUB]
        api_key = source_config['api_key']
        base_url = source_config['base_url']
        
        # Convert timeframe to Finnhub resolution
        resolution_map = {
            '1m': '1', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '4h': '240', '1d': 'D'
        }
        
        resolution = resolution_map.get(timeframe, '60')
        
        # Convert timestamps
        from_ts = int(start.timestamp())
        to_ts = int(end.timestamp())
        
        # Prepare symbol for Finnhub (uppercase)
        finnhub_symbol = symbol.upper()
        
        url = f"{base_url}/stock/candle"
        params = {
            'symbol': finnhub_symbol,
            'resolution': resolution,
            'from': from_ts,
            'to': to_ts,
            'token': api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('s') == 'ok' and 'c' in data:
                            # Convert to DataFrame
                            df = pd.DataFrame({
                                'timestamp': pd.to_datetime(data['t'], unit='s'),
                                'open': data['o'],
                                'high': data['h'],
                                'low': data['l'],
                                'close': data['c'],
                                'volume': data['v'],
                                'symbol': symbol
                            })
                            
                            # Filter by date range
                            df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
                            return df.reset_index(drop=True)
                        else:
                            logger.warning(f"Finnhub returned no data for {symbol}")
                            return pd.DataFrame()
                    else:
                        logger.error(f"Finnhub API error: {response.status}")
                        return pd.DataFrame()
                        
        except Exception as e:
            logger.error(f"Error fetching from Finnhub: {str(e)}")
            return pd.DataFrame()
    
    async def _fetch_coinmarketcap(self, symbol: str, timeframe: str,
                                 start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch data from CoinMarketCap API"""
        if DataSource.COINMARKETCAP not in self.sources:
            raise Exception("CoinMarketCap not configured")
        
        source_config = self.sources[DataSource.COINMARKETCAP]
        api_key = source_config['api_key']
        base_url = source_config['base_url']
        
        # CoinMarketCap doesn't provide OHLCV historical data in free tier
        # This is a placeholder that would need Pro API access
        logger.warning("CoinMarketCap OHLCV data requires Pro API - using mock data")
        return await self._fetch_mock(symbol, timeframe, start, end)
    
    async def _fetch_mock(self, symbol: str, timeframe: str,
                         start: datetime, end: datetime) -> pd.DataFrame:
        """Generate mock OHLCV data"""
        logger.info(f"Generating mock data for {symbol} {timeframe}")
        
        # Generate time series
        tf_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        
        minutes = tf_minutes.get(timeframe, 60)
        periods = int((end - start).total_seconds() / (minutes * 60))
        
        timestamps = pd.date_range(start=start, periods=periods, freq=f'{minutes}min')
        
        # Generate realistic price data
        base_price = 50000 if 'BTC' in symbol else 1.1000 if 'EUR' in symbol else 43000
        
        # Random walk with some trend
        returns = np.random.normal(0, 0.002, len(timestamps))  # 0.2% volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        # Generate OHLCV
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            # Generate realistic OHLC around close price
            volatility = abs(np.random.normal(0, 0.001))  # Intrabar volatility
            
            high = close * (1 + volatility)
            low = close * (1 - volatility)
            open_price = prices[i-1] if i > 0 else close
            
            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            volume = np.random.uniform(100, 10000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'symbol': symbol
            })
        
        return pd.DataFrame(data)

class DataValidator:
    """Validates and cleans OHLCV data"""
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> ValidationResult:
        """Validate OHLCV data and return cleaned DataFrame"""
        if df.empty:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    type=ValidationIssueType.INVALID_OHLC,
                    timestamp="",
                    description="Empty DataFrame",
                    severity="critical"
                )],
                cleaned_df=df,
                original_count=0,
                cleaned_count=0,
                issues_fixed=0
            )
        
        original_count = len(df)
        issues = []
        cleaned_df = df.copy()
        issues_fixed = 0
        
        # Ensure required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
        
        if missing_cols:
            issues.append(ValidationIssue(
                type=ValidationIssueType.INVALID_OHLC,
                timestamp="",
                description=f"Missing columns: {missing_cols}",
                severity="critical"
            ))
            return ValidationResult(
                valid=False,
                issues=issues,
                cleaned_df=cleaned_df,
                original_count=original_count,
                cleaned_count=0,
                issues_fixed=0
            )
        
        # Sort by timestamp
        cleaned_df = cleaned_df.sort_values('timestamp').reset_index(drop=True)
        
        # 1. Check for duplicate timestamps
        duplicates = cleaned_df.duplicated(subset=['timestamp'], keep='last')
        if duplicates.any():
            duplicate_count = duplicates.sum()
            issues.append(ValidationIssue(
                type=ValidationIssueType.DUPLICATE_TIMESTAMP,
                timestamp="multiple",
                description=f"Found {duplicate_count} duplicate timestamps",
                severity="warning",
                fixed=True
            ))
            cleaned_df = cleaned_df[~duplicates].reset_index(drop=True)
            issues_fixed += duplicate_count
        
        # 2. Check for bad ticks (high < low, close outside high/low)
        bad_ticks_mask = (
            (cleaned_df['high'] < cleaned_df['low']) |
            (cleaned_df['close'] > cleaned_df['high']) |
            (cleaned_df['close'] < cleaned_df['low']) |
            (cleaned_df['open'] > cleaned_df['high']) |
            (cleaned_df['open'] < cleaned_df['low'])
        )
        
        if bad_ticks_mask.any():
            bad_tick_indices = cleaned_df[bad_ticks_mask].index.tolist()
            for idx in bad_tick_indices:
                issues.append(ValidationIssue(
                    type=ValidationIssueType.BAD_TICK,
                    timestamp=str(cleaned_df.loc[idx, 'timestamp']),
                    description=f"Invalid OHLC values at index {idx}",
                    severity="error",
                    fixed=True
                ))
            
            # Remove bad ticks
            cleaned_df = cleaned_df[~bad_ticks_mask].reset_index(drop=True)
            issues_fixed += len(bad_tick_indices)
        
        # 3. Check for zero volume (flag but keep for crypto)
        zero_volume_mask = cleaned_df['volume'] == 0
        if zero_volume_mask.any():
            zero_volume_count = zero_volume_mask.sum()
            issues.append(ValidationIssue(
                type=ValidationIssueType.ZERO_VOLUME,
                timestamp="multiple",
                description=f"Found {zero_volume_count} zero volume candles",
                severity="warning",
                fixed=False  # Keep the candles
            ))
        
        # 4. Check for missing candles (gaps in time series)
        if len(cleaned_df) > 1:
            time_diffs = cleaned_df['timestamp'].diff().dropna()
            expected_diff = time_diffs.mode().iloc[0] if not time_diffs.empty else pd.Timedelta(hours=1)
            
            # Find gaps larger than expected
            large_gaps = time_diffs[time_diffs > expected_diff * 3]  # More than 3x expected
            
            if not large_gaps.empty:
                for idx, gap in large_gaps.items():
                    issues.append(ValidationIssue(
                        type=ValidationIssueType.MISSING_CANDLES,
                        timestamp=str(cleaned_df.loc[idx, 'timestamp']),
                        description=f"Gap of {gap} detected",
                        severity="warning",
                        fixed=False
                    ))
            
            # Fill small gaps (up to 3 missing candles) with forward fill
            cleaned_df = DataValidator._fill_small_gaps(cleaned_df, expected_diff)
        
        # 5. Check for price spikes (> 10x ATR)
        if len(cleaned_df) >= 14:  # Need at least 14 periods for ATR
            atr = DataValidator._calculate_atr(cleaned_df, 14)
            
            if len(atr) > 0:
                # Calculate price moves
                price_moves = abs(cleaned_df['close'].diff())
                spike_threshold = atr.iloc[-1] * 10  # 10x ATR
                
                spikes = price_moves > spike_threshold
                if spikes.any():
                    spike_indices = cleaned_df[spikes].index.tolist()
                    for idx in spike_indices:
                        if idx > 0:  # Skip first row (no diff)
                            issues.append(ValidationIssue(
                                type=ValidationIssueType.PRICE_SPIKE,
                                timestamp=str(cleaned_df.loc[idx, 'timestamp']),
                                description=f"Price spike detected: {price_moves.iloc[idx]:.2f} > {spike_threshold:.2f}",
                                severity="warning",
                                fixed=False
                            ))
        
        # Calculate final metrics
        cleaned_count = len(cleaned_df)
        valid = len([issue for issue in issues if issue.severity == "critical"]) == 0
        
        return ValidationResult(
            valid=valid,
            issues=issues,
            cleaned_df=cleaned_df,
            original_count=original_count,
            cleaned_count=cleaned_count,
            issues_fixed=issues_fixed
        )
    
    @staticmethod
    def _fill_small_gaps(df: pd.DataFrame, expected_diff: pd.Timedelta) -> pd.DataFrame:
        """Fill small gaps (up to 3 missing candles) with forward fill"""
        if len(df) < 2:
            return df
        
        filled_data = []
        
        for i in range(len(df)):
            filled_data.append(df.iloc[i].to_dict())
            
            # Check if there's a gap to the next candle
            if i < len(df) - 1:
                current_time = df.iloc[i]['timestamp']
                next_time = df.iloc[i + 1]['timestamp']
                gap = next_time - current_time
                
                # If gap is 2-4 times expected (1-3 missing candles)
                if expected_diff * 2 <= gap <= expected_diff * 4:
                    missing_periods = int(gap / expected_diff) - 1
                    
                    # Fill with forward fill (use current candle's close as OHLC)
                    for j in range(1, missing_periods + 1):
                        fill_time = current_time + expected_diff * j
                        fill_candle = df.iloc[i].to_dict().copy()
                        fill_candle['timestamp'] = fill_time
                        fill_candle['open'] = df.iloc[i]['close']
                        fill_candle['high'] = df.iloc[i]['close']
                        fill_candle['low'] = df.iloc[i]['close']
                        fill_candle['close'] = df.iloc[i]['close']
                        fill_candle['volume'] = 0  # No volume for filled candles
                        filled_data.append(fill_candle)
        
        return pd.DataFrame(filled_data).sort_values('timestamp').reset_index(drop=True)
    
    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr

class DataManager:
    """Enhanced data manager with validation, caching, and multi-source support"""
    
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, max_size_mb=500.0)
        self.source_manager = DataSourceManager()
        self.validator = DataValidator()
        self.db_path = settings.database_url_sync.replace("sqlite:///", "")
        
        # Initialize database
        self._init_database()
        
        logger.info("Enhanced Data Manager initialized")
    
    def _init_database(self):
        """Initialize data quality tracking database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Data quality table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_quality (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        total_candles INTEGER NOT NULL,
                        missing_candles INTEGER DEFAULT 0,
                        bad_ticks INTEGER DEFAULT 0,
                        anomalies INTEGER DEFAULT 0,
                        zero_volume_candles INTEGER DEFAULT 0,
                        duplicate_timestamps INTEGER DEFAULT 0,
                        quality_score REAL DEFAULT 100.0,
                        source TEXT NOT NULL,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timeframe)
                    )
                """)
                
                # Data cache metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_metadata (
                        cache_key TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        record_count INTEGER NOT NULL,
                        source TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        accessed_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Data quality database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing data quality database: {str(e)}")
    
    def _get_cache_key(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> str:
        """Generate cache key for OHLCV data"""
        start_str = start.strftime('%Y%m%d_%H%M')
        end_str = end.strftime('%Y%m%d_%H%M')
        return f"ohlcv_{symbol}_{timeframe}_{start_str}_{end_str}"
    
    def _get_cache_ttl(self, end: datetime) -> int:
        """Determine cache TTL based on data recency"""
        now = datetime.utcnow()
        age = now - end
        
        if age < timedelta(hours=1):
            return 60  # 1 minute for very recent data
        elif age < timedelta(days=1):
            return 300  # 5 minutes for recent data
        else:
            return 3600  # 1 hour for historical data
    
    async def get_ohlcv(self, symbol: str, timeframe: str, 
                       start: datetime, end: datetime, 
                       validate: bool = True) -> pd.DataFrame:
        """Get OHLCV data with caching and validation"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(symbol, timeframe, start, end)
            cached_data = self.cache.get(cache_key)
            
            if cached_data is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
            
            logger.debug(f"Cache miss for {cache_key}")
            
            # Fetch from source
            raw_df = await self.source_manager.fetch_ohlcv(symbol, timeframe, start, end)
            
            if raw_df.empty:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return raw_df
            
            # Validate and clean data
            if validate:
                validation_result = self.validator.validate_ohlcv(raw_df)
                
                if not validation_result.valid:
                    logger.warning(f"Data validation failed for {symbol} {timeframe}")
                    for issue in validation_result.issues:
                        if issue.severity == "critical":
                            logger.error(f"Critical issue: {issue.description}")
                
                cleaned_df = validation_result.cleaned_df
                
                # Store data quality metrics
                await self._store_data_quality(symbol, timeframe, validation_result)
                
            else:
                cleaned_df = raw_df
            
            # Cache the cleaned data
            ttl = self._get_cache_ttl(end)
            self.cache.set(cache_key, cleaned_df, ttl)
            
            # Store cache metadata
            self._store_cache_metadata(cache_key, symbol, timeframe, start, end, 
                                     len(cleaned_df), "binance")  # TODO: track actual source
            
            logger.info(f"Retrieved {len(cleaned_df)} candles for {symbol} {timeframe}")
            return cleaned_df
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {str(e)}")
            raise
    
    async def _store_data_quality(self, symbol: str, timeframe: str, 
                                 validation_result: ValidationResult):
        """Store data quality metrics in database"""
        try:
            # Calculate quality score (0-100)
            total_issues = len(validation_result.issues)
            critical_issues = len([i for i in validation_result.issues if i.severity == "critical"])
            error_issues = len([i for i in validation_result.issues if i.severity == "error"])
            warning_issues = len([i for i in validation_result.issues if i.severity == "warning"])
            
            # Quality score calculation
            quality_score = 100.0
            quality_score -= critical_issues * 50  # Critical issues heavily penalized
            quality_score -= error_issues * 20     # Error issues moderately penalized
            quality_score -= warning_issues * 5    # Warning issues lightly penalized
            quality_score = max(0.0, quality_score)
            
            # Count specific issue types
            missing_candles = len([i for i in validation_result.issues 
                                 if i.type == ValidationIssueType.MISSING_CANDLES])
            bad_ticks = len([i for i in validation_result.issues 
                           if i.type == ValidationIssueType.BAD_TICK])
            anomalies = len([i for i in validation_result.issues 
                           if i.type == ValidationIssueType.PRICE_SPIKE])
            zero_volume = len([i for i in validation_result.issues 
                             if i.type == ValidationIssueType.ZERO_VOLUME])
            duplicates = len([i for i in validation_result.issues 
                            if i.type == ValidationIssueType.DUPLICATE_TIMESTAMP])
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO data_quality 
                    (symbol, timeframe, total_candles, missing_candles, bad_ticks, 
                     anomalies, zero_volume_candles, duplicate_timestamps, 
                     quality_score, source, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, timeframe, validation_result.cleaned_count,
                    missing_candles, bad_ticks, anomalies, zero_volume, duplicates,
                    quality_score, "binance", datetime.utcnow().isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing data quality metrics: {str(e)}")
    
    def _store_cache_metadata(self, cache_key: str, symbol: str, timeframe: str,
                             start: datetime, end: datetime, record_count: int, source: str):
        """Store cache metadata in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_metadata 
                    (cache_key, symbol, timeframe, start_date, end_date, 
                     record_count, source, created_at, accessed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key, symbol, timeframe, start.isoformat(), end.isoformat(),
                    record_count, source, datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing cache metadata: {str(e)}")
    
    def get_data_quality(self, symbol: str, timeframe: str) -> Optional[DataQuality]:
        """Get data quality metrics for symbol/timeframe"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT symbol, timeframe, total_candles, missing_candles, 
                           bad_ticks, anomalies, zero_volume_candles, 
                           duplicate_timestamps, quality_score, source, last_updated
                    FROM data_quality 
                    WHERE symbol = ? AND timeframe = ?
                """, (symbol, timeframe))
                
                row = cursor.fetchone()
                
                if row:
                    return DataQuality(
                        symbol=row[0],
                        timeframe=row[1],
                        total_candles=row[2],
                        missing_candles=row[3],
                        bad_ticks=row[4],
                        anomalies=row[5],
                        zero_volume_candles=row[6],
                        duplicate_timestamps=row[7],
                        quality_score=row[8],
                        source=row[9],
                        last_updated=row[10]
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting data quality: {str(e)}")
            return None
    
    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.cache.stats()
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    async def export_data(self, symbol: str, timeframe: str, 
                         start: datetime, end: datetime, 
                         format: str = 'csv', include_smc: bool = False) -> Union[str, Dict]:
        """Export OHLCV data with optional SMC levels"""
        try:
            # Get OHLCV data
            df = await self.get_ohlcv(symbol, timeframe, start, end)
            
            if df.empty:
                return "" if format == 'csv' else {}
            
            # Add SMC levels if requested
            if include_smc:
                # This would integrate with SMC analysis
                # For now, add placeholder columns
                df['ob_zone'] = None
                df['fvg_zone'] = None
                df['liquidity_zone'] = None
                df['session'] = 'london'  # Placeholder
            
            if format.lower() == 'csv':
                return df.to_csv(index=False)
            elif format.lower() == 'json':
                return df.to_dict('records')
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise
    
    async def validate_data_batch(self, data_requests: List[Dict]) -> Dict[str, ValidationResult]:
        """Validate multiple data sets in batch"""
        results = {}
        
        for request in data_requests:
            try:
                symbol = request['symbol']
                timeframe = request['timeframe']
                start = request['start']
                end = request['end']
                
                df = await self.get_ohlcv(symbol, timeframe, start, end, validate=False)
                validation_result = self.validator.validate_ohlcv(df)
                
                key = f"{symbol}_{timeframe}"
                results[key] = validation_result
                
            except Exception as e:
                logger.error(f"Error in batch validation: {str(e)}")
                results[f"{request.get('symbol', 'unknown')}_{request.get('timeframe', 'unknown')}"] = ValidationResult(
                    valid=False,
                    issues=[ValidationIssue(
                        type=ValidationIssueType.INVALID_OHLC,
                        timestamp="",
                        description=str(e),
                        severity="critical"
                    )],
                    cleaned_df=pd.DataFrame(),
                    original_count=0,
                    cleaned_count=0,
                    issues_fixed=0
                )
        
        return results
    
    def get_cache_info(self, symbol: str = None, timeframe: str = None) -> List[Dict]:
        """Get cache information, optionally filtered by symbol/timeframe"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM cache_metadata"
                params = []
                
                if symbol:
                    query += " WHERE symbol = ?"
                    params.append(symbol)
                    
                    if timeframe:
                        query += " AND timeframe = ?"
                        params.append(timeframe)
                elif timeframe:
                    query += " WHERE timeframe = ?"
                    params.append(timeframe)
                
                query += " ORDER BY created_at DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting cache info: {str(e)}")
            return []
    
    async def preload_cache(self, symbols: List[str], timeframes: List[str], 
                           days_back: int = 30):
        """Preload cache with commonly used data"""
        logger.info(f"Preloading cache for {len(symbols)} symbols, {len(timeframes)} timeframes")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        tasks = []
        for symbol in symbols:
            for timeframe in timeframes:
                task = self.get_ohlcv(symbol, timeframe, start_time, end_time)
                tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = len([r for r in results if not isinstance(r, Exception)])
        failed = len(results) - successful
        
        logger.info(f"Cache preload completed: {successful} successful, {failed} failed")
        
        return {
            'total_requests': len(results),
            'successful': successful,
            'failed': failed,
            'cache_stats': self.get_cache_stats()
        }


# Global instance
data_manager = DataManager()


# Convenience functions
async def get_ohlcv(symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Get OHLCV data with validation and caching"""
    return await data_manager.get_ohlcv(symbol, timeframe, start, end)


def validate_ohlcv(df: pd.DataFrame) -> ValidationResult:
    """Validate OHLCV DataFrame"""
    return DataValidator.validate_ohlcv(df)


async def export_data(symbol: str, timeframe: str, start: datetime, end: datetime, 
                     format: str = 'csv') -> Union[str, Dict]:
    """Export OHLCV data"""
    return await data_manager.export_data(symbol, timeframe, start, end, format)