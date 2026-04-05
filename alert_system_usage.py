#!/usr/bin/env python3
"""
Multi-Channel Alert System Usage Example
Demonstrates how to configure and use the alert system for trading notifications
"""

import sys
import os
import requests
import json
import asyncio
import websockets
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# API Configuration
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "smc_admin_2024"

class AlertSystemDemo:
    """Demonstration of Multi-Channel Alert System functionality"""
    
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
    
    def get_current_preferences(self):
        """Get current alert preferences"""
        try:
            response = requests.get(f"{API_BASE}/api/alerts/preferences", headers=self.headers)
            
            if response.status_code == 200:
                preferences = response.json()
                print("\n⚙️ Current Alert Preferences:")
                print(f"   Telegram Enabled: {'✅' if preferences['telegram_enabled'] else '❌'}")
                print(f"   Email Enabled: {'✅' if preferences['email_enabled'] else '❌'}")
                print(f"   Webhook Enabled: {'✅' if preferences['webhook_enabled'] else '❌'}")
                print(f"   Min Confluence Score: {preferences['min_confluence_to_alert']}")
                print(f"   Alert Sessions: {', '.join(preferences['sessions_to_alert'])}")
                print(f"   Alert Signal Types: {', '.join(preferences['signal_types_to_alert'])}")
                
                if preferences['telegram_chat_id']:
                    print(f"   Telegram Chat ID: {preferences['telegram_chat_id']}")
                if preferences['email_address']:
                    print(f"   Email Address: {preferences['email_address']}")
                if preferences['webhook_url']:
                    print(f"   Webhook URL: {preferences['webhook_url']}")
                
                return preferences
            else:
                print(f"❌ Failed to get preferences: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting preferences: {e}")
            return None
    
    def configure_alert_preferences(self):
        """Configure alert preferences for demonstration"""
        try:
            # Example configuration - adjust these values for your setup
            new_preferences = {
                "telegram_enabled": False,  # Set to True and add credentials to test
                "telegram_chat_id": None,   # Add your Telegram chat ID
                "telegram_bot_token": None, # Add your bot token
                "email_enabled": False,     # Set to True and configure SMTP to test
                "email_address": None,      # Add your email address
                "webhook_enabled": True,    # Enable webhook for testing
                "webhook_url": "https://httpbin.org/post",  # Test webhook URL
                "webhook_secret": "demo-secret-key",
                "min_confluence_to_alert": 75,
                "sessions_to_alert": ["london", "new_york", "overlap"],
                "signal_types_to_alert": ["BOS", "CHOCH", "OB"]
            }
            
            response = requests.put(
                f"{API_BASE}/api/alerts/preferences",
                headers=self.headers,
                json=new_preferences
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Alert preferences updated successfully")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}")
                return True
            else:
                print(f"❌ Failed to update preferences: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error configuring preferences: {e}")
            return False
    
    def test_webhook_alert(self):
        """Test webhook alert functionality"""
        try:
            response = requests.post(f"{API_BASE}/api/alerts/test/webhook", headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🌐 Webhook Test Result:")
                print(f"   Success: {'✅' if result['success'] else '❌'}")
                print(f"   Message: {result['message']}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
                return result['success']
            else:
                print(f"❌ Webhook test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing webhook: {e}")
            return False
    
    def test_telegram_alert(self):
        """Test Telegram alert functionality"""
        try:
            response = requests.post(f"{API_BASE}/api/alerts/test/telegram", headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n📱 Telegram Test Result:")
                print(f"   Success: {'✅' if result['success'] else '❌'}")
                print(f"   Message: {result['message']}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
                return result['success']
            else:
                print(f"❌ Telegram test failed: {response.status_code}")
                if response.status_code == 400:
                    error_data = response.json()
                    print(f"   Reason: {error_data.get('detail', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing Telegram: {e}")
            return False
    
    def send_test_signal_alert(self):
        """Send a test signal alert"""
        try:
            response = requests.post(f"{API_BASE}/api/alerts/send-test-signal", headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🚨 Test Signal Alert Result:")
                print(f"   Success: {'✅' if result['success'] else '❌'}")
                print(f"   Message: {result['message']}")
                
                if result.get('signal_data'):
                    signal = result['signal_data']
                    print(f"   Signal Details:")
                    print(f"     Symbol: {signal['symbol']}")
                    print(f"     Direction: {signal['direction']}")
                    print(f"     Type: {signal['signal_type']}")
                    print(f"     Entry: ${signal['entry_price']:,.2f}")
                    print(f"     Stop Loss: ${signal['stop_loss']:,.2f}")
                    print(f"     Take Profit: ${signal['take_profit']:,.2f}")
                    print(f"     Confluence: {signal['confluence_score']}/100")
                    print(f"     ML Probability: {signal['ml_probability']:.1%}")
                    print(f"     Session: {signal['session'].title()}")
                
                return result['success']
            else:
                print(f"❌ Test signal alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending test signal alert: {e}")
            return False
    
    def get_alert_history(self, limit=10):
        """Get recent alert history"""
        try:
            response = requests.get(
                f"{API_BASE}/api/alerts/history",
                headers=self.headers,
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                alerts = response.json()
                print(f"\n📋 Recent Alert History ({len(alerts)} alerts):")
                
                if alerts:
                    for i, alert in enumerate(alerts[:5], 1):  # Show first 5
                        status_icon = "✅" if alert['status'] == 'sent' else "❌" if alert['status'] == 'failed' else "⏳"
                        print(f"   {i}. {status_icon} {alert['title']}")
                        print(f"      Type: {alert['type'].title()} | Channel: {alert['channel'].title()}")
                        print(f"      Time: {alert['timestamp']}")
                        print(f"      Status: {alert['status'].title()}")
                        if alert['error_message']:
                            print(f"      Error: {alert['error_message']}")
                        print()
                else:
                    print("   📝 No alerts in history yet")
                    print("   💡 Send some test alerts to see them appear here")
                
                return alerts
            else:
                print(f"❌ Failed to get alert history: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting alert history: {e}")
            return []
    
    def get_alert_statistics(self):
        """Get alert statistics"""
        try:
            response = requests.get(f"{API_BASE}/api/alerts/stats", headers=self.headers)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"\n📊 Alert Statistics:")
                print(f"   Total Alerts: {stats['total_alerts']}")
                print(f"   Sent Successfully: {stats['sent_count']}")
                print(f"   Failed: {stats['failed_count']}")
                print(f"   Pending: {stats['pending_count']}")
                print(f"   Success Rate: {stats['success_rate']:.1f}%")
                print(f"   Recent 24h: {stats['recent_24h']}")
                
                if stats['channel_counts']:
                    print(f"   Channel Distribution:")
                    for channel, count in stats['channel_counts'].items():
                        print(f"     {channel.title()}: {count}")
                
                if stats['type_counts']:
                    print(f"   Alert Types:")
                    for alert_type, count in stats['type_counts'].items():
                        print(f"     {alert_type.title()}: {count}")
                
                return stats
            else:
                print(f"❌ Failed to get alert statistics: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting alert statistics: {e}")
            return {}
    
    async def test_websocket_notifications(self):
        """Test WebSocket real-time notifications"""
        try:
            print(f"\n🔌 Testing WebSocket Notifications...")
            print(f"   Connecting to WebSocket...")
            
            # Connect to WebSocket
            uri = f"ws://localhost:8000/api/alerts/ws"
            
            async with websockets.connect(uri) as websocket:
                print(f"   ✅ WebSocket connected")
                print(f"   📡 Listening for real-time alerts...")
                print(f"   💡 Send a test alert in another terminal to see real-time updates")
                
                # Listen for messages for 10 seconds
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    alert_data = json.loads(message)
                    
                    print(f"   🔔 Real-time alert received!")
                    print(f"      Event: {alert_data.get('event', 'unknown')}")
                    
                    if alert_data.get('data'):
                        data = alert_data['data']
                        print(f"      Title: {data.get('title', 'Unknown')}")
                        print(f"      Type: {data.get('type', 'Unknown')}")
                        print(f"      Severity: {data.get('severity', 'Unknown')}")
                        print(f"      Time: {data.get('timestamp', 'Unknown')}")
                    
                    return True
                    
                except asyncio.TimeoutError:
                    print(f"   ⏰ No alerts received in 10 seconds (this is normal)")
                    print(f"   💡 WebSocket connection is working, just no alerts to show")
                    return True
                    
        except Exception as e:
            print(f"   ❌ WebSocket test error: {e}")
            print(f"   💡 Make sure the backend server is running")
            return False
    
    def demonstrate_alert_filtering(self):
        """Demonstrate alert filtering logic"""
        print(f"\n🔍 Alert Filtering Demonstration:")
        print(f"   Current filter settings:")
        
        preferences = self.get_current_preferences()
        if preferences:
            print(f"     Min Confluence: {preferences['min_confluence_to_alert']}")
            print(f"     Allowed Sessions: {', '.join(preferences['sessions_to_alert'])}")
            print(f"     Allowed Signal Types: {', '.join(preferences['signal_types_to_alert'])}")
            
            print(f"\n   📋 Filtering Examples:")
            
            # Example signals
            examples = [
                {
                    "name": "High Quality London BOS",
                    "confluence_score": 85,
                    "session": "london",
                    "signal_type": "BOS",
                    "should_pass": True
                },
                {
                    "name": "Low Confluence Signal",
                    "confluence_score": 60,
                    "session": "london",
                    "signal_type": "BOS",
                    "should_pass": False
                },
                {
                    "name": "Asia Session Signal",
                    "confluence_score": 85,
                    "session": "asia",
                    "signal_type": "BOS",
                    "should_pass": False
                },
                {
                    "name": "FVG Signal (Not Allowed)",
                    "confluence_score": 85,
                    "session": "london",
                    "signal_type": "FVG",
                    "should_pass": False
                }
            ]
            
            for example in examples:
                confluence_ok = example["confluence_score"] >= preferences["min_confluence_to_alert"]
                session_ok = example["session"] in preferences["sessions_to_alert"]
                type_ok = example["signal_type"] in preferences["signal_types_to_alert"]
                
                would_pass = confluence_ok and session_ok and type_ok
                expected = example["should_pass"]
                
                status = "✅ PASS" if would_pass else "❌ FILTERED"
                correct = "✅" if would_pass == expected else "❌"
                
                print(f"     {correct} {example['name']}: {status}")
                
                if not confluence_ok:
                    print(f"         ❌ Confluence too low ({example['confluence_score']} < {preferences['min_confluence_to_alert']})")
                if not session_ok:
                    print(f"         ❌ Session not allowed ({example['session']})")
                if not type_ok:
                    print(f"         ❌ Signal type not allowed ({example['signal_type']})")
    
    def demonstrate_complete_workflow(self):
        """Demonstrate complete alert system workflow"""
        print("\n" + "="*60)
        print("🚨 MULTI-CHANNEL ALERT SYSTEM WORKFLOW DEMONSTRATION")
        print("="*60)
        
        # Step 1: Get current preferences
        print("\n1️⃣ CURRENT ALERT CONFIGURATION")
        current_preferences = self.get_current_preferences()
        
        # Step 2: Configure preferences for demo
        print("\n2️⃣ CONFIGURING ALERT PREFERENCES")
        config_success = self.configure_alert_preferences()
        
        # Step 3: Test individual channels
        print("\n3️⃣ TESTING ALERT CHANNELS")
        
        # Test webhook (should work with httpbin)
        webhook_success = self.test_webhook_alert()
        
        # Test Telegram (will show configuration needed)
        telegram_success = self.test_telegram_alert()
        
        # Step 4: Send test signal alert
        print("\n4️⃣ SENDING TEST SIGNAL ALERT")
        signal_success = self.send_test_signal_alert()
        
        # Step 5: Check alert history
        print("\n5️⃣ ALERT HISTORY AND STATISTICS")
        history = self.get_alert_history()
        stats = self.get_alert_statistics()
        
        # Step 6: Demonstrate filtering logic
        print("\n6️⃣ ALERT FILTERING LOGIC")
        self.demonstrate_alert_filtering()
        
        # Step 7: Test WebSocket (optional)
        print("\n7️⃣ REAL-TIME WEBSOCKET NOTIFICATIONS")
        print("   💡 Testing WebSocket connection (optional)...")
        
        # Summary
        print("\n" + "="*60)
        print("📋 ALERT SYSTEM DEMONSTRATION SUMMARY")
        print("="*60)
        
        print(f"   Configuration: {'✅ Success' if config_success else '❌ Failed'}")
        print(f"   Webhook Test: {'✅ Success' if webhook_success else '❌ Failed'}")
        print(f"   Telegram Test: {'✅ Success' if telegram_success else '⚠️ Not Configured'}")
        print(f"   Signal Alert: {'✅ Success' if signal_success else '❌ Failed'}")
        print(f"   History Retrieved: {'✅ Success' if history else '❌ Failed'}")
        print(f"   Statistics Retrieved: {'✅ Success' if stats else '❌ Failed'}")
        
        print(f"\n   🎯 Alert System Features:")
        print(f"      • Multi-channel delivery (Telegram, Webhook, Email, In-App)")
        print(f"      • Intelligent signal filtering by confluence and session")
        print(f"      • Professional message formatting with trading details")
        print(f"      • Real-time WebSocket notifications")
        print(f"      • Comprehensive alert history and statistics")
        print(f"      • Retry logic with exponential backoff for webhooks")
        print(f"      • Circuit breaker and daily P&L alerts")

async def main():
    """Main demonstration function"""
    print("Multi-Channel Alert System - Usage Example")
    print("=" * 50)
    
    # Create demo instance
    demo = AlertSystemDemo()
    
    # Authenticate
    if not demo.authenticate():
        print("❌ Cannot proceed without authentication")
        print("   Make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    
    # Run demonstration
    demo.demonstrate_complete_workflow()
    
    # Optional: Test WebSocket if user wants to
    print(f"\n🔌 Would you like to test WebSocket notifications?")
    print(f"   This will connect to the WebSocket and listen for 10 seconds...")
    
    try:
        # Try WebSocket test (will timeout gracefully if no alerts)
        await demo.test_websocket_notifications()
    except Exception as e:
        print(f"   ⚠️ WebSocket test skipped: {e}")
    
    print("\n" + "="*60)
    print("🎉 MULTI-CHANNEL ALERT SYSTEM DEMONSTRATION COMPLETE!")
    print("="*60)
    print("\n💡 Key Features Demonstrated:")
    print("   • Multi-channel alert configuration and testing")
    print("   • Professional signal alert formatting")
    print("   • Intelligent filtering by confluence score and session")
    print("   • Alert history and performance statistics")
    print("   • Real-time WebSocket notifications")
    print("   • Webhook integration with retry logic")
    
    print("\n🔧 Integration Points:")
    print("   • Signal generators can send alerts via send_signal_alert()")
    print("   • Risk management can trigger circuit breaker alerts")
    print("   • Daily P&L summaries can be automated at 21:00 UTC")
    print("   • Frontend can connect to WebSocket for real-time updates")
    print("   • External systems can receive webhooks with trading data")
    
    print("\n🚀 Next Steps:")
    print("   • Configure Telegram bot token and chat ID for Telegram alerts")
    print("   • Set up SMTP credentials for email alerts")
    print("   • Configure webhook URLs for external system integration")
    print("   • Integrate alert calls into signal generation workflow")
    print("   • Set up daily P&L alert automation")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)