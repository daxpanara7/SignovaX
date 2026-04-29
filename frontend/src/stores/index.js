import { create } from 'zustand';
import { mockActiveSignal, mockHistoricalTrades } from '../data/mockData';

// Import individual stores
export { usePriceStore } from './priceStore';

export const useSignalStore = create((set, get) => ({
  activeSignal: mockActiveSignal,
  historicalSignals: mockHistoricalTrades,
  signalHistory: mockHistoricalTrades, // alias used by SignalPanel
  scanning: false,
  lastAnalyzed: Date.now() - 120000,
  mlFilterEnabled: true,
  mlThreshold: 60,
  
  setActiveSignal: (signal) => set({ activeSignal: signal }),
  clearActiveSignal: () => set({ activeSignal: null }),
  addHistoricalSignal: (signal) => set((state) => ({
    historicalSignals: [signal, ...state.historicalSignals],
    signalHistory:     [signal, ...state.signalHistory],
  })),
  setScanning: (scanning) => set({ scanning }),
  updateLastAnalyzed: () => set({ lastAnalyzed: Date.now() }),
  setMLFilter: (enabled, threshold) => set({ 
    mlFilterEnabled: enabled, 
    mlThreshold: threshold 
  })
}));

export const useChartStore = create((set, get) => ({
  symbol: 'BTCUSDT',
  timeframe: '15m',
  htf: '4h',
  overlays: {
    orderBlocks: true,
    fvgs: true,
    liquidity: true,
    structure: true,
    sessions: false,
    levels: true,
    htf: false,
    confluence: false
  },
  
  // SMC Data
  smcData: {
    orderBlocks: [],
    fairValueGaps: [],
    liquidityZones: [],
    structureEvents: []
  },
  
  // MTF Data
  mtfData: {
    confluence_score: 0,
    htf_bias: 'neutral',
    mtf_bias: 'neutral',
    ltf_bias: 'neutral',
    confluence_factors: []
  },
  
  setSymbol: (symbol) => set({ symbol }),
  setTimeframe: (timeframe) => set({ timeframe }),
  setHTF: (htf) => set({ htf }),
  toggleOverlay: (overlay) => set((state) => ({
    overlays: {
      ...state.overlays,
      [overlay]: !state.overlays[overlay]
    }
  })),
  
  updateSMCData: (smcData) => set({ smcData }),
  updateMTFData: (mtfData) => set({ mtfData }),
  
  // Get active patterns (non-mitigated/non-filled)
  getActivePatterns: () => {
    const { smcData } = get();
    return {
      orderBlocks: smcData.orderBlocks?.filter(ob => !ob.mitigated) || [],
      fvgs: smcData.fairValueGaps?.filter(fvg => !fvg.filled) || [],
      liquidityZones: smcData.liquidityZones?.filter(lz => !lz.swept) || []
    };
  }
}));

export const useRiskStore = create((set, get) => ({
  balance: 12450.30,
  todayPnL: 234.50,
  todayPnLPercent: 1.9,
  riskPerTrade: 1,
  maxDailyLoss: 5,
  minRR: 1.5,
  maxConcurrentTrades: 3,
  circuitBreaker: true,
  mlFilter: true,
  mlThreshold: 60,
  currentRisk: 35,
  
  // Risk metrics from backend
  riskMetrics: {
    daily_pnl: 0,
    daily_loss_pct: 0,
    concurrent_trades: 0,
    circuit_breaker_active: false,
    max_daily_loss_reached: false
  },
  
  updateBalance: (balance) => set({ balance }),
  updatePnL: (pnl, percent) => set({ todayPnL: pnl, todayPnLPercent: percent }),
  updateRiskSettings: (settings) => set(settings),
  updateRiskMetrics: (metrics) => set({ riskMetrics: metrics }),
  
  // Calculate position size
  calculatePositionSize: async (entry, stopLoss) => {
    const { balance, riskPerTrade } = get();
    const riskAmount = balance * (riskPerTrade / 100);
    const pipRisk = Math.abs(entry - stopLoss);
    return pipRisk > 0 ? riskAmount / pipRisk : 0;
  }
}));

