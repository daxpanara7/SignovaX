# SMC Trading System - Setup Guide

## Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- npm or yarn

### 1. Backend Setup

```bash
# Option 1: Use the startup script (recommended)
./start_backend.sh

# Option 2: Manual setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The backend will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### 2. Frontend Setup

```bash
# Option 1: Use the startup script (recommended)
./start_frontend.sh

# Option 2: Manual setup
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:3000

## System Architecture

### Backend Components
- **FastAPI Server**: RESTful API with automatic documentation
- **Market Data Service**: Fetches OHLCV data (with Binance integration + mock data)
- **SMC Strategy Engine**: Detects Smart Money Concepts patterns
- **Signal Generator**: Creates trading signals based on SMC analysis
- **Backtest Engine**: Historical performance testing

### Frontend Components
- **React Dashboard**: Modern UI with TailwindCSS
- **TradingView Charts**: Interactive candlestick charts with SMC overlays
- **Real-time Updates**: Live market data and signal updates
- **Performance Analytics**: Comprehensive backtesting results

## Smart Money Concepts Implemented

### 1. Liquidity Zones
- Detects equal highs and lows
- Identifies stop-loss clusters
- Marks support/resistance zones

### 2. Order Blocks
- Finds last opposite candle before strong moves
- Marks bullish/bearish order blocks
- Calculates mitigation levels

### 3. Fair Value Gaps (FVG)
- Detects price imbalances
- Identifies unfilled gaps
- Tracks gap filling status

### 4. Break of Structure (BOS)
- Detects higher highs/lower lows
- Confirms trend continuation
- Generates trend-following signals

### 5. Change of Character (CHOCH)
- Identifies trend reversals
- Detects structure breaks
- Early reversal signals

## API Endpoints

### Market Data
- `GET /api/data/ohlcv` - Fetch OHLCV data
- `GET /api/data/symbols` - Available symbols
- `GET /api/data/timeframes` - Supported timeframes

### Analysis
- `POST /api/analysis/smc` - Run SMC analysis
- `GET /api/analysis/patterns/{symbol}` - Pattern summary

### Signals
- `POST /api/signals/generate` - Generate trading signals
- `GET /api/signals/active/{symbol}` - Active signals
- `GET /api/signals/summary` - Multi-symbol summary

### Backtesting
- `POST /api/backtest/run` - Run full backtest
- `GET /api/backtest/quick/{symbol}` - Quick backtest
- `GET /api/backtest/performance/{symbol}` - Performance metrics

## Configuration

### Environment Variables (.env)
```
DATABASE_URL=sqlite:///./trading.db
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
DEBUG=True
```

### Market Data Sources
- **Primary**: Binance API (requires API keys)
- **Fallback**: Mock data generator (for demo purposes)

## Features

### Dashboard
- Real-time system overview
- Active signals summary
- Performance metrics
- Market status indicators

### Analysis Page
- Interactive charts with SMC overlays
- Pattern detection results
- Structure analysis (BOS/CHOCH)
- Multi-timeframe support

### Signals Page
- Live trading signals
- Risk/reward ratios
- Confidence scoring
- Auto-refresh capability

### Backtest Page
- Historical performance testing
- Equity curve visualization
- Trade distribution analysis
- Detailed trade logs

## Trading Logic

### Signal Generation
1. **Pattern Detection**: Identify SMC patterns in market data
2. **Entry Conditions**: Price approaching key levels (order blocks, FVG)
3. **Risk Management**: 1:2 risk/reward ratio, 2% max risk per trade
4. **Confidence Scoring**: Rule-based confidence (60-90%)

### Backtesting
1. **Historical Simulation**: Process each candle sequentially
2. **Realistic Execution**: Use actual high/low for stop/target hits
3. **Performance Metrics**: Win rate, profit factor, max drawdown
4. **Trade Logging**: Complete trade history with reasons

## Customization

### Adding New Patterns
1. Extend `SMCStrategy` class in `backend/app/services/smc_strategy.py`
2. Add detection logic for new pattern
3. Update signal generation in `SignalGenerator`
4. Add visualization in frontend charts

### Modifying Risk Management
- Edit `SignalGenerator` class
- Adjust risk/reward ratios
- Modify position sizing logic
- Update stop-loss/take-profit calculations

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check Python version (3.8+)
   - Verify all dependencies installed
   - Check port 8000 availability

2. **Frontend won't start**
   - Check Node.js version (16+)
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

3. **No market data**
   - System uses mock data by default
   - Add Binance API keys for real data
   - Check internet connection

4. **Charts not loading**
   - Ensure backend is running
   - Check browser console for errors
   - Verify API endpoints responding

### Performance Optimization
- Use shorter timeframes for faster backtests
- Limit historical data range
- Enable data caching (future enhancement)
- Use WebSocket for real-time updates

## Next Steps

### Enhancements
1. **Database Integration**: PostgreSQL for production
2. **Real Trading**: Paper trading integration
3. **Machine Learning**: Signal validation with ML
4. **Alerts**: Telegram/email notifications
5. **Multi-Asset**: Support for stocks, commodities
6. **Advanced Patterns**: Wyckoff, Elliott Wave integration

### Production Deployment
1. **Docker**: Containerize both frontend and backend
2. **Cloud**: Deploy to AWS/GCP/Azure
3. **Security**: Add authentication and rate limiting
4. **Monitoring**: Add logging and error tracking
5. **Scaling**: Load balancing and caching

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Examine browser console for frontend errors
4. Check backend logs for API issues

The system is designed to be educational and should not be used for live trading without proper testing and risk management.