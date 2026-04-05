import React, { useState, useEffect } from 'react';
import { useChartStore, useRiskStore, useAlertStore, usePriceStore } from '../stores';
import { Bell, Settings, Moon, Sun, Zap, Wifi, WifiOff } from 'lucide-react';
import SymbolSearchModal from './modals/SymbolSearchModal';
import SettingsModal from './modals/SettingsModal';
import { fetchSessionData } from '../services/api';

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
  const [session, setSession] = useState('London Open');

  // Get current price and change from price store
  const currentSymbolData = prices[symbol] || {};
  const currentPrice = currentSymbolData.price || 0;
  const priceChange = currentSymbolData.change || 0;

  // Load session data when backend is connected
  useEffect(() => {
    if (backendStatus === 'connected') {
      loadSessionData();
    }
  }, [backendStatus]);

  const loadSessionData = async () => {
    try {
      const sessionData = await fetchSessionData();
      if (sessionData) {
        // Update current session based on backend data
        const activeSession = Object.entries(sessionData).find(([_, data]) => data.active);
        if (activeSession) {
          setSession(`${activeSession[0].charAt(0).toUpperCase() + activeSession[0].slice(1)} Open`);
        }
      }
    } catch (error) {
      console.error('Failed to load session data:', error);
    }
  };

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
      <header className="h-12 bg-[var(--bg-secondary)] border-b border-[var(--border)] flex items-center justify-between px-4 gap-4">
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
            <span style={{ color: 'var(--text-primary)' }}>{session}</span>
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

      {showSymbolSearch && <SymbolSearchModal onClose={() => setShowSymbolSearch(false)} />}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  );
};

export default Header;