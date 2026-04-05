import React, { useState } from 'react';
import { X } from 'lucide-react';
import { useRiskStore } from '../../stores';

const SettingsModal = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('risk');
  const { balance, riskPerTrade, maxDailyLoss, minRR, maxConcurrentTrades, circuitBreaker, mlFilter, mlThreshold } = useRiskStore();

  const tabs = [
    { id: 'risk', label: 'Risk' },
    { id: 'display', label: 'Display' },
    { id: 'data', label: 'Data' },
    { id: 'notifications', label: 'Notifications' }
  ];

  return (
    <div data-testid="settings-modal" className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }} onClick={onClose}>
      <div
        className="w-full max-w-3xl rounded-lg shadow-2xl"
        style={{ backgroundColor: 'var(--bg-secondary)', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Settings</h2>
          <button data-testid="close-settings" onClick={onClose} className="p-1 rounded hover:bg-[var(--bg-hover)]" style={{ color: 'var(--text-secondary)' }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 px-4 pt-3 border-b border-[var(--border)]">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              data-testid={`settings-tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className="px-4 py-2 text-sm font-medium rounded-t transition-colors"
              style={{
                backgroundColor: activeTab === tab.id ? 'var(--bg-tertiary)' : 'transparent',
                color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'risk' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Account Balance</label>
                <input
                  data-testid="settings-balance-input"
                  type="number"
                  defaultValue={balance}
                  className="w-full px-4 py-2.5 rounded border-0"
                  style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                  Risk per trade: {riskPerTrade}% (${(balance * riskPerTrade / 100).toFixed(2)})
                </label>
                <input
                  data-testid="settings-risk-slider"
                  type="range"
                  min="0.5"
                  max="3"
                  step="0.1"
                  defaultValue={riskPerTrade}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                  Max daily loss: {maxDailyLoss}%
                </label>
                <input
                  data-testid="settings-max-loss-slider"
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  defaultValue={maxDailyLoss}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                  Min R:R ratio: {minRR}
                </label>
                <input
                  data-testid="settings-min-rr-slider"
                  type="range"
                  min="1"
                  max="3"
                  step="0.1"
                  defaultValue={minRR}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Max concurrent trades</label>
                <input
                  data-testid="settings-max-trades-input"
                  type="number"
                  min="1"
                  max="5"
                  defaultValue={maxConcurrentTrades}
                  className="w-full px-4 py-2.5 rounded border-0"
                  style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Circuit Breaker</span>
                <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: circuitBreaker ? 'var(--accent-blue)' : 'var(--bg-hover)' }}>
                  <div
                    className="w-5 h-5 rounded-full absolute top-0.5 transition-all"
                    style={{
                      backgroundColor: 'white',
                      left: circuitBreaker ? 'calc(100% - 22px)' : '2px'
                    }}
                  ></div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>ML Filter</span>
                <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: mlFilter ? 'var(--accent-blue)' : 'var(--bg-hover)' }}>
                  <div
                    className="w-5 h-5 rounded-full absolute top-0.5 transition-all"
                    style={{
                      backgroundColor: 'white',
                      left: mlFilter ? 'calc(100% - 22px)' : '2px'
                    }}
                  ></div>
                </div>
              </div>
              {mlFilter && (
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                    ML Threshold: {mlThreshold}%
                  </label>
                  <input
                    data-testid="settings-ml-threshold-slider"
                    type="range"
                    min="50"
                    max="80"
                    step="1"
                    defaultValue={mlThreshold}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          )}

          {activeTab === 'display' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>Theme</label>
                <div className="flex items-center gap-3">
                  <button className="px-4 py-2 rounded" style={{ backgroundColor: 'var(--accent-blue)', color: 'white' }}>Dark</button>
                  <button className="px-4 py-2 rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Light</button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>Chart Style</label>
                <div className="flex items-center gap-3">
                  <button className="px-4 py-2 rounded" style={{ backgroundColor: 'var(--accent-blue)', color: 'white' }}>Candles</button>
                  <button className="px-4 py-2 rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Bars</button>
                  <button className="px-4 py-2 rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Line</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>Data Source</label>
                <select className="w-full px-4 py-2.5 rounded border-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                  <option>Binance</option>
                  <option>Mock Data</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>API Key (Binance)</label>
                <input
                  type="password"
                  placeholder="Enter API key"
                  className="w-full px-4 py-2.5 rounded border-0"
                  style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>API Secret (Binance)</label>
                <input
                  type="password"
                  placeholder="Enter API secret"
                  className="w-full px-4 py-2.5 rounded border-0"
                  style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                />
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Telegram Alerts</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--bg-hover)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 left-0.5 transition-all" style={{ backgroundColor: 'white' }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Email Alerts</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--bg-hover)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 left-0.5 transition-all" style={{ backgroundColor: 'white' }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Browser Notifications</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--accent-blue)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 right-0.5 transition-all" style={{ backgroundColor: 'white' }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Sound Alerts</span>
                  <div className="w-11 h-6 rounded-full relative cursor-pointer" style={{ backgroundColor: 'var(--accent-blue)' }}>
                    <div className="w-5 h-5 rounded-full absolute top-0.5 right-0.5 transition-all" style={{ backgroundColor: 'white' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-[var(--border)]">
          <button
            data-testid="cancel-settings"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium rounded"
            style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
          >
            Cancel
          </button>
          <button
            data-testid="save-settings"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium rounded"
            style={{ backgroundColor: 'var(--accent-blue)', color: 'white' }}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;