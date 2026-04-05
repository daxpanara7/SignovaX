/**
 * Market API Service — connects to the lightweight proxy server
 * Supports: Binance (primary), CoinGecko (fallback)
 */

const PROXY_URL = process.env.REACT_APP_PROXY_URL || 'http://localhost:4000';

// ─── Generic fetch with error handling ───────────────────────────────────────

async function apiFetch(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('Request timed out');
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

// ─── Binance ──────────────────────────────────────────────────────────────────

/**
 * Fetch live price for a symbol
 * @param {string} symbol e.g. "BTCUSDT"
 * @returns {{ symbol, price, cached }}
 */
export async function fetchLivePrice(symbol = 'BTCUSDT') {
  return apiFetch(`${PROXY_URL}/api/binance/price?symbol=${symbol}`);
}

/**
 * Fetch OHLCV candles from Binance
 * @param {string} symbol
 * @param {string} interval  1m|5m|15m|1h|4h|1d
 * @param {number} limit     max 1000
 * @returns {{ symbol, interval, candles: Array, cached }}
 */
export async function fetchCandles(symbol = 'BTCUSDT', interval = '15m', limit = 200) {
  return apiFetch(
    `${PROXY_URL}/api/binance/candles?symbol=${symbol}&interval=${interval}&limit=${limit}`
  );
}

/**
 * Fetch 24h ticker stats
 * @param {string} symbol
 */
export async function fetchTicker24(symbol = 'BTCUSDT') {
  return apiFetch(`${PROXY_URL}/api/binance/ticker24?symbol=${symbol}`);
}

/**
 * Fetch all available USDT trading pairs
 */
export async function fetchSymbols() {
  return apiFetch(`${PROXY_URL}/api/binance/symbols`);
}

// ─── CoinGecko (fallback / alternative) ──────────────────────────────────────

/**
 * Fetch price from CoinGecko
 * @param {string} ids  comma-separated coin ids e.g. "bitcoin,ethereum"
 */
export async function fetchCoinGeckoPrice(ids = 'bitcoin') {
  return apiFetch(`${PROXY_URL}/api/coingecko/price?ids=${ids}`);
}

/**
 * Fetch OHLC candles from CoinGecko
 * @param {string} id   coin id e.g. "bitcoin"
 * @param {number} days 1|7|14|30|90|180|365
 */
export async function fetchCoinGeckoOHLC(id = 'bitcoin', days = 7) {
  return apiFetch(`${PROXY_URL}/api/coingecko/ohlc?id=${id}&days=${days}`);
}

// ─── Signal Engine ────────────────────────────────────────────────────────────

/**
 * Get live signal for a symbol — fetches candles + runs analysis on proxy
 * @param {string} symbol
 * @param {string} interval
 * @returns {{ signal: 'BUY'|'SELL'|'HOLD', confidence, reasoning, ... }}
 */
export async function fetchLiveSignal(symbol = 'BTCUSDT', interval = '15m') {
  return apiFetch(
    `${PROXY_URL}/api/signals/live?symbol=${symbol}&interval=${interval}`
  );
}

/**
 * Analyze custom candle array
 * @param {Array} candles
 * @param {string} symbol
 */
export async function analyzeCandles(candles, symbol = 'BTCUSDT') {
  return apiFetch(`${PROXY_URL}/api/signals/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ candles, symbol }),
  });
}

// ─── Proxy health ─────────────────────────────────────────────────────────────

export async function checkProxyHealth() {
  try {
    const data = await apiFetch(`${PROXY_URL}/health`);
    return data.status === 'ok';
  } catch {
    return false;
  }
}
