import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, CandlestickSeries, LineSeries } from 'lightweight-charts';
import { useChartStore } from '../stores/chartStore';
import { useSignalStore } from '../stores';
import { usePriceStore } from '../stores/priceStore';
import { fetchCandles, fetchLiveSignal } from '../services/marketApi';
import { generateMockCandles, mockOrderBlocks, mockLiquidityZones } from '../data/mockData';
import { Camera, RotateCcw, TrendingUp, Wifi, WifiOff } from 'lucide-react';

// Map UI timeframe labels → Binance interval strings
const TF_MAP = { '1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1D': '1d' };

const ChartPanel = () => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const overlaySeriesRef = useRef([]);

  const {
    symbol, timeframe,
    showOrderBlocks, showFVGs, showLiquidityZones,
    showBosChoch, showSessionBoxes, showHTFLevels,
    toggleOrderBlocks, toggleFVGs, toggleLiquidityZones,
    toggleBosChoch, toggleSessionBoxes, toggleHTFLevels,
  } = useChartStore();

  const { updateLastAnalyzed } = useSignalStore();
  const { prices } = usePriceStore();

  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [signalData, setSignalData] = useState(null);
  const [proxyOnline, setProxyOnline] = useState(null); // null=checking, true, false
  const [error, setError] = useState(null);

  // ── Load candles from Binance via proxy ──────────────────────────────────
  const loadCandles = useCallback(async () => {
    setLoading(true);
    setError(null);
    const binanceInterval = TF_MAP[timeframe] || '15m';
    try {
      const result = await fetchCandles(symbol, binanceInterval, 300);
      if (result?.candles?.length > 0) {
        // Binance returns ms timestamps — lightweight-charts needs seconds
        const formatted = result.candles.map(c => ({
          time: Math.floor(c.time / 1000),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
        formatted.sort((a, b) => a.time - b.time);
        setChartData(formatted);
        setProxyOnline(true);
        if (candleSeriesRef.current) {
          candleSeriesRef.current.setData(formatted);
          chartRef.current?.timeScale().fitContent();
        }
      }
    } catch (err) {
      setError('Proxy offline — showing mock data. Start proxy: cd proxy-server && node server.js');
      setProxyOnline(false);
      // Fallback to mock
      const mock = generateMockCandles(300, 67000);
      setChartData(mock);
      if (candleSeriesRef.current) {
        candleSeriesRef.current.setData(mock);
        chartRef.current?.timeScale().fitContent();
      }
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  // Load on mount + symbol/timeframe change
  useEffect(() => { loadCandles(); }, [loadCandles]);

  // ── Update last candle with live price from priceStore ───────────────────
  useEffect(() => {
    if (!candleSeriesRef.current || chartData.length === 0 || !proxyOnline) return;
    const live = prices[symbol];
    if (!live?.price) return;
    const last = chartData[chartData.length - 1];
    candleSeriesRef.current.update({
      time: last.time,
      open: last.open,
      high: Math.max(last.high, live.price),
      low: Math.min(last.low, live.price),
      close: live.price,
    });
  }, [prices, symbol, chartData, proxyOnline]);

  // ── Initialize TradingView Lightweight Chart ─────────────────────────────
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: { background: { color: '#0a0e17' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1a2235' }, horzLines: { color: '#1a2235' } },
      crosshair: {
        mode: 1,
        vertLine: { color: '#3b82f6', width: 1, style: 0 },
        horzLine: { color: '#3b82f6', width: 1, style: 0 },
      },
      rightPriceScale: { borderColor: '#1e293b' },
      timeScale: { borderColor: '#1e293b', timeVisible: true, secondsVisible: false },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981', downColor: '#ef4444',
      wickUpColor: '#10b981', wickDownColor: '#ef4444',
    });

    if (chartData.length > 0) candleSeries.setData(chartData);

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const onResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chartRef.current?.remove();
    };
  }, []); // only once

  // ── Draw SMC overlays when toggles change ────────────────────────────────
  useEffect(() => {
    if (!chartRef.current) return;

    // Remove old overlay series
    overlaySeriesRef.current.forEach(s => {
      try { chartRef.current.removeSeries(s); } catch (_) {}
    });
    overlaySeriesRef.current = [];

    if (showOrderBlocks) {
      mockOrderBlocks.forEach(ob => {
        const color = ob.type === 'bullish' ? '#10b981' : '#ef4444';
        ['price_high', 'price_low'].forEach(key => {
          const s = chartRef.current.addSeries(LineSeries, {
            color: 'transparent', lineWidth: 0,
            priceLineVisible: false, lastValueVisible: false,
          });
          s.setData([
            { time: Math.floor(ob.time_start), value: ob[key] },
            { time: Math.floor(ob.time_end), value: ob[key] },
          ]);
          s.createPriceLine({ price: ob[key], color, lineWidth: 1, lineStyle: 2, axisLabelVisible: true });
          overlaySeriesRef.current.push(s);
        });
      });
    }

    if (showLiquidityZones) {
      mockLiquidityZones.filter(z => !z.swept).forEach(liq => {
        const s = chartRef.current.addSeries(LineSeries, {
          color: '#8b5cf6', lineWidth: 1, lineStyle: 2, priceLineVisible: false,
        });
        const now = Math.floor(Date.now() / 1000);
        s.setData([
          { time: Math.floor(liq.time), value: liq.price },
          { time: now, value: liq.price },
        ]);
        overlaySeriesRef.current.push(s);
      });
    }

    // Draw live signal levels on chart
    if (signalData && signalData.signal !== 'HOLD') {
      const now = Math.floor(Date.now() / 1000);
      const past = now - 3600;
      const signalColor = signalData.signal === 'BUY' ? '#10b981' : '#ef4444';

      [
        { price: signalData.currentPrice, color: signalColor, label: `${signalData.signal} Entry` },
        { price: signalData.stopLoss, color: '#ef4444', label: 'Stop Loss' },
        { price: signalData.takeProfit, color: '#10b981', label: 'Take Profit' },
      ].filter(l => l.price).forEach(level => {
        const s = chartRef.current.addSeries(LineSeries, {
          color: 'transparent', lineWidth: 0,
          priceLineVisible: false, lastValueVisible: false,
        });
        s.setData([{ time: past, value: level.price }, { time: now, value: level.price }]);
        s.createPriceLine({
          price: level.price, color: level.color,
          lineWidth: 2, lineStyle: 0, axisLabelVisible: true,
          title: level.label,
        });
        overlaySeriesRef.current.push(s);
      });
    }
  }, [showOrderBlocks, showFVGs, showLiquidityZones, showBosChoch, showSessionBoxes, showHTFLevels, signalData]);

  // ── Analyze button — fetch real signal from proxy ────────────────────────
  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const binanceInterval = TF_MAP[timeframe] || '15m';
      const result = await fetchLiveSignal(symbol, binanceInterval);
      setSignalData(result);
      updateLastAnalyzed();
    } catch (err) {
      setError('Signal fetch failed — is proxy running?');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleResetZoom = () => chartRef.current?.timeScale().fitContent();

  const handleScreenshot = () => {
    if (!chartRef.current) return;
    const canvas = chartContainerRef.current?.querySelector('canvas');
    if (canvas) {
      const link = document.createElement('a');
      link.download = `${symbol}_${timeframe}_chart.png`;
      link.href = canvas.toDataURL();
      link.click();
    }
  };

  const livePrice = prices[symbol]?.price;

  return (
    <div className="flex-1 flex flex-col" style={{ backgroundColor: 'var(--bg-primary)' }}>

      {/* ── Signal Banner (shows after Analyze) ── */}
      {signalData && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, padding: '6px 16px',
          backgroundColor: signalData.signal === 'BUY' ? '#052e16' : signalData.signal === 'SELL' ? '#450a0a' : '#1c1917',
          borderBottom: `2px solid ${signalData.signal === 'BUY' ? '#10b981' : signalData.signal === 'SELL' ? '#ef4444' : '#78716c'}`,
        }}>
          <span style={{
            fontWeight: 700, fontSize: 13, letterSpacing: 1, padding: '2px 10px', borderRadius: 4,
            backgroundColor: signalData.signal === 'BUY' ? '#10b981' : signalData.signal === 'SELL' ? '#ef4444' : '#78716c',
            color: '#fff',
          }}>
            {signalData.signal === 'BUY' ? '▲ BUY' : signalData.signal === 'SELL' ? '▼ SELL' : '◆ HOLD'}
          </span>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            Confidence: <b style={{ color: '#f1f5f9' }}>{signalData.confidence}%</b>
          </span>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            RSI: <b style={{ color: '#f1f5f9' }}>{signalData.rsi}</b>
          </span>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            EMA20: <b style={{ color: '#f1f5f9' }}>${Number(signalData.ema20).toLocaleString()}</b>
          </span>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            EMA50: <b style={{ color: '#f1f5f9' }}>${Number(signalData.ema50).toLocaleString()}</b>
          </span>
          {signalData.signal !== 'HOLD' && (
            <>
              <span style={{ fontSize: 12, color: '#ef4444' }}>
                SL: ${Number(signalData.stopLoss).toLocaleString()}
              </span>
              <span style={{ fontSize: 12, color: '#10b981' }}>
                TP: ${Number(signalData.takeProfit).toLocaleString()}
              </span>
              <span style={{ fontSize: 12, color: '#f59e0b' }}>R:R 1:2</span>
            </>
          )}
          <button onClick={() => setSignalData(null)} style={{ marginLeft: 'auto', color: '#64748b', background: 'none', border: 'none', cursor: 'pointer', fontSize: 16 }}>✕</button>
        </div>
      )}

      {/* ── Chart Container ── */}
      <div ref={chartContainerRef} data-testid="trading-chart" className="flex-1 relative">

        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10"
            style={{ backgroundColor: 'rgba(10,14,23,0.85)' }}>
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <div style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 600 }}>
                Loading {symbol} {timeframe} from Binance...
              </div>
            </div>
          </div>
        )}

        {/* Error banner */}
        {error && !loading && (
          <div className="absolute top-2 left-2 right-2 z-10 px-3 py-2 rounded text-xs"
            style={{ backgroundColor: '#450a0a', border: '1px solid #ef4444', color: '#fca5a5' }}>
            ⚠ {error}
          </div>
        )}

        {/* Live price badge */}
        {!loading && livePrice && (
          <div className="absolute top-3 left-3 z-10 px-3 py-1.5 rounded text-xs font-bold"
            style={{ backgroundColor: '#0f172a', border: '1px solid #10b981', color: '#10b981' }}>
            {proxyOnline ? '● LIVE' : '○ MOCK'} &nbsp; ${Number(livePrice).toLocaleString()}
          </div>
        )}

        {/* Data source badge */}
        {!loading && (
          <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 px-2 py-1 rounded text-xs"
            style={{ backgroundColor: '#0f172a', border: `1px solid ${proxyOnline ? '#10b981' : '#ef4444'}` }}>
            {proxyOnline
              ? <><Wifi className="w-3 h-3" style={{ color: '#10b981' }} /><span style={{ color: '#10b981' }}>Binance Live</span></>
              : <><WifiOff className="w-3 h-3" style={{ color: '#ef4444' }} /><span style={{ color: '#ef4444' }}>Mock Data</span></>
            }
          </div>
        )}
      </div>

      {/* ── Chart Toolbar ── */}
      <div className="h-10 border-t border-[var(--border)] flex items-center justify-between px-4"
        style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex items-center gap-2">
          {[
            { key: 'orderBlocks', label: 'OB',      active: showOrderBlocks,    toggle: toggleOrderBlocks },
            { key: 'fvgs',        label: 'FVG',     active: showFVGs,           toggle: toggleFVGs },
            { key: 'liquidity',   label: 'LIQ',     active: showLiquidityZones, toggle: toggleLiquidityZones },
            { key: 'structure',   label: 'BOS',     active: showBosChoch,       toggle: toggleBosChoch },
            { key: 'sessions',    label: 'SESSION', active: showSessionBoxes,   toggle: toggleSessionBoxes },
            { key: 'htf',         label: 'HTF',     active: showHTFLevels,      toggle: toggleHTFLevels },
          ].map(o => (
            <button key={o.key} onClick={o.toggle}
              className="px-3 py-1 text-xs font-medium rounded transition-colors"
              style={{
                backgroundColor: o.active ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: o.active ? 'white' : 'var(--text-secondary)',
              }}>
              {o.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button onClick={handleScreenshot} title="Screenshot"
            className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors"
            style={{ color: 'var(--text-secondary)' }}>
            <Camera className="w-4 h-4" />
          </button>
          <button onClick={handleResetZoom} title="Reset zoom"
            className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors"
            style={{ color: 'var(--text-secondary)' }}>
            <RotateCcw className="w-4 h-4" />
          </button>
          <button onClick={handleAnalyze} disabled={analyzing}
            className="px-4 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-2"
            style={{ backgroundColor: 'var(--accent-blue)', color: 'white', opacity: analyzing ? 0.6 : 1 }}>
            <TrendingUp className="w-3.5 h-3.5" />
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChartPanel;
