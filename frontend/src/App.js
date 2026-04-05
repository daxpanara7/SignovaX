import React, { useEffect, useState, useRef, useCallback } from 'react';
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
import { fetchMultiplePrices, checkProxyHealth } from './services/marketApi';

const WATCHED = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];
const PRICE_INTERVAL_MS = 3000; // refresh prices every 3 seconds

function App() {
  const [proxyOnline, setProxyOnline] = useState(false);
  const pollRef = useRef(null);

  const { updatePrices, setConnectionStatus } = usePriceStore();

  // ── Poll Binance prices directly (no proxy needed) ───────────────────────
  const pollPrices = useCallback(async () => {
    try {
      const map = await fetchMultiplePrices(WATCHED);
      if (Object.keys(map).length > 0) {
        updatePrices(map);
        setConnectionStatus(true);
      }
    } catch {
      // Binance unreachable — don't flip connection status on single failure
    }
  }, [updatePrices, setConnectionStatus]);

  useEffect(() => {
    // Immediate first fetch
    pollPrices();
    // Then every 3 seconds
    pollRef.current = setInterval(pollPrices, PRICE_INTERVAL_MS);
    return () => clearInterval(pollRef.current);
  }, [pollPrices]);

  // ── Check proxy health (for signal engine only) ──────────────────────────
  useEffect(() => {
    const check = async () => {
      const ok = await checkProxyHealth();
      setProxyOnline(ok);
    };
    check();
    const id = setInterval(check, 15000); // recheck every 15s
    return () => clearInterval(id);
  }, []);

  return (
    <div
      className="trading-terminal"
      style={{
        backgroundColor: 'var(--bg-primary)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
      }}
    >
      {/* Header — live prices from priceStore (Binance) */}
      <Header backendStatus="connected" proxyOnline={proxyOnline} />

      {/* Main layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Watchlist — live prices from priceStore */}
        <Watchlist />

        {/* Chart — fetches Binance candles directly */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <ChartPanel />
          <SignalPanel />
        </div>

        {/* Live Signal Panel */}
        <div style={{
          width: 340,
          flexShrink: 0,
          overflowY: 'auto',
          borderLeft: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
        }}>
          <LiveSignalPanel />
        </div>
      </div>

      <BottomPanel />
    </div>
  );
}

export default App;
