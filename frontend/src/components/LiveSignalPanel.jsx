import React, { useState, useEffect, useCallback, useRef } from 'react';
import { fetchLiveSignal, fetchTicker24 } from '../services/marketApi';
import { useChartStore } from '../stores/chartStore';
import { usePriceStore } from '../stores/priceStore';

const SYMBOLS   = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];
const INTERVALS = ['1m', '5m', '15m', '1h', '4h'];
// Recalculate signal at most every 15s when price ticks arrive
const SIGNAL_THROTTLE_MS = 15000;

function Badge({ signal }) {
  const cfg = {
    BUY:  { bg: '#10b981', label: '▲ BUY' },
    SELL: { bg: '#ef4444', label: '▼ SELL' },
    HOLD: { bg: '#f59e0b', label: '◆ HOLD' },
  }[signal] || { bg: '#78716c', label: '— —' };
  return (
    <span style={{
      background: cfg.bg, color: '#fff',
      padding: '5px 18px', borderRadius: 6,
      fontWeight: 800, fontSize: 16, letterSpacing: 2,
    }}>
      {cfg.label}
    </span>
  );
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #1e293b' }}>
      <span style={{ color: '#64748b', fontSize: 11 }}>{label}</span>
      <span style={{ color: color || '#e2e8f0', fontSize: 11, fontWeight: 600 }}>{value ?? '—'}</span>
    </div>
  );
}

