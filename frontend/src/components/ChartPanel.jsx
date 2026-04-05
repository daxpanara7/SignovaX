import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { createChart, CandlestickSeries, LineSeries } from 'lightweight-charts';
import { useChartStore } from '../stores/chartStore';
import { useSignalStore } from '../stores';
import { usePriceStore } from '../stores/priceStore';
import { fetchCandles, fetchLiveSignal } from '../services/marketApi';
import { useBinanceStream } from '../hooks/useBinanceStream';
import { generateMockCandles, mockOrderBlocks, mockLiquidityZones } from '../data/mockData';
import { Camera, RotateCcw, TrendingUp, Wifi, WifiOff } from 'lucide-react';

const TF_MAP = { '1m':'1m', '5m':'5m', '15m':'15m', '1h':'1h', '4h':'4h', '1D':'1d' };

const ChartPanel = () => {
  const chartContainerRef = useRef(null);
  const chartRef          = useRef(null);
  const candleSeriesRef   = useRef(null);
  const overlaySeriesRef  = useRef([]);
  const candleBufferRef   = useRef([]); // holds all candles in memory

  const { symbol, timeframe,
    showOrderBlocks, showFVGs, showLiquidityZones,
    showBosChoch, showSessionBoxes, showHTFLevels,
    toggleOrderBlocks, toggleFVGs, toggleLiquidityZones,
    toggleBosChoch, toggleSessionBoxes, toggleHTFLevels,
  } = useChartStore();

  const { updateLastAnalyzed } = useSignalStore();
  const { prices } = usePriceStore();

  const [loading,    setLoading]    = useState(true);
  const [analyzing,  setAnalyzing]  = useState(false);
  const [signalData, setSignalData] = useState(null);
  const [wsStatus,   setWsStatus]   = useState('CONNECTING');
  const [error,      setError]      = useState(null);

  const binanceInterval = TF_MAP[timeframe] || '15m';

  // ── 1. Load historical candles via REST on mount / symbol / timeframe ────
  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const candles = await fetchCandles(symbol, binanceInterval, 500);
      candles.sort((a, b) => a.time - b.time);
      candleBufferRef.current = candles;
      if (candleSeriesRef.current) {
        candleSeriesRef.current.setData(candles);
        chartRef.current?.timeScale().fitContent();
      }
      setWsStatus('CONNECTING');
    } catch {
      setError('Binance unreachable — showing mock data');
      const mock = generateMockCandles(300, prices[symbol]?.price || 67000);
      candleBufferRef.current = mock;
      if (candleSeriesRef.current) {
        candleSeriesRef.current.setData(mock);
        chartRef.current?.timeScale().fitContent();
      }
    } finally {
      setLoading(false);
    }
  }, [symbol, binanceInterval]); // eslint-disable-line

  useEffect(() => { loadHistory(); }, [loadHistory]);

  // ── 2. WebSocket kline stream — incremental candle updates ───────────────
  const onKline = useCallback((sym, interval, candle) => {
    if (sym !== symbol || interval !== binanceInterval) return;
    if (!candleSeriesRef.current) return;

    const buf = candleBufferRef.current;
    if (buf.length === 0) return;

    const last = buf[buf.length - 1];

    if (candle.time === last.time) {
      // Update current (open) candle in-place
      const updated = {
        time:  candle.time,
        open:  last.open, // open never changes mid-candle
        high:  Math.max(last.high, candle.high),
        low:   Math.min(last.low,  candle.low),
        close: candle.close,
      };
      buf[buf.length - 1] = updated;
      candleSeriesRef.current.update(updated);
    } else if (candle.time > last.time) {
      // New candle opened
      const newCandle = {
        time:  candle.time,
        open:  candle.open,
        high:  candle.high,
        low:   candle.low,
        close: candle.close,
      };
      buf.push(newCandle);
      // Keep buffer from growing unbounded
      if (buf.length > 1000) buf.shift();
      candleSeriesRef.current.update(newCandle);
    }
  }, [symbol, binanceInterval]);

  const onWsStatus = useCallback((status) => {
    setWsStatus(status);
  }, []);

  // Connect kline stream for the active chart symbol
  useBinanceStream([symbol], symbol, binanceInterval, {
    onKline,
    onStatus: onWsStatus,
  });

  // ── 3. Initialize chart (once) ───────────────────────────────────────────
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width:  chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: { background: { color: '#0a0e17' }, textColor: '#94a3b8' },
      grid:   { vertLines: { color: '#1a2235' }, horzLines: { color: '#1a2235' } },
      crosshair: {
        mode: 1,
        vertLine: { color: '#3b82f6', width: 1, style: 0 },
        horzLine: { color: '#3b82f6', width: 1, style: 0 },
      },
      rightPriceScale: { borderColor: '#1e293b' },
      timeScale: { borderColor: '#1e293b', timeVisible: true, secondsVisible: false },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981', downColor: '#ef4444',
      wickUpColor: '#10b981', wickDownColor: '#ef4444',
    });

    chartRef.current        = chart;
    candleSeriesRef.current = series;

    const onResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width:  chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };
    window.addEventListener('resize', onResize);

    return () => {
      window.removeEventListener('resize', onResize);
      chartRef.current?.remove();
      chartRef.current        = null;
      candleSeriesRef.current = null;
    };
  }, []); // only once

  // ── 4. SMC overlays ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!chartRef.current) return;
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
            { time: Math.floor(ob.time_end),   value: ob[key] },
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
          { time: now,                  value: liq.price },
        ]);
        overlaySeriesRef.current.push(s);
      });
    }

    if (signalData && signalData.signal !== 'HOLD') {
      const now  = Math.floor(Date.now() / 1000);
      const past = now - 3600;
      [
        { price: signalData.currentPrice, color: signalData.signal === 'BUY' ? '#10b981' : '#ef4444', title: `${signalData.signal} Entry` },
        { price: signalData.stopLoss,     color: '#ef4444',  title: 'Stop Loss'   },
        { price: signalData.takeProfit,   color: '#10b981',  title: 'Take Profit' },
      ].filter(l => l.price).forEach(level => {
        const s = chartRef.current.addSeries(LineSeries, {
          color: 'transparent', lineWidth: 0,
          priceLineVisible: false, lastValueVisible: false,
        });
        s.setData([{ time: past, value: level.price }, { time: now, value: level.price }]);
        s.createPriceLine({ price: level.price, color: level.color, lineWidth: 2, lineStyle: 0, axisLabelVisible: true, title: level.title });
        overlaySeriesRef.current.push(s);
      });
    }
  }, [showOrderBlocks, showFVGs, showLiquidityZones, showBosChoch, showSessionBoxes, showHTFLevels, signalData]);

  // ── 5. Analyze button ────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const result = await fetchLiveSignal(symbol, binanceInterval);
      setSignalData(result);
      updateLastAnalyzed();
    } catch {
      setError('Signal fetch failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleResetZoom  = () => chartRef.current?.timeScale().fitContent();
  const handleScreenshot = () => {
    const canvas = chartContainerRef.current?.querySelector('canvas');
    if (!canvas) return;
    const a = document.createElement('a');
    a.download = `${symbol}_${timeframe}.png`;
    a.href = canvas.toDataURL();
    a.click();
  };

  const livePrice = prices[symbol]?.price;
  const isLive    = wsStatus === 'LIVE';

  return (
    <div className="flex-1 flex flex-col" style={{ backgroundColor: 'var(--bg-primary)' }}>

      {/* Signal banner */}
      {signalData && (
        <div style={{
          display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 10, padding: '5px 14px',
          backgroundColor: signalData.signal === 'BUY' ? '#052e16' : signalData.signal === 'SELL' ? '#450a0a' : '#1c1917',
          borderBottom: `2px solid ${signalData.signal === 'BUY' ? '#10b981' : signalData.signal === 'SELL' ? '#ef4444' : '#78716c'}`,
        }}>
          <span style={{
            fontWeight: 800, fontSize: 12, letterSpacing: 1, padding: '2px 10px', borderRadius: 4,
            backgroundColor: signalData.signal === 'BUY' ? '#10b981' : signalData.signal === 'SELL' ? '#ef4444' : '#78716c',
            color: '#fff',
          }}>
            {signalData.signal === 'BUY' ? '▲ BUY' : signalData.signal === 'SELL' ? '▼ SELL' : '◆ HOLD'}
          </span>
          {[
            ['Confidence', `${signalData.confidence}%`],
            ['RSI', signalData.rsi],
            ['EMA20', `$${Number(signalData.ema20).toLocaleString()}`],
            ['EMA50', `$${Number(signalData.ema50).toLocaleString()}`],
            ...(signalData.signal !== 'HOLD' ? [
              ['SL', `$${Number(signalData.stopLoss).toLocaleString()}`],
              ['TP', `$${Number(signalData.takeProfit).toLocaleString()}`],
              ['R:R', '1:2'],
            ] : []),
          ].map(([label, val]) => (
            <span key={label} style={{ fontSize: 11, color: '#94a3b8' }}>
              {label}: <b style={{ color: '#f1f5f9' }}>{val}</b>
            </span>
          ))}
          <button onClick={() => setSignalData(null)}
            style={{ marginLeft: 'auto', color: '#64748b', background: 'none', border: 'none', cursor: 'pointer', fontSize: 15 }}>
            ✕
          </button>
        </div>
      )}

      {/* Chart */}
      <div ref={chartContainerRef} className="flex-1 relative">

        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10"
            style={{ backgroundColor: 'rgba(10,14,23,0.85)' }}>
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <div style={{ color: '#f1f5f9', fontSize: 12 }}>Loading {symbol} {timeframe}...</div>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="absolute top-2 left-2 right-2 z-10 px-3 py-2 rounded text-xs"
            style={{ backgroundColor: '#450a0a', border: '1px solid #ef4444', color: '#fca5a5' }}>
            ⚠ {error}
          </div>
        )}

        {/* Live price badge — updates on every WS tick */}
        {!loading && livePrice && (
          <div className="absolute top-3 left-3 z-10 px-3 py-1 rounded text-xs font-bold"
            style={{ backgroundColor: '#0f172a', border: `1px solid ${isLive ? '#10b981' : '#f59e0b'}`, color: isLive ? '#10b981' : '#f59e0b' }}>
            {isLive ? '⚡ LIVE' : wsStatus === 'FALLBACK' ? '↻ REST' : '○ …'}
            &nbsp; ${Number(livePrice).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        )}

        {/* WS status badge */}
        {!loading && (
          <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 px-2 py-1 rounded text-xs"
            style={{ backgroundColor: '#0f172a', border: `1px solid ${isLive ? '#10b981' : wsStatus === 'FALLBACK' ? '#f59e0b' : '#3b82f6'}` }}>
            {isLive
              ? <><Wifi className="w-3 h-3" style={{ color: '#10b981' }} /><span style={{ color: '#10b981' }}>WebSocket Live</span></>
              : wsStatus === 'FALLBACK'
              ? <><WifiOff className="w-3 h-3" style={{ color: '#f59e0b' }} /><span style={{ color: '#f59e0b' }}>REST Fallback</span></>
              : <><Wifi className="w-3 h-3" style={{ color: '#3b82f6' }} /><span style={{ color: '#3b82f6' }}>Connecting...</span></>
            }
          </div>
        )}
      </div>

      {/* Toolbar */}
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
              style={{ backgroundColor: o.active ? 'var(--accent-blue)' : 'var(--bg-tertiary)', color: o.active ? 'white' : 'var(--text-secondary)' }}>
              {o.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleScreenshot} className="p-1.5 rounded hover:bg-[var(--bg-hover)]" style={{ color: 'var(--text-secondary)' }}>
            <Camera className="w-4 h-4" />
          </button>
          <button onClick={handleResetZoom} className="p-1.5 rounded hover:bg-[var(--bg-hover)]" style={{ color: 'var(--text-secondary)' }}>
            <RotateCcw className="w-4 h-4" />
          </button>
          <button onClick={handleAnalyze} disabled={analyzing}
            className="px-4 py-1.5 text-xs font-medium rounded flex items-center gap-2"
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
