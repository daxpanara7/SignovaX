import React, { useState } from 'react';
import { mockHistoricalTrades, mockBacktestResults, mockEquityCurve, mockAlerts } from '../data/mockData';
import { Download, Play, Filter } from 'lucide-react';

const BottomPanel = () => {
  const [activeTab, setActiveTab] = useState('signals');
  const [backtestRunning, setBacktestRunning] = useState(false);
  const [backtestResults, setBacktestResults] = useState(null);

  const tabs = [
    { id: 'signals', label: 'Signals' },
    { id: 'backtest', label: 'Backtest' },
    { id: 'performance', label: 'Performance' },
    { id: 'journal', label: 'Journal' },
    { id: 'alerts', label: 'Alerts' },
  ];

  const runBacktest = () => {
    setBacktestRunning(true);
    setTimeout(() => {
      setBacktestResults(mockBacktestResults);
      setBacktestRunning(false);
    }, 3000);
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}`;
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${months[date.getMonth()]} ${date.getDate()}, ${hours}:${minutes}`;
  };

  return (
    <div className="bottom-panel-root border-t border-[var(--border)] flex flex-col" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      {/* Tab Navigation */}
      <div className="flex items-center gap-1 px-4 pt-2" data-testid="bottom-panel-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            data-testid={`tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className="px-4 py-2 text-sm font-medium rounded-t transition-colors"
            style={{
              backgroundColor: activeTab === tab.id ? 'var(--bg-tertiary)' : 'transparent',
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent-blue)' : 'none'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {/* Signals Tab */}
        {activeTab === 'signals' && (
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between p-3 border-b border-[var(--border)]">
              <div className="flex items-center gap-2">
                <button data-testid="filter-all" className="px-3 py-1 text-xs rounded" style={{ backgroundColor: 'var(--accent-blue)', color: 'white' }}>All</button>
                <button data-testid="filter-active" className="px-3 py-1 text-xs rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Active</button>
                <button data-testid="filter-won" className="px-3 py-1 text-xs rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Won</button>
                <button data-testid="filter-lost" className="px-3 py-1 text-xs rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Lost</button>
              </div>
              <button data-testid="export-csv" className="flex items-center gap-1 px-3 py-1 text-xs rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
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
                  {mockHistoricalTrades.map((trade) => (
                    <tr
                      key={trade.id}
                      data-testid={`signal-row-${trade.id}`}
                      className="border-b border-[var(--border)] hover:bg-[var(--bg-hover)] cursor-pointer transition-colors"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      <td className="p-2">{formatTime(trade.time)}</td>
                      <td className="p-2 font-medium">{trade.symbol}</td>
                      <td className="p-2">
                        <span
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: trade.type === 'BUY' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            color: trade.type === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)'
                          }}
                        >
                          {trade.type}
                        </span>
                      </td>
                      <td className="p-2">{trade.timeframe}</td>
                      <td className="p-2 text-right monospace">${trade.entry.toLocaleString()}</td>
                      <td className="p-2 text-right monospace">${trade.sl.toLocaleString()}</td>
                      <td className="p-2 text-right monospace">${trade.tp.toLocaleString()}</td>
                      <td className="p-2 text-right monospace">{trade.rr.toFixed(1)}</td>
                      <td className="p-2 text-right">{trade.score}</td>
                      <td className="p-2 text-right">{trade.ml}%</td>
                      <td className="p-2">
                        <span
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: trade.status === 'TP HIT' ? 'rgba(16, 185, 129, 0.2)' : trade.status === 'SL HIT' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                            color: trade.status === 'TP HIT' ? 'var(--accent-green)' : trade.status === 'SL HIT' ? 'var(--accent-red)' : 'var(--accent-blue)'
                          }}
                        >
                          {trade.status}
                        </span>
                      </td>
                      <td className="p-2 text-right monospace font-semibold" style={{ color: trade.pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Backtest Tab */}
        {activeTab === 'backtest' && (
          <div className="h-full flex">
            <div className="w-1/3 p-4 border-r border-[var(--border)] space-y-3">
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Symbol</label>
                <select data-testid="backtest-symbol" className="w-full px-3 py-2 text-sm rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                  <option>BTCUSDT</option>
                  <option>ETHUSDT</option>
                  <option>EURUSD</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Timeframe</label>
                <select data-testid="backtest-timeframe" className="w-full px-3 py-2 text-sm rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                  <option>15m</option>
                  <option>1h</option>
                  <option>4h</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Initial Balance</label>
                <input data-testid="backtest-balance" type="number" defaultValue={10000} className="w-full px-3 py-2 text-sm rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }} />
              </div>
              <div>
                <label className="block text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Risk % per trade: 1%</label>
                <input data-testid="backtest-risk-slider" type="range" min="0.5" max="3" step="0.1" defaultValue="1" className="w-full" />
              </div>
              <button
                data-testid="run-backtest-button"
                onClick={runBacktest}
                disabled={backtestRunning}
                className="w-full py-2.5 text-sm font-medium rounded flex items-center justify-center gap-2 transition-colors"
                style={{ backgroundColor: 'var(--accent-blue)', color: 'white', opacity: backtestRunning ? 0.6 : 1 }}
              >
                <Play className="w-4 h-4" />
                {backtestRunning ? 'Running...' : 'RUN BACKTEST'}
              </button>
              {backtestRunning && (
                <div className="text-xs text-center" style={{ color: 'var(--text-secondary)' }}>Analyzing 847 candles...</div>
              )}
            </div>
            <div className="flex-1 p-4">
              {backtestResults ? (
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { label: 'Return', value: `+${backtestResults.return}%`, color: 'var(--accent-green)' },
                    { label: 'Win Rate', value: `${backtestResults.win_rate}%`, color: 'var(--text-primary)' },
                    { label: 'Sharpe', value: backtestResults.sharpe.toFixed(2), color: 'var(--text-primary)' },
                    { label: 'Max DD', value: `${backtestResults.max_dd}%`, color: 'var(--accent-red)' },
                    { label: 'Trades', value: backtestResults.trades, color: 'var(--text-primary)' },
                    { label: 'P.Factor', value: backtestResults.profit_factor.toFixed(2), color: 'var(--text-primary)' },
                    { label: 'Expectancy', value: `+${backtestResults.expectancy}R`, color: 'var(--accent-green)' },
                    { label: 'Calmar', value: backtestResults.calmar.toFixed(2), color: 'var(--text-primary)' },
                  ].map((metric, index) => (
                    <div key={index} data-testid={`backtest-metric-${metric.label.toLowerCase().replace(/\s/g, '-')}`} className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <div className="text-2xl font-bold mb-1" style={{ color: metric.color }}>{metric.value}</div>
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{metric.label}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-center">
                  <div>
                    <div className="text-4xl mb-2">📊</div>
                    <div className="text-sm mb-1" style={{ color: 'var(--text-primary)' }}>Configure and run your first backtest</div>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Select parameters and click Run Backtest</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className="h-full p-4">
            <div className="mb-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Equity Curve</span>
                <div className="flex items-center gap-2">
                  {['1W', '1M', '3M', 'ALL'].map((period) => (
                    <button
                      key={period}
                      className="px-2 py-1 text-xs rounded"
                      style={{ backgroundColor: period === '1M' ? 'var(--accent-blue)' : 'var(--bg-tertiary)', color: period === '1M' ? 'white' : 'var(--text-secondary)' }}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-[200px] flex items-center justify-center text-center" style={{ backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                <div>
                  <div className="text-4xl mb-2">\ud83d\udcc8</div>
                  <div className="text-sm" style={{ color: 'var(--text-primary)' }}>Equity Curve Chart</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Chart visualization coming soon</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Journal Tab */}
        {activeTab === 'journal' && (
          <div className="h-full flex">
            <div className="w-2/5 border-r border-[var(--border)] overflow-y-auto p-3 space-y-2">
              {mockHistoricalTrades.slice(0, 6).map((trade) => (
                <div
                  key={trade.id}
                  data-testid={`journal-entry-${trade.id}`}
                  className="p-3 rounded cursor-pointer hover:bg-[var(--bg-hover)] transition-colors"
                  style={{ backgroundColor: 'var(--bg-tertiary)' }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{formatTime(trade.time)}</span>
                    <span
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{
                        backgroundColor: trade.type === 'BUY' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: trade.type === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)'
                      }}
                    >
                      {trade.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{trade.symbol}</span>
                    <span className="font-semibold monospace" style={{ color: trade.pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl} ({trade.r_multiple.toFixed(1)}R)
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex-1 p-4 flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-2">📋</div>
                <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>Select a trade to view details</div>
              </div>
            </div>
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="h-full flex">
            <div className="flex-1 p-4 space-y-2 overflow-y-auto">
              {mockAlerts.map((alert) => (
                <div
                  key={alert.id}
                  data-testid={`alert-${alert.id}`}
                  className="flex items-start gap-3 p-3 rounded-lg"
                  style={{ backgroundColor: 'var(--bg-tertiary)' }}
                >
                  <span className="text-xl">
                    {alert.severity === 'success' && '🟢'}
                    {alert.severity === 'error' && '🔴'}
                    {alert.severity === 'warning' && '🟡'}
                  </span>
                  <div className="flex-1">
                    <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{formatTime(alert.time)}</div>
                    <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                      {alert.symbol && <span className="font-semibold">{alert.symbol} — </span>}
                      {alert.message}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="w-80 border-l border-[var(--border)] p-4">
              <div className="text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Alert Settings</div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Telegram Alerts</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--bg-hover)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 left-0.5 transition-all" style={{ backgroundColor: 'var(--text-muted)' }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Email Alerts</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--bg-hover)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 left-0.5 transition-all" style={{ backgroundColor: 'var(--text-muted)' }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Browser Notifications</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--accent-blue)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 right-0.5 transition-all" style={{ backgroundColor: 'white' }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Sound Alerts</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--accent-blue)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 right-0.5 transition-all" style={{ backgroundColor: 'white' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BottomPanel;