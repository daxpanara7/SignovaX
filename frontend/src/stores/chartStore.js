import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useChartStore = create(
  persist(
    (set, get) => ({
      // Chart state
      symbol: 'BTCUSDT',
      timeframe: '15m',
      htfTimeframe: '4h',
      isLive: false,
      darkMode: true,
      
      // Chart data
      chartData: [],
      smcLevels: {
        orderBlocks: [],
        fvgs: [],
        liquidityZones: [],
        bosChoch: [],
        sessionBoxes: []
      },
      
      // Chart settings
      showOrderBlocks: true,
      showFVGs: true,
      showLiquidityZones: true,
      showBosChoch: true,
      showSessionBoxes: true,
      showHTFLevels: true,
      
      // Actions
      setSymbol: (symbol) => set({ symbol }),
      setTimeframe: (timeframe) => set({ timeframe }),
      setHTFTimeframe: (htfTimeframe) => set({ htfTimeframe }),
      setIsLive: (isLive) => set({ isLive }),
      setDarkMode: (darkMode) => set({ darkMode }),
      setChartData: (chartData) => set({ chartData }),
      setSMCLevels: (smcLevels) => set({ smcLevels }),
      
      // Toggle overlays
      toggleOrderBlocks: () => set((state) => ({ showOrderBlocks: !state.showOrderBlocks })),
      toggleFVGs: () => set((state) => ({ showFVGs: !state.showFVGs })),
      toggleLiquidityZones: () => set((state) => ({ showLiquidityZones: !state.showLiquidityZones })),
      toggleBosChoch: () => set((state) => ({ showBosChoch: !state.showBosChoch })),
      toggleSessionBoxes: () => set((state) => ({ showSessionBoxes: !state.showSessionBoxes })),
      toggleHTFLevels: () => set((state) => ({ showHTFLevels: !state.showHTFLevels })),
      
      // Update SMC level
      updateSMCLevel: (type, data) => set((state) => ({
        smcLevels: {
          ...state.smcLevels,
          [type]: data
        }
      }))
    }),
    {
      name: 'chart-store',
      partialize: (state) => ({
        symbol: state.symbol,
        timeframe: state.timeframe,
        htfTimeframe: state.htfTimeframe,
        darkMode: state.darkMode,
        showOrderBlocks: state.showOrderBlocks,
        showFVGs: state.showFVGs,
        showLiquidityZones: state.showLiquidityZones,
        showBosChoch: state.showBosChoch,
        showSessionBoxes: state.showSessionBoxes,
        showHTFLevels: state.showHTFLevels
      })
    }
  )
)