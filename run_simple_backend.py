#!/usr/bin/env python3
"""
Simple SMC Trading System Backend Runner
Uses simplified backend without complex dependencies
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting SMC Trading System - Simple Backend")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = "backend"
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found")
        return False
    
    os.chdir(backend_dir)
    
    # Try to run the simplified backend
    try:
        print("📡 Starting simplified backend server...")
        print("🌐 Frontend Dashboard: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("\n⏹️ Press Ctrl+C to stop the server\n")
        
        # Run the simplified backend
        subprocess.run([sys.executable, "app/main_simple.py"])
        
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)