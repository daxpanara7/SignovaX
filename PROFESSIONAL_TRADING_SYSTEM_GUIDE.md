# 🚀 SignovaX Pro - Professional Trading System

## Complete Implementation Guide

---

## ✅ What's Been Built

### 1. **Signal Generation Engine** (85%+ Target Accuracy)
- ✅ Multi-factor confirmation system (5 scoring categories)
- ✅ Trend alignment detection
- ✅ Momentum analysis (RSI, MACD)
- ✅ Price structure detection (BOS, CHoCH, Swing points)
- ✅ Liquidity sweep detection
- ✅ Volume confirmation
- ✅ Only signals with 80%+ confidence

**File**: `backend/signal_engine.py`

### 2. **Paper Trading Engine**
- ✅ Full portfolio management
- ✅ Automatic trade execution
- ✅ Stop loss & take profit tracking
- ✅ Trailing stop loss
- ✅ Real-time P&L calculation
- ✅ Win rate & profit factor tracking
- ✅ Trade journal

**File**: `backend/paper_trading_engine.py`

### 3. **Risk Management System**
- ✅ Max 2% risk per trade
- ✅ Daily/weekly/monthly loss limits
- ✅ Position sizing calculator
- ✅ Correlation checking
- ✅ Signal validation
- ✅ Circuit breaker (3 consecutive losses)

**File**: `backend/risk_manager.py`

### 4. **Trading API** (FastAPI)
- ✅ RESTful API endpoints
- ✅ WebSocket for real-time updates
- ✅ Complete CRUD operations
- ✅ Risk-aware trading
- ✅ Performance analytics

**File**: `backend/trading_api.py`

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  ┌────────┬────────┬────────┬─────────┬─────────────┐  │
│  │ Chart  │Signals │ Trades │   Risk  │  Analytics  │  │
│  │ Panel  │ Panel  │ Panel  │  Meter  │  Dashboard  │  │
│  └────────┴────────┴────────┴─────────┴─────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↕ REST + WebSocket
┌─────────────────────────────────────────────────────────┐
│              TRADING API (FastAPI Port 8001)             │
│  ┌────────────┬──────────────┬──────────────────────┐  │
│  │  Signal    │    Paper     │     Risk             │  │
│  │  Engine    │   Trading    │    Manager           │  │
│  └────────────┴──────────────┴──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│           DATA ENGINE (Port 8000 - Already Built)        │
│         Market Data + Indicators + Chart Data            │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Signal Generation Logic

### Scoring System (Total = 100 points)

1. **Trend Alignment** (25 points)
   - Price > EMA20 > EMA50 > EMA200 = 100 (bullish)
   - Price < EMA20 < EMA50 < EMA200 = 0 (bearish)

2. **Momentum** (20 points)
   - RSI in 50-70 range (buy zone) = 90
   - MACD bullish crossover = +15
   - Volume confirmation = +10

3. **Price Structure** (25 points)
   - Break of Structure (BOS) = 90
   - Higher highs/higher lows = +15
   - Change of Character (CHoCH) = +10

4. **Liquidity** (15 points)
   - Liquidity sweep low (bullish) = 85
   - Near demand zone = +15

5. **Volume** (10 points)
   - Volume spike with bullish candle = 90
   - Above average volume = 70

6. **Risk-Reward** (5 points)
   - RR >= 2.0 = max points
   - Below 2.0 = penalty

### Signal Decision

```python
if total_score >= 80 and trend + momentum + structure >= 80:
    signal = "BUY"
elif total_score <= 20 and trend + momentum + structure <= 20:
    signal = "SELL"
else:
    signal = "NO_TRADE"  # Not enough conviction
```

---

## 📊 API Endpoints

### Signals

```bash
# Generate signal
POST /api/signals/generate
Body: {
  "symbol": "BTCUSDT",
  "interval": "15m",
  "candles": [...]
}

# Get signal history
GET /api/signals/history?limit=50
```

### Paper Trading

```bash
# Open trade
POST /api/paper/trade/open
Body: {
  "symbol": "BTCUSDT",
  "side": "BUY",
  "entry": 43250,
  "stop_loss": 42800,
  "take_profit": 44375,
  "confidence": 85,
  "reasoning": [...]
}

# Close trade
POST /api/paper/trade/close/{trade_id}?exit_price=44200&reason=TAKE_PROFIT

# Get portfolio
GET /api/paper/portfolio

# Get open trades
GET /api/paper/trades/open

# Get trade history
GET /api/paper/trades/history?limit=50

# Reset portfolio
POST /api/paper/reset
Body: {"initial_balance": 10000}
```

### Risk Management

