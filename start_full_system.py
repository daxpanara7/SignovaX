#!/usr/bin/env python3
"""
Start the complete SMC Trading System (Backend + Frontend)
"""

import subprocess
import sys
import time
import os
import signal
import requests
from pathlib import Path

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_frontend_health():
    """Check if frontend is running"""
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_backend():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return None
    
    # Start backend
    backend_process = subprocess.Popen([
        sys.executable, "main_simple.py"
    ], cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for backend to start
    for i in range(30):  # Wait up to 30 seconds
        if check_backend_health():
            print("✅ Backend is running at http://localhost:8000")
            return backend_process
        time.sleep(1)
        print(f"   Waiting for backend... ({i+1}/30)")
    
    print("❌ Backend failed to start")
    backend_process.terminate()
    return None

def start_frontend():
    """Start the frontend development server"""
    print("🎨 Starting frontend server...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return None
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        install_process = subprocess.run([
            "npm", "install"
        ], cwd=frontend_dir)
        
        if install_process.returncode != 0:
            print("❌ Failed to install frontend dependencies")
            return None
    
    # Start frontend
    frontend_process = subprocess.Popen([
        "npm", "run", "dev"
    ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for frontend to start
    for i in range(60):  # Wait up to 60 seconds
        if check_frontend_health():
            print("✅ Frontend is running at http://localhost:3000")
            return frontend_process
        time.sleep(1)
        print(f"   Waiting for frontend... ({i+1}/60)")
    
    print("❌ Frontend failed to start")
    frontend_process.terminate()
    return None

def main():
    """Main function to start both services"""
    print("🎯 Starting SMC Trading System")
    print("=" * 50)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        if not backend_process:
            return 1
        
        print()
        
        # Start frontend
        frontend_process = start_frontend()
        if not frontend_process:
            return 1
        
        print()
        print("🎉 System is running!")
        print("📊 Backend API: http://localhost:8000")
        print("🎨 Frontend UI: http://localhost:3000")
        print("📚 API Docs: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop both services")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process died")
                break
                
            if frontend_process.poll() is not None:
                print("❌ Frontend process died")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    
    finally:
        # Clean up processes
        if backend_process:
            print("   Stopping backend...")
            backend_process.terminate()
            backend_process.wait()
        
        if frontend_process:
            print("   Stopping frontend...")
            frontend_process.terminate()
            frontend_process.wait()
        
        print("✅ System stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())