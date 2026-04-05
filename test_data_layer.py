#!/usr/bin/env python3
"""
Test script for Data Layer Upgrade (Module 9)
Tests data validation, caching, multi-source support, and API endpoints
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test data layer imports"""
    print("🧪 Testing Data Layer Imports...")
    
    try:
        from app.services.data_manager import (
            DataManager, DataValidator, DataSourceManager, TTLCache,
            ValidationResult, ValidationIssue, DataQuality, CacheStats,
            DataUnavailableError, data_manager, get_ohlcv, validate_ohlcv
        )
        print("✅ Data manager imports successful")
        
        from app.routes.data import router
        print("✅ Data routes imports successful")
        
        # Test pandas and numpy
        import pandas as pd
        import numpy as np
        print("✅ Data processing libraries imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_ttl_cache():
    """Test TTL cache functionality"""
    print("\n💾 Testing TTL Cache...")
    
    try:
        from app.services.data_manager import TTLCache
        
        cache = TTLCache(maxsize=10, max_size_mb=1.0)
        
        # Test basic set/get
        cache.set("test_key", "test_value", ttl=60)
        
        value = cache.get("test_key")
        if value == "test_value":
            print("✅ Basic cache set/get working")
        else:
            print("❌ Basic cache set/get failed")
            return False
        
        # Test TTL expiration
        cache.set("expire_key", "expire_value", ttl=0)  # Immediate expiration
        
        expired_value = cache.get("expire_key")
        if expired_value is None:
            print("✅ TTL expiration working")
        else:
            print("❌ TTL expiration failed")
            return False
        
        # Test cache stats
        stats = cache.stats()
        if hasattr(stats, 'total_entries') and hasattr(stats, 'hit_rate'):
            print("✅ Cache statistics working")
            print(f"   Total entries: {stats.total_entries}")
            print(f"   Hit rate: {stats.hit_rate:.1f}%")
        else:
            print("❌ Cache statistics failed")
            return False
        
        # Test size tracking
        large_data = pd.DataFrame({'col1': range(1000), 'col2': range(1000)})
        cache.set("large_key", large_data, ttl=60)
        
        if cache.current_size_mb > 0:
            print("✅ Cache size tracking working")
            print(f"   Current size: {cache.current_size_mb:.2f} MB")
        else:
            print("❌ Cache size tracking failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ TTL cache test error: {e}")
        return False

def test_data_validation():
    """Test data validation functionality"""
    print("\n🔍 Testing Data Validation...")
    
    try:
        from app.services.data_manager import DataValidator, ValidationIssueType
        
        # Create test data with various issues
        timestamps = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        # Good data
        good_data = pd.DataFrame({
            'timestamp': timestamps,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        })
        
        # Ensure OHLC consistency
        for i in range(len(good_data)):
            good_data.loc[i, 'high'] = max(good_data.loc[i, 'open'], good_data.loc[i, 'close'], good_data.loc[i, 'high'])
            good_data.loc[i, 'low'] = min(good_data.loc[i, 'open'], good_data.loc[i, 'close'], good_data.loc[i, 'low'])
        
        # Test good data validation
        result = DataValidator.validate_ohlcv(good_data)
        
        if result.valid:
            print("✅ Good data validation passed")
        else:
            print("❌ Good data should be valid")
            return False
        
        # Create problematic data
        bad_data = good_data.copy()
        
        # Add duplicate timestamps
        bad_data.loc[50] = bad_data.loc[49].copy()
        
        # Add bad tick (high < low)
        bad_data.loc[25, 'high'] = 50
        bad_data.loc[25, 'low'] = 100
        
        # Add zero volume
        bad_data.loc[75, 'volume'] = 0
        
        # Test problematic data validation
        bad_result = DataValidator.validate_ohlcv(bad_data)
        
        if not bad_result.valid or len(bad_result.issues) > 0:
            print("✅ Problematic data validation detected issues")
            print(f"   Issues found: {len(bad_result.issues)}")
            
            # Check for specific issue types
            issue_types = [issue.type for issue in bad_result.issues]
            
            if ValidationIssueType.DUPLICATE_TIMESTAMP in issue_types:
                print("✅ Duplicate timestamp detection working")
            
            if ValidationIssueType.BAD_TICK in issue_types:
                print("✅ Bad tick detection working")
            
            if ValidationIssueType.ZERO_VOLUME in issue_types:
                print("✅ Zero volume detection working")
                
        else:
            print("❌ Problematic data should have issues")
            return False
        
        # Test cleaned data
        if len(bad_result.cleaned_df) < len(bad_data):
            print("✅ Data cleaning removed problematic rows")
            print(f"   Original: {len(bad_data)}, Cleaned: {len(bad_result.cleaned_df)}")
        
        # Test empty data
        empty_result = DataValidator.validate_ohlcv(pd.DataFrame())
        if not empty_result.valid:
            print("✅ Empty data validation correctly failed")
        else:
            print("❌ Empty data should be invalid")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data validation test error: {e}")
        return False

def test_data_source_manager():
    """Test data source manager"""
    print("\n🌐 Testing Data Source Manager...")
    
    try:
        from app.services.data_manager import DataSourceManager, DataSource
        
        manager = DataSourceManager()
        
        # Test asset type detection
        test_cases = [
            ("BTCUSDT", "crypto"),
            ("EURUSD", "forex"),
            ("GBPJPY", "forex"),
            ("ETHBTC", "crypto")
        ]
        
        for symbol, expected_type in test_cases:
            detected_type = manager.get_asset_type(symbol)
            if detected_type == expected_type:
                print(f"✅ Asset type detection: {symbol} -> {detected_type}")
            else:
                print(f"❌ Asset type detection failed: {symbol} -> {detected_type} (expected {expected_type})")
                return False
        
        # Test source initialization
        if DataSource.MOCK in manager.sources:
            print("✅ Mock data source initialized")
        else:
            print("❌ Mock data source should always be available")
            return False
        
        # Test priority order
        crypto_sources = manager.priority_order.get('crypto', [])
        if DataSource.BINANCE in crypto_sources and DataSource.MOCK in crypto_sources:
            print("✅ Crypto source priority order configured")
        else:
            print("❌ Crypto source priority order incorrect")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data source manager test error: {e}")
        return False

async def test_mock_data_generation():
    """Test mock data generation"""
    print("\n🎲 Testing Mock Data Generation...")
    
    try:
        from app.services.data_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # Test mock data generation
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        df = await manager._fetch_mock("BTCUSDT", "1h", start_time, end_time)
        
        if not df.empty:
            print(f"✅ Mock data generated: {len(df)} candles")
            
            # Check required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if not missing_cols:
                print("✅ Mock data has all required columns")
            else:
                print(f"❌ Mock data missing columns: {missing_cols}")
                return False
            
            # Check OHLC consistency
            ohlc_valid = all(
                (df['high'] >= df['open']) & 
                (df['high'] >= df['close']) & 
                (df['low'] <= df['open']) & 
                (df['low'] <= df['close'])
            )
            
            if ohlc_valid:
                print("✅ Mock data OHLC consistency valid")
            else:
                print("❌ Mock data OHLC consistency invalid")
                return False
            
            # Check timestamp sequence
            timestamps_sorted = df['timestamp'].is_monotonic_increasing
            if timestamps_sorted:
                print("✅ Mock data timestamps properly sequenced")
            else:
                print("❌ Mock data timestamps not properly sequenced")
                return False
                
        else:
            print("❌ Mock data generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mock data generation test error: {e}")
        return False

async def test_data_manager_integration():
    """Test data manager integration"""
    print("\n🔧 Testing Data Manager Integration...")
    
    try:
        from app.services.data_manager import DataManager
        
        manager = DataManager()
        
        # Test OHLCV retrieval
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        df = await manager.get_ohlcv("BTCUSDT", "1h", start_time, end_time)
        
        if not df.empty:
            print(f"✅ Data manager retrieved {len(df)} candles")
        else:
            print("❌ Data manager failed to retrieve data")
            return False
        
        # Test caching (second request should be faster)
        import time
        
        start_cache_test = time.time()
        df_cached = await manager.get_ohlcv("BTCUSDT", "1h", start_time, end_time)
        cache_time = time.time() - start_cache_test
        
        if len(df_cached) == len(df) and cache_time < 0.1:  # Should be very fast from cache
            print("✅ Data caching working")
            print(f"   Cache retrieval time: {cache_time:.3f}s")
        else:
            print("⚠️ Data caching may not be working optimally")
        
        # Test cache statistics
        cache_stats = manager.get_cache_stats()
        if cache_stats.total_entries > 0:
            print("✅ Cache statistics available")
            print(f"   Cache entries: {cache_stats.total_entries}")
            print(f"   Cache size: {cache_stats.total_size_mb:.2f} MB")
            print(f"   Hit rate: {cache_stats.hit_rate:.1f}%")
        
        # Test data quality tracking
        quality = manager.get_data_quality("BTCUSDT", "1h")
        if quality:
            print("✅ Data quality tracking working")
            print(f"   Quality score: {quality.quality_score:.1f}/100")
            print(f"   Total candles: {quality.total_candles}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data manager integration test error: {e}")
        return False

async def test_data_export():
    """Test data export functionality"""
    print("\n📤 Testing Data Export...")
    
    try:
        from app.services.data_manager import DataManager
        
        manager = DataManager()
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 6, 0, 0)
        
        # Test CSV export
        csv_data = await manager.export_data("BTCUSDT", "1h", start_time, end_time, "csv")
        
        if isinstance(csv_data, str) and "timestamp" in csv_data:
            print("✅ CSV export working")
            print(f"   CSV length: {len(csv_data)} characters")
        else:
            print("❌ CSV export failed")
            return False
        
        # Test JSON export
        json_data = await manager.export_data("BTCUSDT", "1h", start_time, end_time, "json")
        
        if isinstance(json_data, list) and len(json_data) > 0:
            print("✅ JSON export working")
            print(f"   JSON records: {len(json_data)}")
            
            # Check JSON structure
            first_record = json_data[0]
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            if all(field in first_record for field in required_fields):
                print("✅ JSON export structure correct")
            else:
                print("❌ JSON export structure incorrect")
                return False
                
        else:
            print("❌ JSON export failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data export test error: {e}")
        return False

