#!/usr/bin/env python3
"""
Complete System Startup
Handles environment activation and starts both backend and frontend
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def activate_globalvenv():
    """Activate globalvenv and return the activated Python path"""
    globalvenv_path = Path("globalvenv")
    
    if not globalvenv_path.exists():
        print("❌ globalvenv not found")
        print("💡 Run: python3 setup_global_env.py")
        return None
    
    # Get the Python executable from globalvenv
    if os.name == 'nt':  # Windows
        python_path = globalvenv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        python_path = globalvenv_path / "bin" / "python"
    
    if not python_path.exists():
        print(f"❌ Python not found in globalvenv: {python_path}")
        return None
    
    print(f"✅ Found globalvenv Python: {python_path}")
    return str(python_path)

def check_dependencies(python_path):
    """Check if dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Test backend dependencies
    try:
        result = subprocess.run([
            python_path, "-c", 
            "import uvicorn, fastapi, ccxt, pytz; print('Backend deps OK')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Backend dependencies found")
        else:
            print("❌ Backend dependencies missing")
            print("💡 Installing backend dependencies...")
            subprocess.run([python_path, "-m", "pip", "install", "-r", "backend/requirements.txt"])
            
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return False
    
    # Check frontend dependencies
    if not Path("frontend/node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install", "--legacy-peer-deps"], cwd="frontend")
    else:
        print("✅ Frontend dependencies found")
    
    return True

def start_backend(python_path):
    """Start backend server"""
    print("🚀 Starting backend server...")
    
    env = os.environ.copy()
    env.update({
        'APP_ENV': 'development',
        'HOST': '0.0.0.0',
        'PORT': '8000',
        'LOG_LEVEL': 'INFO'
    })
    
    backend_process = subprocess.Popen([
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], cwd="backend", env=env)
    
    return backend_process

def start_frontend():
    """Start frontend server"""
    print("🎨 Starting frontend server...")
    
    env = os.environ.copy()
    env.update({
        'REACT_APP_BACKEND_URL': 'http://localhost:8000',
        'PORT': '3000'
    })
    
    frontend_process = subprocess.Popen([
        "npm", "start"
    ], cwd="frontend", env=env)
    
    return frontend_process

def main():
    """Main startup function"""
    print("🔥 SMC Trading System - Complete Startup")
    print("=" * 45)
    
    # Step 1: Activate globalvenv
    python_path = activate_globalvenv()
    if not python_path:
        sys.exit(1)
    
    # Step 2: Check dependencies
    if not check_dependencies(python_path):
        print("❌ Dependency check failed")
        sys.exit(1)
    
    processes = []
    
    try:
        # Step 3: Start backend
        backend_process = start_backend(python_path)
        processes.append(backend_process)
        
        print("⏳ Waiting for backend to start...")
        time.sleep(5)
        
        # Step 4: Start frontend
        frontend_process = start_frontend()
        processes.append(frontend_process)
        
        print("\n🎉 System started successfully!")
        print("📊 Backend API: http://localhost:8000")
        print("🎨 Frontend UI: http://localhost:3000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("🔌 WebSocket: ws://localhost:8000/ws")
        print("\n💡 Press Ctrl+C to stop all services")
        print("🚀 Frontend should show LIVE MODE (no demo banner)")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if any process died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    service = "Backend" if i == 0 else "Frontend"
                    print(f"\n❌ {service} process died with code {process.returncode}")
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