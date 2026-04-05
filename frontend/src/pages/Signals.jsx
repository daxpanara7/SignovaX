import React, { useState, useEffect } from 'react'
import { Signal, TrendingUp, TrendingDown, RefreshCw, Target, AlertCircle } from 'lucide-react'
import { signalsAPI, marketDataAPI } from '../services/api'

const Signals = () => {
  const [signals, setSignals] = useState([])
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [minConfidence, setMinConfidence] = useState(70)
  const [symbols, setSymbols] = useState([])
  const [timeframes, setTimeframes] = useState([])
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (selectedSymbol && selectedTimeframe) {
      loadSignals()
    }
  }, [selectedSymbol, selectedTimeframe, minConfidence])

  useEffect(() => {
    let interval
    if (autoRefresh) {
      interval = setInterval(loadSignals, 30000) // Refresh every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh, selectedSymbol, selectedTimeframe, minConfidence])

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

  const loadSignals = async () => {
    try {
      setLoading(true)
      const response = await signalsAPI.generateSignals(
        selectedSymbol,
        selectedTimeframe,
        minConfidence
      )
      setSignals(response.data)
    } catch (error) {
      console.error('Failed to load signals:', error)
      setSignals([])
    } finally {
      setLoading(false)
    }
  }

  const SignalCard = ({ signal }) => {
    const isBuy = signal.signal_type === 'BUY'
    const riskReward = isBuy 
      ? (signal.take_profit - signal.entry_price) / (signal.entry_price - signal.stop_loss)
      : (signal.entry_price - signal.take_profit) / (signal.stop_loss - signal.entry_price)

    return (
      <div className={`border-l-4 ${isBuy ? 'border-green-500' : 'border-red-500'} bg-white rounded-lg shadow-sm p-6`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            {isBuy ? (
              <TrendingUp className="h-6 w-6 text-green-600" />
            ) : (
              <TrendingDown className="h-6 w-6 text-red-600" />
            )}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {signal.signal_type} {signal.symbol}
              </h3>
              <p className="text-sm text-gray-600">{signal.timeframe}</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              signal.confidence >= 80 
                ? 'bg-green-100 text-green-800'
                : signal.confidence >= 70
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {signal.confidence.toFixed(0)}% Confidence
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Entry Price</p>
            <p className="text-lg font-semibold text-gray-900">
              ${signal.entry_price.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Stop Loss</p>
            <p className="text-lg font-semibold text-red-600">
              ${signal.stop_loss.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Take Profit</p>
            <p className="text-lg font-semibold text-green-600">
              ${signal.take_profit.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Risk:Reward</p>
            <p className="text-lg font-semibold text-blue-600">
              1:{riskReward.toFixed(1)}
            </p>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Reasoning:</span> {signal.reasoning}
          </p>
        </div>

        <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
          <span>Generated: {new Date(signal.timestamp).toLocaleString()}</span>
          <span className="flex items-center space-x-1">
            <Target className="h-3 w-3" />
            <span>SMC Strategy</span>
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trading Signals</h1>
          <p className="text-gray-600">Smart Money Concepts based trading signals</p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span>Auto Refresh</span>
          </label>
          <button
            onClick={loadSignals}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              Min Confidence
            </label>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
              className="select-field"
            >
              <option value={60}>60%</option>
              <option value={70}>70%</option>
              <option value={80}>80%</option>
              <option value={90}>90%</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={loadSignals}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              <Signal className="h-4 w-4" />
              <span>Generate</span>
            </button>
          </div>
        </div>
      </div>

      {/* Signals List */}
      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {!loading && signals.length === 0 && (
        <div className="card text-center py-12">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Signals Found</h3>
          <p className="text-gray-600 mb-4">
            No trading signals meet your criteria. Try adjusting the confidence level or timeframe.
          </p>
          <button
            onClick={loadSignals}
            className="btn-primary"
          >
            Refresh Signals
          </button>
        </div>
      )}

      {!loading && signals.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              {signals.length} Active Signal{signals.length !== 1 ? 's' : ''}
            </h2>
            <div className="text-sm text-gray-600">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>

          <div className="space-y-4">
            {signals.map((signal, index) => (
              <SignalCard key={index} signal={signal} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default Signals