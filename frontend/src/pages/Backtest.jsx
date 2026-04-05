import React, { useState, useEffect } from 'react'
import { Play, BarChart3, TrendingUp, TrendingDown, Calendar, DollarSign } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { backtestAPI, marketDataAPI } from '../services/api'

const Backtest = () => {
  const [backtestResult, setBacktestResult] = useState(null)
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [backtestDays, setBacktestDays] = useState(30)
  const [initialCapital, setInitialCapital] = useState(10000)
  const [symbols, setSymbols] = useState([])
  const [timeframes, setTimeframes] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      const [symbolsResponse, timeframesResponse] = await Promise.all([
        marketDataAPI.getSymbols(),
        marketDataAPI.getTimeframes()
      ])
      
      const allSymbols = [
        ...symbolsResponse.data.crypto,
        ...symbolsResponse.data.forex
      ]
      
      setSymbols(allSymbols)
      setTimeframes(timeframesResponse.data.timeframes)
    } catch (error) {
      console.error('Failed to load initial data:', error)
    }
  }

  const runBacktest = async () => {
    try {
      setLoading(true)
      const response = await backtestAPI.quickBacktest(
        selectedSymbol,
        selectedTimeframe,
        backtestDays
      )
      setBacktestResult(response.data)
    } catch (error) {
      console.error('Backtest failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const MetricCard = ({ title, value, subtitle, icon: Icon, color = 'blue' }) => {
    const colorClasses = {
      blue: 'text-blue-600 bg-blue-50',
      green: 'text-green-600 bg-green-50',
      red: 'text-red-600 bg-red-50',
      yellow: 'text-yellow-600 bg-yellow-50'
    }

    return (
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {subtitle && (
              <p className="text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
          <div className={`p-3 rounded-full ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </div>
    )
  }

  const prepareEquityData = (trades) => {
    if (!trades || trades.length === 0) return []
    
    let equity = initialCapital
    const equityData = [{ trade: 0, equity, cumulative_pnl: 0 }]
    
    trades.forEach((trade, index) => {
      const pnlAmount = (equity * trade.pnl_percent) / 100
      equity += pnlAmount
      equityData.push({
        trade: index + 1,
        equity: equity,
        cumulative_pnl: ((equity - initialCapital) / initialCapital) * 100,
        pnl: trade.pnl_percent
      })
    })
    
    return equityData
  }

  const prepareTradeDistribution = (trades) => {
    if (!trades || trades.length === 0) return []
    
    const ranges = [
      { range: '< -5%', min: -Infinity, max: -5, count: 0 },
      { range: '-5% to -2%', min: -5, max: -2, count: 0 },
      { range: '-2% to 0%', min: -2, max: 0, count: 0 },
      { range: '0% to 2%', min: 0, max: 2, count: 0 },
      { range: '2% to 5%', min: 2, max: 5, count: 0 },
      { range: '> 5%', min: 5, max: Infinity, count: 0 }
    ]
    
    trades.forEach(trade => {
      const pnl = trade.pnl_percent
      ranges.forEach(range => {
        if (pnl > range.min && pnl <= range.max) {
          range.count++
        }
      })
    })
    
    return ranges
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Strategy Backtesting</h1>
        <p className="text-gray-600">Test SMC strategy performance on historical data</p>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Symbol
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="select-field"
            >
              {symbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timeframe
            </label>
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="select-field"
            >
              {timeframes.map(tf => (
                <option key={tf.value} value={tf.value}>{tf.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Period (Days)
            </label>
            <select
              value={backtestDays}
              onChange={(e) => setBacktestDays(Number(e.target.value))}
              className="select-field"
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
              <option value={60}>60 Days</option>
              <option value={90}>90 Days</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Initial Capital
            </label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="input-field"
              min="1000"
              step="1000"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={runBacktest}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              <Play className="h-4 w-4" />
              <span>{loading ? 'Running...' : 'Run Backtest'}</span>
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {backtestResult && !loading && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Return"
              value={`${backtestResult.backtest_result.total_pnl.toFixed(2)}%`}
              subtitle={`$${(initialCapital * (1 + backtestResult.backtest_result.total_pnl / 100)).toFixed(0)}`}
              icon={DollarSign}
              color={backtestResult.backtest_result.total_pnl >= 0 ? 'green' : 'red'}
            />
            <MetricCard
              title="Win Rate"
              value={`${backtestResult.backtest_result.win_rate.toFixed(1)}%`}
              subtitle={`${backtestResult.backtest_result.winning_trades}/${backtestResult.backtest_result.total_trades} trades`}
              icon={TrendingUp}
              color="blue"
            />
            <MetricCard
              title="Max Drawdown"
              value={`${backtestResult.backtest_result.max_drawdown.toFixed(2)}%`}
              icon={TrendingDown}
              color="red"
            />
            <MetricCard
              title="Profit Factor"
              value={backtestResult.quick_stats.profit_factor.toFixed(2)}
              subtitle={`Best: ${backtestResult.quick_stats.best_trade.toFixed(1)}%`}
              icon={BarChart3}
              color="yellow"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Equity Curve */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={prepareEquityData(backtestResult.backtest_result.trade_logs)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="trade" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      name === 'equity' ? `$${value.toFixed(0)}` : `${value.toFixed(2)}%`,
                      name === 'equity' ? 'Equity' : 'Cumulative P&L'
                    ]}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="equity" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Trade Distribution */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade P&L Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={prepareTradeDistribution(backtestResult.backtest_result.trade_logs)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade Log */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Trades</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Exit Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P&L %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Exit Reason
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {backtestResult.backtest_result.trade_logs.slice(-10).reverse().map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(trade.entry_time).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          trade.signal_type === 'BUY' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.signal_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${trade.entry_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${trade.exit_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={trade.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.exit_reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Backtest