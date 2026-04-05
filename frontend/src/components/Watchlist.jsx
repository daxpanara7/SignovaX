import React, { useState } from 'react';
import { useChartStore } from '../stores/chartStore';
import { usePriceStore } from '../stores/priceStore';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const SYMBOLS = [
  { symbol: 'BTCUSDT',  name: 'BTC/USDT' },
  { symbol: 'ETHUSDT',  name: 'ETH/USDT' },
  { symbol: 'SOLUSDT',  name: 'SOL/USDT' },
  { symbol: 'BNBUSDT',  name: 'BNB/USDT' },
  { symbol: 'XRPUSDT',  name: 'XRP/USDT' },
];

const Sparkline = ({ change }) => {
  // Simple visual bar based on % change
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
        {SYMBOLS.map(s => (
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
        {SYMBOLS.map(({ symbol, name }) => {
          const live = prices[symbol];
          const price = live?.price ?? null;
          const change = live?.change ?? null;
          const isSelected = selectedSymbol === symbol;
          const positive = change == null ? true : change >= 0;

          return (
            <button key={symbol} onClick={() => setSymbol(symbol)}
              style={{
                width: '100%', padding: '10px 12px',
                borderBottom: '1px solid var(--border)',
                borderLeft: isSelected ? '3px solid var(--accent-blue)' : '3px solid transparent',
                backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                textAlign: 'left', cursor: 'pointer', display: 'block',
              }}>
              {/* Symbol name + change */}
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
                  ? <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>Loading...</span>
                  : `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: price > 100 ? 2 : 4 })}`
                }
              </div>

              {/* Sparkline */}
              <Sparkline change={change ?? 0} />
            </button>
          );
        })}
      </div>

      {/* Footer status */}
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
