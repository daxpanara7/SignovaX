import React, { useState } from 'react';
import { X, Search } from 'lucide-react';
import { useChartStore } from '../../stores';
import { mockWatchlist } from '../../data/mockData';

const SymbolSearchModal = ({ onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const { setSymbol } = useChartStore();

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'crypto', label: 'Crypto' },
    { id: 'forex', label: 'Forex' },
    { id: 'indices', label: 'Indices' }
  ];

  const allSymbols = [...mockWatchlist];

  const filteredSymbols = allSymbols.filter(item =>
    item.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (symbol) => {
    setSymbol(symbol);
    onClose();
  };

  return (
    <div data-testid="symbol-search-modal" className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }} onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-lg shadow-2xl"
        style={{ backgroundColor: 'var(--bg-secondary)', maxHeight: '80vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Search Symbol</h2>
          <button data-testid="close-modal" onClick={onClose} className="p-1 rounded hover:bg-[var(--bg-hover)]" style={{ color: 'var(--text-secondary)' }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
            <input
              data-testid="symbol-search-input"
              type="text"
              placeholder="Search symbols..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
              className="w-full pl-10 pr-4 py-3 rounded-lg border-0 outline-none text-sm"
              style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
            />
          </div>
        </div>

        {/* Categories */}
        <div className="px-4 pb-4 flex items-center gap-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className="px-3 py-1.5 text-xs font-medium rounded transition-colors"
              style={{
                backgroundColor: selectedCategory === cat.id ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: selectedCategory === cat.id ? 'white' : 'var(--text-secondary)'
              }}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Results */}
        <div className="px-4 pb-4 max-h-96 overflow-y-auto">
          <div className="space-y-1">
            {filteredSymbols.length > 0 ? (
              filteredSymbols.map((item) => (
                <button
                  key={item.symbol}
                  data-testid={`search-result-${item.symbol}`}
                  onClick={() => handleSelect(item.symbol)}
                  className="w-full p-3 rounded-lg hover:bg-[var(--bg-hover)] transition-colors text-left"
                  style={{ backgroundColor: 'var(--bg-tertiary)' }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>{item.name}</div>
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{item.symbol}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium monospace mb-1" style={{ color: 'var(--text-primary)' }}>
                        ${item.price.toLocaleString('en', { minimumFractionDigits: 2 })}
                      </div>
                      <div
                        className="text-xs font-medium"
                        style={{ color: item.change >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}
                      >
                        {item.change >= 0 ? '+' : ''}{item.change}%
                      </div>
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="text-center py-8" style={{ color: 'var(--text-secondary)' }}>
                No symbols found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SymbolSearchModal;