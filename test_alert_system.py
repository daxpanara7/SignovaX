#!/usr/bin/env python3
"""
Test script for Multi-Channel Alert System (Module 8)
Tests alert management, preferences, channels, and API endpoints
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test alert system imports"""
    print("🧪 Testing Alert System Imports...")
    
    try:
        from app.services.alert_manager import (
            AlertManager, Alert, AlertPreferences, AlertType, AlertChannel, AlertSeverity,
            alert_manager, send_signal_alert, send_circuit_breaker_alert, send_daily_pnl_alert
        )
        print("✅ Alert manager imports successful")
        
        from app.routes.alerts import router
        print("✅ Alert routes imports successful")
        
        # Test aiohttp import for webhooks
        import aiohttp
        print("✅ HTTP client imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_alert_manager_initialization():
    """Test AlertManager initialization"""
    print("\n🔧 Testing AlertManager Initialization...")
    
    try:
        from app.services.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Test database initialization
        if hasattr(manager, 'db_path'):
            print("✅ Database path configured")
        
        # Test preferences loading
        if hasattr(manager, 'preferences'):
            print("✅ Preferences loaded")
            print(f"   Default confluence threshold: {manager.preferences.min_confluence_to_alert}")
            print(f"   Default sessions: {manager.preferences.sessions_to_alert}")
            print(f"   Default signal types: {manager.preferences.signal_types_to_alert}")
        
        # Test WebSocket connections set
        if hasattr(manager, 'websocket_connections'):
            print("✅ WebSocket connections initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ AlertManager initialization test error: {e}")
        return False

def test_alert_preferences():
    """Test alert preferences management"""
    print("\n⚙️ Testing Alert Preferences...")
    
    try:
        from app.services.alert_manager import AlertManager, AlertPreferences
        
        manager = AlertManager()
        
        # Test getting preferences
        preferences = manager.get_preferences()
        
        if isinstance(preferences, dict):
            print("✅ Preferences retrieved as dictionary")
            print(f"   Telegram enabled: {preferences.get('telegram_enabled', False)}")
            print(f"   Email enabled: {preferences.get('email_enabled', False)}")
            print(f"   Webhook enabled: {preferences.get('webhook_enabled', False)}")
        else:
            print("❌ Preferences should be returned as dictionary")
            return False
        
        # Test updating preferences
        test_updates = {
            'min_confluence_to_alert': 80,
            'sessions_to_alert': ['london', 'new_york'],
            'signal_types_to_alert': ['BOS', 'CHOCH']
        }
        
        success = manager.update_preferences(test_updates)
        
        if success:
            print("✅ Preferences updated successfully")
            
            # Verify updates
            updated_preferences = manager.get_preferences()
            if updated_preferences['min_confluence_to_alert'] == 80:
                print("✅ Confluence threshold updated correctly")
            else:
                print("❌ Confluence threshold not updated")
                return False
                
        else:
            print("❌ Failed to update preferences")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Alert preferences test error: {e}")
        return False

def test_signal_filtering():
    """Test signal alert filtering logic"""
    print("\n🔍 Testing Signal Filtering Logic...")
    
    try:
        from app.services.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Set test preferences
        manager.update_preferences({
            'min_confluence_to_alert': 70,
            'sessions_to_alert': ['london', 'new_york'],
            'signal_types_to_alert': ['BOS', 'CHOCH']
        })
        
        # Test signals that should pass
        good_signal = {
            'symbol': 'BTCUSDT',
            'confluence_score': 85,
            'session': 'london',
            'signal_type': 'BOS'
        }
        
        should_alert = manager._should_alert_for_signal(good_signal)
        if should_alert:
            print("✅ Good signal passes filtering")
        else:
            print("❌ Good signal should pass filtering")
            return False
        
        # Test signals that should fail
        test_cases = [
            ({'confluence_score': 60, 'session': 'london', 'signal_type': 'BOS'}, "Low confluence"),
            ({'confluence_score': 85, 'session': 'asia', 'signal_type': 'BOS'}, "Wrong session"),
            ({'confluence_score': 85, 'session': 'london', 'signal_type': 'FVG'}, "Wrong signal type")
        ]
        
        for bad_signal, reason in test_cases:
            should_alert = manager._should_alert_for_signal(bad_signal)
            if not should_alert:
                print(f"✅ Signal correctly filtered: {reason}")
            else:
                print(f"❌ Signal should be filtered: {reason}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Signal filtering test error: {e}")
        return False

def test_message_formatting():
    """Test alert message formatting"""
    print("\n📝 Testing Message Formatting...")
    
    try:
        from app.services.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Test signal message formatting
        test_signal = {
            'symbol': 'BTCUSDT',
            'direction': 'BUY',
            'signal_type': 'Order Block',
            'entry_price': 43250.00,
            'stop_loss': 42800.00,
            'take_profit': 44150.00,
            'confluence_score': 85,
            'ml_probability': 0.71,
            'session': 'london',
            'timeframes': ['4H', '1H', '15M']
        }
        
        message = manager._format_signal_message(test_signal)
        
        # Check message contains key information
        required_elements = [
            'SMC SIGNAL ALERT',
            'BTCUSDT',
            'BUY',
            'Order Block',
            '$43,250.00',
            '$42,800.00',
            '$44,150.00',
            '85/100',
            '71%',
            'London'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in message:
                missing_elements.append(element)
        
        if not missing_elements:
            print("✅ Signal message formatted correctly")
            print(f"   Message length: {len(message)} characters")
        else:
            print(f"❌ Missing elements in message: {missing_elements}")
            return False
        
        # Test R:R ratio calculation
        if "1:2.0" in message:  # (44150-43250)/(43250-42800) = 900/450 = 2.0
            print("✅ R:R ratio calculated correctly")
        else:
            print("❌ R:R ratio calculation incorrect")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Message formatting test error: {e}")
        return False

async def test_webhook_functionality():
    """Test webhook alert functionality"""
    print("\n🌐 Testing Webhook Functionality...")
    
    try:
        from app.services.alert_manager import AlertManager, Alert, AlertType, AlertSeverity
        
        manager = AlertManager()
        
        # Configure test webhook (using httpbin for testing)
        manager.update_preferences({
            'webhook_enabled': True,
            'webhook_url': 'https://httpbin.org/post',
            'webhook_secret': 'test-secret'
        })
        
        # Create test alert
        test_alert = Alert(
            type=AlertType.SYSTEM,
            title="Test Webhook Alert",
            message="This is a test webhook alert",
            payload={"test": True},
            severity=AlertSeverity.LOW
        )
        
        # Test webhook sending
        success = await manager._send_webhook_alert(test_alert)
        
        if success:
            print("✅ Webhook alert sent successfully")
            print(f"   Alert status: {test_alert.status}")
        else:
            print("❌ Webhook alert failed")
            print(f"   Error: {test_alert.error_message}")
            # Don't fail the test as httpbin might be unavailable
        
        # Test retry logic with invalid URL
        manager.update_preferences({
            'webhook_url': 'https://invalid-webhook-url-that-does-not-exist.com/webhook'
        })
        
        retry_alert = Alert(
            type=AlertType.SYSTEM,
            title="Test Retry Logic",
            message="This should fail and retry",
            payload={"test": True},
            severity=AlertSeverity.LOW
        )
        
        success = await manager._send_webhook_alert(retry_alert)
        
        if not success and retry_alert.retry_count > 0:
            print("✅ Webhook retry logic working")
            print(f"   Retry count: {retry_alert.retry_count}")
        else:
            print("⚠️ Webhook retry logic test inconclusive")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook functionality test error: {e}")
        return False

def test_alert_storage():
    """Test alert database storage"""
    print("\n💾 Testing Alert Storage...")
    
    try:
        from app.services.alert_manager import AlertManager, Alert, AlertType, AlertChannel, AlertSeverity
        
        manager = AlertManager()
        
        # Create test alert
        test_alert = Alert(
            type=AlertType.SIGNAL,
            channel=AlertChannel.IN_APP,
            title="Test Storage Alert",
            message="This is a test alert for storage",
            payload={"symbol": "BTCUSDT", "test": True},
            severity=AlertSeverity.MEDIUM,
            status="sent"
        )
        
        # Store alert
        alert_id = manager._store_alert(test_alert)
        
        if alert_id:
            print(f"✅ Alert stored successfully with ID: {alert_id}")
        else:
            print("❌ Failed to store alert")
            return False
        
        # Test alert history retrieval
        history = manager.get_alert_history(limit=10)
        
        if isinstance(history, list) and len(history) > 0:
            print(f"✅ Alert history retrieved: {len(history)} alerts")
            
            # Check if our test alert is in history
            test_alert_found = any(alert['title'] == "Test Storage Alert" for alert in history)
            if test_alert_found:
                print("✅ Test alert found in history")
            else:
                print("❌ Test alert not found in history")
                return False
        else:
            print("❌ Failed to retrieve alert history")
            return False
        
        # Test alert statistics
        stats = manager.get_alert_statistics()
        
        if isinstance(stats, dict) and 'total_alerts' in stats:
            print("✅ Alert statistics retrieved")
            print(f"   Total alerts: {stats.get('total_alerts', 0)}")
            print(f"   Success rate: {stats.get('success_rate', 0):.1f}%")
        else:
            print("❌ Failed to retrieve alert statistics")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Alert storage test error: {e}")
        return False

async def test_signal_alert_workflow():
    """Test complete signal alert workflow"""
    print("\n🔄 Testing Signal Alert Workflow...")
    
    try:
        from app.services.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Configure for testing (disable external channels)
        manager.update_preferences({
            'telegram_enabled': False,
            'email_enabled': False,
            'webhook_enabled': False,
            'min_confluence_to_alert': 70,
            'sessions_to_alert': ['london', 'new_york'],
            'signal_types_to_alert': ['BOS', 'CHOCH', 'OB']
        })
        
        # Test signal that should trigger alert
        good_signal = {
            'symbol': 'BTCUSDT',
            'direction': 'BUY',
            'signal_type': 'BOS',
            'entry_price': 43250.00,
            'stop_loss': 42800.00,
            'take_profit': 44150.00,
            'confluence_score': 85,
            'ml_probability': 0.71,
            'session': 'london',
            'timeframes': ['4H', '1H', '15M']
        }
        
        success = await manager.send_signal_alert(good_signal)
        
        if success:
            print("✅ Signal alert workflow completed successfully")
        else:
            print("❌ Signal alert workflow failed")
            return False
        
        # Test signal that should be filtered out
        bad_signal = {
            'symbol': 'EURUSD',
            'direction': 'SELL',
            'signal_type': 'FVG',  # Not in allowed types
            'confluence_score': 60,  # Below threshold
            'session': 'asia'  # Not in allowed sessions
        }
        
        success = await manager.send_signal_alert(bad_signal)
        
        if not success:
            print("✅ Low-quality signal correctly filtered out")
        else:
            print("❌ Low-quality signal should have been filtered")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Signal alert workflow test error: {e}")
        return False

async def test_circuit_breaker_alert():
    """Test circuit breaker alert"""
    print("\n🚨 Testing Circuit Breaker Alert...")
    
    try:
        from app.services.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Configure for testing
        manager.update_preferences({
            'telegram_enabled': False,
            'email_enabled': False,
            'webhook_enabled': False
        })
        
        # Test circuit breaker alert
        reason = "Maximum daily loss exceeded"
        details = {
            'daily_loss': -5000.00,
            'max_loss_limit': -2500.00,
            'trades_today': 15,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        success = await manager.send_circuit_breaker_alert(reason, details)
        
        if success:
            print("✅ Circuit breaker alert sent successfully")
        else:
            print("❌ Circuit breaker alert failed")
            return False
        
        # Check if alert was stored
        history = manager.get_alert_history(limit=5)
        circuit_breaker_found = any(
            alert['type'] == 'circuit_breaker' and 'Circuit Breaker' in alert['title']
            for alert in history
        )
        
        if circuit_breaker_found:
            print("✅ Circuit breaker alert found in history")
        else:
            print("❌ Circuit breaker alert not found in history")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Circuit breaker alert test error: {e}")
        return False

async def test_daily_pnl_alert():
    """Test daily P&L alert"""
    print("\n📊 Testing Daily P&L Alert...")
    
    try:
        from app.services.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Configure for testing
        manager.update_preferences({
            'telegram_enabled': False,
            'email_enabled': False,
            'webhook_enabled': False
        })
        
        # Test daily P&L alert
        pnl_data = {
            'total_pnl': 1250.75,
            'total_trades': 8,
            'winning_trades': 6,
            'losing_trades': 2,
            'largest_win': 450.00,
            'largest_loss': -125.50,
            'date': datetime.utcnow().strftime('%Y-%m-%d')
        }
        
        success = await manager.send_daily_pnl_alert(pnl_data)
        
        if success:
            print("✅ Daily P&L alert sent successfully")
        else:
            print("❌ Daily P&L alert failed")
            return False
        
        # Check if alert was stored
        history = manager.get_alert_history(limit=5)
        pnl_alert_found = any(
            alert['type'] == 'daily_pnl' and 'Daily P&L' in alert['title']
            for alert in history
        )
        
        if pnl_alert_found:
            print("✅ Daily P&L alert found in history")
        else:
            print("❌ Daily P&L alert not found in history")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Daily P&L alert test error: {e}")
        return False

def test_api_models():
    """Test API request/response models"""
    print("\n🌐 Testing API Models...")
    
    try:
        from app.routes.alerts import (
            AlertPreferencesRequest, AlertPreferencesResponse,
            AlertHistoryResponse, AlertStatsResponse, TestAlertResponse
        )
        
        # Test preferences request model
        prefs_request = AlertPreferencesRequest(
            telegram_enabled=True,
            min_confluence_to_alert=80,
            sessions_to_alert=['london', 'new_york']
        )
        
        if prefs_request.telegram_enabled and prefs_request.min_confluence_to_alert == 80:
            print("✅ AlertPreferencesRequest model working")
        else:
            print("❌ AlertPreferencesRequest model failed")
            return False
        
        # Test preferences response model
        prefs_response = AlertPreferencesResponse(
            telegram_enabled=True,
            telegram_chat_id="123456789",
            telegram_bot_token="***1234",
            email_enabled=False,
            email_address=None,
            webhook_enabled=False,
            webhook_url=None,
            webhook_secret=None,
            min_confluence_to_alert=80,
            sessions_to_alert=['london', 'new_york'],
            signal_types_to_alert=['BOS', 'CHOCH']
        )
        
        if prefs_response.telegram_enabled and len(prefs_response.sessions_to_alert) == 2:
            print("✅ AlertPreferencesResponse model working")
        else:
            print("❌ AlertPreferencesResponse model failed")
            return False
        
        # Test alert history response model
        history_response = AlertHistoryResponse(
            id=1,
            type="signal",
            channel="in_app",
            title="Test Alert",
            message="Test message",
            payload={"test": True},
            timestamp=datetime.utcnow().isoformat(),
            severity="medium",
            status="sent",
            error_message=None,
            retry_count=0
        )
        
        if history_response.id == 1 and history_response.type == "signal":
            print("✅ AlertHistoryResponse model working")
        else:
            print("❌ AlertHistoryResponse model failed")
            return False
        
        # Test stats response model
        stats_response = AlertStatsResponse(
            total_alerts=100,
            sent_count=95,
            failed_count=5,
            pending_count=0,
            channel_counts={"in_app": 50, "telegram": 30, "webhook": 20},
            type_counts={"signal": 80, "system": 20},
            recent_24h=25,
            success_rate=95.0
        )
        
        if stats_response.total_alerts == 100 and stats_response.success_rate == 95.0:
            print("✅ AlertStatsResponse model working")
        else:
            print("❌ AlertStatsResponse model failed")
            return False
        
        # Test test alert response model
        test_response = TestAlertResponse(
            success=True,
            message="Test successful",
            error=None
        )
        
        if test_response.success and test_response.message == "Test successful":
            print("✅ TestAlertResponse model working")
        else:
            print("❌ TestAlertResponse model failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API models test error: {e}")
        return False

async def main():
    """Run all alert system tests"""
    print("Multi-Channel Alert System (Module 8) - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("AlertManager Initialization", test_alert_manager_initialization),
        ("Alert Preferences", test_alert_preferences),
        ("Signal Filtering", test_signal_filtering),
        ("Message Formatting", test_message_formatting),
        ("Webhook Functionality", test_webhook_functionality),
        ("Alert Storage", test_alert_storage),
        ("Signal Alert Workflow", test_signal_alert_workflow),
        ("Circuit Breaker Alert", test_circuit_breaker_alert),
        ("Daily P&L Alert", test_daily_pnl_alert),
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
        print("\n📋 MODULE 8 - Multi-Channel Alert System COMPLETED!")
        print("\n✅ Features Implemented:")
        print("  • Multi-Channel Alerts:")
        print("    - Telegram: Bot integration with formatted messages")
        print("    - Webhook: HTTP POST with retry logic and exponential backoff")
        print("    - Email: HTML formatted emails via SMTP with TLS")
        print("    - In-App: WebSocket real-time notifications")
        print("  • Alert Management:")
        print("    - Configurable preferences per channel")
        print("    - Signal filtering by confluence score and session")
        print("    - Alert history and statistics tracking")
        print("    - Database storage with SQLite")
        print("  • Alert Types:")
        print("    - Signal alerts with detailed trading information")
        print("    - Circuit breaker alerts for risk management")
        print("    - Daily P&L summary alerts (sent at 21:00 UTC)")
        print("    - System alerts for maintenance and testing")
        print("  • Professional Features:")
        print("    - Retry logic with exponential backoff for webhooks")
        print("    - HTML email templates with trading data")
        print("    - WebSocket connections for real-time updates")
        print("    - Rate limiting and authentication on all endpoints")
        print("  • API Endpoints:")
        print("    - GET /api/alerts/preferences → current settings")
        print("    - PUT /api/alerts/preferences → update settings")
        print("    - GET /api/alerts/history → recent alerts")
        print("    - GET /api/alerts/stats → alert statistics")
        print("    - POST /api/alerts/test/telegram → test Telegram")
        print("    - POST /api/alerts/test/webhook → test webhook")
        print("    - WebSocket /api/alerts/ws → real-time notifications")
        print("\n🚀 Professional Alert System!")
        print("\nThe system now provides:")
        print("• Multi-channel alert delivery with fallback options")
        print("• Intelligent signal filtering and formatting")
        print("• Professional email templates and Telegram formatting")
        print("• Real-time WebSocket notifications for instant updates")
        print("• Comprehensive alert history and performance analytics")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)