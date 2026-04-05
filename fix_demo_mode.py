#!/usr/bin/env python3
"""
Fix Demo Mode Issue
Quick script to verify and fix the demo mode problem
"""

import subprocess
import sys
import os
import time
import requests
import json
from pathlib import Path

def check_backend():
    """Check if backend is running and healthy"""
    print("🔍 Checking backend status...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data['status']}")
            print(f"   Environment: {data['environment']}")
            print(f"   WebSocket connections: {data.get('websocket_connections', 0)}")
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running (connection refused)")
        return False
    except Exception as e:
        print(f"❌ Backend check failed: {e}")
        return False

def test_auth():
    """Test authentication"""
    print("🔑 Testing authentication...")
    
    try:
        response = requests.post("http://localhost:8000/api/auth/login", 
                               json={"username": "admin", "password": "smc_admin_2024"},
                               timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                print("✅ Authentication working")
                return data['access_token']
        
        print(f"❌ Authentication failed: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        return None

def test_data(token):
    """Test data endpoint"""
    print("📊 Testing data retrieval...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"symbol": "BTCUSDT", "timeframe": "1h", "limit": 5}
        
        response = requests.get("http://localhost:8000/api/data/ohlcv", 
                              params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print(f"✅ Data working: {len(data)} candles retrieved")
                print(f"   Latest BTC: ${data[-1]['close']}")
                return True
        
        print(f"❌ Data failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Data test failed: {e}")
        return False

def check_frontend_config():
    """Check frontend configuration"""
    print("🎨 Checking frontend configuration...")
    
    env_file = Path("frontend/.env")
    if env_file.exists():
        content = env_file.read_text()
        print("✅ Frontend .env exists:")
        for line in content.strip().split('\n'):
            if line and not line.startswith('#'):
                print(f"   {line}")
        return True
    else:
        print("❌ Frontend .env missing")
        return False

def main():
    """Main diagnostic function"""
    print("🔧 SMC Trading System - Demo Mode Fix")
    print("=" * 45)
    
    # Check backend
    backend_ok = check_backend()
    
    if not backend_ok:
        print("\n❌ Backend is not running!")
        print("💡 Start backend first:")
        print("   source globalvenv/bin/activate")
        print("   python start_system_main.py")
        return False
    
    # Test auth
    token = test_auth()
    if not token:
        print("\n❌ Authentication not working!")
        return False
    
    # Test data
    data_ok = test_data(token)
    if not data_ok:
        print("\n❌ Data retrieval not working!")
        return False
    
    # Check frontend config
    frontend_config_ok = check_frontend_config()
    
    print("\n📋 Diagnosis Summary:")
    print("=" * 25)
    print(f"Backend Health:     {'✅' if backend_ok else '❌'}")
    print(f"Authentication:     {'✅' if token else '❌'}")
    print(f"Data Retrieval:     {'✅' if data_ok else '❌'}")
    print(f"Frontend Config:    {'✅' if frontend_config_ok else '❌'}")
    
    if all([backend_ok, token, data_ok, frontend_config_ok]):
        print("\n🎉 All backend systems working!")
        print("💡 The issue is likely WebSocket connection.")
        print("🔧 WebSocket support has been added to backend.")
        print("🚀 Restart the system to apply fixes:")
        print("   1. Stop current processes (Ctrl+C)")
        print("   2. Run: python start_system_main.py")
        print("   3. Frontend should now show LIVE MODE")
        return True
    else:
        print("\n❌ Some systems not working")
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)