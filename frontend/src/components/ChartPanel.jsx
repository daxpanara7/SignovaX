import React, { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, LineSeries } from 'lightweight-charts';
import { useChartStore, useSignalStore, usePriceStore } from '../stores';
import { generateMockCandles, mockOrderBlocks, mockFVGs, mockLiquidityZones } from '../data/mockData';
import { fetchData } from '../services/api';
import { Camera, RotateCcw, TrendingUp } from 'lucide-react';

const ChartPanel = () => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const { 
    symbol, 
    timeframe,
    showOrderBlocks, 
    showFVGs, 
    showLiquidityZones, 
    showBosChoch, 
    showSessionBoxes, 
    showHTFLevels,
    toggleOrderBlocks,
    toggleFVGs,
    toggleLiquidityZones,
    toggleBosChoch,
    toggleSessionBoxes,
    toggleHTFLevels
  } = useChartStore();
  const { scanning, updateLastAnalyzed } = useSignalStore();
  const { prices, isConnected } = usePriceStore();
  const [analyzing, setAnalyzing] = useState(false);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load real market data
  useEffect(() => {
    const loadChartData = async () => {
      setLoading(true);
      try {
        // Use the current symbol and timeframe from chart store
        const currentSymbol = symbol || 'BTCUSDT';
        const currentTimeframe = timeframe || '15m';
        console.log(`Loading chart data for ${currentSymbol} ${currentTimeframe}...`);
        
        // Fetch real market data
        const data = await fetchData(currentSymbol, currentTimeframe, 500);
        
        if (data && data.length > 0) {
          // Convert to chart format
          const chartCandles = data.map(candle => ({
            time: Math.floor(new Date(candle.timestamp).getTime() / 1000),
            open: parseFloat(candle.open),
            high: parseFloat(candle.high),
            low: parseFloat(candle.low),
            close: parseFloat(candle.close),
            volume: parseFloat(candle.volume || 0)
          }));
          
          // Sort by time to ensure proper order
          chartCandles.sort((a, b) => a.time - b.time);
          
          setChartData(chartCandles);
          console.log(`Loaded ${chartCandles.length} candles for ${currentSymbol} ${currentTimeframe}`);
          
          // Update the chart series if it exists
          if (candleSeriesRef.current) {
            candleSeriesRef.current.setData(chartCandles);
            // Fit content to show all data smoothly
            if (chartRef.current) {
              setTimeout(() => {
                chartRef.current.timeScale().fitContent();
              }, 100);
            }
          }
        } else {
          console.warn('No real data available, using mock data');
          // Fallback to mock data but with current price
          const currentPrice = prices[symbol]?.price || 66000;
          const mockCandles = generateMockCandles(500, currentPrice);
          setChartData(mockCandles);
          
          if (candleSeriesRef.current) {
            candleSeriesRef.current.setData(mockCandles);
            if (chartRef.current) {
              setTimeout(() => {
                chartRef.current.timeScale().fitContent();
              }, 100);
            }
          }
        }
      } catch (error) {
        console.error('Failed to load chart data:', error);
        // Fallback to mock data with current price
        const currentPrice = prices[symbol]?.price || 66000;
        const mockCandles = generateMockCandles(500, currentPrice);
        setChartData(mockCandles);
        
        if (candleSeriesRef.current) {
          candleSeriesRef.current.setData(mockCandles);
          if (chartRef.current) {
            setTimeout(() => {
              chartRef.current.timeScale().fitContent();
            }, 100);
          }
        }
      } finally {
        setLoading(false);
      }
    };

    loadChartData();
  }, [symbol, timeframe, fetchData]); // Reload when symbol OR timeframe changes

  // Update chart with real-time price updates
  useEffect(() => {
    if (!candleSeriesRef.current || !isConnected || chartData.length === 0) return;
    
    const currentSymbol = symbol || 'BTCUSDT';
    const currentPrice = prices[currentSymbol];
    
    if (currentPrice && currentPrice.price) {
      // Update the last candle with current price
      const lastCandle = chartData[chartData.length - 1];
      if (lastCandle) {
        const updatedCandle = {
          ...lastCandle,
          close: currentPrice.price,
          high: Math.max(lastCandle.high, currentPrice.price),
          low: Math.min(lastCandle.low, currentPrice.price)
        };
        
        // Update just the last candle
        candleSeriesRef.current.update(updatedCandle);
      }
    }
  }, [prices, isConnected, symbol, chartData]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { color: '#0a0e17' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1a2235' },
        horzLines: { color: '#1a2235' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#3b82f6',
          width: 1,
          style: 0,
        },
        horzLine: {
          color: '#3b82f6',
          width: 1,
          style: 0,
        },
      },
      rightPriceScale: {
        borderColor: '#1e293b',
      },
      timeScale: {
        borderColor: '#1e293b',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    // Set initial data if available
    if (chartData.length > 0) {
      candleSeries.setData(chartData);
    }

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [chartData]); // Re-initialize when chart data changes

  useEffect(() => {
    if (!chartRef.current) return;

    // Clear existing overlays
    // Note: In a real implementation, you'd want to track and remove specific series
    
    if (showOrderBlocks) {
      mockOrderBlocks.forEach((ob) => {
        const lineSeries = chartRef.current.addSeries(LineSeries, {
          color: 'transparent',
          lineWidth: 0,
          priceLineVisible: false,
          lastValueVisible: false,
        });

        const obData = [
          { time: ob.time_start, value: ob.price_high },
          { time: ob.time_end, value: ob.price_high },
        ];
        lineSeries.setData(obData);

        lineSeries.createPriceLine({
          price: ob.price_high,
          color: ob.type === 'bullish' ? '#10b981' : '#ef4444',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
        });

        lineSeries.createPriceLine({
          price: ob.price_low,
          color: ob.type === 'bullish' ? '#10b981' : '#ef4444',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
        });
      });
    }

    if (showLiquidityZones) {
      mockLiquidityZones.forEach((liq) => {
        const lineSeries = chartRef.current.addSeries(LineSeries, {
          color: '#8b5cf6',
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
        });

        const currentTime = Date.now() / 1000;
        lineSeries.setData([
          { time: liq.time, value: liq.price },
          { time: currentTime, value: liq.price },
        ]);
      });
    }
  }, [showOrderBlocks, showFVGs, showLiquidityZones, showBosChoch, showSessionBoxes, showHTFLevels]);

  const handleAnalyze = () => {
    setAnalyzing(true);
    setTimeout(() => {
      setAnalyzing(false);
      updateLastAnalyzed();
    }, 2000);
  };

  const handleScreenshot = () => {
    console.log('Taking screenshot...');
  };

  const handleResetZoom = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  };

  return (
    <div className="flex-1 flex flex-col" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Chart Container */}
      <div ref={chartContainerRef} data-testid="trading-chart" className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ backgroundColor: 'rgba(10, 14, 23, 0.8)' }}>
            <div className="text-center">
              <div className="w-12 h-12 border-3 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <div className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Loading {timeframe} Chart...</div>
              <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Fetching {symbol} data...</div>
            </div>
          </div>
        )}
        {analyzing && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ backgroundColor: 'rgba(10, 14, 23, 0.9)' }}>
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <div className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Analyzing Market...</div>
              <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Detecting Order Blocks...</div>
            </div>
          </div>
        )}
        {!loading && !isConnected && (
          <div className="absolute top-4 right-4 px-3 py-2 rounded text-xs font-medium" style={{ backgroundColor: 'var(--accent-red)', color: 'white' }}>
            Chart data may be outdated - WebSocket disconnected
          </div>
        )}
        {!loading && isConnected && (
          <div className="absolute top-4 right-4 px-3 py-2 rounded text-xs font-medium" style={{ backgroundColor: 'var(--accent-green)', color: 'white' }}>
            Live Data
          </div>
        )}
      </div>

      {/* Chart Toolbar */}
      <div className="h-10 border-t border-[var(--border)] flex items-center justify-between px-4" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex items-center gap-2">
          {[
            { key: 'orderBlocks', label: 'OB', active: showOrderBlocks, toggle: toggleOrderBlocks },
            { key: 'fvgs', label: 'FVG', active: showFVGs, toggle: toggleFVGs },
            { key: 'liquidity', label: 'LIQ', active: showLiquidityZones, toggle: toggleLiquidityZones },
            { key: 'structure', label: 'BOS', active: showBosChoch, toggle: toggleBosChoch },
            { key: 'sessions', label: 'SESSION', active: showSessionBoxes, toggle: toggleSessionBoxes },
            { key: 'htf', label: 'HTF', active: showHTFLevels, toggle: toggleHTFLevels },
          ].map((overlay) => (
            <button
              key={overlay.key}
              data-testid={`overlay-${overlay.key}`}
              onClick={overlay.toggle}
              className="px-3 py-1 text-xs font-medium rounded transition-colors"
              style={{
                backgroundColor: overlay.active ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: overlay.active ? 'white' : 'var(--text-secondary)'
              }}
            >
              {overlay.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            data-testid="screenshot-button"
            onClick={handleScreenshot}
            className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Camera className="w-4 h-4" />
          </button>
          <button
            data-testid="reset-zoom-button"
            onClick={handleResetZoom}
            className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            data-testid="analyze-button"
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-2"
            style={{
              backgroundColor: 'var(--accent-blue)',
              color: 'white',
              opacity: analyzing ? 0.6 : 1
            }}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChartPanel;