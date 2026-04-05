#!/usr/bin/env python3
"""
Test Backend Startup
Debug why backend isn't starting
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def test_backend_import():
    """Test if backend can be imported"""
    print("🔍 Testing backend imports...")
    
    try:
        # Add backend to path
        sys.path.insert(0, 'backend')
        
        # Test basic imports
        from app.config import get_settings
        from app.main import app
        
        settings = get_settings()
        print(f"✅ Backend imports successful")
        print(f"   Environment: {settings.APP_ENV}")
        print(f"   Host: {settings.HOST}")
        print(f"   Port: {settings.PORT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_uvicorn_command():
    """Test uvicorn command directly"""
    print("🚀 Testing uvicorn command...")
    
    try:
        # Test the exact command from start_system_main.py
        cmd = [
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ]
        
        print(f"Command: {' '.join(cmd)}")
        print(f"Working directory: backend")
        
        # Start process and capture output
        process = subprocess.Popen(
            cmd,
            cwd='backend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds and check output
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Backend process started successfully")
            print("🔌 Testing connection...")
            
            # Test connection
            import requests
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Backend responding to health check")
                    data = response.json()
                    print(f"   Status: {data['status']}")
                else:
                    print(f"❌ Backend health check failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Connection test failed: {e}")
            
            # Stop the process
            process.terminate()
            process.wait()
            return True
            
        else:
            # Process died
            stdout, stderr = process.communicate()
            print(f"❌ Backend process died with code: {process.returncode}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Uvicorn test failed: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("🌍 Checking environment...")
    
    # Check virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path and 'globalvenv' in venv_path:
        print(f"✅ Global environment active: {Path(venv_path).name}")
    else:
        print("❌ Global environment not active")
        return False
    
    # Check backend directory
    if not Path('backend').exists():
        print("❌ Backend directory not found")
        return False
    
    if not Path('backend/app').exists():
        print("❌ Backend app directory not found")
        return False
    
    if not Path('backend/app/main.py').exists():
        print("❌ Backend main.py not found")
        return False
    
    print("✅ Backend directory structure OK")
    
    # Check .env file
    if Path('backend/.env').exists():
        print("✅ Backend .env file exists")
    else:
        print("⚠️ Backend .env file missing")
    
    return True

def main():
    """Main test function"""
    print("🧪 Backend Startup Diagnostic")
    print("=" * 35)
    
    # Test 1: Environment
    if not check_environment():
        print("\n❌ Environment check failed")
        return False
    
    # Test 2: Imports
    if not test_backend_import():
        print("\n❌ Import test failed")
        return False
    
    # Test 3: Uvicorn
    if not test_uvicorn_command():
        print("\n❌ Uvicorn test failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("💡 Backend should start normally with start_system_main.py")
    return True

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)