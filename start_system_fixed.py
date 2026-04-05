#!/usr/bin/env python3
"""
SMC Trading System - Fixed Startup Script
Ensures backend starts properly before frontend
"""

import subprocess
import sys
import os
import time
import signal
import requests
from pathlib import Path

def check_global_env():
    """Check if global environment is activated"""
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path or 'globalvenv' not in venv_path:
        print("❌ Global environment not activated!")
        print("💡 Please run: source globalvenv/bin/activate")
        return False
    
    print(f"✅ Global environment active: {Path(venv_path).name}")
    return True

def wait_for_backend():
    """Wait for backend to be ready"""
    print("⏳ Waiting for backend to be ready...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get('http://localhost:8000/health', timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Attempt {i+1}/30...")
        time.sleep(1)
    
    print("❌ Backend failed to start within 30 seconds")
    return False

def start_backend():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    
    backend_env = os.environ.copy()
    backend_env.update({
        'APP_ENV': 'development',
        'HOST': '0.0.0.0',
        'PORT': '8000',
        'LOG_LEVEL': 'INFO',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:5173'
    })
    
    # Start backend with output visible
    backend_process = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ], cwd='backend', env=backend_env)
    
    return backend_process

def start_frontend():
    """Start the frontend"""
    print("🎨 Starting frontend...")
    
    frontend_env = os.environ.copy()
    frontend_env.update({
        'REACT_APP_BACKEND_URL': 'http://localhost:8000',
        'PORT': '3000'
    })
    
    frontend_process = subprocess.Popen([
        'npm', 'start'
    ], cwd='frontend', env=frontend_env)
    
    return frontend_process

def main():
    """Main startup function"""
    print("🔥 SMC Trading System - Fixed Startup")
    print("=" * 40)
    
    # Check environment
    if not check_global_env():
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend first
        backend_process = start_backend()
        processes.append(backend_process)
        
        # Wait for backend to be ready
        if not wait_for_backend():
            print("❌ Backend startup failed")
            sys.exit(1)
        
        # Test critical endpoints
        print("🔍 Testing critical endpoints...")
        
        try:
            # Test signals endpoint (this was giving 404)
            signals_response = requests.get('http://localhost:8000/api/signals/current?limit=10', timeout=5)
            print(f"   Signals endpoint: {signals_response.status_code}")
            
            # Test sessions endpoint (this was giving 404)  
            sessions_response = requests.get('http://localhost:8000/api/sessions/data', timeout=5)
            print(f"   Sessions endpoint: {sessions_response.status_code}")
            
        except Exception as e:
            print(f"   Endpoint test error: {e}")
        
        # Now start frontend
        frontend_process = start_frontend()
        processes.append(frontend_process)
        
        print("\n🎉 System started successfully!")
        print("📊 Backend API: http://localhost:8000")
        print("🎨 Frontend UI: http://localhost:3000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("🔌 WebSocket: ws://localhost:8000/ws")
        print("\n💡 Press Ctrl+C to stop all services")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if any process died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"\n❌ Process {i} died with code {process.returncode}")
                    raise KeyboardInterrupt
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()