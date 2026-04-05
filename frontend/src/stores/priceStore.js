import { create } from 'zustand'

export const usePriceStore = create((set, get) => ({
  // Real-time price data
  prices: {},
  
  // Connection status
  isConnected: false,
  lastUpdate: null,
  
  // Actions
  updatePrices: (priceData) => set((state) => ({
    prices: { ...state.prices, ...priceData },
    lastUpdate: new Date().toISOString()
  })),
  
  setConnectionStatus: (connected) => set({ isConnected: connected }),
  
  // Get price for a symbol
  getPrice: (symbol) => {
    const state = get()
    return state.prices[symbol] || null
  },
  
  // Get all prices
  getAllPrices: () => {
    const state = get()
    return state.prices
  },
  
  // Clear all prices
  clearPrices: () => set({ prices: {}, lastUpdate: null })
}))