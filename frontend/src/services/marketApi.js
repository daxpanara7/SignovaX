/**
 * Market API Service
 * 
 * Price + Candles  → Binance public API DIRECTLY (no proxy needed, CORS allowed)
 * Signal engine    → proxy server (localhost:4000) — only needed for /api/signals/live
 * 
 * Binance public endpoints allow browser requests — no API key, no proxy required.
 */

const BINANCE = 'https://api.binance.com';
const PROXY   = process.env.REACT_APP_PROXY_URL || '';

// ─── Generic fetch with timeout ───────────────────────────────────────────────
async function get(url, timeoutMs = 8000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('Request timed out');
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

async function post(url, body, timeoutMs = 10000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('Request timed out');
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

// ─── BINANCE — direct browser calls (no proxy needed) ────────────────────────

/**
 * Live price for one symbol
 * Returns: { symbol, price: number }
 */
export async function fetchLivePrice(symbol = 'BTCUSDT') {
  const data = await get(`${BINANCE}/api/v3/ticker/price?symbol=${symbol}`);
  return { symbol: data.symbol, price: parseFloat(data.price) };
}

/**
 * 24h ticker stats
 * Returns: { priceChangePercent, volume, highPrice, lowPrice, lastPrice }
 */
export async function fetchTicker24(symbol = 'BTCUSDT') {
  return get(`${BINANCE}/api/v3/ticker/24hr?symbol=${symbol}`);
}

/**
 * OHLCV candles — direct from Binance
 * interval: 1m | 5m | 15m | 1h | 4h | 1d
 * Returns: Array of { time (seconds), open, high, low, close, volume }
 */
export async function fetchCandles(symbol = 'BTCUSDT', interval = '15m', limit = 300) {
  const raw = await get(
    `${BINANCE}/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
  );
  return raw.map(k => ({
    time:   Math.floor(k[0] / 1000), // ms → seconds for lightweight-charts
    open:   parseFloat(k[1]),
    high:   parseFloat(k[2]),
    low:    parseFloat(k[3]),
    close:  parseFloat(k[4]),
    volume: parseFloat(k[5]),
  }));
}

/**
 * Fetch prices for multiple symbols in parallel
 * Returns: { BTCUSDT: { price, change, volume, high24h, low24h }, ... }
 */
export async function fetchMultiplePrices(symbols = ['BTCUSDT', 'ETHUSDT']) {
  const results = await Promise.allSettled(
    symbols.map(s => Promise.all([fetchLivePrice(s), fetchTicker24(s)]))
  );
  const map = {};
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') {
      const [price, ticker] = r.value;
      map[symbols[i]] = {
        price:   price.price,
        change:  parseFloat(ticker.priceChangePercent),
        volume:  parseFloat(ticker.volume),
        high24h: parseFloat(ticker.highPrice),
        low24h:  parseFloat(ticker.lowPrice),
      };
    }
  });
  return map;
}

// ─── SIGNAL ENGINE — via proxy (runs EMA/RSI/ATR logic server-side) ───────────

/**
 * Get live BUY/SELL/HOLD signal from proxy
 * Falls back to client-side calculation if proxy is offline
 */
export async function fetchLiveSignal(symbol = 'BTCUSDT', interval = '15m') {
  // If proxy URL is configured, try it first
  if (PROXY) {
    try {
      return await get(`${PROXY}/api/signals/live?symbol=${symbol}&interval=${interval}`, 6000);
    } catch { /* fall through to client-side */ }
  }
  // No proxy or proxy failed — calculate in browser
  const candles = await fetchCandles(symbol, interval, 100);
  return calcSignalClientSide(candles, symbol);
}

// ─── Client-side signal fallback (runs in browser if proxy is down) ───────────

function calcSignalClientSide(candles, symbol) {
  const closes = candles.map(c => c.close);
  const highs   = candles.map(c => c.high);
  const lows    = candles.map(c => c.low);
  const n = closes.length;
  if (n < 20) return { signal: 'HOLD', confidence: 0, reasoning: ['Not enough data'] };

  const ema20 = calcEMA(closes, 20);
  const ema50 = calcEMA(closes, Math.min(50, n - 1));
  const rsi   = calcRSI(closes, 14);
  const atr   = calcATR(candles, 14);

  const price     = closes[n - 1];
  const prevPrice = closes[n - 2];
  const swingHigh = Math.max(...highs.slice(-20));
  const swingLow  = Math.min(...lows.slice(-20));

  let buyScore = 0, sellScore = 0;
  const reasoning = [];

  if (ema20 > ema50)          { buyScore++;  reasoning.push('EMA20 > EMA50 (bullish trend)'); }
  if (ema20 < ema50)          { sellScore++; reasoning.push('EMA20 < EMA50 (bearish trend)'); }
  if (price > ema20)          { buyScore++;  reasoning.push('Price above EMA20'); }
  if (price < ema20)          { sellScore++; reasoning.push('Price below EMA20'); }
  if (rsi < 35)               { buyScore++;  reasoning.push(`RSI oversold (${rsi.toFixed(1)})`); }
  if (rsi > 65)               { sellScore++; reasoning.push(`RSI overbought (${rsi.toFixed(1)})`); }
  if (price <= swingLow*1.005){ buyScore++;  reasoning.push('Near swing low (liquidity)'); }
  if (price >= swingHigh*0.995){ sellScore++; reasoning.push('Near swing high (liquidity)'); }
  if (price > prevPrice)      { buyScore++;  reasoning.push('Bullish candle'); }
  if (price < prevPrice)      { sellScore++; reasoning.push('Bearish candle'); }

  let signal = 'HOLD', confidence = 50;
  if (buyScore >= 3 && buyScore > sellScore) {
    signal = 'BUY'; confidence = Math.round((buyScore / 5) * 100);
  } else if (sellScore >= 3 && sellScore > buyScore) {
    signal = 'SELL'; confidence = Math.round((sellScore / 5) * 100);
  } else {
    reasoning.splice(0, reasoning.length, 'No strong confluence — waiting for setup');
  }

  const sl = signal === 'BUY'  ? price - atr * 1.5
           : signal === 'SELL' ? price + atr * 1.5 : null;
  const tp = signal === 'BUY'  ? price + atr * 3
           : signal === 'SELL' ? price - atr * 3   : null;

  return {
    symbol, signal, confidence,
    currentPrice: price,
    ema20: +ema20.toFixed(4), ema50: +ema50.toFixed(4),
    rsi: +rsi.toFixed(2), atr: +atr.toFixed(4),
    swingHigh, swingLow,
    stopLoss:   sl ? +sl.toFixed(4) : null,
    takeProfit: tp ? +tp.toFixed(4) : null,
    riskReward: 2,
    reasoning,
    timestamp: new Date().toISOString(),
    source: 'client', // flag so UI knows proxy was offline
  };
}

function calcEMA(closes, period) {
  const k = 2 / (period + 1);
  let ema = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < closes.length; i++) ema = closes[i] * k + ema * (1 - k);
  return ema;
}

function calcRSI(closes, period = 14) {
  let gains = 0, losses = 0;
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1];
    if (d > 0) gains += d; else losses += Math.abs(d);
  }
  let ag = gains / period, al = losses / period;
  for (let i = period + 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    ag = (ag * (period - 1) + (d > 0 ? d : 0)) / period;
    al = (al * (period - 1) + (d < 0 ? Math.abs(d) : 0)) / period;
  }
  return al === 0 ? 100 : 100 - 100 / (1 + ag / al);
}

function calcATR(candles, period = 14) {
  const trs = candles.slice(1).map((c, i) => Math.max(
    c.high - c.low,
    Math.abs(c.high - candles[i].close),
    Math.abs(c.low  - candles[i].close)
  ));
  return trs.slice(-period).reduce((a, b) => a + b, 0) / period;
}

// ─── Proxy health check ───────────────────────────────────────────────────────
export async function checkProxyHealth() {
  if (!PROXY) return false;
  try {
    const d = await get(`${PROXY}/health`, 3000);
    return d.status === 'ok';
  } catch { return false; }
}
