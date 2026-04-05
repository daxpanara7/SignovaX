import { create } from 'zustand'

export const useSignalStore = create((set, get) => ({
  // Current active signal
  activeSignal: null,
  
  // Signal history
  signalHistory: [],
  
  // Signal filters
  filters: {
    minConfluence: 70,
    requireMLApproval: true,
    sessionFilter: true,
    allowedSessions: ['london', 'new_york']
  },
  
  // Loading states
  isGeneratingSignal: false,
  isLoadingHistory: false,
  
  // Actions
  setActiveSignal: (signal) => set({ activeSignal: signal }),
  
  addSignalToHistory: (signal) => set((state) => ({
    signalHistory: [signal, ...state.signalHistory].slice(0, 100) // Keep last 100
  })),
  
  setSignalHistory: (history) => set({ signalHistory: history }),
  
  updateFilters: (newFilters) => set((state) => ({
    filters: { ...state.filters, ...newFilters }
  })),
  
  setIsGeneratingSignal: (loading) => set({ isGeneratingSignal: loading }),
  setIsLoadingHistory: (loading) => set({ isLoadingHistory: loading }),
  
  // Clear active signal
  clearActiveSignal: () => set({ activeSignal: null }),
  
  // Get signal by ID
  getSignalById: (id) => {
    const state = get()
    return state.signalHistory.find(signal => signal.id === id) || state.activeSignal
  },
  
  // Get signals by symbol
  getSignalsBySymbol: (symbol) => {
    const state = get()
    return state.signalHistory.filter(signal => signal.symbol === symbol)
  },
  
  // Calculate signal age
  getSignalAge: (signal) => {
    if (!signal || !signal.timestamp) return 'Unknown'
    
    const now = new Date()
    const signalTime = new Date(signal.timestamp)
    const diffMs = now - signalTime
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffDays > 0) return `${diffDays}d ago`
    if (diffHours > 0) return `${diffHours}h ago`
    if (diffMins > 0) return `${diffMins}m ago`
    return 'Just now'
  }
}))