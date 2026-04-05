#!/usr/bin/env python3
"""
Test Backend Startup
Quick test to see if backend can start properly
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def test_backend_startup():
    """Test if backend starts properly"""
    print("🔍 Testing backend startup...")
    
    # Check if we're in the right environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path or 'globalvenv' not in venv_path:
        print("❌ Global environment not activated!")
        print("💡 Please run: source globalvenv/bin/activate")
        return False
    
    print(f"✅ Global environment active: {Path(venv_path).name}")
    
    # Try to start backend
    print("🚀 Starting backend...")
    
    backend_env = os.environ.copy()
    backend_env.update({
        'APP_ENV': 'development',
        'HOST': '0.0.0.0',
        'PORT': '8000',
        'LOG_LEVEL': 'INFO',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:5173'
    })
    
    try:
        backend_process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ], cwd='backend', env=backend_env, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for startup
        print("⏳ Waiting for backend to start...")
        time.sleep(5)
        
        # Test if backend is responding
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Backend is responding!")
                print(f"Health check: {response.json()}")
                
                # Test the problematic endpoints
                print("\n🔍 Testing problematic endpoints...")
                
                # Test signals endpoint
                try:
                    signals_response = requests.get('http://localhost:8000/api/signals/current?limit=10', timeout=5)
                    print(f"Signals endpoint: {signals_response.status_code}")
                    if signals_response.status_code != 200:
                        print(f"Signals error: {signals_response.text}")
                except Exception as e:
                    print(f"Signals endpoint error: {e}")
                
                # Test sessions endpoint
                try:
                    sessions_response = requests.get('http://localhost:8000/api/sessions/data', timeout=5)
                    print(f"Sessions endpoint: {sessions_response.status_code}")
                    if sessions_response.status_code != 200:
                        print(f"Sessions error: {sessions_response.text}")
                except Exception as e:
                    print(f"Sessions endpoint error: {e}")
                
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Backend not responding: {e}")
            
            # Check process output
            stdout, stderr = backend_process.communicate(timeout=1)
            if stdout:
                print(f"Backend stdout: {stdout}")
            if stderr:
                print(f"Backend stderr: {stderr}")
            
            return False
        
        # Terminate backend
        backend_process.terminate()
        backend_process.wait(timeout=5)
        print("✅ Backend test completed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

if __name__ == "__main__":
    test_backend_startup()