# SignovaX Pro - Professional Trading System Architecture

## 🎯 System Overview

A Bloomberg Terminal-style trading platform focused on **high-probability signals** (85-90% accuracy target) with full paper trading capabilities, risk management, and algorithmic execution.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Chart    │Watchlist │ Signals  │ Trades   │ Risk     │Analytics │
│ Panel    │  Panel   │  Panel   │  Panel   │  Meter   │Dashboard │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                              ↕ WebSocket + REST API
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Market   │ Signal   │ Trading  │ Risk     │ Paper    │Analytics │
│ Data     │ Engine   │ Engine   │ Manager  │ Trading  │ Engine   │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (PostgreSQL)                       │
├──────────┬──────────┬──────────┬──────────┬──────────────────────┤
│ OHLCV    │ Signals  │ Trades   │ Portfolio│ Performance         │
│ Data     │ History  │ Journal  │ State    │ Metrics             │
└──────────┴──────────┴──────────┴──────────┴──────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│              EXTERNAL DATA SOURCES                               │
├──────────┬──────────┬──────────┬──────────────────────────────────┤
│ Binance  │ Yahoo    │ Alpha    │ Custom                          │
│ WebSocket│ Finance  │ Vantage  │ Providers                       │
└──────────┴──────────┴──────────┴──────────────────────────────────┘
```

---

## 🧩 Module Breakdown

### 1. MARKET DATA ENGINE

**Purpose**: Real-time and historical data aggregation with intelligent caching.

**Features**:
- Multi-source data aggregation (Binance, Yahoo Finance, Alpha Vantage)
- WebSocket streaming for real-time prices
- Historical data with configurable intervals
- Indicator calculation engine
- Smart caching layer (Redis)

**Indicators Computed**:
```python
- EMA (20, 50, 200)
- RSI (14)
- MACD (12, 26, 9)
- ATR (14)
- Volume MA
- Bollinger Bands
- Swing High/Low detection
- Support/Resistance levels
- Order Blocks (SMC)
- Fair Value Gaps (FVG)
- Liquidity zones
```

**API Endpoints**:
```
GET  /api/market/candles/{symbol}?interval={interval}&limit={limit}
GET  /api/market/indicators/{symbol}?interval={interval}
GET  /api/market/live/{symbol}
WS   /ws/market/{symbol}
```

---

### 2. SIGNAL GENERATION ENGINE

**Purpose**: Generate high-probability trading signals using multi-factor confirmation.

**Signal Scoring System** (0-100):

```python
SIGNAL_CRITERIA = {
    "trend_alignment": {
        "weight": 25,
        "conditions": [
            "price > EMA20 > EMA50 > EMA200",  # Bullish
            "EMA slope alignment",
            "No conflicting timeframes"
        ]
    },
    "momentum": {
        "weight": 20,
        "conditions": [
            "RSI in healthy zone (50-70 for buy)",
            "MACD bullish crossover",
            "Increasing volume"
        ]
    },
    "price_structure": {
        "weight": 25,
        "conditions": [
            "Break of Structure (BOS)",
            "Change of Character (CHoCH)",
            "Clear swing points"
        ]
    },
    "liquidity": {
        "weight": 15,
        "conditions": [
            "Liquidity sweep completed",
            "Fair Value Gap filled",
            "Order block respected"
        ]
    },
    "risk_reward": {
        "weight": 15,
        "conditions": [
            "RR ratio >= 1:2",
            "Clear stop loss level",
            "Defined target zone"
        ]
    }
}
```

**Signal Logic**:
```python
def generate_signal(candles, indicators, timeframe):
    score = 0
    reasons = []

    # 1. TREND CONFIRMATION (25 points)
    if (indicators['price'] > indicators['ema20'] >
        indicators['ema50'] > indicators['ema200']):
        score += 25
        reasons.append("Strong bullish trend alignment")

    # 2. MOMENTUM (20 points)
    if 50 <= indicators['rsi'] <= 70:
        score += 10
        reasons.append("RSI in healthy bullish zone")

    if indicators['macd'] > indicators['macd_signal']:
        score += 10
        reasons.append("MACD bullish crossover")

    # 3. PRICE STRUCTURE (25 points)
    if detect_bos(candles):
        score += 15
        reasons.append("Break of Structure confirmed")

    if detect_swing_high_low(candles):
        score += 10
        reasons.append("Clear swing structure")

    # 4. LIQUIDITY (15 points)
    if liquidity_sweep_detected(candles):
        score += 10
        reasons.append("Liquidity sweep completed")

    if near_order_block(candles, indicators):
        score += 5
        reasons.append("Price at demand zone")

    # 5. RISK-REWARD (15 points)
    entry, sl, tp = calculate_levels(candles, indicators)
    rr = (tp - entry) / (entry - sl)

    if rr >= 2:
        score += 15
        reasons.append(f"Risk:Reward = 1:{rr:.1f}")

    # DECISION
    if score >= 80:
        return {
            "signal": "BUY",
            "confidence": score,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "risk_reward": rr,
            "reasoning": reasons,
            "timestamp": datetime.now()
        }
    elif score <= 20:
        return {"signal": "SELL", "confidence": 100-score, ...}
    else:
        return {"signal": "NO_TRADE", "confidence": 0, ...}
