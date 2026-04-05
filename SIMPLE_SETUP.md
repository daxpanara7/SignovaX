# 🚀 SMC Trading System - Simple Setup Guide

## The Issue
You're running Python 3.14 which is very new and some packages (like pydantic-core) haven't been updated for compatibility yet.

## 🎯 Quick Solution (Recommended)

### Step 1: Create Global Virtual Environment
```bash
# Create global virtual environment for the entire project
python3 -m venv globalvenv

# Activate it
# On macOS/Linux:
source globalvenv/bin/activate
# On Windows:
globalvenv\Scripts\activate
```

### Step 2: Install Compatible Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install essential packages one by one (safer approach)
pip install fastapi>=0.100.0
pip install "uvicorn[standard]>=0.20.0"
pip install pandas>=1.5.0
pip install numpy>=1.21.0
pip install requests>=2.28.0
pip install python-multipart>=0.0.5
pip install sqlalchemy>=1.4.0
pip install aiosqlite>=0.17.0
pip install python-dotenv>=0.19.0
pip install "python-jose[cryptography]>=3.3.0"
pip install bcrypt>=4.0.0

# Optional packages (install if needed)
pip install slowapi>=0.1.7
pip install scipy>=1.9.0
pip install "scikit-learn>=1.1.0"
pip install pytz>=2022.1
pip install aiohttp>=3.8.0
```

### Step 3: Setup Backend Environment
```bash
# Create backend .env file
cd backend
cat > .env << EOL
APP_ENV=development
SECRET_KEY=smc-trading-system-demo-key-2024
DATABASE_URL=sqlite:///./smc_trading.db
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
WORKERS=1
EOL
cd ..
```

### Step 4: Setup Frontend
```bash
cd frontend
npm install
cd ..
```

### Step 5: Run the System

**Terminal 1 - Backend:**
```bash
# Make sure global venv is activated
source globalvenv/bin/activate  # On Windows: globalvenv\Scripts\activate
cd backend
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🌐 Access the System

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Alternative: Use Automated Setup

Run the automated setup script:
```bash
python3 setup_global_env.py
```

This will:
- ✅ Create global virtual environment
- ✅ Install compatible dependencies
- ✅ Setup configuration files
- ✅ Create simple run scripts

## 🎯 What You'll See

Once both servers are running, open http://localhost:3000 to see:

### Professional Trading Terminal
- **Dark theme interface** with terminal aesthetics
- **Real-time price simulation** for BTCUSDT, ETHUSDT, etc.
- **TradingView charts** with SMC pattern overlays
- **Signal generation** every 30-120 seconds
- **Performance analytics** with comprehensive metrics
- **Risk management** controls and settings

### Key Features
1. **Chart Panel** - Professional TradingView integration
2. **Signal Panel** - Active signals with confluence scores
3. **Watchlist** - Multi-symbol price monitoring
4. **Performance Panel** - Backtest results and analytics
5. **Notification Center** - Alert management system
6. **Risk Settings** - Comprehensive risk controls

## 🔧 Troubleshooting

### If Backend Fails to Start
```bash
# Check if all required packages are installed
pip list | grep fastapi
pip list | grep uvicorn
pip list | grep pandas

# If missing, install individually:
pip install fastapi uvicorn pandas numpy
```

### If Frontend Fails to Start
```bash
# Clear npm cache and reinstall
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### If Ports Are Busy
```bash
# Kill processes on ports 3000 and 8000
# macOS/Linux:
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

## 🎉 Demo Features

The system runs with realistic demo data:
- ❌ **No live trading** - Safe to explore
- ❌ **No real money** - Demo account only
- ❌ **No broker connection** - Simulated data
- ✅ **Full functionality** - All features work

### What Happens Automatically
- **Price updates** every 5 seconds
- **Signal generation** every 30-120 seconds
- **Performance calculations** in real-time
- **Risk monitoring** continuous

## 📱 Mobile Access

The dashboard works on mobile devices:
- Find your local IP: `ifconfig` (macOS/Linux) or `ipconfig` (Windows)
- Access via mobile: `http://YOUR_LOCAL_IP:3000`

## 🎯 Success Indicators

You'll know it's working when you see:

1. **Backend Terminal**:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Frontend Terminal**:
   ```
   Local:   http://localhost:3000/
   Network: http://192.168.1.xxx:3000/
   ```

3. **Browser**: Professional dark-themed trading terminal loads

## 🚀 Next Steps

Once running:
1. **Explore the dashboard** - Navigate through all panels
2. **Watch for signals** - Automatic generation every 30-120 seconds
3. **Test different symbols** - Switch between BTCUSDT, ETHUSDT, etc.
4. **Configure risk settings** - Click the settings gear icon
5. **View performance analytics** - Check the Performance tab

**Enjoy your professional SMC Trading System! 📈**