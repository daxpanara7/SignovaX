#!/usr/bin/env python3
"""
Data Layer Upgrade Usage Example
Demonstrates enhanced data pipeline with validation, caching, and multi-source support
"""

import sys
import os
import requests
import json
import asyncio
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# API Configuration
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "smc_admin_2024"

class DataLayerDemo:
    """Demonstration of Enhanced Data Layer functionality"""
    
    def __init__(self):
        self.token = None
        self.headers = {}
    
    def authenticate(self):
        """Authenticate with the API"""
        try:
            response = requests.post(f"{API_BASE}/api/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_ohlcv_data(self, symbol="BTCUSDT", timeframe="1h", hours_back=24):
        """Get OHLCV data with validation"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            response = requests.get(
                f"{API_BASE}/api/data/ohlcv",
                headers=self.headers,
                params={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "validate": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n📊 OHLCV Data Retrieved:")
                print(f"   Symbol: {data['symbol']}")
                print(f"   Timeframe: {data['timeframe']}")
                print(f"   Records: {data['count']}")
                print(f"   Validated: {'✅' if data['validated'] else '❌'}")
                
                if data.get('cache_stats'):
                    cache = data['cache_stats']
                    print(f"   Cache Hit Rate: {cache['hit_rate']:.1f}%")
                    print(f"   Cache Entries: {cache['total_entries']}")
                    print(f"   Cache Size: {cache['total_size_mb']:.2f} MB")
                
                # Show sample data
                if data['data']:
                    sample = data['data'][0]
                    print(f"   Sample Record:")
                    print(f"     Timestamp: {sample['timestamp']}")
                    print(f"     OHLC: {sample['open']:.2f}/{sample['high']:.2f}/{sample['low']:.2f}/{sample['close']:.2f}")
                    print(f"     Volume: {sample['volume']:.2f}")
                
                return data
            else:
                print(f"❌ Failed to get OHLCV data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting OHLCV data: {e}")
            return None
    
    def validate_data_quality(self, symbol="BTCUSDT", timeframe="1h"):
        """Validate data quality"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=48)
            
            response = requests.post(
                f"{API_BASE}/api/data/validate",
                headers=self.headers,
                json={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "validate": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🔍 Data Validation Results:")
                print(f"   Valid: {'✅' if result['valid'] else '❌'}")
                print(f"   Original Records: {result['original_count']}")
                print(f"   Cleaned Records: {result['cleaned_count']}")
                print(f"   Issues Fixed: {result['issues_fixed']}")
                
                if result['issues']:
                    print(f"   Issues Found: {len(result['issues'])}")
                    
                    # Group issues by type
                    issue_types = {}
                    for issue in result['issues']:
                        issue_type = issue['type']
                        if issue_type not in issue_types:
                            issue_types[issue_type] = []
                        issue_types[issue_type].append(issue)
                    
                    for issue_type, issues in issue_types.items():
                        severity_icon = "🔴" if issues[0]['severity'] == "critical" else "🟡" if issues[0]['severity'] == "error" else "🟠"
                        fixed_count = sum(1 for issue in issues if issue['fixed'])
                        print(f"     {severity_icon} {issue_type.replace('_', ' ').title()}: {len(issues)} ({fixed_count} fixed)")
                else:
                    print("   ✅ No issues found")
                
                return result
            else:
                print(f"❌ Failed to validate data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error validating data: {e}")
            return None
    
    def get_data_quality_metrics(self, symbol="BTCUSDT", timeframe="1h"):
        """Get data quality metrics"""
        try:
            response = requests.get(
                f"{API_BASE}/api/data/quality",
                headers=self.headers,
                params={
                    "symbol": symbol,
                    "timeframe": timeframe
                }
            )
            
            if response.status_code == 200:
                quality = response.json()
                
                if quality:
                    print(f"\n📈 Data Quality Metrics:")
                    print(f"   Symbol: {quality['symbol']}")
                    print(f"   Timeframe: {quality['timeframe']}")
                    print(f"   Quality Score: {quality['quality_score']:.1f}/100")
                    print(f"   Total Candles: {quality['total_candles']:,}")
                    print(f"   Data Source: {quality['source'].title()}")
                    print(f"   Last Updated: {quality['last_updated']}")
                    
                    print(f"   Issue Breakdown:")
                    print(f"     Missing Candles: {quality['missing_candles']}")
                    print(f"     Bad Ticks: {quality['bad_ticks']}")
                    print(f"     Anomalies: {quality['anomalies']}")
                    print(f"     Zero Volume: {quality['zero_volume_candles']}")
                    print(f"     Duplicates: {quality['duplicate_timestamps']}")
                    
                    # Quality assessment
                    score = quality['quality_score']
                    if score >= 95:
                        assessment = "🟢 Excellent"
                    elif score >= 85:
                        assessment = "🟡 Good"
                    elif score >= 70:
                        assessment = "🟠 Fair"
                    else:
                        assessment = "🔴 Poor"
                    
                    print(f"   Assessment: {assessment}")
                else:
                    print(f"\n📈 No quality metrics available for {symbol} {timeframe}")
                    print("   💡 Request some data first to generate quality metrics")
                
                return quality
            else:
                print(f"❌ Failed to get quality metrics: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting quality metrics: {e}")
            return None
    
    def get_cache_statistics(self):
        """Get cache performance statistics"""
        try:
            response = requests.get(f"{API_BASE}/api/data/cache/stats", headers=self.headers)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"\n💾 Cache Performance Statistics:")
                print(f"   Total Entries: {stats['total_entries']}")
                print(f"   Total Size: {stats['total_size_mb']:.2f} MB")
                print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
                print(f"   Miss Rate: {stats['miss_rate']:.1f}%")
                print(f"   Evictions: {stats['evictions']}")
                
                if stats['oldest_entry']:
                    print(f"   Oldest Entry: {stats['oldest_entry']}")
                if stats['newest_entry']:
                    print(f"   Newest Entry: {stats['newest_entry']}")
                
                # Performance assessment
                hit_rate = stats['hit_rate']
                if hit_rate >= 80:
                    performance = "🟢 Excellent"
                elif hit_rate >= 60:
                    performance = "🟡 Good"
                elif hit_rate >= 40:
                    performance = "🟠 Fair"
                else:
                    performance = "🔴 Poor"
                
                print(f"   Performance: {performance}")
                
                return stats
            else:
                print(f"❌ Failed to get cache stats: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting cache stats: {e}")
            return None
    
    def export_data(self, symbol="BTCUSDT", timeframe="1h", format="json", hours_back=12):
        """Export data in CSV or JSON format"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            response = requests.get(
                f"{API_BASE}/api/data/export",
                headers=self.headers,
                params={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "format": format,
                    "include_smc": False
                }
            )
            
            if response.status_code == 200:
                if format.lower() == "csv":
                    # CSV is returned as file download
                    print(f"\n📤 CSV Export:")
                    print(f"   Symbol: {symbol}")
                    print(f"   Timeframe: {timeframe}")
                    print(f"   Format: CSV")
                    print(f"   Size: {len(response.content)} bytes")
                    print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                    
                    # Show first few lines
                    csv_content = response.content.decode('utf-8')
                    lines = csv_content.split('\n')[:5]
                    print(f"   Preview:")
                    for line in lines:
                        if line.strip():
                            print(f"     {line}")
                    
                    return csv_content
                else:
                    # JSON format
                    data = response.json()
                    print(f"\n📤 JSON Export:")
                    print(f"   Symbol: {data['symbol']}")
                    print(f"   Timeframe: {data['timeframe']}")
                    print(f"   Format: {data['format'].upper()}")
                    print(f"   Records: {data['count']}")
                    print(f"   SMC Levels: {'✅' if data['include_smc'] else '❌'}")
                    
                    if data['data']:
                        sample = data['data'][0]
                        print(f"   Sample Record:")
                        for key, value in sample.items():
                            if key == 'timestamp':
                                print(f"     {key}: {value}")
                            elif isinstance(value, (int, float)):
                                print(f"     {key}: {value:.4f}")
                            else:
                                print(f"     {key}: {value}")
                    
                    return data
            else:
                print(f"❌ Failed to export data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return None
    
    def preload_cache(self):
        """Preload cache with commonly used data"""
        try:
            response = requests.post(
                f"{API_BASE}/api/data/cache/preload",
                headers=self.headers,
                json={
                    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
                    "timeframes": ["1h", "4h"],
                    "days_back": 7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🚀 Cache Preload Results:")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}")
                
                if result.get('result'):
                    preload_result = result['result']
                    print(f"   Total Requests: {preload_result['total_requests']}")
                    print(f"   Successful: {preload_result['successful']}")
                    print(f"   Failed: {preload_result['failed']}")
                    
                    success_rate = (preload_result['successful'] / preload_result['total_requests']) * 100
                    print(f"   Success Rate: {success_rate:.1f}%")
                
                return result
            else:
                print(f"❌ Failed to preload cache: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error preloading cache: {e}")
            return None
    
    def batch_validate_data(self):
        """Validate multiple data sets in batch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            response = requests.post(
                f"{API_BASE}/api/data/validate/batch",
                headers=self.headers,
                json={
                    "requests": [
                        {
                            "symbol": "BTCUSDT",
                            "timeframe": "1h",
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "validate": True
                        },
                        {
                            "symbol": "ETHUSDT",
                            "timeframe": "1h",
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "validate": True
                        },
                        {
                            "symbol": "ADAUSDT",
                            "timeframe": "4h",
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "validate": True
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"\n📊 Batch Validation Results:")
                print(f"   Total Validations: {len(results)}")
                
                for key, result in results.items():
                    symbol, timeframe = key.split('_', 1)
                    status = "✅ Valid" if result['valid'] else "❌ Invalid"
                    print(f"   {symbol} {timeframe}: {status}")
                    print(f"     Records: {result['original_count']} → {result['cleaned_count']}")
                    print(f"     Issues: {len(result['issues'])} ({result['issues_fixed']} fixed)")
                
                return results
            else:
                print(f"❌ Failed batch validation: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error in batch validation: {e}")
            return None
    
    def demonstrate_caching_performance(self):
        """Demonstrate caching performance benefits"""
        print(f"\n⚡ Caching Performance Demonstration:")
        
        import time
        
        # First request (cache miss)
        print(f"   Making first request (cache miss)...")
        start_time = time.time()
        data1 = self.get_ohlcv_data("BTCUSDT", "1h", 12)
        first_request_time = time.time() - start_time
        
        if data1:
            print(f"   First request time: {first_request_time:.3f}s")
        
        # Second request (cache hit)
        print(f"   Making second request (cache hit)...")
        start_time = time.time()
        data2 = self.get_ohlcv_data("BTCUSDT", "1h", 12)
        second_request_time = time.time() - start_time
        
        if data2:
            print(f"   Second request time: {second_request_time:.3f}s")
            
            if second_request_time < first_request_time:
                speedup = first_request_time / second_request_time
                print(f"   🚀 Cache speedup: {speedup:.1f}x faster")
            else:
                print(f"   ⚠️ Cache may not be working optimally")
    
    def demonstrate_complete_workflow(self):
        """Demonstrate complete data layer workflow"""
        print("\n" + "="*60)
        print("📊 DATA LAYER UPGRADE WORKFLOW DEMONSTRATION")
        print("="*60)
        
        # Step 1: Get OHLCV data with validation
        print("\n1️⃣ OHLCV DATA RETRIEVAL WITH VALIDATION")
        ohlcv_data = self.get_ohlcv_data("BTCUSDT", "1h", 24)
        
        # Step 2: Validate data quality
        print("\n2️⃣ DATA QUALITY VALIDATION")
        validation_result = self.validate_data_quality("BTCUSDT", "1h")
        
        # Step 3: Get quality metrics
        print("\n3️⃣ DATA QUALITY METRICS")
        quality_metrics = self.get_data_quality_metrics("BTCUSDT", "1h")
        
        # Step 4: Cache performance
        print("\n4️⃣ CACHE PERFORMANCE STATISTICS")
        cache_stats = self.get_cache_statistics()
        
        # Step 5: Data export
        print("\n5️⃣ DATA EXPORT CAPABILITIES")
        json_export = self.export_data("BTCUSDT", "1h", "json", 6)
        
        # Step 6: Cache preloading
        print("\n6️⃣ CACHE PRELOADING")
        preload_result = self.preload_cache()
        
        # Step 7: Batch validation
        print("\n7️⃣ BATCH DATA VALIDATION")
        batch_results = self.batch_validate_data()
        
        # Step 8: Caching performance demo
        print("\n8️⃣ CACHING PERFORMANCE DEMONSTRATION")
        self.demonstrate_caching_performance()
        
        # Summary
        print("\n" + "="*60)
        print("📋 DATA LAYER DEMONSTRATION SUMMARY")
        print("="*60)
        
        print(f"   OHLCV Data: {'✅ Success' if ohlcv_data else '❌ Failed'}")
        print(f"   Data Validation: {'✅ Success' if validation_result else '❌ Failed'}")
        print(f"   Quality Metrics: {'✅ Success' if quality_metrics else '❌ Failed'}")
        print(f"   Cache Statistics: {'✅ Success' if cache_stats else '❌ Failed'}")
        print(f"   Data Export: {'✅ Success' if json_export else '❌ Failed'}")
        print(f"   Cache Preload: {'✅ Success' if preload_result else '❌ Failed'}")
        print(f"   Batch Validation: {'✅ Success' if batch_results else '❌ Failed'}")
        
        print(f"\n   🎯 Data Layer Features:")
        print(f"      • Robust data validation with automatic cleaning")
        print(f"      • High-performance caching with intelligent TTL")
        print(f"      • Multi-source data fetching with fallback")
        print(f"      • Comprehensive quality monitoring and scoring")
        print(f"      • Professional data export in CSV/JSON formats")
        print(f"      • Batch processing for efficient operations")
        print(f"      • Cache preloading for performance optimization")

def main():
    """Main demonstration function"""
    print("Data Layer Upgrade - Usage Example")
    print("=" * 50)
    
    # Create demo instance
    demo = DataLayerDemo()
    
    # Authenticate
    if not demo.authenticate():
        print("❌ Cannot proceed without authentication")
        print("   Make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    
    # Run demonstration
    demo.demonstrate_complete_workflow()
    
    print("\n" + "="*60)
    print("🎉 DATA LAYER UPGRADE DEMONSTRATION COMPLETE!")
    print("="*60)
    print("\n💡 Key Features Demonstrated:")
    print("   • Comprehensive data validation with issue detection and fixing")
    print("   • High-performance TTL caching with size tracking")
    print("   • Multi-source data fetching with automatic fallback")
    print("   • Data quality scoring and monitoring")
    print("   • Professional data export capabilities")
    print("   • Batch processing for efficient operations")
    
    print("\n🔧 Integration Points:")
    print("   • Signal generators can use validated OHLCV data")
    print("   • Backtesting can leverage cached historical data")
    print("   • ML models can use quality-scored training data")
    print("   • Risk management can monitor data quality")
    print("   • Analytics can export data for external analysis")
    
    print("\n🚀 Next Steps:")
    print("   • Configure Binance API credentials for live data")
    print("   • Set up Alpha Vantage API for forex data")
    print("   • Integrate data validation into signal generation")
    print("   • Use cache preloading for commonly accessed data")
    print("   • Monitor data quality metrics for trading decisions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)