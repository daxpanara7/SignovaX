#!/bin/bash

# SMC Trading System - Complete Startup
echo "🔥 SMC Trading System - Complete Startup"
echo "========================================"

# Check if globalvenv exists
if [ ! -d "globalvenv" ]; then
    echo "❌ globalvenv not found"
    echo "💡 Run: python3 setup_global_env.py"
    exit 1
fi

# Activate global environment
echo "🔧 Activating global environment..."
source globalvenv/bin/activate

# Verify activation
if [[ "$VIRTUAL_ENV" != *"globalvenv"* ]]; then
    echo "❌ Failed to activate globalvenv"
    exit 1
fi

echo "✅ Global environment activated: $(basename $VIRTUAL_ENV)"

# Check backend dependencies
echo "🔍 Checking backend dependencies..."
if ! python -c "import uvicorn, fastapi, ccxt, pytz" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install --legacy-peer-deps && cd ..
fi

# Start the system
echo "🚀 Starting complete system..."
python start_system_main.py