import React, { useState, useEffect } from 'react';
import { useChartStore } from '../stores/chartStore';
import { usePriceStore } from '../stores/priceStore';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const CRYPTO_SYMBOLS = [
  { symbol: 'BTCUSDT', name: 'BTC/USDT', type: 'crypto' },
  { symbol: 'ETHUSDT', name: 'ETH/USDT', type: 'crypto' },
  { symbol: 'SOLUSDT', name: 'SOL/USDT', type: 'crypto' },
  { symbol: 'BNBUSDT', name: 'BNB/USDT', type: 'crypto' },
  { symbol: 'XRPUSDT', name: 'XRP/USDT', type: 'crypto' },
];

const INDEX_SYMBOLS = [
  { symbol: 'NIFTY50',  name: 'NIFTY 50',  type: 'index' },
  { symbol: 'SENSEX',   name: 'SENSEX',    type: 'index' },
];

const ALL_SYMBOLS = [...CRYPTO_SYMBOLS, ...INDEX_SYMBOLS];

const ML_API = process.env.REACT_APP_ML_API_URL || 'http://localhost:8000';

// Fetch Indian index price from our ML API (fast and reliable)
async function fetchIndexPrice(symbol) {
  try {
    const res = await fetch(
      `${ML_API}/index-candles?symbol=${symbol}&interval=1d&limit=2`,
      { signal: AbortSignal.timeout(5000) }
    );
    const data = await res.json();
    if (!data.candles || data.candles.length < 2) return null;

    const latest = data.candles[data.candles.length - 1];
    const previous = data.candles[data.candles.length - 2];

    const price = latest.close;
    const prevClose = previous.close;
    const change = ((price - prevClose) / prevClose) * 100;

    return { price, change };
  } catch (err) {
    console.error(`Failed to fetch ${symbol} price:`, err);
    return null;
  }
}

const Sparkline = ({ change }) => {
  const positive = change >= 0;
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 20 }}>
      {[0.3, 0.5, 0.4, 0.7, 0.6, 0.8, 1.0].map((h, i) => (
        <div key={i} style={{
          width: 4, borderRadius: 1,
          height: `${h * 20}px`,
          backgroundColor: positive ? '#10b981' : '#ef4444',
          opacity: 0.4 + h * 0.6,
        }} />
      ))}
    </div>
  );
};

const Watchlist = ({ mobileStrip }) => {
  const [collapsed, setCollapsed] = useState(false);
  const { symbol: selectedSymbol, setSymbol } = useChartStore();
  const { prices, isConnected } = usePriceStore();

  // Index prices fetched separately (not from Binance WebSocket)
  const [indexPrices, setIndexPrices] = useState({});

  useEffect(() => {
    const fetchAll = async () => {
      const results = await Promise.all(
        INDEX_SYMBOLS.map(async (s) => {
          const data = await fetchIndexPrice(s.symbol);
          return [s.symbol, data];
        })
      );
      const map = {};
      results.forEach(([sym, data]) => { if (data) map[sym] = data; });
      setIndexPrices(map);
    };

    fetchAll();
    // Refresh every 30s for faster updates
    const timer = setInterval(fetchAll, 30000);
    return () => clearInterval(timer);
  }, []);

  const getPrice = (symbol, type) => {
    if (type === 'crypto') return prices[symbol] ?? null;
    return indexPrices[symbol] ?? null;
  };

  // ── Mobile horizontal strip mode ────────────────────────────────────────
  if (mobileStrip) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'row', overflowX: 'auto',
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border)',
        WebkitOverflowScrolling: 'touch',
        gap: 0,
      }}>
        {ALL_SYMBOLS.map(({ symbol, name, type }) => {
          const live    = getPrice(symbol, type);
          const price   = live?.price ?? null;
          const change  = live?.change ?? null;
          const isSelected = selectedSymbol === symbol;
          const positive   = change == null ? true : change >= 0;

          return (
            <button key={symbol} onClick={() => setSymbol(symbol)}
              style={{
                flexShrink: 0,
                padding: '8px 12px',
                borderRight: '1px solid var(--border)',
                borderBottom: isSelected ? '2px solid var(--accent-blue)' : '2px solid transparent',
                backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                textAlign: 'left', cursor: 'pointer',
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>{name}</span>
                <span style={{ fontSize: 10, color: positive ? '#10b981' : '#ef4444' }}>
                  {change == null ? '—' : `${positive ? '+' : ''}${change.toFixed(2)}%`}
                </span>
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                {price == null
                  ? <span style={{ color: 'var(--text-secondary)', fontSize: 10 }}>{type === 'index' ? 'Fetching...' : 'Loading...'}</span>
                  : type === 'index'
                    ? `₹${price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
                    : `${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}`
                }
              </div>
            </button>
          );
        })}
      </div>
    );
  }

  if (collapsed) {
    return (
      <div style={{
        width: 40, borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        paddingTop: 12, gap: 8, backgroundColor: 'var(--bg-secondary)', flexShrink: 0,
      }}>
        <button onClick={() => setCollapsed(false)}
          style={{ color: 'var(--text-secondary)', background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}>
          <ChevronRight className="w-4 h-4" />
        </button>
        {ALL_SYMBOLS.map(s => (
          <div key={s.symbol} style={{
            fontSize: 9, color: 'var(--text-secondary)',
            writingMode: 'vertical-rl', textOrientation: 'mixed',
          }}>
            {s.name.split('/')[0]}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div style={{
      width: 180, borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      backgroundColor: 'var(--bg-secondary)', flexShrink: 0,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 12px', borderBottom: '1px solid var(--border)',
      }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: 1 }}>
          WATCHLIST
        </span>
        <button onClick={() => setCollapsed(true)}
          style={{ color: 'var(--text-secondary)', background: 'none', border: 'none', cursor: 'pointer' }}>
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Symbol rows */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {ALL_SYMBOLS.map(({ symbol, name, type }) => {
          const live    = getPrice(symbol, type);
          const price   = live?.price ?? null;
          const change  = live?.change ?? null;
          const isSelected = selectedSymbol === symbol;
          const positive   = change == null ? true : change >= 0;

          return (
            <button key={symbol} onClick={() => setSymbol(symbol)}
              style={{
                width: '100%', padding: '10px 12px',
                borderBottom: '1px solid var(--border)',
                borderLeft: isSelected ? '3px solid var(--accent-blue)' : '3px solid transparent',
                backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                textAlign: 'left', cursor: 'pointer', display: 'block',
              }}>
              {/* Name + change */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {name}
                </span>
                <span style={{ fontSize: 10, color: positive ? '#10b981' : '#ef4444' }}>
                  {change == null ? '—' : `${positive ? '+' : ''}${change.toFixed(2)}%`}
                </span>
              </div>

              {/* Price */}
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6, fontFamily: 'monospace' }}>
                {price == null
                  ? <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
                      {type === 'index' ? 'Fetching...' : 'Loading...'}
                    </span>
                  : type === 'index'
                    ? `₹${price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
                    : `${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}`
                }
              </div>

              {/* Sparkline */}
              <Sparkline change={change ?? 0} />

              {/* Index badge */}
              {type === 'index' && (
                <div style={{ fontSize: 8, color: '#f59e0b', marginTop: 2 }}>🇮🇳 NSE/BSE</div>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            backgroundColor: isConnected ? '#10b981' : '#ef4444',
            boxShadow: isConnected ? '0 0 5px #10b981' : 'none',
          }} />
          <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>
            {isConnected ? '⚡ WebSocket Live' : 'Offline'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default Watchlist;
