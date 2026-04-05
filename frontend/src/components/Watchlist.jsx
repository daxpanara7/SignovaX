import React, { useState } from 'react';
import { useChartStore, usePriceStore } from '../stores';
import { mockWatchlist } from '../data/mockData';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';

const Watchlist = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { symbol: selectedSymbol, setSymbol } = useChartStore();
  const { prices, isConnected } = usePriceStore();

  // Create watchlist with real prices
  const watchlistWithRealPrices = mockWatchlist.map(item => {
    const realPrice = prices[item.symbol];
    if (realPrice) {
      return {
        ...item,
        price: realPrice.price || item.price,
        change: realPrice.change || item.change,
        volume: realPrice.volume || 0
      };
    }
    return item;
  });

  const renderSparkline = (data) => {
    const width = 60;
    const height = 20;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    const isPositive = data[data.length - 1] > data[0];
    
    return (
      <svg width={width} height={height} className="inline-block">
        <polyline
          points={points}
          fill="none"
          stroke={isPositive ? 'var(--accent-green)' : 'var(--accent-red)'}
          strokeWidth="1.5"
        />
      </svg>
    );
  };

  if (collapsed) {
    return (
      <div className="w-10 border-r border-[var(--border)] flex flex-col items-center py-4 gap-4" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <button
          data-testid="expand-watchlist"
          onClick={() => setCollapsed(false)}
          className="p-2 rounded hover:bg-[var(--bg-hover)] transition-colors"
          style={{ color: 'var(--text-secondary)' }}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        {mockWatchlist.slice(0, 5).map((item) => (
          <div key={item.symbol} className="text-xs rotate-90 whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>
            {item.symbol.substring(0, 3)}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="w-45 border-r border-[var(--border)] flex flex-col" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-[var(--border)]">
        <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>WATCHLIST</span>
        <div className="flex items-center gap-1">
          <button data-testid="add-symbol" className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors" style={{ color: 'var(--text-secondary)' }}>
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            data-testid="collapse-watchlist"
            onClick={() => setCollapsed(true)}
            className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Watchlist Items */}
      <div className="flex-1 overflow-y-auto">
        {watchlistWithRealPrices.map((item) => (
          <button
            key={item.symbol}
            data-testid={`watchlist-item-${item.symbol}`}
            onClick={() => setSymbol(item.symbol)}
            className="w-full p-3 border-b border-[var(--border)] hover:bg-[var(--bg-hover)] transition-colors text-left"
            style={{
              backgroundColor: selectedSymbol === item.symbol ? 'var(--bg-tertiary)' : 'transparent',
              borderLeft: selectedSymbol === item.symbol ? '3px solid var(--accent-blue)' : '3px solid transparent'
            }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{item.name}</span>
              <span className="text-xs flex items-center gap-0.5" style={{ color: item.change >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                {item.change >= 0 ? '▲' : '▼'} {Math.abs(item.change)}%
              </span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm monospace font-medium" style={{ color: 'var(--text-primary)' }}>
                ${item.price.toLocaleString('en', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex items-center justify-between">
              {renderSparkline(item.sparkline)}
            </div>
            {item.signal !== 'none' && (
              <div className="mt-2 flex items-center gap-1">
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{
                    backgroundColor: item.signal === 'buy' ? 'var(--accent-green)' : item.signal === 'sell' ? 'var(--accent-red)' : 'var(--text-muted)'
                  }}
                ></span>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {item.signal === 'buy' ? 'Active Signal' : item.signal === 'sell' ? 'Sell Signal' : ''}
                </span>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Market Status */}
      <div className="p-3 border-t border-[var(--border)]">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: isConnected ? 'var(--accent-green)' : 'var(--accent-red)' }}></span>
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            {isConnected ? 'Live Data' : 'Disconnected'}
          </span>
        </div>
        <button data-testid="add-symbol-footer" className="w-full py-2 text-xs font-medium rounded transition-colors" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
          + Add Symbol
        </button>
      </div>
    </div>
  );
};

export default Watchlist;