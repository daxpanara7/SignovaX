# 🚀 SMC Trading System - Quick Start Guide

## Overview
This guide will help you run the SMC Trading System locally to see the professional dashboard UI and analysis features without live trading.

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- Git installed

## 📋 Step-by-Step Setup

### 1. Backend Setup (Python/FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Or create .env manually with:
echo "APP_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./smc_trading.db
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000" > .env
```

### 2. Frontend Setup (React/Vite)

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install

# Install additional dependencies we added
npm install zustand react-hot-toast framer-motion
```

### 3. Start the System

#### Option A: Using the provided scripts

```bash
# From project root directory

# Start backend (Terminal 1)
./start_backend.sh

# Start frontend (Terminal 2) 
./start_frontend.sh
```

#### Option B: Manual startup

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Access the Dashboard

Open your browser and go to:
- **Frontend Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

## 🎯 What You'll See

### Professional Trading Terminal
- **Dark theme trading interface** with terminal aesthetics
- **Real-time price updates** (simulated)
- **TradingView charts** with SMC overlays
- **Signal generation** with confluence scoring
- **Performance analytics** with professional metrics
- **Risk management** controls and settings

### Key Features to Explore

1. **Main Dashboard** - Professional trading terminal layout
2. **Chart Panel** - TradingView charts with SMC pattern overlays
3. **Signal Panel** - Active signals with confluence scores
4. **Watchlist** - Real-time price updates for multiple symbols
5. **Performance Panel** - Backtest results and analytics
6. **Notification Center** - Alert management system
7. **Risk Settings** - Comprehensive risk management controls

## 🔧 Demo Features

The system runs in demo mode with:
- **Mock price data** - Realistic price movements
- **Simulated signals** - SMC signals generated automatically
- **Sample backtests** - Pre-loaded performance data
- **Demo notifications** - Alert system demonstrations

## 📊 API Endpoints to Test

With the backend running, you can test these endpoints:

```bash
# Get system health
curl http://localhost:8000/health

# Generate demo signal (requires auth token)
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "timeframe": "15m"}'

# Get market data
curl http://localhost:8000/api/data/ohlcv?symbol=BTCUSDT&timeframe=15m

# Run backtest
curl -X POST http://localhost:8000/api/advanced-backtest/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "timeframe": "15m", "days_back": 30}'
```

## 🎨 Dashboard Features

### Header Bar
- **Symbol selector** - Choose trading pairs
- **Timeframe controls** - Switch between 1m, 5m, 15m, 1h, 4h, 1d
- **Account info** - Balance, P&L, risk level
- **Theme toggle** - Dark/light mode
- **Settings** - Risk management configuration

### Main Content
- **Chart area** - 60% width with TradingView integration
- **Signal panel** - 20% width showing active signals
- **Session heatmap** - Performance by trading session

### Bottom Tabs
- **Signals** - Signal analysis and history
- **Backtest** - Backtesting configuration and results
- **Performance** - Detailed performance metrics
- **Alerts** - Notification management
- **ML Status** - Machine learning model status

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill processes on ports 3000 and 8000
   # On Windows:
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   
   # On macOS/Linux:
   lsof -ti:3000 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

2. **Python dependencies issues**
   ```bash
   # Upgrade pip and reinstall
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **Node.js dependencies issues**
   ```bash
   # Clear npm cache and reinstall
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Database issues**
   ```bash
   # Reset database
   cd backend
   rm -f *.db
   python run.py  # Will recreate databases
   ```

## 📱 Mobile Access

The dashboard is responsive and works on mobile devices:
- Access via your mobile browser at `http://YOUR_LOCAL_IP:3000`
- Find your local IP: `ipconfig` (Windows) or `ifconfig` (macOS/Linux)

## 🔒 Authentication

For demo purposes, use these credentials:
- **Username**: admin
- **Password**: smc_admin_2024

Or create a new account through the API:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

## 🎯 Next Steps

Once you have the system running:

1. **Explore the dashboard** - Navigate through all panels and features
2. **Test signal generation** - Watch for automatic signal creation
3. **Run backtests** - Test different symbols and timeframes
4. **Configure risk settings** - Adjust risk parameters
5. **Monitor performance** - View analytics and metrics

## 📞 Support

If you encounter issues:
1. Check the console logs in both terminals
2. Verify all dependencies are installed
3. Ensure ports 3000 and 8000 are available
4. Check the browser console for frontend errors

The system is designed to work out-of-the-box with demo data, so you can explore all features without connecting to live markets or brokers.

**Enjoy exploring your professional SMC Trading System! 🚀**