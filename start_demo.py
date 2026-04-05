#!/usr/bin/env python3
"""
SMC Trading System - Demo Startup Script
Starts both backend and frontend with demo data
"""

import subprocess
import sys
import os
import time
import threading
import signal
from pathlib import Path

class SMCDemoLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def check_requirements(self):
        """Check if required software is installed"""
        print("🔍 Checking system requirements...")
        
        # Check Python
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ Python: {result.stdout.strip()}")
        except:
            print("❌ Python not found")
            return False
            
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ Node.js: {result.stdout.strip()}")
        except:
            print("❌ Node.js not found. Please install Node.js 16+")
            return False
            
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ npm: {result.stdout.strip()}")
        except:
            print("❌ npm not found")
            return False
            
        return True
    
    def setup_backend(self):
        """Setup backend environment"""
        print("\n🔧 Setting up backend...")
        
        backend_dir = Path("backend")
        if not backend_dir.exists():
            print("❌ Backend directory not found")
            return False
            
        # Create virtual environment if it doesn't exist
        venv_dir = backend_dir / "venv"
        if not venv_dir.exists():
            print("📦 Creating Python virtual environment...")
            subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)])
        
        # Get python executable path
        if os.name == 'nt':  # Windows
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"
        
        # Install requirements
        requirements_file = backend_dir / "requirements.txt"
        if requirements_file.exists():
            print("📚 Installing Python dependencies...")
            subprocess.run([str(pip_exe), 'install', '-r', str(requirements_file)])
        
        # Create .env file if it doesn't exist
        env_file = backend_dir / ".env"
        if not env_file.exists():
            print("⚙️ Creating environment configuration...")
            env_content = """APP_ENV=development
SECRET_KEY=smc-trading-system-demo-key-2024
DATABASE_URL=sqlite:///./smc_trading.db
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
WORKERS=1
"""
            with open(env_file, 'w') as f:
                f.write(env_content)
        
        return True
    
    def setup_frontend(self):
        """Setup frontend environment"""
        print("\n🎨 Setting up frontend...")
        
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        # Install npm dependencies
        print("📦 Installing Node.js dependencies...")
        os.chdir(frontend_dir)
        subprocess.run(['npm', 'install'])
        os.chdir('..')
        
        return True
    
    def start_backend(self):
        """Start the backend server"""
        print("\n🚀 Starting backend server...")
        
        backend_dir = Path("backend")
        venv_dir = backend_dir / "venv"
        
        if os.name == 'nt':  # Windows
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            python_exe = venv_dir / "bin" / "python"
        
        os.chdir(backend_dir)
        self.backend_process = subprocess.Popen([
            str(python_exe), 'run.py'
        ])
        os.chdir('..')
        
        print("✅ Backend started on http://localhost:8000")
        print("📖 API Documentation: http://localhost:8000/docs")
    
    def start_frontend(self):
        """Start the frontend server"""
        print("\n🎨 Starting frontend server...")
        
        frontend_dir = Path("frontend")
        os.chdir(frontend_dir)
        
        self.frontend_process = subprocess.Popen([
            'npm', 'run', 'dev'
        ])
        os.chdir('..')
        
        print("✅ Frontend started on http://localhost:3000")
    
    def wait_for_servers(self):
        """Wait for servers to start"""
        print("\n⏳ Waiting for servers to start...")
        time.sleep(3)
        
        # Check if backend is responding
        try:
            import requests
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Backend is responding")
            else:
                print("⚠️ Backend may not be fully ready")
        except:
            print("⚠️ Backend health check failed (this is normal during startup)")
        
        print("\n🎉 SMC Trading System is starting up!")
        print("=" * 50)
        print("🌐 Frontend Dashboard: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("=" * 50)
        print("\n💡 Demo Features:")
        print("   • Professional trading terminal interface")
        print("   • Real-time price simulation")
        print("   • SMC signal generation")
        print("   • Performance analytics")
        print("   • Risk management tools")
        print("   • Multi-timeframe analysis")
        print("\n🔑 Demo Login (if needed):")
        print("   Username: admin")
        print("   Password: smc_admin_2024")
        print("\n⏹️ Press Ctrl+C to stop all servers")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n⏹️ Shutting down SMC Trading System...")
        self.running = False
        
        if self.backend_process:
            print("🔧 Stopping backend server...")
            self.backend_process.terminate()
            
        if self.frontend_process:
            print("🎨 Stopping frontend server...")
            self.frontend_process.terminate()
            
        print("✅ All servers stopped. Goodbye!")
        sys.exit(0)
    
    def run(self):
        """Main run method"""
        print("🚀 SMC Trading System - Demo Launcher")
        print("=" * 40)
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Check requirements
        if not self.check_requirements():
            print("\n❌ Requirements check failed. Please install missing software.")
            return
        
        # Setup environments
        if not self.setup_backend():
            print("\n❌ Backend setup failed")
            return
            
        if not self.setup_frontend():
            print("\n❌ Frontend setup failed")
            return
        
        # Start servers
        self.start_backend()
        time.sleep(2)  # Give backend time to start
        self.start_frontend()
        
        # Wait and show info
        self.wait_for_servers()
        
        # Keep running until interrupted
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def main():
    """Main function"""
    launcher = SMCDemoLauncher()
    launcher.run()

if __name__ == "__main__":
    main()