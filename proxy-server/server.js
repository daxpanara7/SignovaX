require('dotenv').config();
const express = require('express');
const cors = require('cors');
const NodeCache = require('node-cache');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 4000;

// In-memory cache
const cache = new NodeCache({
  stdTTL: 60,
  checkperiod: 30,
});

// CORS — allow any localhost origin (dev)
app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (curl, Postman) or any localhost
    if (!origin || origin.includes('localhost') || origin.includes('127.0.0.1')) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST'],
}));
app.use(express.json());

// ─── Helpers ────────────────────────────────────────────────────────────────

function cached(key, ttl, fetchFn) {
  const hit = cache.get(key);
  if (hit !== undefined) return Promise.resolve({ data: hit, cached: true });
  return fetchFn().then((data) => {
    cache.set(key, data, ttl);
    return { data, cached: false };
  });
}

// ─── Health ──────────────────────────────────────────────────────────────────

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ─── BINANCE routes (no API key needed) ──────────────────────────────────────

const BINANCE = process.env.BINANCE_BASE_URL || 'https://api.binance.com';

// GET /api/binance/price?symbol=BTCUSDT
app.get('/api/binance/price', async (req, res) => {
  const { symbol = 'BTCUSDT' } = req.query;
  const key = `binance_price_${symbol}`;
  try {
    const result = await cached(key, parseInt(process.env.CACHE_TTL_PRICE) || 10, async () => {
      const r = await axios.get(`${BINANCE}/api/v3/ticker/price`, { params: { symbol } });
      return r.data;
    });
    res.json({ ...result.data, cached: result.cached });
  } catch (err) {
    res.status(502).json({ error: 'Binance price fetch failed', detail: err.message });
  }
});

// GET /api/binance/candles?symbol=BTCUSDT&interval=15m&limit=200
app.get('/api/binance/candles', async (req, res) => {
  const { symbol = 'BTCUSDT', interval = '15m', limit = 200 } = req.query;
  const key = `binance_candles_${symbol}_${interval}_${limit}`;
  try {
    const result = await cached(key, parseInt(process.env.CACHE_TTL_CANDLES) || 60, async () => {
      const r = await axios.get(`${BINANCE}/api/v3/klines`, {
        params: { symbol, interval, limit },
      });
      // Normalize to OHLCV objects
      return r.data.map((k) => ({
        time: k[0],                    // open time ms
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4]),
        volume: parseFloat(k[5]),
        closeTime: k[6],
      }));
    });
    res.json({ symbol, interval, candles: result.data, cached: result.cached });
  } catch (err) {
    res.status(502).json({ error: 'Binance candles fetch failed', detail: err.message });
  }
});

// GET /api/binance/ticker24?symbol=BTCUSDT
app.get('/api/binance/ticker24', async (req, res) => {
  const { symbol = 'BTCUSDT' } = req.query;
  const key = `binance_ticker24_${symbol}`;
  try {
    const result = await cached(key, 30, async () => {
      const r = await axios.get(`${BINANCE}/api/v3/ticker/24hr`, { params: { symbol } });
      return r.data;
    });
    res.json({ ...result.data, cached: result.cached });
  } catch (err) {
    res.status(502).json({ error: 'Binance ticker fetch failed', detail: err.message });
  }
});

// GET /api/binance/symbols — list all USDT pairs
app.get('/api/binance/symbols', async (req, res) => {
  const key = 'binance_symbols';
  try {
    const result = await cached(key, 3600, async () => {
      const r = await axios.get(`${BINANCE}/api/v3/exchangeInfo`);
      return r.data.symbols
        .filter((s) => s.quoteAsset === 'USDT' && s.status === 'TRADING')
        .map((s) => s.symbol);
    });
    res.json({ symbols: result.data, cached: result.cached });
  } catch (err) {
    res.status(502).json({ error: 'Binance symbols fetch failed', detail: err.message });
  }
});

// ─── COINGECKO routes ─────────────────────────────────────────────────────────

const CG_BASE = 'https://api.coingecko.com/api/v3';
const CG_HEADERS = process.env.COINGECKO_API_KEY
  ? { 'x-cg-demo-api-key': process.env.COINGECKO_API_KEY }
  : {};

