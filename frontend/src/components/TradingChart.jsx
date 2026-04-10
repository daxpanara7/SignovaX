import React, { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts'
import { useChartStore } from '../stores/chartStore'
import { useSignalStore } from '../stores/signalStore'
import { fetchCandles } from '../services/marketApi'

const TradingChart = () => {
  const chartContainerRef = useRef()
  const chartRef = useRef()
  const candlestickSeriesRef = useRef()
  
  const { 
    symbol, 
    timeframe, 
    darkMode, 
    setChartData,
    smcLevels,
    showOrderBlocks,
    showFVGs,
    showLiquidityZones,
    showBosChoch,
    showSessionBoxes,
    showHTFLevels
  } = useChartStore()
  
  const { activeSignal } = useSignalStore()
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch chart data
  const fetchChartData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      console.log(`Fetching OHLCV data for ${symbol} ${timeframe}...`)

      // Use fetchCandles which handles both crypto (Binance) and indices (ML API)
      const chartData = await fetchCandles(symbol, timeframe, 500)

      console.log('Received chart data:', chartData.length, 'candles')

      if (chartData && Array.isArray(chartData) && chartData.length > 0) {
        // Data is already in the correct format: { time, open, high, low, close, volume }
        // Sort by time to ensure proper order
        chartData.sort((a, b) => a.time - b.time)

        console.log('First candle:', chartData[0])
        console.log('Last candle:', chartData[chartData.length - 1])

        // Update chart
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(chartData)
          setChartData(chartData)
          console.log('✅ Chart data updated successfully')
        }
      } else {
        throw new Error('No data received from API')
      }

    } catch (error) {
      console.error('Error fetching chart data:', error)
      setError(`Failed to load chart data: ${error.message}`)

      // Generate fallback data
      const fallbackData = generateFallbackData()
      if (candlestickSeriesRef.current) {
        candlestickSeriesRef.current.setData(fallbackData)
        setChartData(fallbackData)
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Generate fallback data if API fails
  const generateFallbackData = () => {
    const data = []
    let price = symbol === 'BTCUSDT' ? 43250 : symbol === 'ETHUSDT' ? 2634 : 0.45
    const now = Math.floor(Date.now() / 1000)
    
    for (let i = 99; i >= 0; i--) {
      const time = now - (i * 15 * 60) // 15 minutes intervals
      const change = (Math.random() - 0.5) * 0.02 // ±1% change
      price *= (1 + change)
      
      const open = price
      const high = price * (1 + Math.random() * 0.01)
      const low = price * (1 - Math.random() * 0.01)
      const close = low + Math.random() * (high - low)
      
      data.push({
        time,
        open: parseFloat(open.toFixed(4)),
        high: parseFloat(high.toFixed(4)),
        low: parseFloat(low.toFixed(4)),
        close: parseFloat(close.toFixed(4))
      })
      
      price = close
    }
    
    return data
  }

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return

    console.log('🎯 Initializing chart...')

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: darkMode ? '#0a0a0a' : '#ffffff' },
        textColor: darkMode ? '#e5e5e5' : '#333333',
      },
      grid: {
        vertLines: { color: darkMode ? '#2a2a2a' : '#e0e0e0' },
        horzLines: { color: darkMode ? '#2a2a2a' : '#e0e0e0' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: darkMode ? '#64748b' : '#94a3b8',
          width: 1,
          style: 2,
        },
        horzLine: {
          color: darkMode ? '#64748b' : '#94a3b8',
          width: 1,
          style: 2,
        },
      },
      rightPriceScale: {
        borderColor: darkMode ? '#2a2a2a' : '#e0e0e0',
        textColor: darkMode ? '#e5e5e5' : '#333333',
      },
      timeScale: {
        borderColor: darkMode ? '#2a2a2a' : '#e0e0e0',
        textColor: darkMode ? '#e5e5e5' : '#333333',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#00d4aa',
      downColor: '#ff6b6b',
      borderDownColor: '#ff6b6b',
      borderUpColor: '#00d4aa',
      wickDownColor: '#ff6b6b',
      wickUpColor: '#00d4aa',
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries

    console.log('✅ Chart initialized successfully')

    // Handle resize
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chart.applyOptions({ 
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      console.log('🧹 Cleaning up chart...')
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [darkMode])

  // Fetch data when symbol or timeframe changes
  useEffect(() => {
    console.log(`📊 Symbol or timeframe changed: ${symbol} ${timeframe}`)
    fetchChartData()
  }, [symbol, timeframe])

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    console.log('⏰ Setting up auto-refresh interval')
    const interval = setInterval(() => {
      if (!isLoading) {
        console.log('🔄 Auto-refreshing chart data...')
        fetchChartData()
      }
    }, 30000)

    return () => {
      console.log('🛑 Clearing auto-refresh interval')
      clearInterval(interval)
    }
  }, [symbol, timeframe, isLoading])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-dark-surface">
        <div className="text-center">
          <div className="text-red-400 mb-2">⚠️</div>
          <p className="text-dark-text mb-2">Chart Error</p>
          <p className="text-dark-muted text-sm mb-4">{error}</p>
          <button
            onClick={fetchChartData}
            className="px-4 py-2 bg-bull text-white rounded hover:bg-bull/80 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-dark-surface">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bull mx-auto mb-2"></div>
          <p className="text-dark-muted text-sm">Loading chart data...</p>
          <p className="text-dark-muted text-xs mt-1">{symbol} {timeframe.toUpperCase()}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full">
      {/* Chart container */}
      <div 
        ref={chartContainerRef} 
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
      
      {/* Chart overlays */}
      <div className="absolute top-4 left-4 z-10">
        <div className="bg-dark-surface/90 backdrop-blur-sm rounded-lg p-3 border border-dark-border">
          <div className="flex items-center space-x-4">
            <div className="text-dark-text font-mono font-semibold">
              {symbol}
            </div>
            <div className="text-dark-muted text-sm">
              {timeframe.toUpperCase()}
            </div>
            {activeSignal && (
              <div className={`px-2 py-1 rounded text-xs font-medium ${
                activeSignal.direction === 'BUY' 
                  ? 'bg-bull/20 text-bull' 
                  : 'bg-bear/20 text-bear'
              }`}>
                {activeSignal.direction} SIGNAL
              </div>
            )}
            <div className="text-xs text-bull">
              ● LIVE
            </div>
          </div>
        </div>
      </div>

      {/* Chart controls */}
      <div className="absolute top-4 right-4 z-10">
        <div className="bg-dark-surface/90 backdrop-blur-sm rounded-lg p-2 border border-dark-border">
          <div className="flex space-x-2">
            <button
              onClick={() => useChartStore.getState().toggleOrderBlocks()}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                showOrderBlocks 
                  ? 'bg-bull/20 text-bull' 
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              OB
            </button>
            <button
              onClick={() => useChartStore.getState().toggleFVGs()}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                showFVGs 
                  ? 'bg-bull/20 text-bull' 
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              FVG
            </button>
            <button
              onClick={() => useChartStore.getState().toggleLiquidityZones()}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                showLiquidityZones 
                  ? 'bg-bull/20 text-bull' 
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              LZ
            </button>
            <button
              onClick={() => useChartStore.getState().toggleBosChoch()}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                showBosChoch 
                  ? 'bg-bull/20 text-bull' 
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              BOS
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TradingChart