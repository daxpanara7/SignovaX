import React, { useState } from 'react';
import { useRiskStore, useAlertStore } from '../stores';
import { useChartStore } from '../stores/chartStore';
import { usePriceStore } from '../stores/priceStore';
import { Bell, Settings, Moon, Sun, Zap, Wifi, WifiOff } from 'lucide-react';
import SymbolSearchModal from './modals/SymbolSearchModal';
import SettingsModal from './modals/SettingsModal';

const timeframes = ['1m', '5m', '15m', '1h', '4h', '1D'];
const htfOptions = ['1h', '4h', '1D'];

const Header = ({ backendStatus = 'disconnected' }) => {
  const { symbol, timeframe, htfTimeframe, setSymbol, setTimeframe, setHTFTimeframe } = useChartStore();
  const { balance, todayPnL, todayPnLPercent } = useRiskStore();
  const { unreadCount } = useAlertStore();
  const { prices, isConnected } = usePriceStore();
  const [darkMode, setDarkMode] = useState(true);
  const [liveMode, setLiveMode] = useState(false);
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Determine current session from UTC time
  const getSession = () => {
    const h = new Date().getUTCHours();
    if (h >= 8 && h < 17) return 'London Open';
    if (h >= 13 && h < 22) return 'New York Open';
    if (h >= 0 && h < 9) return 'Tokyo Open';
    return 'Sydney Open';
  };

  // Get current price and change from price store
  const currentSymbolData = prices[symbol] || {};
  const currentPrice = currentSymbolData.price || 0;
  const priceChange = currentSymbolData.change || 0;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const getConnectionStatus = () => {
    switch (backendStatus) {
      case 'connected':
        return {
          icon: Wifi,
          color: 'var(--accent-green)',
          text: 'Connected'
        };
      case 'checking':
        return {
          icon: Wifi,
          color: 'var(--accent-yellow)',
          text: 'Connecting...'
        };
      default:
        return {
          icon: WifiOff,
          color: 'var(--accent-red)',
          text: 'Disconnected'
        };
    }
  };

  const connectionStatus = getConnectionStatus();

  return (
    <>
      {/* ── Desktop header (single row) ── */}
      <header className="app-header-desktop h-12 bg-[var(--bg-secondary)] border-b border-[var(--border)] flex items-center justify-between px-4 gap-4">
        {/* Left Side */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5" style={{ color: 'var(--accent-blue)' }} />
            <span className="text-white font-semibold text-sm">SMC Terminal</span>
            <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'var(--accent-purple)', color: 'white' }}>
              v2.0 PRO
            </span>
          </div>
          
          {/* Connection Status */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded text-xs" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <connectionStatus.icon className="w-3 h-3" style={{ color: connectionStatus.color }} />
            <span style={{ color: connectionStatus.color }}>{connectionStatus.text}</span>
          </div>
        </div>

        {/* Center */}
        <div className="flex items-center gap-3 flex-1 justify-center">
          {/* Symbol Selector */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setSymbol('BTCUSDT')}
              className="px-3 py-1.5 text-xs font-medium rounded transition-colors"
              style={{
                backgroundColor: symbol === 'BTCUSDT' ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: symbol === 'BTCUSDT' ? 'white' : 'var(--text-secondary)'
              }}
            >
              BTC
            </button>
            <button
              onClick={() => setSymbol('ETHUSDT')}
              className="px-3 py-1.5 text-xs font-medium rounded transition-colors"
              style={{
                backgroundColor: symbol === 'ETHUSDT' ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: symbol === 'ETHUSDT' ? 'white' : 'var(--text-secondary)'
              }}
            >
              ETH
            </button>
          </div>

          {/* Price Display */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <span className="monospace font-semibold" style={{ color: 'var(--text-primary)' }}>
              ${currentPrice.toLocaleString()}
            </span>
            <span className="text-xs" style={{ color: priceChange >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {priceChange >= 0 ? '▲' : '▼'} {Math.abs(priceChange).toFixed(1)}%
            </span>
            {isConnected && (
              <span className="w-2 h-2 rounded-full pulse" style={{ backgroundColor: 'var(--accent-green)' }}></span>
            )}
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center gap-1" data-testid="timeframe-selector">
            {timeframes.map((tf) => (
              <button
                key={tf}
                data-testid={`timeframe-${tf}`}
                onClick={() => setTimeframe(tf)}
                className="px-3 py-1.5 text-xs font-medium rounded transition-colors"
                style={{
                  backgroundColor: timeframe === tf ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                  color: timeframe === tf ? 'white' : 'var(--text-secondary)'
                }}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* HTF Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>HTF:</span>
            <select
              data-testid="htf-selector"
              value={htfTimeframe}
              onChange={(e) => setHTFTimeframe(e.target.value)}
              className="px-2 py-1.5 text-xs rounded border-0 outline-none"
              style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
            >
              {htfOptions.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-4">
          {/* Balance */}
          <div className="flex items-center gap-1 text-sm">
            <span style={{ color: 'var(--text-secondary)' }}>💰</span>
            <span className="monospace font-semibold" style={{ color: todayPnL >= 0 ? 'var(--accent-green)' : 'var(--text-primary)' }}>
              {formatCurrency(balance)}
            </span>
          </div>

          {/* Today's P&L */}
          <div className="flex items-center gap-1 text-sm" data-testid="today-pnl">
            <span>{todayPnL >= 0 ? '📈' : '📉'}</span>
            <span className="monospace font-semibold" style={{ color: todayPnL >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {todayPnL >= 0 ? '+' : ''}{formatCurrency(todayPnL)}
            </span>
            <span className="text-xs" style={{ color: todayPnL >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              ({todayPnL >= 0 ? '+' : ''}{todayPnLPercent.toFixed(2)}%)
            </span>
          </div>

          {/* Session Badge */}
          <div data-testid="session-badge" className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <span className="w-2 h-2 rounded-full pulse" style={{ backgroundColor: 'var(--accent-green)' }}></span>
            <span style={{ color: 'var(--text-primary)' }}>{getSession()}</span>
          </div>

          {/* Live/Paper Toggle */}
          <div className="flex items-center gap-1 px-1 py-1 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <button
              data-testid="paper-mode-button"
              onClick={() => setLiveMode(false)}
              className="px-2 py-1 text-xs font-medium rounded transition-colors"
              style={{
                backgroundColor: !liveMode ? 'var(--accent-blue)' : 'transparent',
                color: !liveMode ? 'white' : 'var(--text-secondary)'
              }}
            >
              PAPER
            </button>
            <button
              data-testid="live-mode-button"
              onClick={() => setLiveMode(true)}
              className="px-2 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1"
              style={{
                backgroundColor: liveMode ? 'var(--accent-red)' : 'transparent',
                color: liveMode ? 'white' : 'var(--text-secondary)'
              }}
              disabled={backendStatus !== 'connected'}
            >
              {liveMode && <span className="w-1.5 h-1.5 rounded-full pulse" style={{ backgroundColor: 'white' }}></span>}
              LIVE
            </button>
          </div>

          {/* Alerts */}
          <button data-testid="alerts-button" className="relative" style={{ color: 'var(--text-secondary)' }}>
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-xs flex items-center justify-center" style={{ backgroundColor: 'var(--accent-red)', color: 'white' }}>
                {unreadCount}
              </span>
            )}
          </button>

          {/* Settings */}
          <button data-testid="settings-button" onClick={() => setShowSettings(true)} style={{ color: 'var(--text-secondary)' }}>
            <Settings className="w-5 h-5" />
          </button>

          {/* Theme Toggle */}
          <button data-testid="theme-toggle" onClick={() => setDarkMode(!darkMode)} style={{ color: 'var(--text-secondary)' }}>
            {darkMode ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* ── Mobile header (two compact rows) ── */}
      <header className="app-header-mobile" style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
        {/* Row 1: brand + price + icons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 12px', gap: 8 }}>
          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
            <Zap style={{ width: 14, height: 14, color: 'var(--accent-blue)' }} />
            <span style={{ color: 'white', fontWeight: 700, fontSize: 12 }}>SMC</span>
            <span style={{ fontSize: 9, padding: '1px 5px', borderRadius: 3, backgroundColor: 'var(--accent-purple)', color: 'white' }}>PRO</span>
          </div>

          {/* Price */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, justifyContent: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 5, backgroundColor: 'var(--bg-tertiary)' }}>
              <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>
                ${currentPrice > 0 ? currentPrice.toLocaleString() : '—'}
              </span>
              <span style={{ fontSize: 10, color: priceChange >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                {priceChange >= 0 ? '▲' : '▼'}{Math.abs(priceChange).toFixed(1)}%
              </span>
              {isConnected && <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--accent-green)', display: 'inline-block' }} />}
            </div>
          </div>

          {/* Icons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            {/* Paper/Live */}
            <div style={{ display: 'flex', gap: 2, padding: '2px 3px', borderRadius: 5, backgroundColor: 'var(--bg-tertiary)' }}>
              <button
                data-testid="paper-mode-button"
                onClick={() => setLiveMode(false)}
                style={{ padding: '2px 7px', fontSize: 9, fontWeight: 700, borderRadius: 3, border: 'none', cursor: 'pointer',
                  backgroundColor: !liveMode ? 'var(--accent-blue)' : 'transparent',
                  color: !liveMode ? 'white' : 'var(--text-secondary)' }}
              >PAPER</button>
              <button
                data-testid="live-mode-button"
                onClick={() => setLiveMode(true)}
                disabled={backendStatus !== 'connected'}
                style={{ padding: '2px 7px', fontSize: 9, fontWeight: 700, borderRadius: 3, border: 'none', cursor: 'pointer',
                  backgroundColor: liveMode ? 'var(--accent-red)' : 'transparent',
                  color: liveMode ? 'white' : 'var(--text-secondary)' }}
              >LIVE</button>
            </div>
            <button data-testid="alerts-button" style={{ position: 'relative', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 2 }}>
              <Bell style={{ width: 16, height: 16 }} />
              {unreadCount > 0 && (
                <span style={{ position: 'absolute', top: -2, right: -2, width: 14, height: 14, borderRadius: '50%', fontSize: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--accent-red)', color: 'white' }}>
                  {unreadCount}
                </span>
              )}
            </button>
            <button data-testid="settings-button" onClick={() => setShowSettings(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 2 }}>
              <Settings style={{ width: 16, height: 16 }} />
            </button>
          </div>
        </div>

        {/* Row 2: symbol + timeframes + HTF */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 12px 6px', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
          {/* Symbol buttons */}
          <button onClick={() => setSymbol('BTCUSDT')} style={{ padding: '3px 8px', fontSize: 10, fontWeight: 700, borderRadius: 4, border: 'none', cursor: 'pointer', flexShrink: 0,
            backgroundColor: symbol === 'BTCUSDT' ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
            color: symbol === 'BTCUSDT' ? 'white' : 'var(--text-secondary)' }}>BTC</button>
          <button onClick={() => setSymbol('ETHUSDT')} style={{ padding: '3px 8px', fontSize: 10, fontWeight: 700, borderRadius: 4, border: 'none', cursor: 'pointer', flexShrink: 0,
            backgroundColor: symbol === 'ETHUSDT' ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
            color: symbol === 'ETHUSDT' ? 'white' : 'var(--text-secondary)' }}>ETH</button>

          <div style={{ width: 1, height: 14, backgroundColor: 'var(--border)', flexShrink: 0 }} />

          {/* Timeframes */}
          {timeframes.map((tf) => (
            <button key={tf} data-testid={`timeframe-${tf}`} onClick={() => setTimeframe(tf)}
              style={{ padding: '3px 7px', fontSize: 10, fontWeight: 600, borderRadius: 4, border: 'none', cursor: 'pointer', flexShrink: 0,
                backgroundColor: timeframe === tf ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: timeframe === tf ? 'white' : 'var(--text-secondary)' }}>
              {tf}
            </button>
          ))}

          <div style={{ width: 1, height: 14, backgroundColor: 'var(--border)', flexShrink: 0 }} />

          {/* HTF */}
          <span style={{ fontSize: 9, color: 'var(--text-secondary)', flexShrink: 0 }}>HTF:</span>
          <select data-testid="htf-selector" value={htfTimeframe} onChange={(e) => setHTFTimeframe(e.target.value)}
            style={{ padding: '3px 6px', fontSize: 10, borderRadius: 4, border: 'none', outline: 'none', flexShrink: 0,
              backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
            {htfOptions.map((tf) => <option key={tf} value={tf}>{tf}</option>)}
          </select>

          {/* Session */}
          <div data-testid="session-badge" style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 7px', borderRadius: 4, backgroundColor: 'var(--bg-tertiary)', flexShrink: 0 }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: 'var(--accent-green)', display: 'inline-block' }} />
            <span style={{ fontSize: 9, color: 'var(--text-primary)' }}>{getSession()}</span>
          </div>

          {/* Connection */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 3, padding: '3px 7px', borderRadius: 4, backgroundColor: 'var(--bg-tertiary)', flexShrink: 0 }}>
            <connectionStatus.icon style={{ width: 10, height: 10, color: connectionStatus.color }} />
            <span style={{ fontSize: 9, color: connectionStatus.color }}>{connectionStatus.text}</span>
          </div>
        </div>
      </header>

      {showSymbolSearch && <SymbolSearchModal onClose={() => setShowSymbolSearch(false)} />}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  );
};

export default Header;