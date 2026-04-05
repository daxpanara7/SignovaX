# 🎯 EASIEST WAY TO RUN SMC Trading System

## The Problem
Your Python 3.14 is too new and some packages don't support it yet.

## ✅ SOLUTION (Just 4 Commands!)

### 1. Create Global Environment
```bash
python3 -m venv globalvenv
source globalvenv/bin/activate
```

### 2. Install Essential Packages Only
```bash
pip install fastapi uvicorn pandas numpy requests python-multipart sqlalchemy aiosqlite python-dotenv bcrypt aiohttp
```

### 3. Start Backend (Terminal 1)
```bash
source globalvenv/bin/activate
cd backend
python run.py
```

### 4. Start Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Open Your Browser
Go to: **http://localhost:3000**

## 🎉 That's It!

You'll see your professional SMC Trading Terminal with:
- ✅ Real-time price simulation
- ✅ Professional dark theme
- ✅ TradingView charts
- ✅ Signal generation
- ✅ Performance analytics
- ✅ Risk management

## 🔧 If Something Fails

**Backend Issues:**
```bash
# Try minimal install
pip install fastapi uvicorn
cd backend
python run.py
```

**Frontend Issues:**
```bash
cd frontend
npm cache clean --force
npm install
npm run dev
```

**Port Issues:**
```bash
# Kill processes on busy ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

## 📱 What You'll See

Professional trading terminal with:
- **Chart Panel**: TradingView charts with SMC overlays
- **Signal Panel**: Active signals with confluence scores  
- **Watchlist**: Real-time price updates
- **Performance Panel**: Trading metrics and analytics
- **Risk Settings**: Professional risk management

**Everything runs with demo data - no live trading, completely safe to explore!**

---

**🚀 Your professional SMC Trading System is ready!**