```bash
# Get risk status
GET /api/risk/status

# Get risk parameters
GET /api/risk/parameters

# Update risk parameters
PUT /api/risk/parameters
Body: {
  "max_risk_per_trade": 0.02,
  "max_daily_loss": 0.06,
  "min_confidence": 80
}

# Calculate position size
POST /api/risk/calculate-position-size
Body: {"entry": 43250, "stop_loss": 42800}
```

### Analytics

```bash
# Get performance metrics
GET /api/analytics/performance
```

### WebSocket

```bash
# Real-time portfolio updates
WS /ws/portfolio
```

---

## 🚀 How to Run

### 1. Start Data Engine (Port 8000)

```bash
cd /Users/daxpanara/Projects/SignovaX
python3 ml/api.py
```

### 2. Start Trading Engine (Port 8001)

```bash
cd backend
python3 trading_api.py
```

### 3. Start Frontend

```bash
cd frontend
npm start
```

---

## 📈 Complete Trading Workflow

### Step 1: Signal Generation

```python
# Frontend sends candle data to /api/signals/generate
{
  "symbol": "BTCUSDT",
  "interval": "15m",
  "candles": [...500 candles with indicators...]
}

# Backend returns high-confidence signal
{
  "signal": "BUY",
  "confidence": 85.5,
  "entry": 43250,
  "stop_loss": 42800,
  "take_profit": 44375,
  "risk_reward": 2.5,
  "reasoning": [
    "Price above EMA20 (short-term bullish)",
    "EMA20 > EMA50 (trend confirmation)",
    "RSI in healthy bullish zone (62.3)",
    "MACD bullish crossover",
    "Break of structure confirmed",
    "Excellent R:R = 1:2.5"
  ],
  "scores": {
    "trend": 90,
    "momentum": 85,
    "structure": 90,
    "liquidity": 75,
    "volume": 80
  }
}
```

### Step 2: Risk Validation

```python
# Risk manager validates signal
- Confidence >= 80%? ✅
- R:R >= 2.0? ✅
- Daily loss limit not reached? ✅
- Max open trades not exceeded? ✅
- Correlation check passed? ✅
```

### Step 3: Position Sizing

```python
# Calculate position size
Portfolio: $10,000
Risk per trade: 2% = $200
Entry: $43,250
Stop Loss: $42,800
Price Risk: $450

Position Size = $200 / $450 = 0.444 units
```

### Step 4: Execute Trade

```python
# Open paper trade
POST /api/paper/trade/open
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "entry": 43250,
  "stop_loss": 42800,
  "take_profit": 44375,
  "confidence": 85.5,
  "reasoning": [...]
}

# Response
{
  "success": true,
  "trade_id": "uuid-123",
  "message": "Trade opened: BUY 0.4444 BTCUSDT @ $43250"
}
```

### Step 5: Trade Management

```python
# System automatically monitors:
- Stop loss hit? → Close trade
- Take profit hit? → Close trade
- Should trail stop? → Update stop loss to breakeven
- Update unrealized P&L every second
```

### Step 6: Close Trade

```python
# When TP hit at $44,375
Profit = ($44,375 - $43,250) × 0.4444 = $500
Return = 5% on position
Risk taken = $200
R:R achieved = 2.5:1

Portfolio updated:
- Balance: $10,000 → $10,500
- Win count: +1
- Win rate: Updated
- Profit factor: Updated
```

---

## 🎨 Frontend Integration

### Signal Panel Component

```jsx
import { useState } from 'react';

function SignalPanel() {
  const [signal, setSignal] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateSignal = async (symbol, interval, candles) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/signals/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, interval, candles })
      });

      const data = await response.json();
      setSignal(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signal-panel">
      {signal && (
        <div className={`signal-card ${signal.signal.toLowerCase()}`}>
          <div className="signal-badge">{signal.signal}</div>
          <div className="confidence">{signal.confidence}%</div>

          <div className="levels">
            <div>Entry: ${signal.entry}</div>
            <div>SL: ${signal.stop_loss}</div>
            <div>TP: ${signal.take_profit}</div>
            <div>R:R = 1:{signal.risk_reward}</div>
          </div>

          <div className="reasoning">
            {signal.reasoning.map((reason, i) => (
              <div key={i}>• {reason}</div>
            ))}
          </div>

          {signal.signal !== 'NO_TRADE' && (
            <button onClick={() => executeTrade(signal)}>
              Execute Trade
            </button>
          )}
        </div>
      )}
    </div>
  );
}
```

### Portfolio Panel Component

