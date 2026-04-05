import React, { useState, useEffect } from 'react'
import { Settings, Play, Square, BarChart3, Clock, Moon, Sun, Maximize2 } from 'lucide-react'
import { useChartStore } from '../stores/chartStore'
import { useSignalStore } from '../stores/signalStore'
import { useRiskStore } from '../stores/riskStore'
import { useAlertStore } from '../stores/alertStore'
import TradingChart from '../components/TradingChart'
import SignalPanel from '../components/SignalPanel'
import PerformancePanel from '../components/PerformancePanel'
import Watchlist from '../components/Watchlist'
import NotificationCenter from '../components/NotificationCenter'
import SessionHeatmap from '../components/SessionHeatmap'
import RiskConfigModal from '../components/RiskConfigModal'
import toast, { Toaster } from 'react-hot-toast'

const Dashboard = () => {
  const [activeBottomTab, setActiveBottomTab] = useState('signals')
  const [isWatchlistCollapsed, setIsWatchlistCollapsed] = useState(false)
  const [isRiskModalOpen, setIsRiskModalOpen] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const { 
    symbol, 
    timeframe, 
    htfTimeframe, 
    isLive, 
    darkMode, 
    setSymbol, 
    setTimeframe, 
    setHTFTimeframe, 
    setIsLive, 
    setDarkMode 
  } = useChartStore()

  const { activeSignal, setActiveSignal } = useSignalStore()
  const { accountBalance, dailyPnL, riskLevel } = useRiskStore()
  const { addAlert } = useAlertStore()

  // Mock data for demo
  useEffect(() => {
    // Simulate receiving a signal after 3 seconds
    const timer = setTimeout(() => {
      const mockSignal = {
        id: Date.now(),
        symbol: 'BTCUSDT',
        direction: 'BUY',
        entry_price: 45250,
        stop_loss: 44800,
        take_profit: 46150,
        confluence_score: 85,
        ml_probability: 0.73,
        session: 'london',
        timeframes: ['4h', '1h', '15m'],
        timestamp: new Date().toISOString(),
        type: 'Order Block + FVG'
      }
      
      setActiveSignal(mockSignal)
      
      addAlert({
        type: 'signal',
        message: `New ${mockSignal.direction} signal for ${mockSignal.symbol}`,
        data: mockSignal
      })
      
      toast.success('New signal generated!')
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
  const htfTimeframes = ['1h', '4h', '1d', '1w']

  const bottomTabs = [
    { id: 'signals', label: 'Signals', icon: BarChart3 },
    { id: 'backtest', label: 'Backtest', icon: Play },
    { id: 'performance', label: 'Performance', icon: BarChart3 },
    { id: 'alerts', label: 'Alerts', icon: Clock },
    { id: 'ml', label: 'ML Status', icon: Settings }
  ]

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    toast.loading('Analyzing market conditions...', { id: 'analyze' })
    
    // Simulate analysis
    setTimeout(() => {
      setIsAnalyzing(false)
      toast.success('Analysis complete', { id: 'analyze' })
    }, 2000)
  }

  const handleRunBacktest = () => {
    toast.success('Backtest started in background')
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'LOW': return 'text-bull'
      case 'MEDIUM': return 'text-warning-500'
      case 'HIGH': return 'text-orange-500'
      case 'CRITICAL': return 'text-bear'
      default: return 'text-dark-muted'
    }
  }

  return (
    <div className={`h-screen flex flex-col ${darkMode ? 'dark' : ''}`}>
      <div className="flex-1 bg-dark-bg text-dark-text overflow-hidden">
        {/* Header */}
        <div className="h-16 bg-dark-surface border-b border-dark-border flex items-center justify-between px-6">
          {/* Left: Logo & Symbol */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-bull rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">SMC</span>
              </div>
              <h1 className="text-xl font-bold">Trading Terminal</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="bg-dark-bg border border-dark-border rounded px-3 py-2 text-dark-text focus:outline-none focus:border-bull"
              >
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="ETHUSDT">ETHUSDT</option>
                <option value="ADAUSDT">ADAUSDT</option>
                <option value="SOLUSDT">SOLUSDT</option>
              </select>
              
              <div className="flex items-center space-x-1">
                {timeframes.map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      timeframe === tf
                        ? 'bg-bull text-white'
                        : 'text-dark-muted hover:text-dark-text'
                    }`}
                  >
                    {tf.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Center: Account Info */}
          <div className="flex items-center space-x-6">
            <div className="text-center">
              <div className="text-xs text-dark-muted">Balance</div>
              <div className="font-semibold">{formatCurrency(accountBalance)}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-dark-muted">P&L</div>
              <div className={`font-semibold ${dailyPnL >= 0 ? 'text-bull' : 'text-bear'}`}>
                {dailyPnL >= 0 ? '+' : ''}{formatCurrency(dailyPnL)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-dark-muted">Risk</div>
              <div className={`font-semibold ${getRiskLevelColor(riskLevel)}`}>
                {riskLevel}
              </div>
            </div>
          </div>

          {/* Right: Controls */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 text-dark-muted hover:text-dark-text transition-colors"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            
            <NotificationCenter />
            
            <button
              onClick={toggleFullscreen}
              className="p-2 text-dark-muted hover:text-dark-text transition-colors"
            >
              <Maximize2 className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => setIsRiskModalOpen(true)}
              className="p-2 text-dark-muted hover:text-dark-text transition-colors"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Watchlist Sidebar */}
          <Watchlist 
            isCollapsed={isWatchlistCollapsed}
            onToggleCollapse={() => setIsWatchlistCollapsed(!isWatchlistCollapsed)}
          />

          {/* Chart Area */}
          <div className="flex-1 flex flex-col">
            {/* Controls Bar */}
            <div className="h-12 bg-dark-surface border-b border-dark-border flex items-center justify-between px-4">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-dark-muted">HTF:</span>
                  <select
                    value={htfTimeframe}
                    onChange={(e) => setHTFTimeframe(e.target.value)}
                    className="bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-dark-text focus:outline-none focus:border-bull"
                  >
                    {htfTimeframes.map((tf) => (
                      <option key={tf} value={tf}>{tf.toUpperCase()}</option>
                    ))}
                  </select>
                </div>
                
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className={`flex items-center space-x-2 px-3 py-1 rounded text-sm font-medium transition-colors ${
                    isAnalyzing
                      ? 'bg-dark-border text-dark-muted cursor-not-allowed'
                      : 'bg-bull/20 text-bull hover:bg-bull/30'
                  }`}
                >
                  {isAnalyzing ? (
                    <div className="w-4 h-4 border-2 border-dark-muted border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <BarChart3 className="w-4 h-4" />
                  )}
                  <span>{isAnalyzing ? 'Analyzing...' : 'Analyze'}</span>
                </button>
                
                <button
                  onClick={handleRunBacktest}
                  className="flex items-center space-x-2 px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-sm font-medium hover:bg-blue-500/30 transition-colors"
                >
                  <Play className="w-4 h-4" />
                  <span>Backtest</span>
                </button>
              </div>

              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setIsLive(!isLive)}
                  className={`flex items-center space-x-2 px-3 py-1 rounded text-sm font-medium transition-colors ${
                    isLive
                      ? 'bg-bull/20 text-bull'
                      : 'bg-dark-border text-dark-muted'
                  }`}
                >
                  {isLive ? (
                    <div className="w-2 h-2 bg-bull rounded-full animate-pulse" />
                  ) : (
                    <Square className="w-3 h-3" />
                  )}
                  <span>{isLive ? 'Live' : 'Paused'}</span>
                </button>
              </div>
            </div>

            {/* Chart & Panels */}
            <div className="flex-1 flex">
              {/* Chart */}
              <div className="flex-1 bg-dark-surface">
                <TradingChart />
              </div>

              {/* Right Panels */}
              <div className="w-80 flex flex-col space-y-4 p-4">
                {/* Signal Panel */}
                <div className="h-1/2">
                  <SignalPanel />
                </div>

                {/* Session Heatmap */}
                <div className="h-1/2">
                  <SessionHeatmap />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Tabs */}
        <div className="h-64 bg-dark-surface border-t border-dark-border">
          {/* Tab Navigation */}
          <div className="flex border-b border-dark-border">
            {bottomTabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveBottomTab(tab.id)}
                  className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium transition-colors ${
                    activeBottomTab === tab.id
                      ? 'text-bull border-b-2 border-bull bg-bull/5'
                      : 'text-dark-muted hover:text-dark-text'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>

          {/* Tab Content */}
          <div className="flex-1 p-4">
            {activeBottomTab === 'performance' && <PerformancePanel />}
            {activeBottomTab === 'signals' && (
              <div className="text-center text-dark-muted">
                <BarChart3 className="w-12 h-12 mx-auto mb-3" />
                <p>Signal analysis panel coming soon</p>
              </div>
            )}
            {activeBottomTab === 'backtest' && (
              <div className="text-center text-dark-muted">
                <Play className="w-12 h-12 mx-auto mb-3" />
                <p>Backtest configuration panel coming soon</p>
              </div>
            )}
            {activeBottomTab === 'alerts' && (
              <div className="text-center text-dark-muted">
                <Clock className="w-12 h-12 mx-auto mb-3" />
                <p>Alert management panel coming soon</p>
              </div>
            )}
            {activeBottomTab === 'ml' && (
              <div className="text-center text-dark-muted">
                <Settings className="w-12 h-12 mx-auto mb-3" />
                <p>ML model status panel coming soon</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Risk Config Modal */}
      <RiskConfigModal 
        isOpen={isRiskModalOpen}
        onClose={() => setIsRiskModalOpen(false)}
      />

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1a1a1a',
            color: '#e5e5e5',
            border: '1px solid #2a2a2a'
          },
          success: {
            iconTheme: {
              primary: '#00d4aa',
              secondary: '#1a1a1a'
            }
          },
          error: {
            iconTheme: {
              primary: '#ff6b6b',
              secondary: '#1a1a1a'
            }
          }
        }}
      />
    </div>
  )
}

export default Dashboard