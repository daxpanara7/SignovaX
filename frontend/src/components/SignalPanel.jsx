import React from 'react';
import { useSignalStore } from '../stores';
import { mockActiveSignal, mockMTFBias, mockMarketRegime, mockQuickStats, mockRiskMeter } from '../data/mockData';
import { Copy, CheckCircle, X, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const SignalPanel = () => {
  const { activeSignal, scanning } = useSignalStore();
  const signal = activeSignal || mockActiveSignal;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const formatTime = (timestamp) => {
    const minutes = Math.floor((Date.now() - timestamp) / 60000);
    return minutes < 60 ? `${minutes} min ago` : `${Math.floor(minutes / 60)} hr ago`;
  };

  return (
    <div className="w-70 border-l border-[var(--border)] flex flex-col overflow-y-auto" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      {/* Active Signal Card */}
      {signal ? (
        <div data-testid="active-signal-card" className="m-3 rounded-lg overflow-hidden" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          {/* Header */}
          <div className="p-3 flex items-center justify-between" style={{ backgroundColor: signal.type === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            <div className="flex items-center gap-2">
              {signal.type === 'BUY' ? <TrendingUp className="w-5 h-5 text-white" /> : <TrendingDown className="w-5 h-5 text-white" />}
              <span className="font-semibold text-white">{signal.type} SIGNAL</span>
            </div>
          </div>

          <div className="p-3">
            <div className="flex items-center justify-between mb-3">
              <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{signal.symbol || 'N/A'} • {signal.timeframe || 'N/A'}</span>
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{formatTime(signal.timestamp || Date.now())}</span>
            </div>
            <div className="text-xs mb-3" style={{ color: 'var(--text-secondary)' }}>{signal.session || 'Unknown Session'}</div>

            {/* Confluence Score */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Confluence Score</span>
                <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>{signal.confluence_score || 0}/100</span>
              </div>
              <div className="w-full h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${signal.confluence_score || 0}%`,
                    backgroundColor: (signal.confluence_score || 0) >= 80 ? 'var(--accent-green)' : (signal.confluence_score || 0) >= 60 ? 'var(--accent-yellow)' : 'var(--accent-red)'
                  }}
                ></div>
              </div>
            </div>

            {/* Trade Levels */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: 'var(--text-secondary)' }}>Entry</span>
                <div className="flex items-center gap-2">
                  <span className="monospace font-semibold" style={{ color: 'var(--text-primary)' }}>${(signal.entry || 0).toFixed(2)}</span>
                  <button onClick={() => copyToClipboard((signal.entry || 0).toString())} className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors">
                    <Copy className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: 'var(--text-secondary)' }}>Stop</span>
                <div className="flex items-center gap-2">
                  <span className="monospace font-semibold" style={{ color: 'var(--accent-red)' }}>${(signal.stop_loss || 0).toFixed(2)}</span>
                  <button onClick={() => copyToClipboard((signal.stop_loss || 0).toString())} className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors">
                    <Copy className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: 'var(--text-secondary)' }}>Target</span>
                <div className="flex items-center gap-2">
                  <span className="monospace font-semibold" style={{ color: 'var(--accent-green)' }}>${(signal.take_profit || 0).toFixed(2)}</span>
                  <button onClick={() => copyToClipboard((signal.take_profit || 0).toString())} className="p-1 rounded hover:bg-[var(--bg-hover)] transition-colors">
                    <Copy className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: 'var(--text-secondary)' }}>R:R</span>
                <span className="monospace font-semibold" style={{ color: 'var(--text-primary)' }}>1 : {(signal.risk_reward || 0).toFixed(1)}</span>
              </div>
            </div>

            {/* ML & Risk Info */}
            <div className="space-y-2 mb-4 p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center gap-2 text-sm">
                <span>🤖</span>
                <span style={{ color: 'var(--text-secondary)' }}>ML Filter:</span>
                <span className="font-semibold" style={{ color: 'var(--accent-green)' }}>✓ {signal.ml_confidence || 0}%</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span>📐</span>
                <span style={{ color: 'var(--text-secondary)' }}>Risk:</span>
                <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>${signal.risk_amount || 0} ({signal.risk_percent || 0}%)</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span>📊</span>
                <span style={{ color: 'var(--text-secondary)' }}>Size:</span>
                <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{signal.position_size || 0} BTC</span>
              </div>
            </div>

            {/* Reasons */}
            <div className="mb-4">
              <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>WHY THIS SIGNAL:</div>
              <div className="space-y-1">
                {(signal.reasons || []).map((reason, index) => (
                  <div key={index} className="flex items-start gap-2 text-xs">
                    <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: 'var(--accent-green)' }} />
                    <span style={{ color: 'var(--text-primary)' }}>{reason}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button data-testid="take-trade-button" className="flex-1 py-2 text-sm font-medium rounded transition-colors" style={{ backgroundColor: 'var(--accent-green)', color: 'white' }}>
                ✓ TAKE TRADE
              </button>
              <button data-testid="skip-trade-button" className="flex-1 py-2 text-sm font-medium rounded transition-colors flex items-center justify-center gap-1" style={{ backgroundColor: 'var(--bg-hover)', color: 'var(--text-primary)' }}>
                <X className="w-4 h-4" /> SKIP
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div data-testid="scanning-state" className="m-3 p-8 text-center rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <div className="w-16 h-16 border-4 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>SCANNING MARKET...</div>
          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Last scan: 2 minutes ago</div>
        </div>
      )}

      {/* MTF Bias */}
      <div className="mx-3 mb-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>MTF BIAS</div>
        <div className="space-y-2">
          {mockMTFBias.map((bias) => (
            <div key={bias.timeframe}>
              <div className="flex items-center justify-between mb-1 text-xs">
                <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{bias.timeframe}</span>
                <div className="flex items-center gap-1">
                  <span className="font-semibold" style={{ color: bias.direction === 'up' ? 'var(--accent-green)' : bias.direction === 'down' ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
                    {bias.bias}
                  </span>
                  {bias.direction === 'up' && <TrendingUp className="w-3 h-3" style={{ color: 'var(--accent-green)' }} />}
                  {bias.direction === 'down' && <TrendingDown className="w-3 h-3" style={{ color: 'var(--accent-red)' }} />}
                  {bias.direction === 'neutral' && <Minus className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} />}
                </div>
              </div>
              <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${bias.strength}%`,
                    backgroundColor: bias.direction === 'up' ? 'var(--accent-green)' : bias.direction === 'down' ? 'var(--accent-red)' : 'var(--text-secondary)'
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Market Regime */}
      <div className="mx-3 mb-3 p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>MARKET REGIME</div>
        <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full" style={{ backgroundColor: 'var(--bg-secondary)' }}>
          <span>{mockMarketRegime.icon}</span>
          <span className="text-sm font-semibold" style={{ color: `var(--accent-${mockMarketRegime.color})` }}>{mockMarketRegime.status}</span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="mx-3 mb-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>TODAY'S STATS</div>
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{mockQuickStats.signals_today}</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Signals</div>
          </div>
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--accent-green)' }}>{mockQuickStats.win_rate}%</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Win %</div>
          </div>
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--accent-green)' }}>+{mockQuickStats.pnl_r}R</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>P&L</div>
          </div>
          <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xl font-bold mb-1" style={{ color: 'var(--accent-red)' }}>{mockQuickStats.drawdown}%</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>DD</div>
          </div>
        </div>
      </div>

      {/* Risk Meter */}
      <div className="mx-3 mb-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="text-xs font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>RISK METER</div>
        <div className="relative w-32 h-32 mx-auto">
          <svg className="transform -rotate-90" width="128" height="128">
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="var(--bg-secondary)"
              strokeWidth="12"
              fill="none"
            />
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke={mockRiskMeter.current < 40 ? 'var(--accent-green)' : mockRiskMeter.current < 70 ? 'var(--accent-yellow)' : 'var(--accent-red)'}
              strokeWidth="12"
              fill="none"
              strokeDasharray={`${(mockRiskMeter.current / 100) * 352} 352`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{mockRiskMeter.current}%</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Used</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignalPanel;