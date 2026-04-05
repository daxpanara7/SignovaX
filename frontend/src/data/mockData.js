// Generate realistic mock data for the SMC Trading Terminal

export const generateMockCandles = (count = 500, startPrice = 66000) => {
  const candles = [];
  let currentTime = Date.now() - count * 15 * 60 * 1000; // 15-minute candles
  let price = startPrice;

  for (let i = 0; i < count; i++) {
    const trend = Math.random() > 0.5 ? 1 : -1;
    const volatility = Math.random() * 200 + 50;
    
    const open = price;
    const close = price + (trend * Math.random() * volatility);
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    
    candles.push({
      time: currentTime / 1000,
      open,
      high,
      low,
      close,
      volume: Math.random() * 1000000 + 500000
    });
    
    price = close;
    currentTime += 15 * 60 * 1000;
  }
  
  return candles;
};

export const mockOrderBlocks = [
  {
    id: 'ob1',
    type: 'bullish',
    price_low: 65800,
    price_high: 65950,
    formed_at: Date.now() - 7200000,
    status: 'active',
    time_start: (Date.now() - 7200000) / 1000,
    time_end: (Date.now() - 3600000) / 1000
  },
  {
    id: 'ob2',
    type: 'bearish',
    price_low: 67800,
    price_high: 68000,
    formed_at: Date.now() - 10800000,
    status: 'active',
    time_start: (Date.now() - 10800000) / 1000,
    time_end: (Date.now() - 7200000) / 1000
  },
  {
    id: 'ob3',
    type: 'bullish',
    price_low: 65200,
    price_high: 65400,
    formed_at: Date.now() - 14400000,
    status: 'mitigated',
    time_start: (Date.now() - 14400000) / 1000,
    time_end: (Date.now() - 10800000) / 1000
  }
];

export const mockFVGs = [
  {
    id: 'fvg1',
    type: 'bullish',
    price_low: 66100,
    price_high: 66300,
    fill_percent: 23,
    time_start: (Date.now() - 5400000) / 1000,
    time_end: (Date.now() - 1800000) / 1000
  },
  {
    id: 'fvg2',
    type: 'bearish',
    price_low: 66600,
    price_high: 66750,
    fill_percent: 67,
    time_start: (Date.now() - 9000000) / 1000,
    time_end: (Date.now() - 5400000) / 1000
  },
  {
    id: 'fvg3',
    type: 'bullish',
    price_low: 65500,
    price_high: 65650,
    fill_percent: 8,
    time_start: (Date.now() - 12600000) / 1000,
    time_end: (Date.now() - 9000000) / 1000
  }
];

export const mockLiquidityZones = [
  {
    id: 'liq1',
    type: 'EQH',
    price: 67150,
    swept: false,
    time: (Date.now() - 3600000) / 1000
  },
  {
    id: 'liq2',
    type: 'EQL',
    price: 65150,
    swept: true,
    time: (Date.now() - 7200000) / 1000
  },
  {
    id: 'liq3',
    type: 'EQH',
    price: 66900,
    swept: false,
    time: (Date.now() - 10800000) / 1000
  }
];

export const mockStructure = [
  {
    id: 'bos1',
    type: 'BOS',
    direction: 'bullish',
    price: 43200,
    time: (Date.now() - 5400000) / 1000
  },
  {
    id: 'choch1',
    type: 'CHOCH',
    direction: 'bearish',
    price: 43700,
    time: (Date.now() - 7200000) / 1000
  }
];

export const mockActiveSignal = {
  id: 'signal_001',
  type: 'BUY',
  symbol: 'BTCUSDT',
  timeframe: '15M',
  session: 'London Open',
  timestamp: Date.now() - 120000,
  confluence_score: 85,
  entry: 66250.00,
  stop_loss: 65800.00,
  take_profit: 67150.00,
  risk_reward: 2.1,
  ml_confidence: 71,
  risk_amount: 215,
  risk_percent: 1,
  position_size: 0.005,
  reasons: [
    '4H Order Block',
    '1H BOS Confirmed',
    'FVG Present (23% fill)',
    'Liquidity swept',
    'London session open'
  ]
};

export const mockHistoricalTrades = [
  { id: 1, time: Date.now() - 86400000, symbol: 'BTCUSDT', type: 'BUY', timeframe: '15M', entry: 42800, sl: 42400, tp: 43600, rr: 2.0, score: 78, ml: 65, status: 'TP HIT', pnl: 800, r_multiple: 2.0 },
  { id: 2, time: Date.now() - 82800000, symbol: 'ETHUSDT', type: 'SELL', timeframe: '1H', entry: 2280, sl: 2320, tp: 2200, rr: 2.0, score: 82, ml: 72, status: 'TP HIT', pnl: 400, r_multiple: 2.0 },
  { id: 3, time: Date.now() - 79200000, symbol: 'BTCUSDT', type: 'BUY', timeframe: '5M', entry: 43100, sl: 42900, tp: 43500, rr: 2.0, score: 71, ml: 58, status: 'SL HIT', pnl: -200, r_multiple: -1.0 },
  { id: 4, time: Date.now() - 72000000, symbol: 'EURUSD', type: 'BUY', timeframe: '15M', entry: 1.0850, sl: 1.0830, tp: 1.0890, rr: 2.0, score: 88, ml: 79, status: 'TP HIT', pnl: 320, r_multiple: 2.0 }
];

export const mockWatchlist = [
  { symbol: 'BTCUSDT', name: 'BTC/USDT', price: 66895.86, change: 2.3, signal: 'buy', sparkline: [65800, 65900, 66000, 65850, 65950, 66100, 66895] },
  { symbol: 'ETHUSDT', name: 'ETH/USDT', price: 2038.08, change: -0.01, signal: 'none', sparkline: [2060, 2055, 2050, 2045, 2040, 2039, 2038] }
];

export const mockMTFBias = [
  { timeframe: '4H', bias: 'BULLISH', strength: 85, direction: 'up' },
  { timeframe: '1H', bias: 'BULLISH', strength: 72, direction: 'up' },
  { timeframe: '15M', bias: 'NEUTRAL', strength: 48, direction: 'neutral' },
  { timeframe: '5M', bias: 'BEARISH', strength: 35, direction: 'down' }
];

export const mockMarketRegime = {
  status: 'TRENDING UP',
  color: 'green',
  icon: '🟢'
};

export const mockQuickStats = {
  signals_today: 4,
  win_rate: 75,
  pnl_r: 2.3,
  drawdown: -0.5
};

export const mockRiskMeter = {
  current: 35,
  max: 100,
  status: 'safe'
};

export const mockBacktestResults = {
  return: 34.2,
  win_rate: 67.3,
  sharpe: 1.84,
  max_dd: -8.2,
  trades: 142,
  profit_factor: 2.31,
  expectancy: 0.43,
  calmar: 4.17
};

export const mockEquityCurve = Array.from({ length: 30 }, (_, i) => ({
  date: Date.now() - (29 - i) * 86400000,
  equity: 10000 + i * 400 + Math.random() * 200 - 100,
  drawdown: -(Math.random() * 500)
}));

export const mockAlerts = [
  { id: 1, time: Date.now() - 1920000, type: 'signal', severity: 'success', symbol: 'BTCUSDT', message: 'BUY Signal — Score: 85' },
  { id: 2, time: Date.now() - 7200000, type: 'risk', severity: 'error', message: 'Circuit Breaker — Daily limit reached' },
  { id: 3, time: Date.now() - 9000000, type: 'news', severity: 'warning', message: 'News Event — NFP in 30 minutes' }
];