// GET /api/coingecko/price?ids=bitcoin,ethereum
app.get('/api/coingecko/price', async (req, res) => {
  const { ids = 'bitcoin', vs_currencies = 'usd' } = req.query;
  const key = `cg_price_${ids}_${vs_currencies}`;
  try {
    const result = await cached(key, 15, async () => {
      const r = await axios.get(`${CG_BASE}/simple/price`, {
        params: { ids, vs_currencies, include_24hr_change: true, include_24hr_vol: true },
        headers: CG_HEADERS,
      });
      return r.data;
    });
    res.json({ data: result.data, cached: result.cached });
  } catch (err) {
    res.status(502).json({ error: 'CoinGecko price fetch failed', detail: err.message });
  }
});

// GET /api/coingecko/ohlc?id=bitcoin&days=7
app.get('/api/coingecko/ohlc', async (req, res) => {
  const { id = 'bitcoin', days = 7 } = req.query;
  const key = `cg_ohlc_${id}_${days}`;
  try {
    const result = await cached(key, parseInt(process.env.CACHE_TTL_CANDLES) || 60, async () => {
      const r = await axios.get(`${CG_BASE}/coins/${id}/ohlc`, {
        params: { vs_currency: 'usd', days },
        headers: CG_HEADERS,
      });
      // CoinGecko returns [timestamp, open, high, low, close]
      return r.data.map((c) => ({
        time: c[0],
        open: c[1],
        high: c[2],
        low: c[3],
        close: c[4],
      }));
    });
    res.json({ id, days, candles: result.data, cached: result.cached });
  } catch (err) {
    res.status(502).json({ error: 'CoinGecko OHLC fetch failed', detail: err.message });
  }
});

// ─── SIGNAL ENGINE (Phase 8) ──────────────────────────────────────────────────

// POST /api/signals/analyze  body: { candles: [...], symbol: "BTCUSDT" }
app.post('/api/signals/analyze', (req, res) => {
  const { candles, symbol = 'BTCUSDT' } = req.body;
  if (!candles || candles.length < 20) {
    return res.status(400).json({ error: 'Need at least 20 candles for analysis' });
  }
  const signal = analyzeSignal(candles, symbol);
  res.json(signal);
});

// GET /api/signals/live?symbol=BTCUSDT&interval=15m
app.get('/api/signals/live', async (req, res) => {
  const { symbol = 'BTCUSDT', interval = '15m' } = req.query;
  try {
    // Fetch candles from Binance
    const r = await axios.get(`${BINANCE}/api/v3/klines`, {
      params: { symbol, interval, limit: 100 },
    });
    const candles = r.data.map((k) => ({
      time: k[0],
      open: parseFloat(k[1]),
      high: parseFloat(k[2]),
      low: parseFloat(k[3]),
      close: parseFloat(k[4]),
      volume: parseFloat(k[5]),
    }));
    const signal = analyzeSignal(candles, symbol);
    res.json({ symbol, interval, ...signal, candles: candles.slice(-5) });
  } catch (err) {
    res.status(502).json({ error: 'Live signal fetch failed', detail: err.message });
  }
});

// ─── Signal Logic (Phase 8) ───────────────────────────────────────────────────

