#!/bin/bash

# SMC Trading System - Start with Global Environment
echo "🔥 SMC Trading System - Starting with Global Environment"
echo "========================================================"

# Check if globalvenv exists
if [ ! -d "globalvenv" ]; then
    echo "❌ globalvenv not found in current directory"
    echo "💡 Make sure you're in the project root directory"
    exit 1
fi

# Activate global environment
echo "🔧 Activating global environment..."
source globalvenv/bin/activate

# Check if uvicorn is available
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn not found in globalvenv"
    echo "💡 Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start the integrated system
echo "🚀 Starting integrated system..."
python start_integrated_system.py