```

**API Endpoints**:
```
POST /api/signals/generate
GET  /api/signals/active
GET  /api/signals/history
PUT  /api/signals/{id}/review
```

---

### 3. ALGO TRADING ENGINE

**Purpose**: Automated trade execution based on signals and algorithmic rules.

**Trade Execution Flow**:
```
Signal Generated (Confidence >= 80%)
         ↓
Risk Manager Validation
         ↓
Position Size Calculation
         ↓
Order Creation
         ↓
Trade Monitoring (Real-time)
         ↓
Trade Management (Stop/Target)
```

**Key Functions**:

```python
class TradingEngine:
    def __init__(self, risk_manager, portfolio):
        self.risk_manager = risk_manager
        self.portfolio = portfolio
        self.active_trades = {}

    def execute_signal(self, signal):
        """Execute trade based on signal"""
        # 1. Validate signal
        if signal['confidence'] < 80:
            return {"status": "rejected", "reason": "Low confidence"}

        # 2. Check risk limits
        if not self.risk_manager.can_trade():
            return {"status": "rejected", "reason": "Risk limit reached"}

        # 3. Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            signal['entry'],
            signal['stop_loss']
        )

        # 4. Create order
        order = {
            "symbol": signal['symbol'],
            "side": signal['signal'],
            "entry": signal['entry'],
            "quantity": position_size,
            "stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit'],
            "confidence": signal['confidence'],
            "timestamp": datetime.now()
        }

        # 5. Execute (Paper Trading)
        trade_id = self.portfolio.open_trade(order)

        # 6. Monitor
        self.active_trades[trade_id] = order

        return {"status": "executed", "trade_id": trade_id}

    def manage_trades(self):
        """Real-time trade management"""
        for trade_id, trade in self.active_trades.items():
            current_price = get_live_price(trade['symbol'])

            # Check Stop Loss
            if self.hit_stop_loss(trade, current_price):
                self.close_trade(trade_id, current_price, "STOP_LOSS")

            # Check Take Profit
            elif self.hit_take_profit(trade, current_price):
                self.close_trade(trade_id, current_price, "TAKE_PROFIT")

            # Trailing Stop
            elif self.should_trail_stop(trade, current_price):
                self.update_stop_loss(trade_id, current_price)

            # Break Even
            elif self.should_move_to_breakeven(trade, current_price):
                self.move_stop_to_breakeven(trade_id)
