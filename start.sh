#!/bin/bash
# SignovaX Trading Terminal - Startup Script

echo "🚀 Starting SignovaX Trading Terminal..."
echo ""

# Kill any existing instances
echo "1️⃣  Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Check if we're in the right directory
if [ ! -f "ml/api.py" ]; then
    echo "❌ Error: Please run this script from the SignovaX root directory"
    echo "   cd /Users/daxpanara/Projects/SignovaX"
    exit 1
fi

# Start ML API
echo "2️⃣  Starting ML API (Backend)..."
python3 ml/api.py > logs/ml_api.log 2>&1 &
ML_PID=$!
echo "   ML API started (PID: $ML_PID)"
echo "   Logs: logs/ml_api.log"

# Wait for ML API to be ready
echo "3️⃣  Waiting for ML API to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ ML API is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ ML API failed to start. Check logs/ml_api.log"
        exit 1
    fi
    sleep 1
done

# Test the API
echo ""
echo "4️⃣  Testing ML API..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "   $HEALTH"

echo ""
echo "✅ Backend is running!"
echo ""
echo "📊 To start the frontend, run:"
echo "   cd frontend && npm start"
echo ""
echo "🛑 To stop the backend:"
echo "   kill $ML_PID"
echo "   or: lsof -ti:8000 | xargs kill"
echo ""
echo "📝 ML API logs: tail -f logs/ml_api.log"
echo ""
