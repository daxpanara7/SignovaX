#!/usr/bin/env python3
"""
SMC Trading System - Global Environment Setup
Creates a single virtual environment for the entire project
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception running command: {command}")
        print(f"Error: {e}")
        return False

def main():
    print("🚀 SMC Trading System - Global Environment Setup")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Remove existing backend venv if it exists
    backend_venv = Path("backend/venv")
    if backend_venv.exists():
        print("🗑️  Removing existing backend virtual environment...")
        shutil.rmtree(backend_venv)
    
    # Create global virtual environment
    globalvenv_path = Path("globalvenv")
    if globalvenv_path.exists():
        print("🗑️  Removing existing global virtual environment...")
        shutil.rmtree(globalvenv_path)
    
    print("📦 Creating global virtual environment...")
    if not run_command(f"{sys.executable} -m venv globalvenv"):
        return False
    
    # Determine python and pip paths
    if os.name == 'nt':  # Windows
        python_exe = globalvenv_path / "Scripts" / "python.exe"
        pip_exe = globalvenv_path / "Scripts" / "pip.exe"
        activate_script = globalvenv_path / "Scripts" / "activate.bat"
    else:  # Unix/Linux/macOS
        python_exe = globalvenv_path / "bin" / "python"
        pip_exe = globalvenv_path / "bin" / "pip"
        activate_script = globalvenv_path / "bin" / "activate"
    
    # Upgrade pip
    print("⬆️  Upgrading pip...")
    if not run_command(f"{pip_exe} install --upgrade pip"):
        return False
    
    # Create a simplified requirements file for compatibility
    print("📝 Creating compatible requirements file...")
    compatible_requirements = """fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
websockets>=10.0
python-multipart>=0.0.5
pydantic>=2.0.0,<2.5.0
sqlalchemy>=1.4.0
aiosqlite>=0.17.0
python-dotenv>=0.19.0
ccxt>=3.0.0
python-jose[cryptography]>=3.3.0
bcrypt>=4.0.0
slowapi>=0.1.7
scipy>=1.9.0
scikit-learn>=1.1.0
pydantic-settings>=2.0.0,<2.3.0
pytz>=2022.1
aiohttp>=3.8.0
python-telegram-bot>=20.0
"""
    
    with open("compatible_requirements.txt", "w") as f:
        f.write(compatible_requirements)
    
    # Install compatible requirements
    print("📚 Installing compatible Python dependencies...")
    if not run_command(f"{pip_exe} install -r compatible_requirements.txt"):
        print("⚠️  Some packages failed to install. Trying individual installation...")
        
        # Try installing packages individually
        essential_packages = [
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.20.0", 
            "pandas>=1.5.0",
            "numpy>=1.21.0",
            "requests>=2.28.0",
            "python-multipart>=0.0.5",
            "sqlalchemy>=1.4.0",
            "aiosqlite>=0.17.0",
            "python-dotenv>=0.19.0",
            "python-jose[cryptography]>=3.3.0",
            "bcrypt>=4.0.0"
        ]
        
        for package in essential_packages:
            print(f"Installing {package}...")
            run_command(f"{pip_exe} install {package}")
    
    # Create backend .env file
    backend_env = Path("backend/.env")
    if not backend_env.exists():
        print("⚙️  Creating backend environment configuration...")
        env_content = """APP_ENV=development
SECRET_KEY=smc-trading-system-demo-key-2024
DATABASE_URL=sqlite:///./smc_trading.db
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
WORKERS=1
"""
        with open(backend_env, 'w') as f:
            f.write(env_content)
    
    # Setup frontend
    print("\n🎨 Setting up frontend...")
    frontend_path = Path("frontend")
    if frontend_path.exists():
        print("📦 Installing Node.js dependencies...")
        if not run_command("npm install", cwd="frontend"):
            print("⚠️  npm install failed, but continuing...")
    
    print("\n✅ Global environment setup complete!")
    print("=" * 50)
    print(f"🐍 Python executable: {python_exe}")
    print(f"📦 Pip executable: {pip_exe}")
    print(f"🔧 Activate script: {activate_script}")
    
    # Create simple run scripts
    print("\n📝 Creating simplified run scripts...")
    
    # Simple backend runner
    simple_backend_script = f"""#!/bin/bash
echo "🚀 Starting SMC Trading System Backend..."
cd backend
{python_exe} run.py
"""
    
    with open("run_backend_simple.sh", "w") as f:
        f.write(simple_backend_script)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod("run_backend_simple.sh", 0o755)
    
    # Simple frontend runner
    simple_frontend_script = """#!/bin/bash
echo "🎨 Starting SMC Trading System Frontend..."
cd frontend
npm run dev
"""
    
    with open("run_frontend_simple.sh", "w") as f:
        f.write(simple_frontend_script)
    
    if os.name != 'nt':
        os.chmod("run_frontend_simple.sh", 0o755)
    
    # Windows batch files
    if os.name == 'nt':
        backend_bat = f"""@echo off
echo 🚀 Starting SMC Trading System Backend...
cd backend
{python_exe} run.py
pause
"""
        with open("run_backend_simple.bat", "w") as f:
            f.write(backend_bat)
        
        frontend_bat = """@echo off
echo 🎨 Starting SMC Trading System Frontend...
cd frontend
npm run dev
pause
"""
        with open("run_frontend_simple.bat", "w") as f:
            f.write(frontend_bat)
    
    print("\n🎯 How to run the system:")
    print("=" * 30)
    
    if os.name == 'nt':  # Windows
        print("Backend:  run_backend_simple.bat")
        print("Frontend: run_frontend_simple.bat")
    else:  # Unix/Linux/macOS
        print("Backend:  ./run_backend_simple.sh")
        print("Frontend: ./run_frontend_simple.sh")
    
    print("\n🌐 Access URLs:")
    print("Frontend Dashboard: http://localhost:3000")
    print("Backend API: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    
    print("\n🎉 Setup complete! You can now run the system.")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup successful!")
        sys.exit(0)