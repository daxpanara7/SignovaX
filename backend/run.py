#!/usr/bin/env python3
"""
SMC Trading System - Backend Server
Run this script to start the FastAPI backend server
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print("🚀 Starting SMC Trading System Backend...")
    print(f"📡 Server will be available at: http://{host}:{port}")
    print(f"📊 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Debug mode: {debug}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )