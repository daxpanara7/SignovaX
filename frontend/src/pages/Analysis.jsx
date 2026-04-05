import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react'
import TradingChart from '../components/TradingChart'
import { marketDataAPI, analysisAPI } from '../services/api'

const Analysis = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [marketData, setMarketData] = useState(null)
  const [smcAnalysis, setSmcAnalysis] = useState(null)
  const [symbols, setSymbols] = useState([])
  const [timeframes, setTimeframes] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (selectedSymbol && selectedTimeframe) {
      loadAnalysis()
    }
  }, [selectedSymbol, selectedTimeframe])

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

  const loadAnalysis = async () => {
    try {
      setLoading(true)
      
      // Load market data and SMC analysis in parallel
      const [marketResponse, analysisResponse] = await Promise.all([
        marketDataAPI.getOHLCV(selectedSymbol, selectedTimeframe, 500),
        analysisAPI.analyzeSMC(selectedSymbol, selectedTimeframe, 500)
      ])
      
      setMarketData(marketResponse.data)
      setSmcAnalysis(analysisResponse.data)
      
    } catch (error) {
      console.error('Failed to load analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const PatternCard = ({ title, count, items, color = 'blue' }) => {
    const colorClasses = {
      blue: 'border-blue-200 bg-blue-50',
      green: 'border-green-200 bg-green-50',
      red: 'border-red-200 bg-red-50',
      yellow: 'border-yellow-200 bg-yellow-50'
    }

    return (
      <div className={`border rounded-lg p-4 ${colorClasses[color]}`}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-gray-900">{title}</h3>
          <span className="text-2xl font-bold text-gray-700">{count}</span>
        </div>
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {items.slice(0, 3).map((item, index) => (
            <div key={index} className="text-sm text-gray-600 bg-white p-2 rounded">
              {typeof item === 'object' ? (
                <div>
                  <div className="font-medium">
                    {item.zone_type || item.block_type || item.gap_type || item.type}
                  </div>
                  <div>Level: {item.level?.toFixed(2) || item.mitigation_level?.toFixed(2) || 'N/A'}</div>
                </div>
              ) : (
                item
              )}
            </div>
          ))}
          {items.length > 3 && (
            <div className="text-xs text-gray-500 text-center">
              +{items.length - 3} more
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Market Analysis</h1>
          <p className="text-gray-600">Smart Money Concepts pattern detection</p>
        </div>
        <button
          onClick={loadAnalysis}
          disabled={loading}
          className="btn-primary flex items-center space-x-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
          <div className="flex items-end">
            <button
              onClick={loadAnalysis}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              <Search className="h-4 w-4" />
              <span>Analyze</span>
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {marketData && smcAnalysis && !loading && (
        <>
          {/* Chart */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {selectedSymbol} - {selectedTimeframe}
            </h3>
            <TradingChart 
              data={marketData.data} 
              smcAnalysis={smcAnalysis}
              className="w-full"
            />
          </div>

          {/* Pattern Analysis */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <PatternCard
              title="Liquidity Zones"
              count={smcAnalysis.liquidity_zones?.length || 0}
              items={smcAnalysis.liquidity_zones || []}
              color="blue"
            />
            <PatternCard
              title="Order Blocks"
              count={smcAnalysis.order_blocks?.length || 0}
              items={smcAnalysis.order_blocks || []}
              color="green"
            />
            <PatternCard
              title="Fair Value Gaps"
              count={smcAnalysis.fair_value_gaps?.length || 0}
              items={smcAnalysis.fair_value_gaps || []}
              color="yellow"
            />
          </div>

          {/* Structure Analysis */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                Break of Structure (BOS)
              </h3>
              <div className="space-y-3">
                {smcAnalysis.bos_signals?.length > 0 ? (
                  smcAnalysis.bos_signals.slice(0, 5).map((signal, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className={`font-medium ${
                          signal.type?.includes('bullish') ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {signal.type?.replace('_', ' ').toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-600">
                          {signal.level?.toFixed(2)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Previous: {signal.previous_level?.toFixed(2)}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No BOS signals detected</p>
                )}
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingDown className="h-5 w-5 mr-2 text-orange-600" />
                Change of Character (CHOCH)
              </h3>
              <div className="space-y-3">
                {smcAnalysis.choch_signals?.length > 0 ? (
                  smcAnalysis.choch_signals.slice(0, 5).map((signal, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className={`font-medium ${
                          signal.type?.includes('bullish') ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {signal.type?.replace('_', ' ').toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-600">
                          {signal.level?.toFixed(2)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Broken: {signal.broken_level?.toFixed(2)}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No CHOCH signals detected</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Analysis