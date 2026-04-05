#!/usr/bin/env python3
"""
Session Awareness Engine Usage Example
Demonstrates how to use the session management system for optimal trading
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# API Configuration
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "smc_admin_2024"

class SessionAwarenessDemo:
    """Demonstration of Session Awareness Engine functionality"""
    
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
    
    def get_current_session_status(self):
        """Get current market session status"""
        try:
            response = requests.get(f"{API_BASE}/api/sessions/status", headers=self.headers)
            
            if response.status_code == 200:
                status = response.json()
                print("\n📊 Current Session Status:")
                print(f"   Current Session: {status['current_session'].upper()}")
                print(f"   Trading Hours: {'✅ YES' if status['is_trading_hours'] else '❌ NO'}")
                print(f"   Session Overlap: {'✅ YES' if status['is_overlap'] else '❌ NO'}")
                
                if status['optimal_pairs']:
                    print(f"   Optimal Pairs: {', '.join(status['optimal_pairs'])}")
                
                if status['session_info']:
                    info = status['session_info']
                    print(f"   Session Time: {info['start_time']} - {info['end_time']} UTC")
                    print(f"   Session Color: {info['color']}")
                
                if status['next_session']:
                    print(f"   Next Session: {status['next_session']} in {status['time_to_next_session']}")
                
                return status
            else:
                print(f"❌ Failed to get session status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting session status: {e}")
            return None
    
    def check_trading_time_for_signals(self):
        """Check optimal trading times for different signal types"""
        print("\n⏰ Trading Time Analysis:")
        
        signal_types = ["CHOCH", "BOS", "OB", "FVG"]
        
        for signal_type in signal_types:
            try:
                response = requests.post(f"{API_BASE}/api/sessions/check-trading-time",
                    headers=self.headers,
                    json={
                        "signal_type": signal_type,
                        "utc_time": None  # Use current time
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    status_icon = "✅" if result['is_optimal'] else "❌"
                    print(f"   {status_icon} {signal_type} signals: {'OPTIMAL' if result['is_optimal'] else 'NOT OPTIMAL'}")
                    print(f"      Current Session: {result['current_session']}")
                    print(f"      Reasoning: {'; '.join(result['reasoning'])}")
                    
                else:
                    print(f"   ❌ Failed to check {signal_type}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error checking {signal_type}: {e}")
    
    def get_session_boxes_for_chart(self, symbol="BTCUSDT", date=None):
        """Get session boxes for chart overlay"""
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        try:
            response = requests.get(f"{API_BASE}/api/sessions/boxes",
                headers=self.headers,
                params={
                    "symbol": symbol,
                    "date": date
                }
            )
            
            if response.status_code == 200:
                boxes = response.json()
                print(f"\n📦 Session Boxes for {symbol} on {date}:")
                
                if boxes:
                    for box in boxes:
                        print(f"   📊 {box['session'].upper()} Session:")
                        print(f"      Time: {box['start_time']} - {box['end_time']}")
                        print(f"      Range: {box['high']:.2f} - {box['low']:.2f}")
                        print(f"      Pips: {box['range_pips']:.1f}")
                        print(f"      Color: {box['color']}")
                        print(f"      Active: {'✅' if box['is_active'] else '❌'}")
                else:
                    print("   📝 No session boxes available (no historical data)")
                    print("   💡 Session boxes will appear after market data is processed")
                
                return boxes
            else:
                print(f"❌ Failed to get session boxes: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting session boxes: {e}")
            return []
    
    def get_session_statistics(self, symbol="BTCUSDT", days=30):
        """Get session trading statistics"""
        try:
            response = requests.get(f"{API_BASE}/api/sessions/stats",
                headers=self.headers,
                params={
                    "symbol": symbol,
                    "days": days
                }
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"\n📈 Session Statistics for {symbol} (Last {days} days):")
                
                if stats:
                    # Find best session by win rate
                    best_session = None
                    best_win_rate = 0
                    
                    for session_name, session_stats in stats.items():
                        win_rate = session_stats['win_rate']
                        if win_rate > best_win_rate:
                            best_win_rate = win_rate
                            best_session = session_name
                        
                        print(f"   📊 {session_name.upper()} Session:")
                        print(f"      Total Signals: {session_stats['total_signals']}")
                        print(f"      Winning Signals: {session_stats['winning_signals']}")
                        print(f"      Win Rate: {win_rate:.1%}")
                        print(f"      Avg Range: {session_stats['avg_range_size']:.2f}")
                        print(f"      Avg Volume: {session_stats['avg_volume']:.2f}")
                        print(f"      Best Pairs: {', '.join(session_stats['best_pairs'])}")
                    
                    if best_session:
                        print(f"\n🏆 Best Session: {best_session.upper()} ({best_win_rate:.1%} win rate)")
                else:
                    print("   📝 No statistics available yet")
                    print("   💡 Statistics will accumulate as signals are processed")
                
                return stats
            else:
                print(f"❌ Failed to get session statistics: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting session statistics: {e}")
            return {}
    
    def get_optimal_pairs_by_session(self):
        """Get optimal trading pairs for each session"""
        print("\n💱 Optimal Trading Pairs by Session:")
        
        sessions = ["asia", "london", "new_york"]
        
        for session in sessions:
            try:
                response = requests.get(f"{API_BASE}/api/sessions/pairs/{session}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"   🌏 {session.upper()} Session:")
                    print(f"      Time: {data['session_info']['start_time']} - {data['session_info']['end_time']} UTC")
                    print(f"      Optimal Pairs: {', '.join(data['optimal_pairs'])}")
                    print(f"      Total Pairs: {data['total_pairs']}")
                    
                else:
                    print(f"   ❌ Failed to get pairs for {session}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error getting pairs for {session}: {e}")
    
    def demonstrate_session_filtering(self):
        """Demonstrate session-based signal filtering"""
        print("\n🔍 Session-Based Signal Filtering Examples:")
        
        # Example signals at different times
        test_signals = [
            {
                "name": "London Open CHOCH",
                "signal_type": "CHOCH",
                "time": "2024-01-15T07:30:00",  # 30 min after London open
                "expected": True
            },
            {
                "name": "London Late CHOCH", 
                "signal_type": "CHOCH",
                "time": "2024-01-15T10:00:00",  # 3 hours after London open
                "expected": False
            },
            {
                "name": "New York BOS",
                "signal_type": "BOS", 
                "time": "2024-01-15T14:00:00",  # During NY session
                "expected": True
            },
            {
                "name": "Off Hours Signal",
                "signal_type": "BOS",
                "time": "2024-01-15T22:00:00",  # Off hours
                "expected": False
            }
        ]
        
        for test in test_signals:
            try:
                response = requests.post(f"{API_BASE}/api/sessions/check-trading-time",
                    headers=self.headers,
                    json={
                        "signal_type": test["signal_type"],
                        "utc_time": test["time"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    status_icon = "✅" if result['is_optimal'] else "❌"
                    expected_icon = "✅" if test["expected"] else "❌"
                    
                    print(f"   {status_icon} {test['name']}:")
                    print(f"      Signal Type: {test['signal_type']}")
                    print(f"      Time: {test['time']}")
                    print(f"      Session: {result['current_session']}")
                    print(f"      Optimal: {result['is_optimal']} (Expected: {test['expected']} {expected_icon})")
                    print(f"      Reasoning: {'; '.join(result['reasoning'])}")
                    
                else:
                    print(f"   ❌ Failed to check {test['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error checking {test['name']}: {e}")
    
    def demonstrate_complete_workflow(self):
        """Demonstrate complete session awareness workflow"""
        print("\n" + "="*60)
        print("🌍 SESSION AWARENESS ENGINE WORKFLOW DEMONSTRATION")
        print("="*60)
        
        # Step 1: Check current session status
        print("\n1️⃣ CURRENT SESSION STATUS")
        current_status = self.get_current_session_status()
        
        # Step 2: Analyze trading times for different signals
        print("\n2️⃣ SIGNAL TYPE ANALYSIS")
        self.check_trading_time_for_signals()
        
        # Step 3: Get optimal pairs for each session
        print("\n3️⃣ OPTIMAL PAIRS BY SESSION")
        self.get_optimal_pairs_by_session()
        
        # Step 4: Get session boxes for chart
        print("\n4️⃣ CHART OVERLAY DATA")
        boxes = self.get_session_boxes_for_chart()
        
        # Step 5: Get session statistics
        print("\n5️⃣ SESSION PERFORMANCE STATISTICS")
        stats = self.get_session_statistics()
        
        # Step 6: Demonstrate signal filtering
        print("\n6️⃣ SESSION-BASED SIGNAL FILTERING")
        self.demonstrate_session_filtering()
        
        # Summary
        print("\n" + "="*60)
        print("📋 SESSION AWARENESS SUMMARY")
        print("="*60)
        
        if current_status:
            print(f"   Current Session: {current_status['current_session'].upper()}")
            print(f"   Trading Active: {'YES' if current_status['is_trading_hours'] else 'NO'}")
            
            if current_status['optimal_pairs']:
                print(f"   Recommended Pairs: {', '.join(current_status['optimal_pairs'][:3])}...")
        
        print(f"\n   🎯 Session Awareness Benefits:")
        print(f"      • Optimal timing for different signal types")
        print(f"      • Session-specific pair recommendations")
        print(f"      • Liquidity-based trading decisions")
        print(f"      • Historical session performance analysis")
        print(f"      • Chart overlay integration for visual analysis")

def main():
    """Main demonstration function"""
    print("Session Awareness Engine - Usage Example")
    print("=" * 50)
    
    # Create demo instance
    demo = SessionAwarenessDemo()
    
    # Authenticate
    if not demo.authenticate():
        print("❌ Cannot proceed without authentication")
        print("   Make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    
    # Run demonstration
    demo.demonstrate_complete_workflow()
    
    print("\n" + "="*60)
    print("🎉 SESSION AWARENESS ENGINE DEMONSTRATION COMPLETE!")
    print("="*60)
    print("\n💡 Key Features:")
    print("   • Real-time session detection (Asia, London, New York)")
    print("   • Overlap period identification for high liquidity")
    print("   • Signal type optimization (CHOCH vs BOS timing)")
    print("   • Session-specific pair recommendations")
    print("   • Historical performance analysis by session")
    print("   • Chart overlay integration with session boxes")
    
    print("\n🔧 Integration Points:")
    print("   • Signal generators can check optimal timing")
    print("   • Risk management can adjust based on session")
    print("   • Charts can display session ranges and overlaps")
    print("   • Backtesting can filter by session performance")
    print("   • ML models can use session as a feature")
    
    print("\n🚀 Next Steps:")
    print("   • Integrate session checks into signal generation")
    print("   • Add session filtering to backtesting")
    print("   • Use session data in ML feature engineering")
    print("   • Implement session-based position sizing")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)