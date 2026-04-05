# 🚀 How to Run the SMC Trading System

## Quick Start (Easiest Method)

### Option 1: One-Command Demo Launcher

**For macOS/Linux:**
```bash
python3 start_demo.py
```

**For Windows:**
```bash
start_demo.bat
```

This will automatically:
- ✅ Check system requirements
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Create configuration files
- ✅ Start both backend and frontend
- ✅ Open the professional dashboard

## Option 2: Manual Setup (Step by Step)

### 1. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend
python run.py
```

### 2. Frontend Setup (New Terminal)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

## 🌐 Access the System

Once both servers are running:

- **🎯 Main Dashboard**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📖 API Documentation**: http://localhost:8000/docs

## 🎨 What You'll See

### Professional Trading Terminal
![Trading Terminal](https://via.placeholder.com/800x400/0a0a0a/00d4aa?text=SMC+Trading+Terminal)

The dashboard includes:

1. **Header Bar**
   - Symbol selector (BTCUSDT, ETHUSDT, etc.)
   - Timeframe controls (1m, 5m, 15m, 1h, 4h, 1d)
   - Account balance and P&L
   - Dark/light theme toggle
   - Settings and notifications

2. **Main Chart Area**
   - TradingView Lightweight Charts
   - SMC pattern overlays (Order Blocks, FVGs, Liquidity Zones)
   - Real-time price simulation
   - Interactive chart controls

3. **Signal Panel**
   - Active signal display
   - Confluence score (circular progress)
   - Entry, Stop Loss, Take Profit levels
   - Risk:Reward ratio visualization
   - ML approval probability
   - Session indicators

4. **Watchlist Sidebar**
   - Multiple symbol monitoring
   - Real-time price updates
   - 24h change indicators
   - Mini sparkline charts
   - Add/remove symbols

5. **Performance Panel**
   - **Metrics Tab**: Win rate, Profit factor, Sharpe ratio, etc.
   - **Equity Curve**: Portfolio performance over time
   - **Monte Carlo**: Risk simulation analysis
   - **Trade Log**: Detailed trade history

6. **Bottom Tabs**
   - Signals analysis
   - Backtest configuration
   - Performance analytics
   - Alert management
   - ML model status

## 🎯 Demo Features

The system runs with realistic demo data:

### Real-time Simulation
- **Price Updates**: Every 5 seconds
- **Signal Generation**: Every 30-120 seconds
- **Market Data**: Realistic OHLCV data
- **Performance Metrics**: Sample backtest results

### SMC Analysis
- **Order Block Detection**: Bullish/bearish order blocks
- **Fair Value Gaps**: Price imbalance areas
- **Liquidity Zones**: Support/resistance levels
- **BOS/CHOCH**: Market structure changes

### Signal Generation
- **Confluence Scoring**: 0-100 point system
- **ML Filtering**: Machine learning approval
- **Session Awareness**: Trading session optimization
- **Risk Validation**: Automatic risk checks

## 🔑 Demo Credentials

If authentication is required:
- **Username**: `admin`
- **Password**: `smc_admin_2024`

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill processes on ports 3000 and 8000
   # Windows:
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   
   # macOS/Linux:
   lsof -ti:3000 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

2. **Python Dependencies**
   ```bash
   # Upgrade pip and reinstall
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **Node.js Dependencies**
   ```bash
   # Clear cache and reinstall
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Database Issues**
   ```bash
   # Reset databases
   cd backend
   rm -f *.db
   python run.py  # Will recreate
   ```

### System Requirements

- **Python**: 3.8 or higher
- **Node.js**: 16 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Browser**: Chrome, Firefox, Safari, Edge (latest versions)

## 📱 Mobile Access

The dashboard is responsive and works on mobile:
- Find your local IP: `ipconfig` (Windows) or `ifconfig` (macOS/Linux)
- Access via mobile browser: `http://YOUR_LOCAL_IP:3000`

## 🎯 Key Features to Explore

### 1. Chart Analysis
- Switch between different symbols (BTCUSDT, ETHUSDT, etc.)
- Change timeframes to see different perspectives
- Toggle SMC overlays (OB, FVG, LZ, BOS buttons)
- Watch for automatic signal generation

### 2. Signal Management
- Monitor the Signal Panel for new signals
- Check confluence scores and ML approval
- Copy price levels to clipboard
- View risk:reward ratios

### 3. Performance Analytics
- Explore the Performance Panel tabs
- View equity curves and drawdown analysis
- Check Monte Carlo simulations
- Review trade log details

### 4. Risk Management
- Click the settings gear to open risk configuration
- Adjust risk per trade and max daily loss
- Toggle safety features (circuit breaker, ML filter)
- Monitor risk levels in the header

### 5. Real-time Features
- Watch the watchlist for price updates
- Monitor notifications in the bell icon
- See live session performance in the heatmap
- Observe automatic signal generation

## 🚀 Next Steps

Once you're familiar with the demo:

1. **Explore API Endpoints**: Visit http://localhost:8000/docs
2. **Test Different Symbols**: Try ETHUSDT, ADAUSDT, SOLUSDT
3. **Run Backtests**: Test different timeframes and parameters
4. **Configure Alerts**: Set up notification preferences
5. **Analyze Performance**: Review metrics and optimize settings

## 📞 Need Help?

If you encounter issues:
1. Check both terminal windows for error messages
2. Ensure all dependencies are installed correctly
3. Verify ports 3000 and 8000 are available
4. Check browser console for frontend errors
5. Try the troubleshooting steps above

**The system is designed to work out-of-the-box with demo data - no live market connections required!**

---

**🎉 Enjoy exploring your professional SMC Trading System!**