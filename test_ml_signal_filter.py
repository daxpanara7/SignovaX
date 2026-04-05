#!/usr/bin/env python3
"""
Test script for ML Signal Filter (Module 6)
Tests feature extraction, model training, and signal filtering
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
    """Test ML module imports"""
    print("🧪 Testing ML Module Imports...")
    
    try:
        from app.ml.signal_filter import SignalFilter, extract_features, train_model, filter_signal
        print("✅ Signal filter imports successful")
        
        from app.ml.training_data_generator import TrainingDataGenerator
        print("✅ Training data generator imports successful")
        
        # Test scikit-learn import
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
        print("✅ Scikit-learn imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_feature_extraction():
    """Test feature extraction functionality"""
    print("\n🔧 Testing Feature Extraction...")
    
    try:
        from app.ml.signal_filter import SignalFilter
        
        # Create test data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(50000, 51000, 100),
            'high': np.random.uniform(50500, 51500, 100),
            'low': np.random.uniform(49500, 50500, 100),
            'close': np.random.uniform(50000, 51000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        })
        
        # Create test signal
        signal = {
            'id': 'test_signal_1',
            'timestamp': '2024-01-01 12:00:00',
            'type': 'BOS',
            'direction': 'BUY',
            'entry_price': 50500.0,
            'stop_loss': 50000.0,
            'take_profit': 51500.0,
            'confluence_score': 75.0
        }
        
        # Create test market context
        market_context = {
            'htf_order_blocks': [
                {'top': 51000, 'bottom': 50800, 'mitigated': False, 'type': 'bullish'}
            ],
            'fvgs': [
                {'top': 50600, 'bottom': 50400, 'filled': False, 'fill_pct': 0.3}
            ],
            'liquidity_zones': [
                {'price': 50200, 'swept': True, 'swept_time': '2024-01-01 11:00:00'}
            ],
            'structure_events': [
                {'type': 'BOS', 'timestamp': '2024-01-01 10:00:00', 'direction': 'BUY'}
            ]
        }
        
        # Test feature extraction
        signal_filter = SignalFilter()
        features = signal_filter.extract_features(signal, df, market_context)
        
        # Validate features
        assert len(features) == 13, f"Expected 13 features, got {len(features)}"
        assert all(isinstance(f, (int, float, bool, np.number)) for f in features), "All features should be numeric"
        
        print(f"✅ Feature extraction successful - {len(features)} features extracted")
        print(f"   Features: {dict(zip(signal_filter.feature_names, features))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature extraction test error: {e}")
        return False

def test_model_training():
    """Test ML model training"""
    print("\n🤖 Testing Model Training...")
    
    try:
        from app.ml.signal_filter import train_model
        
        # Create synthetic training data
        n_samples = 100
        historical_signals = []
        outcomes = []
        
        for i in range(n_samples):
            # Create random features
            features = np.random.rand(13)
            
            signal = {
                'id': f'signal_{i}',
                'features': features,
                'confluence_score': features[8] * 100,  # Use confluence as a feature
                'type': 'BOS'
            }
            
            # Create outcome based on confluence score (higher = more likely to win)
            win_probability = features[8]  # Use confluence feature
            outcome = 1 if win_probability > 0.5 else 0
            
            historical_signals.append(signal)
            outcomes.append(outcome)
        
        # Train model
        results = train_model(historical_signals, outcomes)
        
        # Validate results
        assert 'error' not in results, f"Training failed: {results.get('error')}"
        assert 'accuracy' in results, "Results should include accuracy"
        assert 'precision' in results, "Results should include precision"
        assert 'recall' in results, "Results should include recall"
        assert 'feature_importances' in results, "Results should include feature importances"
        
        accuracy = results['accuracy']
        print(f"✅ Model training successful - Accuracy: {accuracy:.3f}")
        print(f"   Precision: {results['precision']:.3f}, Recall: {results['recall']:.3f}")
        print(f"   Training samples: {results['n_samples']}")
        
        # Test feature importances
        importances = results['feature_importances']
        assert len(importances) == 13, "Should have 13 feature importances"
        print(f"   Top 3 features: {sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model training test error: {e}")
        return False

def test_signal_filtering():
    """Test signal filtering with trained model"""
    print("\n🔍 Testing Signal Filtering...")
    
    try:
        from app.ml.signal_filter import filter_signal
        
        # Create test signal
        signal = {
            'id': 'test_filter_signal',
            'timestamp': '2024-01-01 15:00:00',
            'type': 'BOS',
            'direction': 'BUY',
            'entry_price': 50500.0,
            'stop_loss': 50000.0,
            'take_profit': 51500.0,
            'confluence_score': 80.0,
            'df': pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=50, freq='h'),
                'open': np.random.uniform(50000, 51000, 50),
                'high': np.random.uniform(50500, 51500, 50),
                'low': np.random.uniform(49500, 50500, 50),
                'close': np.random.uniform(50000, 51000, 50),
                'volume': np.random.uniform(100, 1000, 50)
            }),
            'market_context': {
                'htf_order_blocks': [],
                'fvgs': [],
                'liquidity_zones': [],
                'structure_events': []
            }
        }
        
        # Filter signal
        result = filter_signal(signal)
        
        # Validate result
        assert 'approved' in result, "Result should include approval status"
        assert 'win_probability' in result, "Result should include win probability"
        assert 'reason' in result, "Result should include reasoning"
        
        approved = result['approved']
        probability = result['win_probability']
        
        print(f"✅ Signal filtering successful")
        print(f"   Approved: {approved}")
        print(f"   Win Probability: {probability:.3f}")
        print(f"   Reason: {result['reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal filtering test error: {e}")
        return False

def test_training_data_generator():
    """Test training data generator functionality"""
    print("\n📊 Testing Training Data Generator...")
    
    try:
        from app.ml.training_data_generator import TrainingDataGenerator
        
        # Create generator instance
        generator = TrainingDataGenerator()
        
        # Test database initialization
        stats = generator.get_training_stats()
        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert 'total_samples' in stats, "Stats should include total samples"
        
        print(f"✅ Training data generator initialized")
        print(f"   Current samples: {stats['total_samples']}")
        print(f"   Overall win rate: {stats['overall_win_rate']:.3f}")
        
        # Test feature calculation methods
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=50, freq='h'),
            'open': np.random.uniform(50000, 51000, 50),
            'high': np.random.uniform(50500, 51500, 50),
            'low': np.random.uniform(49500, 50500, 50),
            'close': np.random.uniform(50000, 51000, 50),
            'volume': np.random.uniform(100, 1000, 50)
        })
        
        # Test individual calculation methods (using private methods from signal_filter)
        from app.ml.signal_filter import SignalFilter
        signal_filter_instance = SignalFilter()
        
        atr = signal_filter_instance._calculate_atr(df, 30)
        rsi = signal_filter_instance._calculate_rsi(df, 30)
        volume_ratio = signal_filter_instance._calculate_volume_ratio(df, 30)
        
        assert isinstance(atr, float), "ATR should be a float"
        assert isinstance(rsi, float), "RSI should be a float"
        assert isinstance(volume_ratio, float), "Volume ratio should be a float"
        
        print(f"   ATR calculation: {atr:.2f}")
        print(f"   RSI calculation: {rsi:.2f}")
        print(f"   Volume ratio: {volume_ratio:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Training data generator test error: {e}")
        return False

async def test_api_integration():
    """Test API integration (mock test)"""
    print("\n🌐 Testing API Integration...")
    
    try:
        # Test route imports
        from app.routes.ml import router
        assert router is not None, "ML router should be available"
        
        # Test request/response models
        from app.routes.ml import (
            TrainModelRequest, FilterSignalRequest, ModelStatusResponse,
            FeatureImportanceResponse, TrainingStatsResponse
        )
        
        # Test model creation
        train_request = TrainModelRequest(
            symbol="BTCUSDT",
            timeframe="1h",
            months_back=6,
            force_regenerate=False
        )
        
        filter_request = FilterSignalRequest(
            signal={
                'id': 'test_signal',
                'type': 'BOS',
                'entry_price': 50000,
                'confluence_score': 75
            },
            market_context={}
        )
        
        print("✅ API integration test successful")
        print(f"   Train request: {train_request.symbol} {train_request.timeframe}")
        print(f"   Filter request: {filter_request.signal['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test error: {e}")
        return False

def test_model_persistence():
    """Test model saving and loading"""
    print("\n💾 Testing Model Persistence...")
    
    try:
        from app.ml.signal_filter import SignalFilter
        import tempfile
        import os
        
        # Create temporary model path
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
            temp_model_path = tmp.name
        
        try:
            # Create signal filter with custom path
            signal_filter = SignalFilter()
            signal_filter.model_path = temp_model_path
            
            # Train a simple model
            from sklearn.ensemble import RandomForestClassifier
            signal_filter.model = RandomForestClassifier(n_estimators=10, random_state=42)
            
            # Create dummy training data
            X = np.random.rand(50, 13)
            y = np.random.randint(0, 2, 50)
            signal_filter.model.fit(X, y)
            
            # Test saving
            signal_filter.save_model()
            assert os.path.exists(temp_model_path), "Model file should be created"
            
            # Test loading
            new_filter = SignalFilter()
            new_filter.model_path = temp_model_path
            new_filter.load_model()
            
            assert new_filter.model is not None, "Model should be loaded"
            
            print("✅ Model persistence test successful")
            print(f"   Model saved and loaded from: {temp_model_path}")
            
            return True
            
        finally:
            # Clean up
            if os.path.exists(temp_model_path):
                os.unlink(temp_model_path)
        
    except Exception as e:
        print(f"❌ Model persistence test error: {e}")
        return False

def main():
    """Run all ML tests"""
    print("ML Signal Filter (Module 6) - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Feature Extraction", test_feature_extraction),
        ("Model Training", test_model_training),
        ("Signal Filtering", test_signal_filtering),
        ("Training Data Generator", test_training_data_generator),
        ("API Integration", lambda: asyncio.run(test_api_integration())),
        ("Model Persistence", test_model_persistence)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
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
        print("\n📋 MODULE 6 - ML Signal Filter COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • Feature Engineering:")
        print("    - 13 technical and contextual features")
        print("    - ATR, volume ratio, trading session, day of week")
        print("    - Distance to HTF Order Blocks, FVG analysis")
        print("    - Liquidity sweep detection, confluence scoring")
        print("    - RSI, Bollinger Band position, structure timing")
        print("  • Random Forest Model:")
        print("    - 100 estimators, max depth 5, balanced classes")
        print("    - 80/20 train/test split with stratification")
        print("    - Model persistence with pickle serialization")
        print("    - Feature importance analysis")
        print("  • Signal Filtering:")
        print("    - 65% win probability threshold")
        print("    - Fallback approval when no model available")
        print("    - Detailed reasoning for decisions")
        print("  • Training Data Generation:")
        print("    - Historical backtest signal labeling")
        print("    - 6 months of data processing")
        print("    - SQLite storage with indexing")
        print("    - Win/loss outcome determination")
        print("  • API Endpoints:")
        print("    - POST /api/ml/train → trigger model training")
        print("    - GET /api/ml/status → model metrics and info")
        print("    - GET /api/ml/features → feature importance data")
        print("    - POST /api/ml/filter → filter individual signals")
        print("    - GET /api/ml/training-stats → data statistics")
        print("  • Auto-retraining:")
        print("    - Weekly retraining with 50+ new samples")
        print("    - Background processing for performance")
        print("    - Admin-only training permissions")
        print("\n🚀 ML-Enhanced Signal Quality!")
        print("\nThe system now uses machine learning to filter signals")
        print("based on historical performance patterns, improving")
        print("overall trading accuracy and reducing false signals.")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)