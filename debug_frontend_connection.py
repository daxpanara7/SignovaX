#!/usr/bin/env python3
"""
Debug frontend connection issues by simulating exact frontend calls
"""

import requests
import json
import time

def debug_frontend_calls():
    """Debug the exact calls frontend makes"""
    print("🔍 Debugging Frontend Connection Issues")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    frontend_origin = "http://localhost:3000"
    
    # Step 1: Health check (first thing frontend does)
    print("1. Testing health check (frontend's first call)...")
    try:
        response = requests.get(f"{base_url}/health", 
                              headers={'Origin': frontend_origin},
                              timeout=5)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health: {data}")
        else:
            print(f"   ❌ Health failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health error: {e}")
        return False
    
    # Step 2: Auto-login attempt
    print("\n2. Testing auto-login...")
    try:
        login_data = {
            "username": "admin",
            "password": "smc_admin_2024"
        }
        
        response = requests.post(f"{base_url}/api/auth/login",
                               json=login_data,
                               headers={
                                   'Origin': frontend_origin,
                                   'Content-Type': 'application/json'
                               },
                               timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print(f"   ✅ Login successful, token: {access_token[:20]}...")
        else:
            print(f"   ❌ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Step 3: Test data fetch (what frontend does after login)
    print("\n3. Testing data fetch with token...")
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Origin': frontend_origin,
            'Content-Type': 'application/json'
        }
        
        # Test the fetchData function equivalent
        response = requests.get(f"{base_url}/api/data/ohlcv",
                              params={
                                  'symbol': 'BTCUSDT',
                                  'timeframe': '1h',
                                  'start': '2024-12-01T00:00:00Z',
                                  'end': '2024-12-31T23:59:59Z',
                                  'limit': 500
                              },
                              headers=headers,
                              timeout=15)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Data retrieved: {len(data)} candles")
            
            if data and len(data) > 0:
                latest = data[-1]
                print(f"   📊 Latest BTC: ${latest.get('close')}")
                print(f"   📅 Timestamp: {latest.get('timestamp')}")
            
        else:
            print(f"   ❌ Data failed: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Data error: {e}")
    
    # Step 4: Test risk status (another frontend call)
    print("\n4. Testing risk status...")
    try:
        response = requests.get(f"{base_url}/api/risk/status",
                              headers=headers,
                              timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            risk_data = response.json()
            print(f"   ✅ Risk data: {risk_data}")
        else:
            print(f"   ⚠️  Risk failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Risk error: {e}")
    
    # Step 5: Check CORS headers specifically
    print("\n5. Checking CORS configuration...")
    try:
        # OPTIONS request (preflight)
        response = requests.options(f"{base_url}/api/data/ohlcv",
                                  headers={
                                      'Origin': frontend_origin,
                                      'Access-Control-Request-Method': 'GET',
                                      'Access-Control-Request-Headers': 'Authorization,Content-Type'
                                  })
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print(f"   CORS Headers: {cors_headers}")
        
        if cors_headers['Access-Control-Allow-Origin']:
            print("   ✅ CORS properly configured")
        else:
            print("   ❌ CORS missing - this could be the issue!")
            
    except Exception as e:
        print(f"   ⚠️  CORS check error: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 Debugging Summary:")
    print("   • If health check fails: Backend not running")
    print("   • If login fails: Authentication issue")
    print("   • If data fails: Token or endpoint issue")
    print("   • If CORS missing: Frontend can't connect")
    print("\n💡 Next steps:")
    print("   1. Restart backend if health fails")
    print("   2. Check .env file if login fails")
    print("   3. Restart frontend to pick up changes")
    
    return True

if __name__ == "__main__":
    debug_frontend_calls()