import React, { useState, useEffect, useCallback } from 'react';
import { fetchLiveSignal, fetchLivePrice, fetchTicker24 } from '../services/marketApi';

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];
const INTERVALS = ['5m', '15m', '1h', '4h'];

function SignalBadge({ signal }) {
  const colors = {
    BUY:  { bg: '#10b981', text: '#fff', label: '▲ BUY' },
    SELL: { bg: '#ef4444', text: '#fff', label: '▼ SELL' },
    HOLD: { bg: '#f59e0b', text: '#000', label: '◆ HOLD' },
  };
  const cfg = colors[signal] || colors.HOLD;
  return (
    <span
      style={{
        backgroundColor: cfg.bg,
        color: cfg.text,
        padding: '4px 14px',
        borderRadius: 6,
        fontWeight: 700,
        fontSize: 15,
        letterSpacing: 1,
      }}
    >
      {cfg.label}
    </span>
  );
}

function MetricRow({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #1e293b' }}>
      <span style={{ color: '#94a3b8', fontSize: 12 }}>{label}</span>
      <span style={{ color: color || '#e2e8f0', fontSize: 12, fontWeight: 600 }}>{value}</span>
    </div>
  );
}

export default function LiveSignalPanel() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('15m');
  const [signalData, setSignalData] = useState(null);
  const [priceData, setPriceData] = useState(null);
  const [ticker, setTicker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sig, price, tick] = await Promise.all([
        fetchLiveSignal(symbol, interval),
        fetchLivePrice(symbol),
        fetchTicker24(symbol),
      ]);
      setSignalData(sig);
      setPriceData(price);
      setTicker(tick);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [symbol, interval]);

  // Initial load + symbol/interval change
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto-refresh every 30s
  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(refresh, 30000);
    return () => clearInterval(id);
  }, [autoRefresh, refresh]);

  const fmt = (n, decimals = 2) =>
    n != null ? parseFloat(n).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : '—';

  const changeColor = ticker
    ? parseFloat(ticker.priceChangePercent) >= 0 ? '#10b981' : '#ef4444'
    : '#94a3b8';

  return (
    <div
      style={{
        backgroundColor: '#0d1117',
        border: '1px solid #1e293b',
        borderRadius: 10,
        padding: 20,
        minWidth: 320,
        maxWidth: 400,
        fontFamily: 'monospace',
        color: '#e2e8f0',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#3b82f6', letterSpacing: 1 }}>
          ⚡ LIVE SIGNAL ENGINE
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <div
            style={{
              width: 8, height: 8, borderRadius: '50%',
              backgroundColor: error ? '#ef4444' : loading ? '#f59e0b' : '#10b981',
            }}
          />
          <span style={{ fontSize: 10, color: '#64748b' }}>
            {error ? 'ERROR' : loading ? 'LOADING' : 'LIVE'}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          style={{
            flex: 1, backgroundColor: '#1e293b', color: '#e2e8f0',
            border: '1px solid #334155', borderRadius: 6, padding: '6px 8px', fontSize: 12,
          }}
        >
          {SYMBOLS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
          style={{
            backgroundColor: '#1e293b', color: '#e2e8f0',
            border: '1px solid #334155', borderRadius: 6, padding: '6px 8px', fontSize: 12,
          }}
        >
          {INTERVALS.map((i) => <option key={i} value={i}>{i}</option>)}
        </select>
        <button
          onClick={refresh}
          disabled={loading}
          style={{
            backgroundColor: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: 6, padding: '6px 12px', fontSize: 12, cursor: 'pointer',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? '...' : '↻'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ backgroundColor: '#450a0a', border: '1px solid #ef4444', borderRadius: 6, padding: 10, marginBottom: 12, fontSize: 11, color: '#fca5a5' }}>
          ⚠ {error}
          <div style={{ marginTop: 4, color: '#94a3b8' }}>Make sure proxy server is running on port 4000</div>
        </div>
      )}

      {/* Price */}
      {priceData && (
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9' }}>
            ${fmt(priceData.price, 2)}
          </div>
          {ticker && (
            <div style={{ fontSize: 13, color: changeColor, marginTop: 2 }}>
              {parseFloat(ticker.priceChangePercent) >= 0 ? '+' : ''}
              {fmt(ticker.priceChangePercent, 2)}% (24h)
              &nbsp;·&nbsp; Vol: {parseFloat(ticker.volume).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </div>
          )}
        </div>
      )}

      {/* Signal */}
      {signalData && (
        <>
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <SignalBadge signal={signalData.signal} />
            <div style={{ marginTop: 8, fontSize: 12, color: '#94a3b8' }}>
              Confidence: <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{signalData.confidence}%</span>
            </div>
          </div>

          {/* Metrics */}
          <div style={{ marginBottom: 14 }}>
            <MetricRow label="EMA 20" value={fmt(signalData.ema20, 2)} />
            <MetricRow label="EMA 50" value={fmt(signalData.ema50, 2)} />
            <MetricRow label="RSI (14)" value={fmt(signalData.rsi, 1)}
              color={signalData.rsi > 70 ? '#ef4444' : signalData.rsi < 30 ? '#10b981' : '#e2e8f0'} />
            <MetricRow label="ATR (14)" value={fmt(signalData.atr, 2)} />
            <MetricRow label="Swing High" value={fmt(signalData.swingHigh, 2)} color="#ef4444" />
            <MetricRow label="Swing Low" value={fmt(signalData.swingLow, 2)} color="#10b981" />
          </div>

          {/* Trade levels */}
          {signalData.signal !== 'HOLD' && (
            <div style={{ backgroundColor: '#0f172a', borderRadius: 8, padding: 12, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
                Trade Levels
              </div>
              <MetricRow label="Entry" value={`$${fmt(signalData.currentPrice, 2)}`} color="#3b82f6" />
              <MetricRow label="Stop Loss" value={`$${fmt(signalData.stopLoss, 2)}`} color="#ef4444" />
              <MetricRow label="Take Profit" value={`$${fmt(signalData.takeProfit, 2)}`} color="#10b981" />
              <MetricRow label="Risk:Reward" value={`1:${signalData.riskReward}`} color="#f59e0b" />
            </div>
          )}

          {/* Reasoning */}
          <div style={{ backgroundColor: '#0f172a', borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 11, color: '#64748b', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
              Analysis
            </div>
            {signalData.reasoning.map((r, i) => (
              <div key={i} style={{ fontSize: 11, color: '#94a3b8', padding: '2px 0' }}>
                • {r}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Footer */}
      <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 10, color: '#475569' }}>
          {lastUpdated ? `Updated: ${lastUpdated.toLocaleTimeString()}` : ''}
        </div>
        <label style={{ fontSize: 10, color: '#475569', display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            style={{ cursor: 'pointer' }}
          />
          Auto-refresh (30s)
        </label>
      </div>

      {/* Data source attribution */}
      <div style={{ marginTop: 8, fontSize: 9, color: '#334155', textAlign: 'center' }}>
        Data: Binance Public API · Proxy: localhost:4000
      </div>
    </div>
  );
}