```

**API Endpoints**:
```
POST /api/trades/execute
GET  /api/trades/active
GET  /api/trades/history
PUT  /api/trades/{id}/close
PUT  /api/trades/{id}/modify
```

---

### 4. RISK MANAGEMENT SYSTEM

**Purpose**: Protect capital and enforce trading discipline.

**Risk Rules**:

```python
RISK_PARAMETERS = {
    "max_risk_per_trade": 0.02,      # 2% max risk per trade
    "max_daily_loss": 0.06,           # 6% max daily loss
    "max_open_trades": 3,             # Max 3 concurrent trades
    "max_correlation": 0.7,           # Avoid correlated positions
    "required_confidence": 80,        # Min 80% confidence
    "required_rr": 2.0,               # Min 1:2 risk-reward
}

class RiskManager:
    def __init__(self, portfolio_value):
        self.portfolio_value = portfolio_value
        self.daily_pnl = 0
        self.open_trades = []

    def can_trade(self):
        """Check if we can open new trade"""
        # Check daily loss limit
        if self.daily_pnl <= -self.portfolio_value * RISK_PARAMETERS['max_daily_loss']:
            return False

        # Check max open trades
        if len(self.open_trades) >= RISK_PARAMETERS['max_open_trades']:
            return False

        return True

    def calculate_position_size(self, entry, stop_loss):
        """Calculate position size based on risk"""
        risk_amount = self.portfolio_value * RISK_PARAMETERS['max_risk_per_trade']
        price_risk = abs(entry - stop_loss)
        position_size = risk_amount / price_risk

        return position_size

    def validate_signal(self, signal):
        """Validate signal meets risk criteria"""
        if signal['confidence'] < RISK_PARAMETERS['required_confidence']:
            return False

        if signal['risk_reward'] < RISK_PARAMETERS['required_rr']:
            return False

        return True