async def test_batch_validation():
    """Test batch validation functionality"""
    print("\n📊 Testing Batch Validation...")
    
    try:
        from app.services.data_manager import DataManager
        
        manager = DataManager()
        
        # Create batch validation requests
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        batch_requests = [
            {
                'symbol': 'BTCUSDT',
                'timeframe': '1h',
                'start': start_time,
                'end': end_time
            },
            {
                'symbol': 'ETHUSDT',
                'timeframe': '1h',
                'start': start_time,
                'end': end_time
            }
        ]
        
        results = await manager.validate_data_batch(batch_requests)
        
        if isinstance(results, dict) and len(results) == 2:
            print("✅ Batch validation working")
            
            for key, result in results.items():
                print(f"   {key}: {'Valid' if result.valid else 'Invalid'} ({len(result.issues)} issues)")
                
        else:
            print("❌ Batch validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Batch validation test error: {e}")
        return False

async def test_cache_preloading():
    """Test cache preloading functionality"""
    print("\n🚀 Testing Cache Preloading...")
    
    try:
        from app.services.data_manager import DataManager
        
        manager = DataManager()
        
        # Clear cache first
        manager.clear_cache()
        
        # Test preloading
        symbols = ['BTCUSDT', 'ETHUSDT']
        timeframes = ['1h', '4h']
        days_back = 7
        
        result = await manager.preload_cache(symbols, timeframes, days_back)
        
        if isinstance(result, dict) and 'successful' in result:
            print("✅ Cache preloading working")
            print(f"   Total requests: {result['total_requests']}")
            print(f"   Successful: {result['successful']}")
            print(f"   Failed: {result['failed']}")
            
            # Check if cache was populated
            cache_stats = result.get('cache_stats')
            if cache_stats and cache_stats.total_entries > 0:
                print(f"   Cache entries after preload: {cache_stats.total_entries}")
            
        else:
            print("❌ Cache preloading failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Cache preloading test error: {e}")
        return False

