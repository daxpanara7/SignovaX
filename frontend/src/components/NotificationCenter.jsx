import React, { useState, useRef, useEffect } from 'react'
import { Bell, X, Check, Trash2, Settings } from 'lucide-react'
import { useAlertStore } from '../stores/alertStore'
import { motion, AnimatePresence } from 'framer-motion'

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)
  
  const {
    alerts,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAllAlerts,
    removeAlert,
    getAlertColor,
    getAlertIcon
  } = useAlertStore()

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `${diffDays}d ago`
    if (diffHours > 0) return `${diffHours}h ago`
    if (diffMins > 0) return `${diffMins}m ago`
    return 'Just now'
  }

  const getAlertTypeLabel = (type) => {
    const labels = {
      signal: 'Signal',
      risk: 'Risk Alert',
      error: 'Error',
      success: 'Success',
      info: 'Info'
    }
    return labels[type] || 'Notification'
  }

  const handleAlertClick = (alert) => {
    if (!alert.read) {
      markAsRead(alert.id)
    }
    
    // Handle navigation based on alert type
    if (alert.type === 'signal' && alert.data?.symbol) {
      // Navigate to chart with symbol
      console.log('Navigate to chart:', alert.data.symbol)
    }
  }

  const recentAlerts = alerts.slice(0, 10) // Show last 10 alerts

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-dark-muted hover:text-dark-text transition-colors"
      >
        <Bell className="w-5 h-5" />
        
        {/* Badge */}
        {unreadCount > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-bear rounded-full flex items-center justify-center"
          >
            <span className="text-xs font-bold text-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          </motion.div>
        )}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 top-full mt-2 w-80 bg-dark-surface border border-dark-border rounded-lg shadow-xl z-50"
          >
            {/* Header */}
            <div className="p-4 border-b border-dark-border">
              <div className="flex items-center justify-between">
                <h3 className="text-dark-text font-semibold">Notifications</h3>
                <div className="flex items-center space-x-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-bull hover:text-bull/80 transition-colors"
                    >
                      Mark all read
                    </button>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-dark-muted hover:text-dark-text transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              {unreadCount > 0 && (
                <p className="text-xs text-dark-muted mt-1">
                  {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
                </p>
              )}
            </div>

            {/* Alerts List */}
            <div className="max-h-96 overflow-y-auto">
              {recentAlerts.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="w-12 h-12 text-dark-muted mx-auto mb-3" />
                  <p className="text-dark-muted">No notifications yet</p>
                  <p className="text-xs text-dark-muted mt-1">
                    You'll see alerts and updates here
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-dark-border">
                  {recentAlerts.map((alert) => (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`p-4 hover:bg-dark-bg/50 cursor-pointer transition-colors ${
                        !alert.read ? 'bg-bull/5 border-l-2 border-l-bull' : ''
                      }`}
                      onClick={() => handleAlertClick(alert)}
                    >
                      <div className="flex items-start space-x-3">
                        {/* Icon */}
                        <div className={`flex-shrink-0 text-lg ${getAlertColor(alert.type)}`}>
                          {getAlertIcon(alert.type)}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-sm font-medium text-dark-text">
                              {getAlertTypeLabel(alert.type)}
                            </p>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-dark-muted">
                                {formatTime(alert.timestamp)}
                              </span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  removeAlert(alert.id)
                                }}
                                className="text-dark-muted hover:text-bear transition-colors"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                          
                          <p className="text-sm text-dark-muted line-clamp-2">
                            {alert.message}
                          </p>

                          {/* Alert Data */}
                          {alert.data && (
                            <div className="mt-2 p-2 bg-dark-bg rounded text-xs">
                              {alert.type === 'signal' && alert.data.symbol && (
                                <div className="flex items-center justify-between">
                                  <span className="font-mono">{alert.data.symbol}</span>
                                  <span className={`px-2 py-1 rounded ${
                                    alert.data.direction === 'BUY' 
                                      ? 'bg-bull/20 text-bull' 
                                      : 'bg-bear/20 text-bear'
                                  }`}>
                                    {alert.data.direction}
                                  </span>
                                </div>
                              )}
                              
                              {alert.data.confluence_score && (
                                <div className="flex items-center justify-between mt-1">
                                  <span>Confluence:</span>
                                  <span className="font-medium">{alert.data.confluence_score}/100</span>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Unread indicator */}
                          {!alert.read && (
                            <div className="flex items-center justify-end mt-2">
                              <div className="w-2 h-2 bg-bull rounded-full"></div>
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {recentAlerts.length > 0 && (
              <div className="p-3 border-t border-dark-border">
                <div className="flex items-center justify-between">
                  <button
                    onClick={clearAllAlerts}
                    className="flex items-center space-x-1 text-xs text-dark-muted hover:text-bear transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Clear all</span>
                  </button>
                  
                  <button
                    onClick={() => {
                      setIsOpen(false)
                      // Navigate to alert settings
                      console.log('Open alert settings')
                    }}
                    className="flex items-center space-x-1 text-xs text-dark-muted hover:text-dark-text transition-colors"
                  >
                    <Settings className="w-3 h-3" />
                    <span>Settings</span>
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default NotificationCenter