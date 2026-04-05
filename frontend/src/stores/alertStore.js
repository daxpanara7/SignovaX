import { create } from 'zustand'

export const useAlertStore = create((set, get) => ({
  // Alerts
  alerts: [],
  unreadCount: 0,
  
  // Alert preferences
  preferences: {
    telegram_enabled: false,
    email_enabled: false,
    webhook_url: '',
    min_confluence_to_alert: 70,
    sessions_to_alert: ['london', 'new_york']
  },
  
  // Loading states
  isLoadingAlerts: false,
  isUpdatingPreferences: false,
  
  // Actions
  addAlert: (alert) => set((state) => {
    const newAlert = {
      ...alert,
      id: Date.now(),
      timestamp: new Date().toISOString(),
      read: false
    }
    
    return {
      alerts: [newAlert, ...state.alerts].slice(0, 100), // Keep last 100
      unreadCount: state.unreadCount + 1
    }
  }),
  
  setAlerts: (alerts) => set({ 
    alerts,
    unreadCount: alerts.filter(a => !a.read).length
  }),
  
  markAsRead: (alertId) => set((state) => ({
    alerts: state.alerts.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ),
    unreadCount: Math.max(0, state.unreadCount - 1)
  })),
  
  markAllAsRead: () => set((state) => ({
    alerts: state.alerts.map(alert => ({ ...alert, read: true })),
    unreadCount: 0
  })),
  
  clearAllAlerts: () => set({ alerts: [], unreadCount: 0 }),
  
  removeAlert: (alertId) => set((state) => {
    const alert = state.alerts.find(a => a.id === alertId)
    const wasUnread = alert && !alert.read
    
    return {
      alerts: state.alerts.filter(a => a.id !== alertId),
      unreadCount: wasUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount
    }
  }),
  
  // Preferences
  updatePreferences: (newPreferences) => set((state) => ({
    preferences: { ...state.preferences, ...newPreferences }
  })),
  
  setIsLoadingAlerts: (loading) => set({ isLoadingAlerts: loading }),
  setIsUpdatingPreferences: (loading) => set({ isUpdatingPreferences: loading }),
  
  // Get alerts by type
  getAlertsByType: (type) => {
    const state = get()
    return state.alerts.filter(alert => alert.type === type)
  },
  
  // Get recent alerts (last 24 hours)
  getRecentAlerts: () => {
    const state = get()
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
    return state.alerts.filter(alert => new Date(alert.timestamp) > oneDayAgo)
  },
  
  // Alert type colors
  getAlertColor: (type) => {
    const colors = {
      signal: 'text-blue-400',
      risk: 'text-orange-400',
      error: 'text-red-400',
      success: 'text-green-400',
      info: 'text-gray-400'
    }
    return colors[type] || colors.info
  },
  
  // Alert type icons
  getAlertIcon: (type) => {
    const icons = {
      signal: '📊',
      risk: '⚠️',
      error: '❌',
      success: '✅',
      info: 'ℹ️'
    }
    return icons[type] || icons.info
  }
}))