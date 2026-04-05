import React, { useEffect, useState, useRef, useCallback } from 'react';
import './styles/globals.css';
import Header from './components/Header';
import Watchlist from './components/Watchlist';
import ChartPanel from './components/ChartPanel';
import SignalPanel from './components/SignalPanel';
import BottomPanel from './components/BottomPanel';
import LiveSignalPanel from './components/LiveSignalPanel';
import { usePriceStore } from './stores/priceStore';
import { useChartStore } from './stores/chartStore';
import { useBinanceStream } from './hooks/useBinanceStream';
import { fetchMultiplePrices } from './services/marketApi';

const WATCHED = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];

// ── Fallback REST poll (only used when WebSocket fails) ──────────────────────
const FALLBACK_INTERVAL_MS = 2000;

function App() {
  const [wsStatus, setWsStatus] = useState('CONNECTING'); // CONNECTING | LIVE | FALLBACK
  const fallbackRef = useRef(null);

  const { updatePrices, setConnectionStatus } = usePriceStore();
  const { symbol, timeframe } = useChartStore();

  // ── WebSocket handlers ───────────────────────────────────────────────────
  const onTicker = useCallback((sym, data) => {
    // Called on every Binance miniTicker event (~1s per symbol)
    updatePrices({ [sym]: data });
    setConnectionStatus(true);
  }, [updatePrices, setConnectionStatus]);

  const onStatus = useCallback((status) => {
    setWsStatus(status);
    setConnectionStatus(status === 'LIVE');

    if (status === 'FALLBACK') {
      // WebSocket gave up — start REST fallback at 2s
      const poll = async () => {
        try {
          const map = await fetchMultiplePrices(WATCHED);
          updatePrices(map);
        } catch { /* ignore */ }
      };
      poll();
      fallbackRef.current = setInterval(poll, FALLBACK_INTERVAL_MS);
    } else {
      // WebSocket recovered — stop fallback polling
      clearInterval(fallbackRef.current);
    }
  }, [updatePrices]);

  // ── Connect Binance WebSocket ────────────────────────────────────────────
  // onKline is handled inside ChartPanel directly (it has its own stream)
  useBinanceStream(WATCHED, symbol, timeframe, {
    onTicker,
    onStatus,
    // onKline not needed here — ChartPanel manages its own kline stream
  });

  // Cleanup fallback on unmount
  useEffect(() => () => clearInterval(fallbackRef.current), []);

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
      <Header backendStatus="connected" wsStatus={wsStatus} />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Watchlist wsStatus={wsStatus} />

        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <ChartPanel />
          <SignalPanel />
        </div>

        <div style={{
          width: 340, flexShrink: 0,
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
