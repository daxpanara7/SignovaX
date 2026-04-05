#!/usr/bin/env python3
"""
ML Signal Filter Usage Example
Demonstrates how to use the ML-based signal filtering system
"""

import sys
import os
import asyncio
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# API Configuration
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "smc_admin_2024"

class MLSignalFilterDemo:
    """Demonstration of ML Signal Filter functionality"""
    
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
    
    def check_model_status(self):
        """Check ML model status"""
        try:
            response = requests.get(f"{API_BASE}/api/ml/status", headers=self.headers)
            
            if response.status_code == 200:
                status = response.json()
                print("\n📊 ML Model Status:")
                print(f"   Model Trained: {status['model_trained']}")
                print(f"   Win Threshold: {status['win_threshold']}")
                print(f"   Feature Count: {status['feature_count']}")
                
                if status['model_trained']:
                    print(f"   Accuracy: {status.get('accuracy', 'N/A')}")
                    print(f"   Precision: {status.get('precision', 'N/A')}")
                    print(f"   Recall: {status.get('recall', 'N/A')}")
                    print(f"   Training Samples: {status.get('n_samples', 'N/A')}")
                    print(f"   Last Trained: {status.get('last_trained', 'N/A')}")
                else:
                    print("   ⚠️ No model trained yet")
                
                return status
            else:
                print(f"❌ Failed to get model status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error checking model status: {e}")
            return None
    
    def get_training_stats(self):
        """Get training data statistics"""
        try:
            response = requests.get(f"{API_BASE}/api/ml/training-stats", headers=self.headers)
            
            if response.status_code == 200:
                stats = response.json()
                print("\n📈 Training Data Statistics:")
                print(f"   Total Samples: {stats['total_samples']}")
                print(f"   Overall Win Rate: {stats['overall_win_rate']:.3f}")
                
                if stats['by_symbol']:
                    print("   By Symbol:")
                    for symbol_stat in stats['by_symbol']:
                        print(f"     {symbol_stat['symbol']}: {symbol_stat['count']} samples, {symbol_stat['win_rate']:.3f} win rate")
                
                if stats['by_signal_type']:
                    print("   By Signal Type:")
                    for type_stat in stats['by_signal_type']:
                        print(f"     {type_stat['signal_type']}: {type_stat['count']} samples, {type_stat['win_rate']:.3f} win rate")
                
                return stats
            else:
                print(f"❌ Failed to get training stats: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting training stats: {e}")
            return None
    
    def get_feature_importances(self):
        """Get feature importance data"""
        try:
            response = requests.get(f"{API_BASE}/api/ml/features", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                features = data['features']
                
                print("\n🔍 Feature Importances:")
                print(f"   Total Features: {data['total_features']}")
                
                # Sort by importance
                sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)
                
                print("   Top 10 Most Important Features:")
                for i, (feature, importance) in enumerate(sorted_features[:10], 1):
                    print(f"     {i:2d}. {feature:20s}: {importance:.4f}")
                
                return features
            else:
                print(f"❌ Failed to get feature importances: {response.status_code}")
                if response.status_code == 404:
                    print("   (No trained model available)")
                return None
                
        except Exception as e:
            print(f"❌ Error getting feature importances: {e}")
            return None
    
    def generate_training_data(self, symbol="BTCUSDT", timeframe="1h", months_back=6):
        """Generate training data (background process)"""
        try:
            print(f"\n🔄 Generating training data for {symbol} {timeframe}...")
            
            response = requests.post(f"{API_BASE}/api/ml/generate-data", 
                headers=self.headers,
                json={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "months_back": months_back,
                    "force_regenerate": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Training data generation started")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}")
                print(f"   Estimated Duration: {result['estimated_duration']}")
                return True
            else:
                print(f"❌ Failed to start training data generation: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating training data: {e}")
            return False
    
    def train_model(self, symbol="BTCUSDT", timeframe="1h", months_back=6):
        """Train ML model (background process)"""
        try:
            print(f"\n🤖 Training ML model for {symbol} {timeframe}...")
            
            response = requests.post(f"{API_BASE}/api/ml/train", 
                headers=self.headers,
                json={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "months_back": months_back,
                    "force_regenerate": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Model training started")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}")
                print(f"   Estimated Duration: {result['estimated_duration']}")
                return True
            else:
                print(f"❌ Failed to start model training: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error training model: {e}")
            return False
    
    def filter_signal_examples(self):
        """Test signal filtering with example signals"""
        print("\n🔍 Testing Signal Filtering...")
        
        # Example signals with different characteristics
        test_signals = [
            {
                "name": "High Confluence BOS",
                "signal": {
                    "id": "test_bos_high_conf",
                    "timestamp": "2024-01-15T10:00:00",
                    "type": "BOS",
                    "direction": "BUY",
                    "entry_price": 50500.0,
                    "stop_loss": 50000.0,
                    "take_profit": 51500.0,
                    "confluence_score": 85.0
                },
                "market_context": {
                    "htf_order_blocks": [
                        {"top": 51000, "bottom": 50800, "mitigated": False, "type": "bullish"}
                    ],
                    "fvgs": [
                        {"top": 50600, "bottom": 50400, "filled": False, "fill_pct": 0.2}
                    ],
                    "liquidity_zones": [
                        {"price": 50200, "swept": True, "swept_time": "2024-01-15T09:00:00"}
                    ]
                }
            },
            {
                "name": "Low Confluence CHOCH",
                "signal": {
                    "id": "test_choch_low_conf",
                    "timestamp": "2024-01-15T14:00:00",
                    "type": "CHOCH",
                    "direction": "SELL",
                    "entry_price": 50200.0,
                    "stop_loss": 50700.0,
                    "take_profit": 49200.0,
                    "confluence_score": 45.0
                },
                "market_context": {
                    "htf_order_blocks": [],
                    "fvgs": [],
                    "liquidity_zones": []
                }
            },
            {
                "name": "Order Block Signal",
                "signal": {
                    "id": "test_ob_signal",
                    "timestamp": "2024-01-15T16:00:00",
                    "type": "OB",
                    "direction": "BUY",
                    "entry_price": 50300.0,
                    "stop_loss": 49800.0,
                    "take_profit": 51300.0,
                    "confluence_score": 70.0
                },
                "market_context": {
                    "htf_order_blocks": [
                        {"top": 50400, "bottom": 50200, "mitigated": False, "type": "bullish"}
                    ],
                    "fvgs": [
                        {"top": 50350, "bottom": 50250, "filled": False, "fill_pct": 0.0}
                    ]
                }
            }
        ]
        
        results = []
        
        for test in test_signals:
            try:
                response = requests.post(f"{API_BASE}/api/ml/filter",
                    headers=self.headers,
                    json={
                        "signal": test["signal"],
                        "market_context": test["market_context"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "name": test["name"],
                        "approved": result["approved"],
                        "win_probability": result["win_probability"],
                        "reason": result["reason"]
                    })
                    
                    print(f"\n   📊 {test['name']}:")
                    print(f"      Signal ID: {result['signal_id']}")
                    print(f"      Approved: {'✅ YES' if result['approved'] else '❌ NO'}")
                    print(f"      Win Probability: {result['win_probability']:.3f}")
                    print(f"      Threshold: {result['threshold']}")
                    print(f"      Reason: {result['reason']}")
                    
                else:
                    print(f"   ❌ Failed to filter {test['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error filtering {test['name']}: {e}")
        
        return results
    
    def demonstrate_workflow(self):
        """Demonstrate complete ML workflow"""
        print("\n" + "="*60)
        print("🤖 ML SIGNAL FILTER WORKFLOW DEMONSTRATION")
        print("="*60)
        
        # Step 1: Check current status
        print("\n1️⃣ CHECKING CURRENT STATUS")
        status = self.check_model_status()
        stats = self.get_training_stats()
        
        # Step 2: Generate training data if needed
        if not stats or stats['total_samples'] < 50:
            print("\n2️⃣ GENERATING TRAINING DATA")
            print("   (This would normally take 10-30 minutes)")
            self.generate_training_data()
            print("   ⏳ Training data generation started in background...")
        else:
            print(f"\n2️⃣ TRAINING DATA AVAILABLE ({stats['total_samples']} samples)")
        
        # Step 3: Train model if needed
        if not status or not status['model_trained']:
            print("\n3️⃣ TRAINING ML MODEL")
            print("   (This would normally take 5-15 minutes)")
            self.train_model()
            print("   ⏳ Model training started in background...")
        else:
            print(f"\n3️⃣ MODEL ALREADY TRAINED (Accuracy: {status.get('accuracy', 'N/A')})")
        
        # Step 4: Show feature importances (if model exists)
        print("\n4️⃣ FEATURE ANALYSIS")
        self.get_feature_importances()
        
        # Step 5: Test signal filtering
        print("\n5️⃣ SIGNAL FILTERING EXAMPLES")
        results = self.filter_signal_examples()
        
        # Summary
        print("\n" + "="*60)
        print("📋 WORKFLOW SUMMARY")
        print("="*60)
        
        if results:
            approved_count = sum(1 for r in results if r['approved'])
            print(f"   Signals Tested: {len(results)}")
            print(f"   Signals Approved: {approved_count}")
            print(f"   Approval Rate: {approved_count/len(results)*100:.1f}%")
            
            print("\n   Signal Results:")
            for result in results:
                status_icon = "✅" if result['approved'] else "❌"
                print(f"     {status_icon} {result['name']}: {result['win_probability']:.3f} probability")
        
        print(f"\n   🎯 The ML filter helps improve signal quality by:")
        print(f"      • Analyzing 13 technical and contextual features")
        print(f"      • Learning from historical win/loss patterns")
        print(f"      • Filtering out low-probability signals")
        print(f"      • Providing probability-based decision making")

def main():
    """Main demonstration function"""
    print("ML Signal Filter - Usage Example")
    print("=" * 50)
    
    # Create demo instance
    demo = MLSignalFilterDemo()
    
    # Authenticate
    if not demo.authenticate():
        print("❌ Cannot proceed without authentication")
        print("   Make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    
    # Run demonstration
    demo.demonstrate_workflow()
    
    print("\n" + "="*60)
    print("🎉 ML SIGNAL FILTER DEMONSTRATION COMPLETE!")
    print("="*60)
    print("\n💡 Key Benefits:")
    print("   • Improved signal quality through ML filtering")
    print("   • Historical performance-based learning")
    print("   • Automated feature extraction and analysis")
    print("   • Probability-based decision making")
    print("   • Continuous model improvement with new data")
    
    print("\n🔧 Next Steps:")
    print("   • Let training data generation complete (10-30 min)")
    print("   • Let model training complete (5-15 min)")
    print("   • Integrate ML filtering into your trading strategy")
    print("   • Monitor model performance and retrain periodically")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)