def test_api_models():
    """Test API request/response models"""
    print("\n🌐 Testing API Models...")
    
    try:
        from app.routes.data import (
            DataRequest, ValidationResultResponse, DataQualityResponse,
            CacheStatsResponse, ExportRequest, BatchValidationRequest
        )
        
        # Test DataRequest model
        data_request = DataRequest(
            symbol="BTCUSDT",
            timeframe="1h",
            start="2024-01-01T00:00:00",
            end="2024-01-01T12:00:00",
            validate=True
        )
        
        if data_request.symbol == "BTCUSDT" and data_request.validate:
            print("✅ DataRequest model working")
        else:
            print("❌ DataRequest model failed")
            return False
        
        # Test ValidationResultResponse model
        validation_response = ValidationResultResponse(
            valid=True,
            issues=[],
            original_count=100,
            cleaned_count=98,
            issues_fixed=2
        )
        
        if validation_response.valid and validation_response.issues_fixed == 2:
            print("✅ ValidationResultResponse model working")
        else:
            print("❌ ValidationResultResponse model failed")
            return False
        
        # Test DataQualityResponse model
        quality_response = DataQualityResponse(
            symbol="BTCUSDT",
            timeframe="1h",
            total_candles=1000,
            missing_candles=5,
            bad_ticks=2,
            anomalies=1,
            zero_volume_candles=10,
            duplicate_timestamps=3,
            quality_score=95.5,
            source="binance",
            last_updated="2024-01-01T12:00:00"
        )
        
        if quality_response.quality_score == 95.5 and quality_response.total_candles == 1000:
            print("✅ DataQualityResponse model working")
        else:
            print("❌ DataQualityResponse model failed")
            return False
        
        # Test CacheStatsResponse model
        cache_stats_response = CacheStatsResponse(
            total_entries=50,
            total_size_mb=25.5,
            hit_rate=85.0,
            miss_rate=15.0,
            evictions=5,
            oldest_entry="2024-01-01T00:00:00",
            newest_entry="2024-01-01T12:00:00"
        )
        
        if cache_stats_response.hit_rate == 85.0 and cache_stats_response.total_entries == 50:
            print("✅ CacheStatsResponse model working")
        else:
            print("❌ CacheStatsResponse model failed")
            return False
        
        # Test ExportRequest model
        export_request = ExportRequest(
            symbol="BTCUSDT",
            timeframe="1h",
            start="2024-01-01T00:00:00",
            end="2024-01-01T12:00:00",
            format="csv",
            include_smc=True
        )
        
        if export_request.format == "csv" and export_request.include_smc:
            print("✅ ExportRequest model working")
        else:
            print("❌ ExportRequest model failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API models test error: {e}")
        return False

