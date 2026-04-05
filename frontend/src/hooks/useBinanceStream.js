/**
 * useBinanceStream
 *
 * Single WebSocket connection to Binance combined stream.
 * Handles: miniTicker (price) + kline (candles) for multiple symbols.
 * Auto-reconnects on disconnect. Falls back to REST polling if WS fails 3x.
 *
 * Binance combined stream URL:
 *   wss://stream.binance.com:9443/stream?streams=s1/s2/s3
 *
 * Stream names:
 *   btcusdt@miniTicker   → live price, 24h change, volume (every ~1s)
 *   btcusdt@kline_15m    → candle updates on every trade tick
 */

import { useEffect, useRef, useCallback } from 'react';

const WS_BASE = 'wss://stream.binance.com:9443/stream';
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY_MS = 2000;

/**
 * @param {string[]} symbols      e.g. ['BTCUSDT','ETHUSDT']
 * @param {string}   klineSymbol  the symbol whose kline we stream (active chart symbol)
 * @param {string}   klineInterval e.g. '15m'
 * @param {object}   handlers
 *   handlers.onTicker(symbol, { price, change, volume, high, low })
 *   handlers.onKline(symbol, interval, candle { time, open, high, low, close, volume, isClosed })
 *   handlers.onStatus('LIVE' | 'FALLBACK' | 'CONNECTING')
 */
export function useBinanceStream(symbols, klineSymbol, klineInterval, handlers) {
  const wsRef            = useRef(null);
  const reconnectCount   = useRef(0);
  const reconnectTimer   = useRef(null);
  const handlersRef      = useRef(handlers);
  const mountedRef       = useRef(true);
  const fallbackTimer    = useRef(null);

  // Keep handlers ref fresh without re-running the effect
  useEffect(() => { handlersRef.current = handlers; });

  const buildStreamUrl = useCallback((syms, kSym, kInt) => {
    const tickers = syms.map(s => `${s.toLowerCase()}@miniTicker`);
    const kline   = `${kSym.toLowerCase()}@kline_${kInt}`;
    const streams = [...new Set([...tickers, kline])].join('/');
    return `${WS_BASE}?streams=${streams}`;
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    handlersRef.current?.onStatus?.('CONNECTING');

    const url = buildStreamUrl(symbols, klineSymbol, klineInterval);
    const ws  = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      reconnectCount.current = 0;
      clearTimeout(fallbackTimer.current);
      handlersRef.current?.onStatus?.('LIVE');
    };

    ws.onmessage = (evt) => {
      if (!mountedRef.current) return;
      try {
        const msg    = JSON.parse(evt.data);
        const stream = msg.stream || '';
        const data   = msg.data   || msg;

        if (stream.includes('@miniTicker')) {
          // { e, E, s, c, o, h, l, v, q }
          const sym = data.s; // e.g. "BTCUSDT"
          handlersRef.current?.onTicker?.(sym, {
            price:  parseFloat(data.c),
            open:   parseFloat(data.o),
            high:   parseFloat(data.h),
            low:    parseFloat(data.l),
            volume: parseFloat(data.v),
            // 24h change % = (close - open) / open * 100
            change: ((parseFloat(data.c) - parseFloat(data.o)) / parseFloat(data.o)) * 100,
          });
        } else if (stream.includes('@kline_')) {
          // { e, E, s, k: { t, T, s, i, o, c, h, l, v, x, ... } }
          const k   = data.k;
          const sym = data.s;
          handlersRef.current?.onKline?.(sym, k.i, {
            time:     Math.floor(k.t / 1000), // ms → seconds
            open:     parseFloat(k.o),
            high:     parseFloat(k.h),
            low:      parseFloat(k.l),
            close:    parseFloat(k.c),
            volume:   parseFloat(k.v),
            isClosed: k.x, // true when candle is finalized
          });
        }
      } catch (e) {
        // malformed message — ignore
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror — handle reconnect there
    };

    ws.onclose = (evt) => {
      if (!mountedRef.current) return;

      if (reconnectCount.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectCount.current++;
        const delay = RECONNECT_DELAY_MS * reconnectCount.current;
        handlersRef.current?.onStatus?.('CONNECTING');
        reconnectTimer.current = setTimeout(connect, delay);
      } else {
        // Exhausted reconnects — signal fallback mode
        handlersRef.current?.onStatus?.('FALLBACK');
      }
    };
  }, [symbols, klineSymbol, klineInterval, buildStreamUrl]);

  // Connect on mount / when symbol or interval changes
  useEffect(() => {
    mountedRef.current = true;
    reconnectCount.current = 0;

    // Close existing connection cleanly
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect loop
      wsRef.current.close();
    }
    clearTimeout(reconnectTimer.current);

    connect();

    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      clearTimeout(fallbackTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);
}
