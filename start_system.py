#!/usr/bin/env python3
"""
Quick start script for SMC Trading System
This script helps you get the system running quickly
"""

import subprocess
import sys
import os
import time
import platform

def run_command(command, cwd=None, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    
    if version.major == 3 and version.minor >= 14:
        print("⚠️ Python 3.14 detected - some packages may have compatibility issues")
    
    return True

def check_node():
    """Check if Node.js is installed"""
    success, stdout, stderr = run_command("node --version")
    if success:
        print(f"📦 Node.js version: {stdout.strip()}")
        return True
    else:
        print("❌ Node.js not found. Please install Node.js from https://nodejs.org/")
        return False

def setup_backend():
    """Set up the backend environment"""
    print("\n🔧 Setting up backend...")
    
    # Check if globalvenv exists
    if not os.path.exists("globalvenv"):
        print("📦 Creating global virtual environment...")
        success, stdout, stderr = run_command("python3 -m venv globalvenv")
        if not success:
            print(f"❌ Failed to create virtual environment: {stderr}")
            return False
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    # Activate and install packages
    print("📦 Installing Python packages...")
    
    # Determine activation command based on OS
    if platform.system() == "Windows":
        activate_cmd = "globalvenv\\Scripts\\activate"
        pip_cmd = f"{activate_cmd} && pip install fastapi uvicorn pandas numpy requests python-multipart sqlalchemy aiosqlite python-dotenv bcrypt aiohttp"
    else:
        activate_cmd = "source globalvenv/bin/activate"
        pip_cmd = f"{activate_cmd} && pip install fastapi uvicorn pandas numpy requests python-multipart sqlalchemy aiosqlite python-dotenv bcrypt aiohttp"
    
    success, stdout, stderr = run_command(pip_cmd)
    if not success:
        print(f"⚠️ Some packages may have failed to install: {stderr}")
        print("🔄 Trying with essential packages only...")
        
        essential_cmd = f"{activate_cmd} && pip install fastapi uvicorn pandas numpy requests aiohttp"
        success, stdout, stderr = run_command(essential_cmd)
        
        if not success:
            print(f"❌ Failed to install essential packages: {stderr}")
            return False
    
    print("✅ Backend packages installed")
    return True

def setup_frontend():
    """Set up the frontend"""
    print("\n🎨 Setting up frontend...")
    
    if not os.path.exists("frontend"):
        print("❌ Frontend directory not found")
        return False
    
    # Install npm packages
    print("📦 Installing npm packages...")
    success, stdout, stderr = run_command("npm install", cwd="frontend")
    
    if not success:
        print(f"⚠️ npm install had issues: {stderr}")
        print("🔄 Trying npm cache clean...")
        run_command("npm cache clean --force", cwd="frontend")
        success, stdout, stderr = run_command("npm install", cwd="frontend")
        
        if not success:
            print(f"❌ Failed to install npm packages: {stderr}")
            return False
    
    print("✅ Frontend packages installed")
    return True

def main():
    """Main setup function"""
    print("🚀 SMC Trading System - Quick Start Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python():
        return False
    
    if not check_node():
        return False
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        return False
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Open Terminal 1 and run:")
    print("   source globalvenv/bin/activate")
    print("   cd backend")
    print("   python run.py")
    print("\n2. Open Terminal 2 and run:")
    print("   cd frontend")
    print("   npm run dev")
    print("\n3. Open your browser to: http://localhost:3000")
    print("\n💡 You can also test the backend with:")
    print("   python test_simple_backend.py")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")