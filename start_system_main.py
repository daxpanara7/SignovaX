#!/usr/bin/env python3
"""
SMC Trading System - Main Branch Startup
Starts the perfect backend from main branch with new UI
"""

import subprocess
import sys
import os
import time
import signal
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

def check_requirements():
    """Check if required dependencies are installed"""
    print("🔍 Checking requirements...")
    
    # Check if we're in globalvenv
    if not check_global_env():
        return False
    
    # Check Python dependencies
    try:
        import uvicorn
        import fastapi
        import ccxt
        import pytz  # This was causing the error
        print("✅ Python backend dependencies found")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("💡 Run: pip install -r backend/requirements.txt")
        return False
    
    # Test backend imports
    try:
        sys.path.append('backend')
        from app.config import get_settings
        settings = get_settings()
        print(f"✅ Backend configuration loaded - Environment: {settings.APP_ENV}")
        print(f"✅ API Keys: Binance={'✅' if settings.BINANCE_API_KEY else '❌'}, Finnhub={'✅' if settings.FINNHUB_API_KEY else '❌'}")
    except Exception as e:
        print(f"❌ Backend import test failed: {e}")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js found: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        print("💡 Install Node.js from https://nodejs.org/")
        return False
    
    # Check if frontend dependencies are installed
    if not (Path("frontend/node_modules").exists()):
        print("❌ Frontend dependencies not installed")
        print("💡 Run: cd frontend && npm install --legacy-peer-deps")
        return False
    else:
        print("✅ Frontend dependencies found")
    
    return True

def start_backend():
    """Start the main branch backend server"""
    print("🚀 Starting main branch backend server...")
    
    backend_env = os.environ.copy()
    backend_env.update({
        'APP_ENV': 'development',
        'HOST': '0.0.0.0',
        'PORT': '8000',
        'LOG_LEVEL': 'INFO',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:5173'
    })
    
    backend_process = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ], cwd='backend', env=backend_env)
    
    return backend_process

def start_frontend():
    """Start the new frontend"""
    print("🎨 Starting new modern frontend...")
    
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
    print("🔥 SMC Trading System - Main Branch with New UI")
    print("=" * 55)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please install missing dependencies.")
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        processes.append(backend_process)
        
        # Wait a moment for backend to start
        print("⏳ Waiting for backend to initialize...")
        time.sleep(3)
        
        # Start frontend
        frontend_process = start_frontend()
        processes.append(frontend_process)
        
        print("\n🎉 System started successfully!")
        print("📊 Backend API: http://localhost:8000")
        print("🎨 Frontend UI: http://localhost:3000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("🔌 WebSocket: ws://localhost:8000/ws")
        print("\n✨ Features Available:")
        print("  • Real Market Data (Binance API)")
        print("  • Live WebSocket Updates")
        print("  • Modern UI with all 10 modules")
        print("  • MTF Confluence Analysis")
        print("  • Risk Management System")
        print("  • Precise SMC Analysis")
        print("  • Advanced Backtesting")
        print("  • ML Signal Filter")
        print("  • Session Management")
        print("  • Alert System")
        print("  • Data Management")
        print("  • Authentication & Security")
        print("\n💡 Press Ctrl+C to stop all services")
        print("🚀 Frontend should now show LIVE MODE (no demo banner)")
        print("📈 Real-time price updates every 15 seconds")
        print("\n🔧 Troubleshooting:")
        print("  • If you see 404 errors, wait for backend to fully start")
        print("  • If authentication fails, check backend logs")
        print("  • If prices don't update, check WebSocket connection")
        print("  • Backend logs will show API calls and errors")
        
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