export const useAlertStore = create((set, get) => ({
  alerts: [],
  unreadCount: 2,
  notifications: {
    telegram: false,
    email: false,
    browser: true,
    sound: true
  },
  
  // Alert settings
  alertSettings: {
    telegram_enabled: false,
    email_enabled: false,
    browser_enabled: true,
    sound_enabled: true,
    telegram_bot_token: '',
    telegram_chat_id: '',
    email_smtp_server: '',
    email_username: '',
    email_password: ''
  },
  
  addAlert: (alert) => set((state) => ({
    alerts: [{ ...alert, id: Date.now(), timestamp: new Date() }, ...state.alerts],
    unreadCount: state.unreadCount + 1
  })),
  clearAlerts: () => set({ alerts: [], unreadCount: 0 }),
  markAsRead: () => set({ unreadCount: 0 }),
  updateNotifications: (notifications) => set({ notifications }),
  updateAlertSettings: (settings) => set({ alertSettings: settings }),
  
  // Load alerts from backend
  loadAlerts: (alerts) => set({ 
    alerts: alerts.map(alert => ({
      ...alert,
      timestamp: new Date(alert.timestamp)
    }))
  })
}));

export const useBacktestStore = create((set, get) => ({
  // Current backtest configuration
  config: {
    symbol: 'BTCUSDT',
    timeframe: '15m',
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    initial_balance: 10000,
    risk_per_trade: 1,
    use_ml_filter: true,
    ml_threshold: 60
  },
  
  // Backtest results
  results: null,
  isRunning: false,
  progress: 0,
  
  // Advanced backtest results
  walkForwardResults: null,
  monteCarloResults: null,
  
  updateConfig: (config) => set((state) => ({
    config: { ...state.config, ...config }
  })),
  
  setResults: (results) => set({ results }),
  setRunning: (isRunning) => set({ isRunning }),
  setProgress: (progress) => set({ progress }),
  
  setWalkForwardResults: (results) => set({ walkForwardResults: results }),
  setMonteCarloResults: (results) => set({ monteCarloResults: results }),
  
  clearResults: () => set({ 
    results: null, 
    walkForwardResults: null, 
    monteCarloResults: null,
    progress: 0 
  })
}));

export const useSessionStore = create((set, get) => ({
  // Current session data
  currentSession: 'london',
  sessionData: {
    london: { active: false, start: '08:00', end: '17:00', volatility: 'medium' },
    newyork: { active: true, start: '13:00', end: '22:00', volatility: 'high' },
    tokyo: { active: false, start: '00:00', end: '09:00', volatility: 'low' },
    sydney: { active: false, start: '22:00', end: '07:00', volatility: 'low' }
  },
  
  // Session heatmap data
  heatmapData: [],
  
  updateSessionData: (data) => set({ sessionData: data }),
  setCurrentSession: (session) => set({ currentSession: session }),
  updateHeatmapData: (data) => set({ heatmapData: data }),
  
  // Get active session
  getActiveSession: () => {
    const { sessionData } = get();
    return Object.entries(sessionData).find(([_, data]) => data.active)?.[0] || null;
  }
}));

export const useMLStore = create((set, get) => ({
  // ML Filter status
  isEnabled: true,
  threshold: 60,
  accuracy: 0.73,
  precision: 0.68,
  recall: 0.81,
  
  // Training status
  isTraining: false,
  trainingProgress: 0,
  lastTrainingDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
  
  // Model metrics
  metrics: {
    accuracy: 0.73,
    precision: 0.68,
    recall: 0.81,
    f1_score: 0.74,
    total_signals_processed: 1247,
    signals_filtered: 312
  },
  
  updateSettings: (enabled, threshold) => set({ 
    isEnabled: enabled, 
    threshold: threshold 
  }),
  
  updateMetrics: (metrics) => set({ metrics }),
  setTraining: (isTraining, progress = 0) => set({ 
    isTraining, 
    trainingProgress: progress 
  }),
  
  updateTrainingDate: () => set({ lastTrainingDate: new Date() })
}));