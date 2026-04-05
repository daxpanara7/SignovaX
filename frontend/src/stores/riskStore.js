import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useRiskStore = create(
  persist(
    (set, get) => ({
      // Risk settings
      riskPerTrade: 2.0, // 2% per trade
      maxDailyLoss: 6.0, // 6% max daily loss
      accountBalance: 10000, // $10,000 default
      circuitBreakerEnabled: true,
      mlFilterEnabled: true,
      sessionFilterEnabled: true,
      
      // Current risk metrics
      dailyPnL: 0,
      dailyLoss: 0,
      openPositions: [],
      totalExposure: 0,
      
      // Risk status
      circuitBreakerTriggered: false,
      riskLevel: 'LOW', // LOW, MEDIUM, HIGH, CRITICAL
      
      // Actions
      updateRiskSettings: (settings) => set((state) => ({
        ...state,
        ...settings
      })),
      
      setAccountBalance: (balance) => set({ accountBalance: balance }),
      setRiskPerTrade: (risk) => set({ riskPerTrade: risk }),
      setMaxDailyLoss: (loss) => set({ maxDailyLoss: loss }),
      
      toggleCircuitBreaker: () => set((state) => ({ 
        circuitBreakerEnabled: !state.circuitBreakerEnabled 
      })),
      toggleMLFilter: () => set((state) => ({ 
        mlFilterEnabled: !state.mlFilterEnabled 
      })),
      toggleSessionFilter: () => set((state) => ({ 
        sessionFilterEnabled: !state.sessionFilterEnabled 
      })),
      
      // Risk calculations
      calculatePositionSize: (entryPrice, stopLoss) => {
        const state = get()
        const riskAmount = state.accountBalance * (state.riskPerTrade / 100)
        const stopDistance = Math.abs(entryPrice - stopLoss)
        const positionSize = riskAmount / stopDistance
        return positionSize
      },
      
      calculateRiskReward: (entryPrice, stopLoss, takeProfit) => {
        const risk = Math.abs(entryPrice - stopLoss)
        const reward = Math.abs(takeProfit - entryPrice)
        return reward / risk
      },
      
      // Update daily metrics
      updateDailyPnL: (pnl) => set({ dailyPnL: pnl }),
      updateDailyLoss: (loss) => set({ dailyLoss: loss }),
      
      // Position management
      addPosition: (position) => set((state) => ({
        openPositions: [...state.openPositions, position]
      })),
      
      removePosition: (positionId) => set((state) => ({
        openPositions: state.openPositions.filter(p => p.id !== positionId)
      })),
      
      updateTotalExposure: (exposure) => set({ totalExposure: exposure }),
      
      // Risk level calculation
      updateRiskLevel: () => set((state) => {
        const dailyLossPercent = (state.dailyLoss / state.accountBalance) * 100
        const exposurePercent = (state.totalExposure / state.accountBalance) * 100
        
        let riskLevel = 'LOW'
        
        if (dailyLossPercent >= state.maxDailyLoss * 0.8 || exposurePercent >= 50) {
          riskLevel = 'CRITICAL'
        } else if (dailyLossPercent >= state.maxDailyLoss * 0.6 || exposurePercent >= 30) {
          riskLevel = 'HIGH'
        } else if (dailyLossPercent >= state.maxDailyLoss * 0.3 || exposurePercent >= 15) {
          riskLevel = 'MEDIUM'
        }
        
        return { riskLevel }
      }),
      
      // Circuit breaker
      triggerCircuitBreaker: () => set({ circuitBreakerTriggered: true }),
      resetCircuitBreaker: () => set({ circuitBreakerTriggered: false }),
      
      // Check if trading is allowed
      isTradingAllowed: () => {
        const state = get()
        if (state.circuitBreakerTriggered && state.circuitBreakerEnabled) return false
        
        const dailyLossPercent = (state.dailyLoss / state.accountBalance) * 100
        if (dailyLossPercent >= state.maxDailyLoss) return false
        
        return true
      }
    }),
    {
      name: 'risk-store',
      partialize: (state) => ({
        riskPerTrade: state.riskPerTrade,
        maxDailyLoss: state.maxDailyLoss,
        accountBalance: state.accountBalance,
        circuitBreakerEnabled: state.circuitBreakerEnabled,
        mlFilterEnabled: state.mlFilterEnabled,
        sessionFilterEnabled: state.sessionFilterEnabled
      })
    }
  )
)