# Smart Money Concepts (SMC) Algorithmic Trading System 🎯

A production-ready algorithmic trading platform that detects Smart Money Concepts and generates professional-grade trading signals.

![SMC Trading System](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-18+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)

## 🚀 Features

### Smart Money Concepts Detection
- **Liquidity Zones**: Equal highs/lows identification
- **Order Blocks**: Last opposite candle before strong moves
- **Fair Value Gaps (FVG)**: Price imbalance detection
- **Break of Structure (BOS)**: Trend continuation signals
- **Change of Character (CHOCH)**: Trend reversal detection

### Trading Capabilities
- **Multi-timeframe Analysis**: 1m, 5m, 15m, 1h, 4h, 1d support
- **Real-time Signal Generation**: Live market analysis
- **Risk Management**: 1:2 risk/reward ratios, position sizing
- **Backtesting Engine**: Historical performance validation
- **Performance Analytics**: Win rate, profit factor, drawdown analysis

### Modern Interface
- **Interactive Charts**: TradingView Lightweight Charts with SMC overlays
- **Real-time Dashboard**: Live market data and system status
- **Signal Management**: Active signals with confidence scoring
- **Performance Tracking**: Comprehensive backtesting results

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, Pandas, NumPy, CCXT
- **Frontend**: React (Vite), TailwindCSS, Recharts
- **Charts**: TradingView Lightweight Charts
- **Database**: SQLite → PostgreSQL ready
- **API**: RESTful with automatic OpenAPI documentation

## ⚡ Quick Start

### Option 1: One-Click Setup (Recommended)
```bash
# Start backend
./start_backend.sh

# Start frontend (in new terminal)
./start_frontend.sh
```

### Option 2: Manual Setup
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📊 Demo Data

Generate realistic demo data with embedded SMC patterns:
```bash
python3 demo_data.py
```

## 🎯 Core SMC Strategies Implemented

### 1. Liquidity Zone Detection
```python
# Identifies areas where price repeatedly tests the same level
- Equal highs/lows detection
- Stop-loss cluster identification  
- Support/resistance strength scoring
```

### 2. Order Block Analysis
```python
# Finds institutional order areas
- Last bearish candle before bullish move (bullish OB)
- Last bullish candle before bearish move (bearish OB)
- Mitigation level calculation
```

### 3. Fair Value Gap (FVG) Detection
```python
# Identifies price imbalances
- Bullish FVG: Gap between previous high and next low
- Bearish FVG: Gap between previous low and next high
- Gap filling tracking
```

### 4. Structure Analysis
```python
# BOS (Break of Structure): Trend continuation
- Higher highs in uptrend
- Lower lows in downtrend

# CHOCH (Change of Character): Trend reversal
- Break of previous structure after opposite moves
```

## 📈 API Endpoints

### Market Data
- `GET /api/data/ohlcv` - Historical OHLCV data
- `GET /api/data/symbols` - Available trading pairs
- `GET /api/data/timeframes` - Supported timeframes

### Analysis
- `POST /api/analysis/smc` - Run complete SMC analysis
- `GET /api/analysis/patterns/{symbol}` - Pattern summary

### Signals
- `POST /api/signals/generate` - Generate trading signals
- `GET /api/signals/active/{symbol}` - Active signals
- `GET /api/signals/summary` - Multi-symbol overview

### Backtesting
- `POST /api/backtest/run` - Full historical backtest
- `GET /api/backtest/quick/{symbol}` - Quick performance test
- `GET /api/backtest/performance/{symbol}` - Detailed metrics

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Market Data    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Binance)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │ SMC Strategy    │              │
         └──────────────►│ Engine          │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Signal Generator│
                        │ & Backtester    │
                        └─────────────────┘
```

## 🎮 Usage Examples

### Generate Signals
```python
# Via API
POST /api/signals/generate
{
  "symbol": "BTCUSDT",
  "timeframe": "1h", 
  "min_confidence": 75.0
}

# Response
[
  {
    "signal_type": "BUY",
    "entry_price": 50000,
    "stop_loss": 49000,
    "take_profit": 52000,
    "confidence": 85.0,
    "reasoning": "Bullish Order Block at 50000"
  }
]
```

### Run Backtest
```python
POST /api/backtest/run
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "initial_capital": 10000
}

# Returns comprehensive performance metrics
```

## 📋 Configuration

### Environment Variables (.env)
```bash
DATABASE_URL=sqlite:///./trading.db
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here  
DEBUG=True
```

### Market Data Sources
- **Primary**: Binance API (real-time data)
- **Fallback**: Realistic mock data generator
- **Demo**: Pre-generated data with SMC patterns

## 🔧 Customization

### Adding New SMC Patterns
1. Extend `SMCStrategy` class
2. Implement pattern detection logic
3. Update signal generation rules
4. Add chart visualization

### Risk Management
- Modify position sizing algorithms
- Adjust risk/reward ratios
- Customize stop-loss strategies
- Implement portfolio-level risk controls

## 📊 Performance Metrics

The system tracks comprehensive performance metrics:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Average Trade Duration**: Time in market per trade

## 🚨 Important Notes

### Educational Purpose
This system is designed for educational and research purposes. Always:
- Paper trade before live implementation
- Understand the risks involved
- Never risk more than you can afford to lose
- Backtest thoroughly on historical data

### Production Considerations
- Add proper authentication and authorization
- Implement rate limiting and error handling
- Use PostgreSQL for production database
- Add comprehensive logging and monitoring
- Consider regulatory compliance requirements

## 📚 Documentation

- **Setup Guide**: [SETUP.md](SETUP.md) - Detailed installation instructions
- **API Documentation**: Available at `/docs` when backend is running
- **Architecture**: Modular design with clear separation of concerns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please ensure compliance with local regulations before any live trading implementation.

---

**⚠️ Risk Disclaimer**: Trading involves substantial risk of loss. This software is for educational purposes only and should not be used for live trading without proper testing and risk management.