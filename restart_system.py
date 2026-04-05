#!/usr/bin/env python3
"""
Restart SMC Trading System
Stops any running processes and starts fresh
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def kill_existing_processes():
    """Kill any existing backend/frontend processes"""
    print("🛑 Stopping existing processes...")
    
    try:
        # Kill processes on port 8000 (backend)
        subprocess.run(['pkill', '-f', 'uvicorn.*8000'], capture_output=True)
        subprocess.run(['lsof', '-ti:8000'], capture_output=True, text=True)
        
        # Kill processes on port 3000 (frontend)  
        subprocess.run(['pkill', '-f', 'react-scripts'], capture_output=True)
        subprocess.run(['lsof', '-ti:3000'], capture_output=True, text=True)
        
        print("✅ Existing processes stopped")
        time.sleep(2)
        
    except Exception as e:
        print(f"⚠️ Error stopping processes: {e}")

def check_global_env():
    """Check if global environment is activated"""
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path or 'globalvenv' not in venv_path:
        print("❌ Global environment not activated!")
        print("💡 Please run: source globalvenv/bin/activate")
        return False
    
    print(f"✅ Global environment active: {Path(venv_path).name}")
    return True

def main():
    """Main restart function"""
    print("🔄 SMC Trading System - Restart")
    print("=" * 40)
    
    # Check environment
    if not check_global_env():
        sys.exit(1)
    
    # Kill existing processes
    kill_existing_processes()
    
    # Start fresh
    print("🚀 Starting fresh system...")
    
    try:
        # Run the main startup script
        subprocess.run([sys.executable, 'start_system_main.py'])
    except KeyboardInterrupt:
        print("\n🛑 Restart interrupted")
    except Exception as e:
        print(f"❌ Restart failed: {e}")

if __name__ == "__main__":
    main()