#!/usr/bin/env python3
"""
Start Backend Only
Simple script to start just the backend for debugging
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_environment():
    """Check if environment is ready"""
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path or 'globalvenv' not in venv_path:
        print("❌ Global environment not activated!")
        print("💡 Please run: source globalvenv/bin/activate")
        return False
    
    print(f"✅ Global environment active: {Path(venv_path).name}")
    return True

def start_backend():
    """Start backend with detailed output"""
    print("🚀 Starting backend server...")
    print("📍 Working directory: backend/")
    print("🔧 Command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("=" * 60)
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env.update({
            'APP_ENV': 'development',
            'HOST': '0.0.0.0',
            'PORT': '8000',
            'LOG_LEVEL': 'INFO'
        })
        
        # Start backend process
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload',
            '--log-level', 'info'
        ], cwd='backend', env=env)
        
        print(f"🆔 Backend process ID: {process.pid}")
        print("⏳ Starting up... (this may take a few seconds)")
        print("🔍 Watch for startup messages below:")
        print("-" * 60)
        
        # Wait for the process
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping backend...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✅ Backend stopped gracefully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("🔪 Backend force killed")
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

def main():
    """Main function"""
    print("🔧 SMC Trading System - Backend Only")
    print("=" * 40)
    
    if not check_environment():
        sys.exit(1)
    
    print("\n💡 This will start ONLY the backend server")
    print("📊 Backend will be available at: http://localhost:8000")
    print("📚 API docs will be at: http://localhost:8000/docs")
    print("🔌 WebSocket will be at: ws://localhost:8000/ws")
    print("\n🚀 Starting in 3 seconds... (Ctrl+C to cancel)")
    
    try:
        time.sleep(3)
        start_backend()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")

if __name__ == "__main__":
    main()