import React, { useEffect, useState, useCallback } from 'react';
import './styles/globals.css';
import Header from './components/Header';
import Watchlist from './components/Watchlist';
import ChartPanel from './components/ChartPanel';
import SignalPanel from './components/SignalPanel';
import BottomPanel from './components/BottomPanel';
import LiveSignalPanel from './components/LiveSignalPanel';
import { useRiskStore, useAlertStore } from './stores';
import { usePriceStore } from './stores/priceStore';
import { useChartStore } from './stores/chartStore';
import { fetchLivePrice, fetchTicker24, checkProxyHealth } from './services/marketApi';
import { AlertTriangle, Wifi, WifiOff } from 'lucide-react';

// Symbols to poll prices for (watchlist + header)
const WATCHED_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];

function App() {
  const [proxyStatus, setProxyStatus] = useState('checking'); // checking | online | offline
  const [showBanner, setShowBanner] = useState(true);

  const { updatePrices, setConnectionStatus } = usePriceStore();
  const { symbol } = useChartStore();

  // ── Poll Binance prices every 5 seconds ──────────────────────────────────
  const pollPrices = useCallback(async () => {
    try {
      // Fetch all watched symbols in parallel
      const results = await Promise.allSettled(
        WATCHED_SYMBOLS.map(sym =>
          Promise.all([
            fetchLivePrice(sym),
            fetchTicker24(sym),
          ])
        )
      );

      const priceMap = {};
      results.forEach((result, i) => {
        if (result.status === 'fulfilled') {
          const [priceData, tickerData] = result.value;
          const sym = WATCHED_SYMBOLS[i];
          priceMap[sym] = {
            price: parseFloat(priceData.price),
            change: parseFloat(tickerData.priceChangePercent),
            volume: parseFloat(tickerData.volume),
            high24h: parseFloat(tickerData.highPrice),
            low24h: parseFloat(tickerData.lowPrice),
          };
        }
      });

      if (Object.keys(priceMap).length > 0) {
        updatePrices(priceMap);
        setConnectionStatus(true);
        setProxyStatus('online');
      }
    } catch (err) {
      setConnectionStatus(false);
      setProxyStatus('offline');
    }
  }, [updatePrices, setConnectionStatus]);

  // ── Check proxy health on startup, then start polling ───────────────────
  useEffect(() => {
    const init = async () => {
      const healthy = await checkProxyHealth();
      setProxyStatus(healthy ? 'online' : 'offline');
      setConnectionStatus(healthy);
      if (healthy) pollPrices();
    };
    init();

    // Poll every 5 seconds
    const interval = setInterval(pollPrices, 5000);
    return () => clearInterval(interval);
  }, [pollPrices, setConnectionStatus]);

  // ── Banner config ────────────────────────────────────────────────────────
  const getBanner = () => {
    if (proxyStatus === 'checking') return {
      color: '#1e40af', icon: Wifi,
      msg: '🔄 Connecting to Binance via proxy server...',
    };
    if (proxyStatus === 'offline') return {
      color: '#7f1d1d', icon: WifiOff,
      msg: '⚠ Proxy offline — showing mock data. Run: cd trading-terminal/proxy-server && node server.js',
    };
    return null; // online — no banner
  };

  const banner = getBanner();

  return (
    <div className="trading-terminal" style={{ backgroundColor: 'var(--bg-primary)', display: 'flex', flexDirection: 'column', height: '100vh' }}>

      {/* Status Banner */}
      {banner && showBanner && (
        <div className="flex items-center justify-between px-4 py-2"
          style={{ backgroundColor: banner.color, color: '#fff', flexShrink: 0 }}>
          <div className="flex items-center gap-2">
            <banner.icon className="w-4 h-4" />
            <span className="text-sm font-medium">{banner.msg}</span>
          </div>
          <button onClick={() => setShowBanner(false)}
            className="text-xs px-3 py-1 rounded hover:bg-white/10 transition-colors">
            Dismiss
          </button>
        </div>
      )}

      {/* Header — gets live prices from priceStore */}
      <Header backendStatus={proxyStatus === 'online' ? 'connected' : 'disconnected'} />

      {/* Main layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Watchlist — gets live prices from priceStore */}
        <Watchlist />

        {/* Chart — fetches Binance candles directly */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <ChartPanel />
          <SignalPanel />
        </div>

        {/* Live Signal Panel — real Binance signal engine */}
        <div style={{
          width: 340, overflowY: 'auto', flexShrink: 0,
          borderLeft: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
        }}>
          <LiveSignalPanel />
        </div>
      </div>

      {/* Bottom Panel */}
      <BottomPanel />
    </div>
  );
}

export default App;