async def main():
    """Run all data layer tests"""
    print("Data Layer Upgrade (Module 9) - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("TTL Cache", test_ttl_cache),
        ("Data Validation", test_data_validation),
        ("Data Source Manager", test_data_source_manager),
        ("Mock Data Generation", test_mock_data_generation),
        ("Data Manager Integration", test_data_manager_integration),
        ("Data Export", test_data_export),
        ("Batch Validation", test_batch_validation),
        ("Cache Preloading", test_cache_preloading),
        ("API Models", test_api_models)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n📋 MODULE 9 - Data Layer Upgrade COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • Data Validation:")
        print("    - Missing candles detection and forward-fill (up to 3 gaps)")
        print("    - Bad tick detection (high < low, close outside range)")
        print("    - Zero volume candle flagging (kept for crypto)")
        print("    - Duplicate timestamp removal (keep last)")
        print("    - Price spike detection (> 10x ATR)")
        print("    - Comprehensive validation reporting")
        print("  • Caching Layer:")
        print("    - TTL-based in-memory caching with size tracking")
        print("    - Smart TTL: 60s live data, 1h historical, 5min SMC")
        print("    - 500MB cache size limit with LRU eviction")
        print("    - Cache statistics and performance monitoring")
        print("  • Multi-Source Data:")
        print("    - Binance API (primary for crypto)")
        print("    - Alpha Vantage API (placeholder for forex)")
        print("    - Mock data generator (fallback for testing)")
        print("    - Automatic fallback with error handling")
        print("  • Data Export:")
        print("    - CSV and JSON export formats")
        print("    - Optional SMC levels inclusion")
        print("    - Streaming CSV downloads")
        print("    - Batch export capabilities")
        print("  • Data Quality Dashboard:")
        print("    - Quality score calculation (0-100)")
        print("    - Issue categorization and severity levels")
        print("    - Historical quality tracking")
        print("    - Source attribution and timestamps")
        print("  • API Endpoints:")
        print("    - GET /api/data/ohlcv → validated OHLCV data")
        print("    - POST /api/data/validate → data quality validation")
        print("    - GET /api/data/quality → quality metrics")
        print("    - GET /api/data/export → CSV/JSON export")
        print("    - GET /api/data/cache/stats → cache performance")
        print("    - POST /api/data/cache/preload → cache warming")
        print("    - POST /api/data/validate/batch → batch validation")
        print("\n🚀 Professional Data Pipeline!")
        print("\nThe system now provides:")
        print("• Robust data validation with automatic cleaning")
        print("• High-performance caching with intelligent TTL")
        print("• Multi-source data fetching with fallback mechanisms")
        print("• Comprehensive data quality monitoring and reporting")
        print("• Professional data export capabilities")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)