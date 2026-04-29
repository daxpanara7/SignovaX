import React, { useState, useRef } from 'react';
import { useSignalStore, useAlertStore, useBacktestStore } from '../stores';
import { Download, Play } from 'lucide-react';

const ML_API = process.env.REACT_APP_ML_API_URL || 'http://localhost:8000';

// ── Reusable Toggle switch ────────────────────────────────────────────────────
function Toggle({ on, onChange }) {
  return (
    <div
      onClick={onChange}
      style={{
        width: 44, height: 24, borderRadius: 12, position: 'relative', cursor: 'pointer',
        backgroundColor: on ? 'var(--accent-blue)' : 'var(--bg-hover)',
        transition: 'background-color 0.2s',
        flexShrink: 0,
      }}
    >
      <div style={{
        width: 18, height: 18, borderRadius: '50%',
        backgroundColor: on ? 'white' : 'var(--text-muted)',
        position: 'absolute', top: 3,
        left: on ? 23 : 3,
        transition: 'left 0.2s, background-color 0.2s',
      }} />
    </div>
  );
}

// ── Alerts tab — extracted so it can use its own state ────────────────────────
function AlertsTab({ alerts, markAsRead, formatTime }) {
  const { notifications, updateNotifications } = useAlertStore();
  const [browserPermission, setBrowserPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );

  const toggle = async (key) => {
    const next = !notifications[key];

    // Browser Notifications: request permission when enabling
    if (key === 'browser' && next) {
      if (typeof Notification !== 'undefined' && Notification.permission !== 'granted') {
        const perm = await Notification.requestPermission();
        setBrowserPermission(perm);
        if (perm !== 'granted') return; // don't enable if denied
      }
    }

    // Sound Alerts: play a test beep when enabling
    if (key === 'sound' && next) {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value = 880;
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.3);
      } catch { /* AudioContext not available */ }
    }

    updateNotifications({ ...notifications, [key]: next });
  };

  const SETTINGS = [
    { key: 'telegram', label: 'Telegram Alerts'      },
    { key: 'email',    label: 'Email Alerts'          },
    { key: 'browser',  label: 'Browser Notifications' },
    { key: 'sound',    label: 'Sound Alerts'          },
  ];

  return (
    <div className="h-full flex">
      {/* Alert list */}
      <div className="flex-1 p-4 space-y-2 overflow-y-auto" onClick={markAsRead}>
        {alerts.length > 0 ? alerts.map((alert) => (
          <div key={alert.id} data-testid={`alert-${alert.id}`}
            className="flex items-start gap-3 p-3 rounded-lg"
            style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <span className="text-xl">
              {alert.severity === 'success' ? '🟢' : alert.severity === 'error' ? '🔴' : '🟡'}
            </span>
            <div className="flex-1">
              <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>
                {alert.timestamp ? formatTime(alert.timestamp) : 'Just now'}
              </div>
              <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                {alert.symbol && <span className="font-semibold">{alert.symbol} — </span>}
                {alert.message}
              </div>
            </div>
          </div>
        )) : (
          <div className="text-center p-6" style={{ color: 'var(--text-secondary)' }}>
            <div className="text-3xl mb-2">🔔</div>
            No alerts yet — signals will appear here automatically
          </div>
        )}
      </div>

      {/* Settings panel */}
      <div className="w-80 border-l border-[var(--border)] p-4">
        <div className="text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Alert Settings</div>
        <div className="space-y-3">
          {SETTINGS.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>
              <Toggle on={!!notifications[key]} onChange={() => toggle(key)} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const BottomPanel = () => {
  const [activeTab,    setActiveTab]    = useState('signals');
  const [signalFilter, setSignalFilter] = useState('all');

  // Backtest state
  const { config, results, isRunning, setResults, setRunning, updateConfig } = useBacktestStore();
  const [btSymbol,    setBtSymbol]    = useState(config.symbol    || 'BTCUSDT');
  const [btTimeframe, setBtTimeframe] = useState(config.timeframe || '15m');
  const [btBalance,   setBtBalance]   = useState(config.initial_balance || 10000);
  const [btRisk,      setBtRisk]      = useState(config.risk_per_trade  || 1);
  const [btError,     setBtError]     = useState(null);

  // Signal history from store — only use mock if truly nothing has been generated yet
  const { signalHistory, historicalSignals } = useSignalStore();
  // signalHistory = signals added by SignalPanel during this session (real)
  // historicalSignals = initialized with mock in store — ignore it, use empty array as base
  const allSignals = signalHistory?.length > 0 ? signalHistory : [];

  // Alerts from store
  const { alerts, markAsRead } = useAlertStore();

  const tabs = [
    { id: 'signals',     label: 'Signals'     },
    { id: 'backtest',    label: 'Backtest'     },
    { id: 'performance', label: 'Performance'  },
    { id: 'journal',     label: 'Journal'      },
    { id: 'alerts',      label: 'Alerts'       },
  ];

  const formatTime = (timestamp) => {
    const date = new Date(typeof timestamp === 'string' ? timestamp : timestamp);
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const h = String(date.getHours()).padStart(2,'0');
    const m = String(date.getMinutes()).padStart(2,'0');
    return `${months[date.getMonth()]} ${date.getDate()}, ${h}:${m}`;
  };

  // ── Real backtest via backend ──────────────────────────────────────────
  const runBacktest = async () => {
    setRunning(true);
    setBtError(null);
    try {
      const payload = {
        symbol:          btSymbol,
        timeframe:       btTimeframe,
        initial_capital: parseFloat(btBalance),
        risk_per_trade:  parseFloat(btRisk),
      };
      const res = await fetch(`${ML_API}/api/backtest/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      // Normalise response shape
      setResults({
        return:         data.total_return_pct   ?? data.return         ?? 0,
        win_rate:       data.win_rate            ?? 0,
        sharpe:         data.sharpe_ratio        ?? data.sharpe         ?? 0,
        max_dd:         data.max_drawdown_pct    ?? data.max_dd         ?? 0,
        trades:         data.total_trades        ?? data.trades         ?? 0,
        profit_factor:  data.profit_factor       ?? 0,
        expectancy:     data.expectancy_r        ?? data.expectancy     ?? 0,
        calmar:         data.calmar_ratio        ?? data.calmar         ?? 0,
      });
    } catch (err) {
      console.error('Backtest error:', err);
      setBtError(`Backtest failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  // ── Export signals as CSV ──────────────────────────────────────────────
  const exportCSV = () => {
    const header = 'Time,Symbol,Type,TF,Entry,SL,TP,R:R,Score,ML,Status,P&L\n';
    const rows = allSignals.map(t =>
      `${formatTime(t.time)},${t.symbol},${t.type},${t.timeframe},${t.entry},${t.sl},${t.tp},${t.rr},${t.score},${t.ml},${t.status},${t.pnl}`
    ).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'signals.csv'; a.click();
  };

  // ── Filter signals ─────────────────────────────────────────────────────
  const filteredSignals = allSignals.filter(s => {
    if (signalFilter === 'active') return s.status === 'ACTIVE';
    if (signalFilter === 'won')    return s.status === 'TP HIT';
    if (signalFilter === 'lost')   return s.status === 'SL HIT';
    return true;
  });

  const backtestResults = results;

  return (
    <div className="bottom-panel-root border-t border-[var(--border)] flex flex-col" style={{ backgroundColor: 'var(--bg-secondary)' }}>

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 px-4 pt-2" data-testid="bottom-panel-tabs">
        {tabs.map((tab) => (
          <button key={tab.id} data-testid={`tab-${tab.id}`} onClick={() => setActiveTab(tab.id)}
            className="px-4 py-2 text-sm font-medium rounded-t transition-colors"
            style={{
              backgroundColor: activeTab === tab.id ? 'var(--bg-tertiary)' : 'transparent',
              color:            activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom:     activeTab === tab.id ? '2px solid var(--accent-blue)' : 'none',
            }}>
            {tab.label}
            {tab.id === 'alerts' && alerts.length > 0 && (
              <span style={{ marginLeft: 5, fontSize: 9, padding: '1px 5px', borderRadius: 8, backgroundColor: 'var(--accent-red)', color: 'white' }}>
                {alerts.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">

        {/* ── Signals Tab ── */}
        {activeTab === 'signals' && (
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between p-3 border-b border-[var(--border)]">
              <div className="flex items-center gap-2">
                {[
                  { id: 'all',    label: 'All'    },
                  { id: 'active', label: 'Active' },
                  { id: 'won',    label: 'Won'    },
                  { id: 'lost',   label: 'Lost'   },
                ].map(f => (
                  <button key={f.id} data-testid={`filter-${f.id}`} onClick={() => setSignalFilter(f.id)}
                    className="px-3 py-1 text-xs rounded"
                    style={{ backgroundColor: signalFilter === f.id ? 'var(--accent-blue)' : 'var(--bg-tertiary)', color: signalFilter === f.id ? 'white' : 'var(--text-secondary)' }}>
                    {f.label}
                  </button>
                ))}
              </div>
              <button data-testid="export-csv" onClick={exportCSV}
                className="flex items-center gap-1 px-3 py-1 text-xs rounded"
                style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                <Download className="w-3 h-3" /> Export CSV
              </button>
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                  <tr className="border-b border-[var(--border)]" style={{ color: 'var(--text-secondary)' }}>
                    <th className="text-left p-2 font-medium">Time</th>
                    <th className="text-left p-2 font-medium">Symbol</th>
                    <th className="text-left p-2 font-medium">Type</th>
                    <th className="text-left p-2 font-medium">TF</th>
                    <th className="text-right p-2 font-medium">Entry</th>
                    <th className="text-right p-2 font-medium">SL</th>
                    <th className="text-right p-2 font-medium">TP</th>
                    <th className="text-right p-2 font-medium">R:R</th>
                    <th className="text-right p-2 font-medium">Score</th>
                    <th className="text-right p-2 font-medium">ML</th>
                    <th className="text-left p-2 font-medium">Status</th>
                    <th className="text-right p-2 font-medium">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSignals.map((trade, idx) => (
                    <tr key={trade.id ?? idx} data-testid={`signal-row-${trade.id ?? idx}`}
                      className="border-b border-[var(--border)] hover:bg-[var(--bg-hover)] cursor-pointer transition-colors"
                      style={{ color: 'var(--text-primary)' }}>
                      <td className="p-2">{formatTime(trade.time)}</td>
                      <td className="p-2 font-medium">{trade.symbol}</td>
                      <td className="p-2">
                        <span className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{ backgroundColor: trade.type === 'BUY' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)', color: trade.type === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                          {trade.type}
                        </span>
                      </td>
                      <td className="p-2">{trade.timeframe}</td>
                      <td className="p-2 text-right monospace">${parseFloat(trade.entry || 0).toLocaleString()}</td>
                      <td className="p-2 text-right monospace">${parseFloat(trade.sl   || 0).toLocaleString()}</td>
                      <td className="p-2 text-right monospace">${parseFloat(trade.tp   || 0).toLocaleString()}</td>
                      <td className="p-2 text-right monospace">{parseFloat(trade.rr || 0).toFixed(1)}</td>
                      <td className="p-2 text-right">{trade.score}</td>
                      <td className="p-2 text-right">{trade.ml > 0 ? `${trade.ml}%` : '—'}</td>
                      <td className="p-2">
                        <span className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: trade.status === 'TP HIT' ? 'rgba(16,185,129,0.2)' : trade.status === 'SL HIT' ? 'rgba(239,68,68,0.2)' : 'rgba(59,130,246,0.2)',
                            color:           trade.status === 'TP HIT' ? 'var(--accent-green)'  : trade.status === 'SL HIT' ? 'var(--accent-red)'   : 'var(--accent-blue)',
                          }}>
                          {trade.status}
                        </span>
                      </td>
                      <td className="p-2 text-right monospace font-semibold"
                        style={{ color: (trade.pnl || 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {(trade.pnl || 0) >= 0 ? '+' : ''}${trade.pnl || 0}
                      </td>
                    </tr>
                  ))}
                  {filteredSignals.length === 0 && (
                    <tr><td colSpan={12} className="p-6 text-center" style={{ color: 'var(--text-secondary)' }}>No signals yet — run an analysis to generate signals</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Backtest Tab ── */}
        {activeTab === 'backtest' && (
          <div className="h-full flex">
            <div className="w-1/3 p-4 border-r border-[var(--border)] space-y-3">
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Symbol</label>
                <select data-testid="backtest-symbol" value={btSymbol} onChange={e => setBtSymbol(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                  <option>BTCUSDT</option><option>ETHUSDT</option><option>SOLUSDT</option><option>BNBUSDT</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Timeframe</label>
                <select data-testid="backtest-timeframe" value={btTimeframe} onChange={e => setBtTimeframe(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                  <option>1m</option><option>5m</option><option>15m</option><option>1h</option><option>4h</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Initial Balance ($)</label>
                <input data-testid="backtest-balance" type="number" value={btBalance} onChange={e => setBtBalance(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }} />
              </div>
              <div>
                <label className="block text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Risk % per trade: {btRisk}%</label>
                <input data-testid="backtest-risk-slider" type="range" min="0.5" max="3" step="0.1" value={btRisk}
                  onChange={e => setBtRisk(e.target.value)} className="w-full" />
              </div>
              <button data-testid="run-backtest-button" onClick={runBacktest} disabled={isRunning}
                className="w-full py-2.5 text-sm font-medium rounded flex items-center justify-center gap-2 transition-colors"
                style={{ backgroundColor: 'var(--accent-blue)', color: 'white', opacity: isRunning ? 0.6 : 1 }}>
                <Play className="w-4 h-4" />
                {isRunning ? 'Running...' : 'RUN BACKTEST'}
              </button>
              {isRunning && <div className="text-xs text-center" style={{ color: 'var(--text-secondary)' }}>Fetching candles & running SMC analysis...</div>}
              {btError  && <div className="text-xs text-center" style={{ color: 'var(--accent-red)' }}>{btError}</div>}
            </div>
            <div className="flex-1 p-4">
              {backtestResults ? (
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { label: 'Return',      value: `${backtestResults.return >= 0 ? '+' : ''}${parseFloat(backtestResults.return).toFixed(1)}%`, color: backtestResults.return >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' },
                    { label: 'Win Rate',    value: `${parseFloat(backtestResults.win_rate).toFixed(1)}%`,  color: 'var(--text-primary)' },
                    { label: 'Sharpe',      value: parseFloat(backtestResults.sharpe).toFixed(2),          color: 'var(--text-primary)' },
                    { label: 'Max DD',      value: `${parseFloat(backtestResults.max_dd).toFixed(1)}%`,    color: 'var(--accent-red)' },
                    { label: 'Trades',      value: backtestResults.trades,                                 color: 'var(--text-primary)' },
                    { label: 'P.Factor',    value: parseFloat(backtestResults.profit_factor).toFixed(2),   color: 'var(--text-primary)' },
                    { label: 'Expectancy',  value: `${backtestResults.expectancy >= 0 ? '+' : ''}${parseFloat(backtestResults.expectancy).toFixed(2)}R`, color: 'var(--accent-green)' },
                    { label: 'Calmar',      value: parseFloat(backtestResults.calmar).toFixed(2),          color: 'var(--text-primary)' },
                  ].map((metric, i) => (
                    <div key={i} data-testid={`backtest-metric-${metric.label.toLowerCase().replace(/\s/g,'-')}`}
                      className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <div className="text-2xl font-bold mb-1" style={{ color: metric.color }}>{metric.value}</div>
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{metric.label}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-center">
                  <div>
                    <div className="text-4xl mb-2">📊</div>
                    <div className="text-sm mb-1" style={{ color: 'var(--text-primary)' }}>Configure and run a backtest</div>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Results will appear here</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Performance Tab ── */}
        {activeTab === 'performance' && (
          <div className="h-full p-4">
            <div className="mb-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Equity Curve</span>
                <div className="flex items-center gap-2">
                  {['1W','1M','3M','ALL'].map(p => (
                    <button key={p} className="px-2 py-1 text-xs rounded"
                      style={{ backgroundColor: p === '1M' ? 'var(--accent-blue)' : 'var(--bg-tertiary)', color: p === '1M' ? 'white' : 'var(--text-secondary)' }}>
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-[200px] flex items-center justify-center text-center" style={{ backgroundColor: 'var(--bg-tertiary)', borderRadius: 8 }}>
                <div>
                  <div className="text-4xl mb-2">📈</div>
                  <div className="text-sm" style={{ color: 'var(--text-primary)' }}>Equity Curve Chart</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Run a backtest to see equity curve</div>
                </div>
              </div>
            </div>
            {/* Summary stats from backtest if available */}
            {backtestResults && (
              <div className="grid grid-cols-4 gap-2 mt-3">
                {[
                  { label: 'Total Return', value: `${backtestResults.return >= 0 ? '+' : ''}${parseFloat(backtestResults.return).toFixed(1)}%` },
                  { label: 'Win Rate',     value: `${parseFloat(backtestResults.win_rate).toFixed(1)}%` },
                  { label: 'Max Drawdown', value: `${parseFloat(backtestResults.max_dd).toFixed(1)}%` },
                  { label: 'Total Trades', value: backtestResults.trades },
                ].map((m, i) => (
                  <div key={i} className="p-3 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{m.value}</div>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{m.label}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Journal Tab ── */}
        {activeTab === 'journal' && (
          <div className="h-full flex">
            <div className="w-2/5 border-r border-[var(--border)] overflow-y-auto p-3 space-y-2">
              {filteredSignals.slice(0, 20).map((trade, idx) => (
                <div key={trade.id ?? idx} data-testid={`journal-entry-${trade.id ?? idx}`}
                  className="p-3 rounded cursor-pointer hover:bg-[var(--bg-hover)] transition-colors"
                  style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{formatTime(trade.time)}</span>
                    <span className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{ backgroundColor: trade.type === 'BUY' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)', color: trade.type === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                      {trade.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{trade.symbol}</span>
                    <span className="font-semibold monospace" style={{ color: (trade.pnl || 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                      {(trade.pnl || 0) >= 0 ? '+' : ''}${trade.pnl || 0} ({parseFloat(trade.r_multiple || 0).toFixed(1)}R)
                    </span>
                  </div>
                </div>
              ))}
              {filteredSignals.length === 0 && (
                <div className="text-center p-6" style={{ color: 'var(--text-secondary)' }}>No trades yet</div>
              )}
            </div>
            <div className="flex-1 p-4 flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-2">📋</div>
                <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>Select a trade to view details</div>
              </div>
            </div>
          </div>
        )}

        {/* ── Alerts Tab ── */}
        {activeTab === 'alerts' && (
          <AlertsTab alerts={alerts} markAsRead={markAsRead} formatTime={formatTime} />
        )}

      </div>
    </div>
  );
};

export default BottomPanel;