export default function LiveSignalPanel() {
  const { symbol: chartSymbol } = useChartStore();
  const { prices } = usePriceStore();

  const [symbol,    setSymbol]    = useState(chartSymbol || 'BTCUSDT');
  const [interval,  setInterval]  = useState('15m');
  const [signal,    setSignal]    = useState(null);
  const [ticker,    setTicker]    = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);

  const lastSignalTime = useRef(0);
  const fallbackTimer  = useRef(null);

  // Sync symbol with chart when user clicks watchlist
  useEffect(() => { setSymbol(chartSymbol); }, [chartSymbol]);

  const refresh = useCallback(async (sym, intv) => {
    setLoading(true);
    setError(null);
    try {
      const [sig, tick] = await Promise.all([
        fetchLiveSignal(sym, intv),
        fetchTicker24(sym),
      ]);
      setSignal(sig);
      setTicker(tick);
      setUpdatedAt(new Date());
      lastSignalTime.current = Date.now();
    } catch {
      setError('Fetch failed — retrying...');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load on symbol / interval change + 30s fallback timer
  useEffect(() => {
    refresh(symbol, interval);
    clearInterval(fallbackTimer.current);
    fallbackTimer.current = setInterval(() => refresh(symbol, interval), 30000);
    return () => clearInterval(fallbackTimer.current);
  }, [symbol, interval, refresh]);

  // Recalculate signal when WebSocket price ticks arrive (throttled)
  const livePrice  = prices[symbol]?.price;
  const liveChange = prices[symbol]?.change;

  useEffect(() => {
    if (!livePrice) return;
    if (Date.now() - lastSignalTime.current >= SIGNAL_THROTTLE_MS) {
      refresh(symbol, interval);
    }
  }, [livePrice]); // eslint-disable-line

  const fmt = (n, d = 2) =>
    n != null
      ? parseFloat(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
      : '—';

  const changeColor = liveChange != null
    ? liveChange >= 0 ? '#10b981' : '#ef4444'
    : '#94a3b8';

  return (
    <div style={{ padding: 16, fontFamily: 'monospace', color: '#e2e8f0', minHeight: '100%' }}>

      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: '#3b82f6', letterSpacing: 1 }}>
          ⚡ LIVE SIGNAL ENGINE
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            backgroundColor: error ? '#ef4444' : loading ? '#f59e0b' : '#10b981',
            boxShadow: (!error && !loading) ? '0 0 6px #10b981' : 'none',
          }} />
          <span style={{ fontSize: 9, color: '#475569' }}>
            {error ? 'ERROR' : loading ? 'FETCHING' : 'LIVE'}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        <select value={symbol} onChange={e => setSymbol(e.target.value)}
          style={{ flex: 1, background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 5, padding: '5px 6px', fontSize: 11 }}>
          {SYMBOLS.map(s => <option key={s}>{s}</option>)}
        </select>
        <select value={interval} onChange={e => setInterval(e.target.value)}
          style={{ background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 5, padding: '5px 6px', fontSize: 11 }}>
          {INTERVALS.map(i => <option key={i}>{i}</option>)}
        </select>
        <button onClick={() => refresh(symbol, interval)} disabled={loading}
          style={{ background: '#3b82f6', color: '#fff', border: 'none', borderRadius: 5, padding: '5px 10px', fontSize: 12, cursor: 'pointer', opacity: loading ? 0.5 : 1 }}>
          ↻
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 5, padding: 8, marginBottom: 10, fontSize: 10, color: '#fca5a5' }}>
          ⚠ {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !signal && (
        <div style={{ textAlign: 'center', padding: '30px 0', color: '#475569', fontSize: 12 }}>
          <div style={{ marginBottom: 8 }}>Fetching {symbol}...</div>
          <div style={{ fontSize: 10 }}>Calculating EMA · RSI · ATR</div>
        </div>
      )}

      {/* Live price — from WebSocket priceStore (updates every ~1s) */}
      {livePrice && (
        <div style={{ textAlign: 'center', marginBottom: 14, padding: '10px 0', borderBottom: '1px solid #1e293b' }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: '#f1f5f9' }}>
            ${fmt(livePrice, livePrice > 100 ? 2 : 4)}
          </div>
          <div style={{ fontSize: 12, color: changeColor, marginTop: 3 }}>
            {liveChange != null ? `${liveChange >= 0 ? '+' : ''}${fmt(liveChange, 2)}%` : ''}
            {ticker && (
              <span style={{ color: '#64748b' }}>
                &nbsp;·&nbsp; Vol {parseFloat(ticker.volume).toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Signal */}
      {signal && (
        <>
          <div style={{ textAlign: 'center', marginBottom: 14 }}>
            <Badge signal={signal.signal} />
            <div style={{ marginTop: 8, fontSize: 11, color: '#94a3b8' }}>
              Confidence &nbsp;
              <span style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14 }}>{signal.confidence}%</span>
              {signal.source === 'client' && (
                <span style={{ marginLeft: 6, fontSize: 9, color: '#f59e0b' }}>(offline mode)</span>
              )}
            </div>
          </div>

          {/* Indicators */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 9, color: '#475569', letterSpacing: 1, marginBottom: 4, textTransform: 'uppercase' }}>Indicators</div>
            <Row label="EMA 20"     value={`$${fmt(signal.ema20, 2)}`} />
            <Row label="EMA 50"     value={`$${fmt(signal.ema50, 2)}`} />
            <Row label="RSI (14)"   value={fmt(signal.rsi, 1)}
              color={signal.rsi > 70 ? '#ef4444' : signal.rsi < 30 ? '#10b981' : '#e2e8f0'} />
            <Row label="ATR (14)"   value={fmt(signal.atr, 2)} />
            <Row label="Swing High" value={`$${fmt(signal.swingHigh, 2)}`} color="#ef4444" />
            <Row label="Swing Low"  value={`$${fmt(signal.swingLow, 2)}`}  color="#10b981" />
          </div>

          {/* Trade levels */}
          {signal.signal !== 'HOLD' && signal.stopLoss && (
            <div style={{ background: '#0f172a', borderRadius: 6, padding: 10, marginBottom: 12 }}>
              <div style={{ fontSize: 9, color: '#475569', letterSpacing: 1, marginBottom: 6, textTransform: 'uppercase' }}>Trade Levels</div>
              <Row label="Entry"       value={`$${fmt(signal.currentPrice, 2)}`} color="#3b82f6" />
              <Row label="Stop Loss"   value={`$${fmt(signal.stopLoss, 2)}`}     color="#ef4444" />
              <Row label="Take Profit" value={`$${fmt(signal.takeProfit, 2)}`}   color="#10b981" />
              <Row label="Risk:Reward" value="1 : 2"                             color="#f59e0b" />
            </div>
          )}

          {/* Reasoning */}
          <div style={{ background: '#0f172a', borderRadius: 6, padding: 10 }}>
            <div style={{ fontSize: 9, color: '#475569', letterSpacing: 1, marginBottom: 6, textTransform: 'uppercase' }}>Analysis</div>
            {signal.reasoning.map((r, i) => (
              <div key={i} style={{ fontSize: 10, color: '#94a3b8', padding: '2px 0' }}>• {r}</div>
            ))}
          </div>
        </>
      )}

      {/* Footer */}
      <div style={{ fontSize: 9, color: '#334155', display: 'flex', justifyContent: 'space-between', marginTop: 10 }}>
        <span>{updatedAt ? `Signal: ${updatedAt.toLocaleTimeString()}` : ''}</span>
        <span style={{ color: '#10b981' }}>⚡ Price: WebSocket</span>
      </div>
      <div style={{ marginTop: 4, fontSize: 9, color: '#1e293b', textAlign: 'center' }}>
        Binance Public API · No key required
      </div>
    </div>
  );
}
