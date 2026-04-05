import React, { useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { TrendingUp, TrendingDown, Target, DollarSign, Activity, AlertTriangle, Download } from 'lucide-react'
import { useBacktestStore } from '../stores/backtestStore'

const PerformancePanel = () => {
  const [activeTab, setActiveTab] = useState('metrics')
  const { currentResults, formatCurrency, formatPercentage } = useBacktestStore()

  const tabs = [
    { id: 'metrics', label: 'Metrics', icon: Activity },
    { id: 'equity', label: 'Equity Curve', icon: TrendingUp },
    { id: 'montecarlo', label: 'Monte Carlo', icon: Target },
    { id: 'trades', label: 'Trade Log', icon: DollarSign }
  ]

  const MetricCard = ({ title, value, change, icon: Icon, color = 'text-dark-text' }) => (
    <div className="bg-dark-bg border border-dark-border rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        {change !== undefined && (
          <span className={`text-xs ${change >= 0 ? 'text-bull' : 'text-bear'}`}>
            {change >= 0 ? '+' : ''}{change}%
          </span>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-xs text-dark-muted">{title}</p>
        <p className={`text-lg font-bold ${color}`}>{value}</p>
      </div>
    </div>
  )

  const renderMetricsTab = () => {
    if (!currentResults) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Activity className="w-12 h-12 text-dark-muted mx-auto mb-3" />
            <p className="text-dark-muted">No backtest results available</p>
            <p className="text-xs text-dark-muted mt-1">Run a backtest to see performance metrics</p>
          </div>
        </div>
      )
    }

    const metrics = currentResults.metrics || {}

    return (
      <div className="grid grid-cols-2 gap-3 h-full overflow-y-auto">
        <MetricCard
          title="Win Rate"
          value={formatPercentage(metrics.win_rate || 0)}
          change={5.2}
          icon={Target}
          color={metrics.win_rate >= 50 ? 'text-bull' : 'text-bear'}
        />
        <MetricCard
          title="Profit Factor"
          value={(metrics.profit_factor || 0).toFixed(2)}
          change={-2.1}
          icon={TrendingUp}
          color={metrics.profit_factor >= 1.5 ? 'text-bull' : 'text-bear'}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={(metrics.sharpe_ratio || 0).toFixed(2)}
          icon={Activity}
          color={metrics.sharpe_ratio >= 1 ? 'text-bull' : 'text-bear'}
        />
        <MetricCard
          title="Max Drawdown"
          value={formatPercentage(metrics.max_drawdown || 0)}
          icon={AlertTriangle}
          color="text-bear"
        />
        <MetricCard
          title="Total Return"
          value={formatPercentage(metrics.total_return_percent || 0)}
          change={metrics.total_return_percent}
          icon={DollarSign}
          color={metrics.total_return_percent >= 0 ? 'text-bull' : 'text-bear'}
        />
        <MetricCard
          title="Expectancy"
          value={formatCurrency(metrics.expectancy || 0)}
          icon={Target}
          color={metrics.expectancy >= 0 ? 'text-bull' : 'text-bear'}
        />
        <MetricCard
          title="Total Trades"
          value={(metrics.total_trades || 0).toString()}
          icon={Activity}
          color="text-dark-text"
        />
        <MetricCard
          title="Calmar Ratio"
          value={(metrics.calmar_ratio || 0).toFixed(2)}
          icon={TrendingUp}
          color={metrics.calmar_ratio >= 1 ? 'text-bull' : 'text-bear'}
        />
      </div>
    )
  }

  const renderEquityTab = () => {
    if (!currentResults?.equity_curve) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <TrendingUp className="w-12 h-12 text-dark-muted mx-auto mb-3" />
            <p className="text-dark-muted">No equity curve data available</p>
          </div>
        </div>
      )
    }

    const equityData = currentResults.equity_curve.map((point, index) => ({
      index,
      equity: point.equity,
      drawdown: point.drawdown || 0,
      benchmark: point.benchmark || point.equity * 0.8 // Mock benchmark
    }))

    return (
      <div className="h-full space-y-4">
        <div className="h-2/3">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis 
                dataKey="index" 
                stroke="#a3a3a3" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#a3a3a3" 
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #2a2a2a',
                  borderRadius: '8px',
                  color: '#e5e5e5'
                }}
                formatter={(value, name) => [
                  name === 'equity' ? formatCurrency(value) : `$${(value / 1000).toFixed(1)}k`,
                  name === 'equity' ? 'Portfolio' : 'Benchmark'
                ]}
              />
              <Area
                type="monotone"
                dataKey="equity"
                stroke="#00d4aa"
                fill="url(#equityGradient)"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="benchmark"
                stroke="#64748b"
                strokeWidth={1}
                strokeDasharray="5 5"
              />
              <defs>
                <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        <div className="h-1/3">
          <h4 className="text-sm text-dark-muted mb-2">Drawdown</h4>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis 
                dataKey="index" 
                stroke="#a3a3a3" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#a3a3a3" 
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `${value.toFixed(0)}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #2a2a2a',
                  borderRadius: '8px',
                  color: '#e5e5e5'
                }}
                formatter={(value) => [`${value.toFixed(2)}%`, 'Drawdown']}
              />
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#ff6b6b"
                fill="url(#drawdownGradient)"
                strokeWidth={2}
              />
              <defs>
                <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff6b6b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff6b6b" stopOpacity={0} />
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  const renderMonteCarloTab = () => {
    if (!currentResults?.monte_carlo) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Target className="w-12 h-12 text-dark-muted mx-auto mb-3" />
            <p className="text-dark-muted">No Monte Carlo data available</p>
          </div>
        </div>
      )
    }

    // Mock Monte Carlo data
    const monteCarloData = Array.from({ length: 100 }, (_, i) => ({
      index: i,
      p5: 8000 + i * 50 + Math.random() * 1000,
      p25: 9000 + i * 60 + Math.random() * 1000,
      p50: 10000 + i * 70 + Math.random() * 1000,
      p75: 11000 + i * 80 + Math.random() * 1000,
      p95: 12000 + i * 90 + Math.random() * 1000,
    }))

    return (
      <div className="h-full space-y-4">
        <div className="h-3/4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={monteCarloData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis 
                dataKey="index" 
                stroke="#a3a3a3" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#a3a3a3" 
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #2a2a2a',
                  borderRadius: '8px',
                  color: '#e5e5e5'
                }}
              />
              <Area
                type="monotone"
                dataKey="p95"
                stroke="none"
                fill="#00d4aa"
                fillOpacity={0.1}
              />
              <Area
                type="monotone"
                dataKey="p75"
                stroke="none"
                fill="#00d4aa"
                fillOpacity={0.2}
              />
              <Area
                type="monotone"
                dataKey="p25"
                stroke="none"
                fill="#00d4aa"
                fillOpacity={0.2}
              />
              <Area
                type="monotone"
                dataKey="p5"
                stroke="none"
                fill="#00d4aa"
                fillOpacity={0.1}
              />
              <Line
                type="monotone"
                dataKey="p50"
                stroke="#00d4aa"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-dark-bg border border-dark-border rounded-lg p-3 text-center">
            <p className="text-xs text-dark-muted">Worst Case DD</p>
            <p className="text-lg font-bold text-bear">-15.2%</p>
          </div>
          <div className="bg-dark-bg border border-dark-border rounded-lg p-3 text-center">
            <p className="text-xs text-dark-muted">Ruin Probability</p>
            <p className="text-lg font-bold text-warning-500">2.1%</p>
          </div>
          <div className="bg-dark-bg border border-dark-border rounded-lg p-3 text-center">
            <p className="text-xs text-dark-muted">Confidence</p>
            <p className="text-lg font-bold text-bull">95%</p>
          </div>
        </div>
      </div>
    )
  }

  const renderTradesTab = () => {
    if (!currentResults?.trades) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <DollarSign className="w-12 h-12 text-dark-muted mx-auto mb-3" />
            <p className="text-dark-muted">No trade data available</p>
          </div>
        </div>
      )
    }

    const trades = currentResults.trades.slice(0, 20) // Show last 20 trades

    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm text-dark-muted">Recent Trades</h4>
          <button className="flex items-center space-x-1 text-xs text-dark-muted hover:text-dark-text transition-colors">
            <Download className="w-3 h-3" />
            <span>Export CSV</span>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="space-y-2">
            {trades.map((trade, index) => (
              <div
                key={index}
                className={`p-2 rounded border text-xs ${
                  trade.pnl >= 0
                    ? 'bg-bull/10 border-bull/20'
                    : 'bg-bear/10 border-bear/20'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-dark-text">{trade.symbol}</span>
                    <span className={`px-1 rounded text-xs ${
                      trade.type === 'BUY' ? 'bg-bull/20 text-bull' : 'bg-bear/20 text-bear'
                    }`}>
                      {trade.type}
                    </span>
                  </div>
                  <span className={`font-bold ${
                    trade.pnl >= 0 ? 'text-bull' : 'text-bear'
                  }`}>
                    {formatCurrency(trade.pnl)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-dark-muted">
                  <div className="flex space-x-3">
                    <span>Entry: {formatCurrency(trade.entry_price)}</span>
                    <span>Exit: {formatCurrency(trade.exit_price)}</span>
                  </div>
                  <div className="flex space-x-2">
                    <span>R: {trade.r_multiple?.toFixed(1)}</span>
                    <span>{trade.duration}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full bg-dark-surface border border-dark-border rounded-lg flex flex-col">
      {/* Tab Navigation */}
      <div className="flex border-b border-dark-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-1 py-3 px-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-bull border-b-2 border-bull bg-bull/5'
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              <Icon className="w-3 h-3" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 p-4 overflow-hidden">
        {activeTab === 'metrics' && renderMetricsTab()}
        {activeTab === 'equity' && renderEquityTab()}
        {activeTab === 'montecarlo' && renderMonteCarloTab()}
        {activeTab === 'trades' && renderTradesTab()}
      </div>
    </div>
  )
}

export default PerformancePanel