```

**API Endpoints**:
```
GET  /api/risk/status
GET  /api/risk/metrics
POST /api/risk/validate
PUT  /api/risk/parameters
```

---

### 5. PAPER TRADING ENGINE

**Purpose**: Simulate real trading with virtual capital.

**Portfolio Schema**:
```python
{
    "portfolio_id": "uuid",
    "user_id": "uuid",
    "initial_balance": 10000,
    "current_balance": 11250,
    "total_pnl": 1250,
    "realized_pnl": 850,
    "unrealized_pnl": 400,
    "trades_count": 25,
    "win_rate": 0.88,
    "profit_factor": 3.2,
    "max_drawdown": 0.08,
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

**Trade Journal Schema**:
```python
{
    "trade_id": "uuid",
    "portfolio_id": "uuid",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "entry_price": 43250.50,
    "quantity": 0.05,
    "stop_loss": 42800.00,
    "take_profit": 44150.00,
    "current_price": 43600.00,
    "pnl": 17.50,
    "pnl_percent": 0.81,
    "confidence": 85,
    "reasoning": ["Trend aligned", "BOS confirmed"],
    "status": "OPEN",  # OPEN, CLOSED, STOPPED
    "opened_at": "timestamp",
    "closed_at": null,
    "exit_reason": null
}
```

**Functions**:
```python
class PaperTradingEngine:
    def open_trade(self, order):
        """Open new paper trade"""
        pass

    def close_trade(self, trade_id, exit_price, reason):
        """Close trade and update portfolio"""
        pass

    def update_unrealized_pnl(self):
        """Update all open trades with current prices"""
        pass

    def get_portfolio_state(self):
        """Get current portfolio metrics"""
        pass
```

**API Endpoints**:
```
GET  /api/paper/portfolio
GET  /api/paper/trades
POST /api/paper/reset
GET  /api/paper/performance
```

---

## 📊 Database Schema

```sql
-- Markets
CREATE TABLE markets (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(20),  -- crypto, forex, index
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OHLCV Data
CREATE TABLE candles (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) REFERENCES markets(symbol),
    interval VARCHAR(10),
    open_time TIMESTAMP,
    open DECIMAL(20,8),
    high DECIMAL(20,8),
    low DECIMAL(20,8),
    close DECIMAL(20,8),
    volume DECIMAL(30,8),
    UNIQUE(symbol, interval, open_time)
);
CREATE INDEX idx_candles_symbol_interval ON candles(symbol, interval, open_time DESC);

-- Signals
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20),
    interval VARCHAR(10),
    signal VARCHAR(10),  -- BUY, SELL, NO_TRADE
    confidence DECIMAL(5,2),
    entry DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    risk_reward DECIMAL(5,2),
    reasoning JSONB,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
CREATE INDEX idx_signals_symbol ON signals(symbol, created_at DESC);

-- Portfolios
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    name VARCHAR(100),
    initial_balance DECIMAL(20,2),
    current_balance DECIMAL(20,2),
    total_pnl DECIMAL(20,2),
    realized_pnl DECIMAL(20,2),
    unrealized_pnl DECIMAL(20,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trades
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    signal_id UUID REFERENCES signals(id),
    symbol VARCHAR(20),
    side VARCHAR(10),
    entry_price DECIMAL(20,8),
    quantity DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    current_price DECIMAL(20,8),
    pnl DECIMAL(20,2),
    pnl_percent DECIMAL(10,4),
    confidence DECIMAL(5,2),
    reasoning JSONB,
    status VARCHAR(20),  -- OPEN, CLOSED, STOPPED
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    exit_reason VARCHAR(50)
);
CREATE INDEX idx_trades_portfolio ON trades(portfolio_id, opened_at DESC);
CREATE INDEX idx_trades_status ON trades(status, portfolio_id);

-- Performance Metrics
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    date DATE,
    trades_count INTEGER,
    wins INTEGER,
    losses INTEGER,
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(10,2),
    avg_win DECIMAL(20,2),
    avg_loss DECIMAL(20,2),
    max_win DECIMAL(20,2),
    max_loss DECIMAL(20,2),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    daily_pnl DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_metrics_portfolio_date ON performance_metrics(portfolio_id, date DESC);
```

---

## 🎨 UI Components Structure

```
src/
├── components/
│   ├── Chart/
│   │   ├── TradingChart.jsx (TradingView integration)
│   │   ├── IndicatorPanel.jsx
│   │   └── DrawingTools.jsx
│   ├── Watchlist/
│   │   ├── SymbolList.jsx
│   │   ├── PriceCard.jsx
│   │   └── MarketOverview.jsx
│   ├── Signals/
│   │   ├── SignalCard.jsx
│   │   ├── SignalHistory.jsx
│   │   ├── ConfidenceMeter.jsx
│   │   └── ReasoningPanel.jsx
│   ├── Trading/
│   │   ├── OrderPanel.jsx
│   │   ├── ActiveTrades.jsx
│   │   ├── TradeHistory.jsx
│   │   └── PositionManager.jsx
│   ├── Risk/
│   │   ├── RiskMeter.jsx
│   │   ├── ExposureChart.jsx
│   │   └── DrawdownGraph.jsx
│   └── Analytics/
│       ├── PerformanceDashboard.jsx
│       ├── WinRateChart.jsx
│       ├── ProfitFactorCard.jsx
│       └── EquityCurve.jsx
├── stores/
│   ├── marketStore.js
│   ├── signalStore.js
│   ├── tradingStore.js
│   ├── portfolioStore.js
│   └── riskStore.js
└── services/
    ├── marketApi.js
    ├── signalApi.js
    ├── tradingApi.js
    └── analyticsApi.js
```

---

## 🚀 Next Steps

1. ✅ **Phase 1**: Market data engine + indicators (DONE)
2. 🔄 **Phase 2**: Signal generation with scoring system
3. ⏳ **Phase 3**: Paper trading engine
4. ⏳ **Phase 4**: Risk management system
5. ⏳ **Phase 5**: Analytics dashboard
6. ⏳ **Phase 6**: ML enhancement layer

**Current Status**: You have Phase 1 working. Ready to build Phase 2!

Would you like me to implement the complete Signal Generation Engine next?
