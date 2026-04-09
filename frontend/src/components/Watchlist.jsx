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
  { symbol: 'NIFTY50',  name: 'NIFTY 50',  yahooTicker: '%5ENSEI',  type: 'index' },
  { symbol: 'SENSEX',   name: 'SENSEX',     yahooTicker: '%5EBSESN', type: 'index' },
  { symbol: 'SGXNIFTY', name: 'SGX Nifty',  yahooTicker: 'NI%3DFUT', type: 'index' },
];

const ALL_SYMBOLS = [...CRYPTO_SYMBOLS, ...INDEX_SYMBOLS];

// Fetch Indian index price from Yahoo Finance via allorigins proxy (no CORS issues)
async function fetchIndexPrice(yahooTicker) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${yahooTicker}?interval=1d&range=2d`;
    const proxy = `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`;
    const res = await fetch(proxy, { signal: AbortSignal.timeout(8000) });
    const json = await res.json();
    const data = JSON.parse(json.contents);
    const meta = data?.chart?.result?.[0]?.meta;
    if (!meta) return null;
    const price = meta.regularMarketPrice;
    const prev  = meta.chartPreviousClose || meta.previousClose;
    const change = prev ? ((price - prev) / prev) * 100 : 0;
    return { price, change };
  } catch {
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

const Watchlist = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { symbol: selectedSymbol, setSymbol } = useChartStore();
  const { prices, isConnected } = usePriceStore();

  // Index prices fetched separately (not from Binance WebSocket)
  const [indexPrices, setIndexPrices] = useState({});

  useEffect(() => {
    const fetchAll = async () => {
      const results = await Promise.all(
        INDEX_SYMBOLS.map(async (s) => {
          const data = await fetchIndexPrice(s.yahooTicker);
          return [s.symbol, data];
        })
      );
      const map = {};
      results.forEach(([sym, data]) => { if (data) map[sym] = data; });
      setIndexPrices(map);
    };

    fetchAll();
    // Refresh every 60s (indices don't need real-time)
    const timer = setInterval(fetchAll, 60000);
    return () => clearInterval(timer);
  }, []);

  const getPrice = (symbol, type) => {
    if (type === 'crypto') return prices[symbol] ?? null;
    return indexPrices[symbol] ?? null;
  };

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