function analyzeSignal(candles, symbol) {
  const closes = candles.map((c) => c.close);
  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  const n = closes.length;

  const currentPrice = closes[n - 1];
  const prevPrice = closes[n - 2];

  // EMA calculation
  const ema20 = calcEMA(closes, 20);
  const ema50 = calcEMA(closes, 50);

  // RSI
  const rsi = calcRSI(closes, 14);

  // Recent swing high/low (last 20 candles)
  const recentHighs = highs.slice(-20);
  const recentLows = lows.slice(-20);
  const swingHigh = Math.max(...recentHighs);
  const swingLow = Math.min(...recentLows);

  // Simple SMC-inspired logic
  // BUY: price above EMA20, EMA20 > EMA50, RSI not overbought, price near swing low
  // SELL: price below EMA20, EMA20 < EMA50, RSI not oversold, price near swing high
  // HOLD: everything else

  let signal = 'HOLD';
  let confidence = 0;
  let reasoning = [];

  const nearSwingLow = currentPrice <= swingLow * 1.005;
  const nearSwingHigh = currentPrice >= swingHigh * 0.995;
  const bullishTrend = ema20 > ema50;
  const bearishTrend = ema20 < ema50;
  const priceAboveEMA20 = currentPrice > ema20;
  const priceBelowEMA20 = currentPrice < ema20;
  const rsiOversold = rsi < 35;
  const rsiOverbought = rsi > 65;
  const bullishCandle = currentPrice > prevPrice;
  const bearishCandle = currentPrice < prevPrice;

  // BUY conditions
  let buyScore = 0;
  if (bullishTrend) { buyScore++; reasoning.push('EMA20 > EMA50 (bullish trend)'); }
  if (priceAboveEMA20) { buyScore++; reasoning.push('Price above EMA20'); }
  if (rsiOversold) { buyScore++; reasoning.push(`RSI oversold (${rsi.toFixed(1)})`); }
  if (nearSwingLow) { buyScore++; reasoning.push('Price near swing low (liquidity zone)'); }
  if (bullishCandle) { buyScore++; reasoning.push('Bullish candle close'); }

  // SELL conditions
  let sellScore = 0;
  if (bearishTrend) { sellScore++; reasoning.push('EMA20 < EMA50 (bearish trend)'); }
  if (priceBelowEMA20) { sellScore++; reasoning.push('Price below EMA20'); }
  if (rsiOverbought) { sellScore++; reasoning.push(`RSI overbought (${rsi.toFixed(1)})`); }
  if (nearSwingHigh) { sellScore++; reasoning.push('Price near swing high (liquidity zone)'); }
  if (bearishCandle) { sellScore++; reasoning.push('Bearish candle close'); }

  if (buyScore >= 3 && buyScore > sellScore) {
    signal = 'BUY';
    confidence = Math.round((buyScore / 5) * 100);
  } else if (sellScore >= 3 && sellScore > buyScore) {
    signal = 'SELL';
    confidence = Math.round((sellScore / 5) * 100);
  } else {
    signal = 'HOLD';
    confidence = 50;
    reasoning = ['No strong confluence — waiting for setup'];
  }

  // Risk levels
  const atr = calcATR(candles, 14);
  const stopLoss = signal === 'BUY'
    ? currentPrice - atr * 1.5
    : signal === 'SELL'
    ? currentPrice + atr * 1.5
    : null;
  const takeProfit = signal === 'BUY'
    ? currentPrice + atr * 3
    : signal === 'SELL'
    ? currentPrice - atr * 3
    : null;

  return {
    symbol,
    signal,
    confidence,
    currentPrice,
    ema20: parseFloat(ema20.toFixed(4)),
    ema50: parseFloat(ema50.toFixed(4)),
    rsi: parseFloat(rsi.toFixed(2)),
    swingHigh,
    swingLow,
    atr: parseFloat(atr.toFixed(4)),
    stopLoss: stopLoss ? parseFloat(stopLoss.toFixed(4)) : null,
    takeProfit: takeProfit ? parseFloat(takeProfit.toFixed(4)) : null,
    riskReward: stopLoss && takeProfit ? 2.0 : null,
    reasoning,
    timestamp: new Date().toISOString(),
  };
}

function calcEMA(closes, period) {
  const k = 2 / (period + 1);
  let ema = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < closes.length; i++) {
    ema = closes[i] * k + ema * (1 - k);
  }
  return ema;
}

function calcRSI(closes, period = 14) {
  let gains = 0, losses = 0;
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) gains += diff;
    else losses += Math.abs(diff);
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;
  for (let i = period + 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + (diff > 0 ? diff : 0)) / period;
    avgLoss = (avgLoss * (period - 1) + (diff < 0 ? Math.abs(diff) : 0)) / period;
  }
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function calcATR(candles, period = 14) {
  const trs = candles.slice(1).map((c, i) => {
    const prev = candles[i];
    return Math.max(
      c.high - c.low,
      Math.abs(c.high - prev.close),
      Math.abs(c.low - prev.close)
    );
  });
  return trs.slice(-period).reduce((a, b) => a + b, 0) / period;
}

// ─── Start ────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`\n🚀 Trading Proxy Server running on http://localhost:${PORT}`);
  console.log(`   Health:  GET  /health`);
  console.log(`   Price:   GET  /api/binance/price?symbol=BTCUSDT`);
  console.log(`   Candles: GET  /api/binance/candles?symbol=BTCUSDT&interval=15m`);
  console.log(`   Signal:  GET  /api/signals/live?symbol=BTCUSDT&interval=15m`);
  console.log(`   CoinGecko OHLC: GET /api/coingecko/ohlc?id=bitcoin&days=7\n`);
});
