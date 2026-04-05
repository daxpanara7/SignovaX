#!/usr/bin/env python3
"""
Test Authentication and Endpoints
Tests login and authenticated endpoints
"""

import requests
import json

def test_auth_flow():
    """Test the complete authentication flow"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing authentication flow...")
    
    # Test health endpoint (no auth required)
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health endpoint: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test login
    try:
        login_data = {
            "username": "admin",
            "password": "smc_admin_2024"
        }
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=5)
        print(f"Login response: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get('access_token')
            print(f"✅ Login successful, token: {access_token[:20]}...")
            
            # Test authenticated endpoints
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Test signals endpoint (no auth required)
            try:
                signals_response = requests.get(f"{base_url}/api/signals/current?limit=10", timeout=5)
                print(f"Signals endpoint (no auth): {signals_response.status_code}")
            except Exception as e:
                print(f"Signals endpoint error: {e}")
            
            # Test sessions endpoint (auth required)
            try:
                sessions_response = requests.get(f"{base_url}/api/sessions/data", headers=headers, timeout=5)
                print(f"Sessions endpoint (with auth): {sessions_response.status_code}")
                if sessions_response.status_code == 200:
                    print(f"Sessions data: {json.dumps(sessions_response.json(), indent=2)}")
                else:
                    print(f"Sessions error: {sessions_response.text}")
            except Exception as e:
                print(f"Sessions endpoint error: {e}")
            
            # Test sessions endpoint without auth
            try:
                sessions_no_auth = requests.get(f"{base_url}/api/sessions/data", timeout=5)
                print(f"Sessions endpoint (no auth): {sessions_no_auth.status_code}")
            except Exception as e:
                print(f"Sessions no auth error: {e}")
            
            return True
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Testing Authentication and Endpoints")
    print("=" * 40)
    
    success = test_auth_flow()
    if success:
        print("\n✅ Authentication flow working!")
    else:
        print("\n❌ Authentication flow has issues!")