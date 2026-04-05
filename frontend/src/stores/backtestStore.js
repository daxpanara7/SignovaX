import { create } from 'zustand'

export const useBacktestStore = create((set, get) => ({
  // Backtest results
  currentResults: null,
  resultsHistory: [],
  
  // Backtest configuration
  config: {
    symbol: 'BTCUSDT',
    timeframe: '15m',
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    endDate: new Date().toISOString().split('T')[0],
    initialBalance: 10000,
    riskPerTrade: 2.0,
    useMLFilter: true,
    useSessionFilter: true,
    walkForwardEnabled: false,
    monteCarloRuns: 1000
  },
  
  // Loading states
  isRunningBacktest: false,
  isLoadingResults: false,
  
  // Progress tracking
  backtestProgress: 0,
  currentStep: '',
  
  // Actions
  setCurrentResults: (results) => set({ currentResults: results }),
  
  addToHistory: (results) => set((state) => ({
    resultsHistory: [results, ...state.resultsHistory].slice(0, 20) // Keep last 20
  })),
  
  setResultsHistory: (history) => set({ resultsHistory: history }),
  
  updateConfig: (newConfig) => set((state) => ({
    config: { ...state.config, ...newConfig }
  })),
  
  setIsRunningBacktest: (running) => set({ isRunningBacktest: running }),
  setIsLoadingResults: (loading) => set({ isLoadingResults: loading }),
  
  updateProgress: (progress, step) => set({ 
    backtestProgress: progress,
    currentStep: step 
  }),
  
  resetProgress: () => set({ 
    backtestProgress: 0,
    currentStep: '' 
  }),
  
  // Get results by ID
  getResultsById: (id) => {
    const state = get()
    return state.resultsHistory.find(result => result.id === id) || state.currentResults
  },
  
  // Calculate performance metrics
  calculateSharpeRatio: (returns, riskFreeRate = 0.02) => {
    if (!returns || returns.length === 0) return 0
    
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    const stdDev = Math.sqrt(variance)
    
    return stdDev === 0 ? 0 : (avgReturn - riskFreeRate) / stdDev
  },
  
  calculateMaxDrawdown: (equityCurve) => {
    if (!equityCurve || equityCurve.length === 0) return 0
    
    let maxDrawdown = 0
    let peak = equityCurve[0]
    
    for (let i = 1; i < equityCurve.length; i++) {
      if (equityCurve[i] > peak) {
        peak = equityCurve[i]
      } else {
        const drawdown = (peak - equityCurve[i]) / peak
        maxDrawdown = Math.max(maxDrawdown, drawdown)
      }
    }
    
    return maxDrawdown * 100 // Return as percentage
  },
  
  calculateWinRate: (trades) => {
    if (!trades || trades.length === 0) return 0
    
    const winningTrades = trades.filter(trade => trade.pnl > 0).length
    return (winningTrades / trades.length) * 100
  },
  
  calculateProfitFactor: (trades) => {
    if (!trades || trades.length === 0) return 0
    
    const grossProfit = trades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0)
    const grossLoss = Math.abs(trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0))
    
    return grossLoss === 0 ? (grossProfit > 0 ? Infinity : 0) : grossProfit / grossLoss
  },
  
  // Format currency
  formatCurrency: (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  },
  
  // Format percentage
  formatPercentage: (value, decimals = 2) => {
    return `${value.toFixed(decimals)}%`
  },
  
  // Clear results
  clearCurrentResults: () => set({ currentResults: null }),
  clearHistory: () => set({ resultsHistory: [] })
}))