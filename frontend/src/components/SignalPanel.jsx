import React, { useEffect, useState, useRef } from 'react';
import { useSignalStore, useAlertStore } from '../stores';
import { useChartStore } from '../stores/chartStore';
import { usePriceStore } from '../stores/priceStore';
import { useRiskStore } from '../stores';
import { fetchLiveSignal, fetchCandles } from '../services/marketApi';
import { Copy, CheckCircle, X, TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';

// ── Derive MTF bias by fetching signals for 4 timeframes ─────────────────────
const MTF_TIMEFRAMES = ['4h', '1h', '15m', '5m'];

function deriveRegime(signal) {
  if (!signal) return { status: 'UNKNOWN', color: 'yellow', icon: '⚪' };
  if (signal.signal === 'BUY'  && signal.confidence >= 70) return { status: 'TRENDING UP',   color: 'green',  icon: '🟢' };
  if (signal.signal === 'SELL' && signal.confidence >= 70) return { status: 'TRENDING DOWN',  color: 'red',    icon: '🔴' };
  if (signal.confidence >= 60) return { status: 'RANGING',       color: 'yellow', icon: '🟡' };
  return { status: 'CONSOLIDATING', color: 'yellow', icon: '⚪' };
}

const SignalPanel = () => {
  const { activeSignal, signalHistory, setActiveSignal, addHistoricalSignal } = useSignalStore();
  const { addAlert } = useAlertStore();
  const { symbol, timeframe } = useChartStore();
  const { prices } = usePriceStore();
  const { balance, riskPerTrade, currentRisk } = useRiskStore();

  const [loading,    setLoading]    = useState(false);
  const [mtfBias,    setMtfBias]    = useState([]);
  const [mtfLoading, setMtfLoading] = useState(false);
  const [updatedAt,  setUpdatedAt]  = useState(null);
  const isFetching = useRef(false);
  const timerRef   = useRef(null);
  const symbolRef  = useRef(symbol);
  const tfRef      = useRef(timeframe);
  symbolRef.current = symbol;
  tfRef.current     = timeframe;

  // ── Fetch main signal ──────────────────────────────────────────────────
  const doFetch = async () => {
    if (isFetching.current) return;
    isFetching.current = true;
    setLoading(true);
    try {
      const sig = await fetchLiveSignal(symbolRef.current, tfRef.current);
      setActiveSignal(sig);
      setUpdatedAt(new Date());
      // Add to history if high confidence
      if (sig && sig.signal !== 'HOLD' && sig.confidence >= 60) {
        addHistoricalSignal({
          id:        Date.now(),
          time:      Date.now(),
          symbol:    symbolRef.current,
          type:      sig.signal,
          timeframe: tfRef.current.toUpperCase(),
          entry:     sig.entry ?? sig.currentPrice ?? 0,
          sl:        sig.stopLoss ?? 0,
          tp:        sig.takeProfit ?? 0,
          rr:        sig.riskReward ?? 2,
          score:     sig.confidence ?? 0,
          ml:        sig.source === 'ml' ? sig.confidence : 0,
          status:    'ACTIVE',
          pnl:       0,
          r_multiple: 0,
        });
        addAlert({
          type: 'signal',
          severity: sig.signal === 'BUY' ? 'success' : 'error',
          symbol: symbolRef.current,
          message: `${sig.signal} Signal — Confidence: ${sig.confidence}%`,
        });
      }
    } catch (e) {
      console.error('SignalPanel fetch error:', e);
    } finally {
      setLoading(false);
      isFetching.current = false;
    }
  };

  // ── Fetch MTF bias ─────────────────────────────────────────────────────
  const fetchMTF = async () => {
    setMtfLoading(true);
    try {
      const results = await Promise.allSettled(
        MTF_TIMEFRAMES.map(tf => fetchLiveSignal(symbolRef.current, tf))
      );
      const biases = MTF_TIMEFRAMES.map((tf, i) => {
        const r = results[i];
        if (r.status !== 'fulfilled') return { timeframe: tf.toUpperCase(), bias: 'NEUTRAL', strength: 50, direction: 'neutral' };
        const s = r.value;
        const direction = s.signal === 'BUY' ? 'up' : s.signal === 'SELL' ? 'down' : 'neutral';
        const bias      = s.signal === 'BUY' ? 'BULLISH' : s.signal === 'SELL' ? 'BEARISH' : 'NEUTRAL';
        return { timeframe: tf.toUpperCase(), bias, strength: s.confidence ?? 50, direction };
      });
      setMtfBias(biases);
    } catch (e) {
      console.error('MTF fetch error:', e);
    } finally {
      setMtfLoading(false);
    }
  };

  // ── Poll every 60s, re-fetch on symbol/timeframe change ────────────────
  useEffect(() => {
    doFetch();
    fetchMTF();
    timerRef.current = setInterval(() => { doFetch(); fetchMTF(); }, 60000);
    return () => clearInterval(timerRef.current);
  }, [symbol, timeframe]); // eslint-disable-line

  // ── Derived values ─────────────────────────────────────────────────────
  const signal   = activeSignal;
  const regime   = deriveRegime(signal);
  const livePrice = prices[symbol]?.price ?? 0;

  // Stats from signal history
  const todayStart = new Date(); todayStart.setHours(0,0,0,0);
  const todaySignals = (signalHistory || []).filter(s => s.time >= todayStart.getTime());
  const wonToday     = todaySignals.filter(s => s.status === 'TP HIT');
  const winRate      = todaySignals.length > 0 ? Math.round((wonToday.length / todaySignals.length) * 100) : 0;
  const pnlR         = todaySignals.reduce((acc, s) => acc + (s.r_multiple || 0), 0);
  const drawdown     = Math.min(0, ...todaySignals.map(s => s.r_multiple || 0));

  // Risk meter: % of daily loss limit used
  const riskUsed = currentRisk ?? 35;

  const copyToClipboard = (text) => navigator.clipboard.writeText(String(text));

  const formatTime = (ts) => {
    if (!ts) return '—';
    const ms = typeof ts === 'string' ? new Date(ts).getTime() : ts;
    const minutes = Math.floor((Date.now() - ms) / 60000);
    return minutes < 60 ? `${minutes} min ago` : `${Math.floor(minutes / 60)} hr ago`;
  };

  const fmt = (n, d = 2) => n != null ? parseFloat(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—';

  // Normalise signal fields (ML API uses different keys than client fallback)
  const entry      = signal?.entry      ?? signal?.currentPrice ?? 0;
  const stopLoss   = signal?.stopLoss   ?? signal?.stop_loss    ?? 0;
  const takeProfit = signal?.takeProfit ?? signal?.take_profit  ?? signal?.target ?? 0;
  const rr         = signal?.riskReward ?? signal?.rr_ratio     ?? signal?.risk_reward ?? 2;
  const confidence = signal?.confidence ?? 0;
  const sigType    = signal?.signal     ?? signal?.type         ?? 'HOLD';
  const reasons    = signal?.reasoning  ?? signal?.reasons      ?? [];
  const mlConf     = signal?.source === 'ml' ? confidence : (signal?.ml_confidence ?? 0);

  return (
    <div className="signal-panel-root border-l border-[var(--border)] flex flex-col overflow-y-auto" style={{ backgroundColor: 'var(--bg-secondary)' }}>

      {/* ── Refresh button ── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '6px 12px 0' }}>
        <button onClick={() => { doFetch(); fetchMTF(); }} disabled={loading}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', opacity: loading ? 0.4 : 1, display: 'flex', alignItems: 'center', gap: 4, fontSize: 10 }}>
          <RefreshCw style={{ width: 11, height: 11, animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          {updatedAt ? updatedAt.toLocaleTimeString() : 'Loading...'}
        </button>
      </div>

      {/* ── Active Signal Card ── */}
      {loading && !signal ? (
        <div data-testid="scanning-state" className="m-3 p-8 text-center rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <div className="w-16 h-16 border-4 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>SCANNING MARKET...</div>
          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{symbol} · {timeframe}</div>
        </div>
      ) : signal ? (
        <div data-testid="active-signal-card" className="m-3 rounded-lg overflow-hidden" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          {/* Header */}
          <div className="p-3 flex items-center justify-between"
            style={{ backgroundColor: sigType === 'BUY' ? 'var(--accent-green)' : sigType === 'SELL' ? 'var(--accent-red)' : 'var(--text-muted)' }}>
            <div className="flex items-center gap-2">
              {sigType === 'BUY'  ? <TrendingUp   className="w-5 h-5 text-white" /> :
               sigType === 'SELL' ? <TrendingDown  className="w-5 h-5 text-white" /> :
                                    <Minus         className="w-5 h-5 text-white" />}
              <span className="font-semibold text-white">{sigType} SIGNAL</span>
            </div>
            <span className="text-xs text-white opacity-80">
              {signal.source === 'ml' ? '🤖 ML' : '📐 EMA/RSI'}
            </span>
          </div>

          <div className="p-3">
            <div className="flex items-center justify-between mb-3">
              <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{symbol} · {timeframe.toUpperCase()}</span>
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{formatTime(signal.timestamp)}</span>
            </div>

            {/* Live price */}
            {livePrice > 0 && (
              <div className="text-xs mb-3 monospace" style={{ color: 'var(--text-secondary)' }}>
                Live: <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>${fmt(livePrice)}</span>
              </div>
            )}

            {/* Confidence */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Confidence</span>
                <span className="text-xs font-bold" style={{ color: confidence >= 75 ? 'var(--accent-green)' : confidence >= 60 ? 'var(--accent-yellow)' : 'var(--accent-red)' }}>
                  {confidence}%{confidence >= 75 && <span style={{ marginLeft: 4, fontSize: 9 }}>✓ HIGH</span>}
                </span>
              </div>
              <div className="w-full h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${confidence}%`, backgroundColor: confidence >= 75 ? 'var(--accent-green)' : confidence >= 60 ? 'var(--accent-yellow)' : 'var(--accent-red)' }} />
              </div>
            </div>

            {/* Trade Levels */}
            {sigType !== 'HOLD' && (
              <div className="space-y-2 mb-4">
                {[
                  { label: 'Entry',  value: entry,      color: 'var(--text-primary)',  key: 'entry' },
                  { label: 'Stop',   value: stopLoss,   color: 'var(--accent-red)',    key: 'sl' },
                  { label: 'Target', value: takeProfit, color: 'var(--accent-green)',  key: 'tp' },
                ].map(({ label, value, color, key }) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                    <div className="flex items-center gap-2">
                      <span className="monospace font-semibold" style={{ color }}>${fmt(value)}</span>
                      <button onClick={() => copyToClipboard(value)} className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors">
                        <Copy className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} />
                      </button>
                    </div>
                  </div>
                ))}
                <div className="flex items-center justify-between text-sm">
                  <span style={{ color: 'var(--text-secondary)' }}>R:R</span>
                  <span className="monospace font-semibold" style={{ color: 'var(--text-primary)' }}>1 : {parseFloat(rr).toFixed(1)}</span>
                </div>
              </div>
            )}

            {/* ML Info */}
            <div className="space-y-2 mb-4 p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center gap-2 text-sm">
                <span>🤖</span>
                <span style={{ color: 'var(--text-secondary)' }}>ML:</span>
                <span className="font-semibold" style={{ color: mlConf >= 60 ? 'var(--accent-green)' : 'var(--text-secondary)' }}>
                  {mlConf > 0 ? `✓ ${mlConf}%` : 'Offline — EMA/RSI'}
                </span>
              </div>
              {signal.source === 'ml' && signal.xgbPred && (
                <>
                  <div className="flex items-center gap-2 text-xs">
                    <span style={{ color: 'var(--text-secondary)', width: 90 }}>XGBoost:</span>
                    <span style={{ color: signal.xgbPred === 'BUY' ? 'var(--accent-green)' : signal.xgbPred === 'SELL' ? 'var(--accent-red)' : 'var(--text-secondary)', fontWeight: 700 }}>{signal.xgbPred}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span style={{ color: 'var(--text-secondary)', width: 90 }}>Random Forest:</span>
                    <span style={{ color: signal.rfPred === 'BUY' ? 'var(--accent-green)' : signal.rfPred === 'SELL' ? 'var(--accent-red)' : 'var(--text-secondary)', fontWeight: 700 }}>{signal.rfPred}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span style={{ color: 'var(--text-secondary)', width: 90 }}>SMC Filter:</span>
                    <span style={{ color: signal.smcPred === 'BUY' ? 'var(--accent-green)' : signal.smcPred === 'SELL' ? 'var(--accent-red)' : 'var(--text-secondary)', fontWeight: 700 }}>{signal.smcPred}</span>
                  </div>
                </>
              )}
            </div>

            {/* Reasons */}
            {reasons.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>WHY THIS SIGNAL:</div>
                <div className="space-y-1">
                  {reasons.map((reason, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: 'var(--accent-green)' }} />
                      <span style={{ color: 'var(--text-primary)' }}>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button data-testid="take-trade-button" className="flex-1 py-2 text-sm font-medium rounded transition-colors" style={{ backgroundColor: 'var(--accent-green)', color: 'white' }}>
                ✓ TAKE TRADE
              </button>
              <button data-testid="skip-trade-button" onClick={() => setActiveSignal(null)}
                className="flex-1 py-2 text-sm font-medium rounded transition-colors flex items-center justify-center gap-1"
                style={{ backgroundColor: 'var(--bg-hover)', color: 'var(--text-primary)' }}>
                <X className="w-4 h-4" /> SKIP
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div data-testid="scanning-state" className="m-3 p-8 text-center rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <div className="w-16 h-16 border-4 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>SCANNING MARKET...</div>
          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{symbol} · {timeframe}</div>
        </div>
      )}

      {/* ── MTF Bias ── */}
      <div className="mx-3 mb-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>MTF BIAS</span>
          {mtfLoading && <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>updating...</span>}
        </div>
        <div className="space-y-2">
          {(mtfBias.length > 0 ? mtfBias : [
            { timeframe: '4H', bias: '—', strength: 50, direction: 'neutral' },
            { timeframe: '1H', bias: '—', strength: 50, direction: 'neutral' },
            { timeframe: '15M', bias: '—', strength: 50, direction: 'neutral' },
            { timeframe: '5M', bias: '—', strength: 50, direction: 'neutral' },
          ]).map((bias) => (
            <div key={bias.timeframe}>
              <div className="flex items-center justify-between mb-1 text-xs">
                <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{bias.timeframe}</span>
                <div className="flex items-center gap-1">
                  <span className="font-semibold" style={{ color: bias.direction === 'up' ? 'var(--accent-green)' : bias.direction === 'down' ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
                    {bias.bias}
                  </span>
                  {bias.direction === 'up'      && <TrendingUp   className="w-3 h-3" style={{ color: 'var(--accent-green)' }} />}
                  {bias.direction === 'down'    && <TrendingDown  className="w-3 h-3" style={{ color: 'var(--accent-red)' }} />}
                  {bias.direction === 'neutral' && <Minus         className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} />}
                </div>
              </div>
              <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="h-full rounded-full"
                  style={{ width: `${bias.strength}%`, backgroundColor: bias.direction === 'up' ? 'var(--accent-green)' : bias.direction === 'down' ? 'var(--accent-red)' : 'var(--text-secondary)' }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Market Regime ── */}
      <div className="mx-3 mb-3 p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>MARKET REGIME</div>
        <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full" style={{ backgroundColor: 'var(--bg-secondary)' }}>
          <span>{regime.icon}</span>
          <span className="text-sm font-semibold" style={{ color: `var(--accent-${regime.color})` }}>{regime.status}</span>
        </div>
      </div>

      {/* ── Today's Stats ── */}
      <div className="mx-3 mb-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>TODAY'S STATS</div>
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{todaySignals.length}</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Signals</div>
          </div>
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--accent-green)' }}>{winRate}%</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Win %</div>
          </div>
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: pnlR >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {pnlR >= 0 ? '+' : ''}{pnlR.toFixed(1)}R
            </div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>P&L</div>
          </div>
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--accent-red)' }}>{drawdown.toFixed(1)}%</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>DD</div>
          </div>
        </div>
      </div>

      {/* ── Risk Meter ── */}
      <div className="mx-3 mb-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>RISK METER</div>
        <div className="relative w-32 h-32 mx-auto">
          <svg className="transform -rotate-90" width="128" height="128">
            <circle cx="64" cy="64" r="56" stroke="var(--bg-secondary)" strokeWidth="12" fill="none" />
            <circle cx="64" cy="64" r="56"
              stroke={riskUsed < 40 ? 'var(--accent-green)' : riskUsed < 70 ? 'var(--accent-yellow)' : 'var(--accent-red)'}
              strokeWidth="12" fill="none"
              strokeDasharray={`${(riskUsed / 100) * 352} 352`}
              strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{riskUsed}%</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Used</div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default SignalPanel;