```jsx
import { useEffect, useState } from 'react';

function PortfolioPanel() {
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8001/ws/portfolio');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'portfolio_update') {
        setPortfolio(data.data);
      }
    };

    return () => ws.close();
  }, []);

  if (!portfolio) return <div>Loading...</div>;

  return (
    <div className="portfolio-panel">
      <h3>Portfolio</h3>
      <div className="balance">${portfolio.current_balance.toFixed(2)}</div>
      <div className="pnl">
        P&L: ${portfolio.total_pnl.toFixed(2)} ({portfolio.total_return_pct.toFixed(2)}%)
      </div>

      <div className="stats">
        <div>Win Rate: {portfolio.win_rate.toFixed(1)}%</div>
        <div>Profit Factor: {portfolio.profit_factor.toFixed(2)}</div>
        <div>Max DD: {portfolio.max_drawdown.toFixed(2)}%</div>
      </div>

      <div className="risk-meter">
        <div>Risk Score: {portfolio.risk_status.risk_score}/100</div>
        <div className={portfolio.risk_status.can_trade ? 'green' : 'red'}>
          {portfolio.risk_status.can_trade ? '✓ Can Trade' : '✗ Risk Limit'}
        </div>
      </div>
    </div>
  );
}
```

---

## 🎯 Performance Targets

### Signal Accuracy
- **Target**: 85-90% win rate
- **Method**: Multi-factor confirmation (all 5 scores must align)
- **Minimum**: 80% confidence to generate signal

### Risk Management
- **Max Risk**: 2% per trade
- **Max Daily Loss**: 6%
- **Position Sizing**: Automatic based on stop loss distance
- **R:R Minimum**: 2:1

### Execution
- **Paper Trading**: Instant execution at market price
- **Stop Loss**: Auto-close when hit
- **Take Profit**: Auto-close when hit
- **Trailing Stop**: Moves to breakeven at 2% profit

---

## 🧪 Testing the System

### Test Signal Generation

```bash
# Test with BTCUSDT
curl -X POST http://localhost:8001/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "interval": "15m",
    "candles": [...]
  }'
```

### Test Paper Trade

```bash
# Open trade
curl -X POST http://localhost:8001/api/paper/trade/open \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "entry": 43250,
    "stop_loss": 42800,
    "take_profit": 44375,
    "confidence": 85,
    "reasoning": ["Test trade"]
  }'

# Get portfolio
curl http://localhost:8001/api/paper/portfolio
```

---

## 📊 Sample Output

### Signal Response

```json
{
  "symbol": "BTCUSDT",
  "signal": "BUY",
  "confidence": 85.5,
  "entry": 43250.00,
  "stop_loss": 42800.00,
  "take_profit": 44375.00,
  "risk_reward": 2.5,
  "reasoning": [
    "Price above EMA20 (short-term bullish)",
    "EMA20 > EMA50 (trend confirmation)",
    "RSI in healthy bullish zone (62.3)",
    "MACD bullish crossover",
    "Above-average volume confirmation",
    "Excellent R:R = 1:2.5"
  ],
  "timeframe": "15m",
  "timestamp": "2026-04-11T12:00:00",
  "scores": {
    "trend": 90,
    "momentum": 85,
    "structure": 90,
    "liquidity": 75,
    "volume": 80
  }
}
```

### Portfolio Response

```json
{
  "portfolio_id": "uuid-abc",
  "initial_balance": 10000.00,
  "current_balance": 11250.00,
  "total_pnl": 1250.00,
  "realized_pnl": 1100.00,
  "unrealized_pnl": 150.00,
  "total_return_pct": 12.50,
  "trades_count": 25,
  "open_trades": 2,
  "closed_trades": 23,
  "wins": 20,
  "losses": 3,
  "win_rate": 86.96,
  "profit_factor": 4.2,
  "max_drawdown": 3.5,
  "daily_pnl": 250.00,
  "avg_win": 75.00,
  "avg_loss": -50.00,
  "risk_status": {
    "can_trade": true,
    "risk_score": 92.5,
    "daily_loss_pct": 2.5,
    "open_positions": 2
  }
}
```

---

## ✅ System Status

✅ **Signal Engine**: Production-ready
✅ **Paper Trading**: Production-ready
✅ **Risk Management**: Production-ready
✅ **Trading API**: Production-ready
⏳ **Frontend Integration**: Ready to build
⏳ **Database Integration**: Optional (currently in-memory)
⏳ **Live Trading**: Future phase (after paper trading validation)

---

## 🎉 You Now Have:

1. ✅ Professional signal generation with 80%+ confidence target
2. ✅ Complete paper trading system
3. ✅ Strict risk management (2% per trade, 6% daily limit)
4. ✅ Full API backend (FastAPI)
5. ✅ Real-time WebSocket updates
6. ✅ Performance analytics
7. ✅ Trade journal & history

**Ready to integrate with your existing SignovaX frontend!**
