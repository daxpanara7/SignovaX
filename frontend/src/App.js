import React, { useEffect, useState } from 'react';
import './styles/globals.css';
import Header from './components/Header';
import Watchlist from './components/Watchlist';
import ChartPanel from './components/ChartPanel';
import SignalPanel from './components/SignalPanel';
import BottomPanel from './components/BottomPanel';
import useWebSocket from './hooks/useWebSocket';
import { useSignalStore, useRiskStore, useAlertStore, useChartStore, usePriceStore } from './stores';
import { checkHealth, fetchRiskStatus, fetchSignals, login } from './services/api';
import { Info, AlertTriangle } from 'lucide-react';

function App() {
  const [showDemoBanner, setShowDemoBanner] = useState(true);
  const [backendStatus, setBackendStatus] = useState('checking');
  const { setActiveSignal, addHistoricalSignal } = useSignalStore();
  const { updatePnL, updateRiskMetrics } = useRiskStore();
  const { addAlert } = useAlertStore();
  const { updateSMCData, updateMTFData } = useChartStore();
  const { updatePrices, setConnectionStatus } = usePriceStore();

  // Check backend health on startup
  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const health = await checkHealth();
        if (health && health.status === 'healthy') {
          setBackendStatus('connected');
          
          // Try auto-login if no token exists
          const existingToken = localStorage.getItem('auth_token');
          if (!existingToken && process.env.REACT_APP_AUTO_LOGIN === 'true') {
            console.log('Attempting auto-login...');
            try {
              const loginResult = await login(
                process.env.REACT_APP_DEFAULT_USERNAME || 'admin',
                process.env.REACT_APP_DEFAULT_PASSWORD || 'smc_admin_2024'
              );
              if (loginResult && loginResult.access_token) {
                console.log('Auto-login successful');
                setBackendStatus('connected');
                // Wait a moment for token to be set, then load data
                setTimeout(() => {
                  loadInitialData();
                }, 500);
                return; // Don't load data immediately
              }
            } catch (loginError) {
              console.error('Auto-login failed:', loginError);
            }
          } else if (existingToken) {
            console.log('Using existing auth token');
          }
          
          // Load initial data
          loadInitialData();
        } else {
          setBackendStatus('disconnected');
        }
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendStatus('disconnected');
      }
    };

    checkBackendHealth();
    
    // Check health every 30 seconds
    const healthInterval = setInterval(checkBackendHealth, 30000);
    
    return () => clearInterval(healthInterval);
  }, []);

  const loadInitialData = async () => {
    try {
      // Load risk status
      const riskStatus = await fetchRiskStatus();
      if (riskStatus) {
        updateRiskMetrics(riskStatus);
      }

      // Load recent signals
      const signals = await fetchSignals(null, 10);
      if (signals && Array.isArray(signals) && signals.length > 0) {
        // Set most recent as active if it's still active
        const activeSignal = signals.find(s => s && s.status === 'ACTIVE');
        if (activeSignal) {
          setActiveSignal(activeSignal);
        }
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data);
    
    try {
      switch (data.type) {
        case 'connection':
          console.log('✅ Connected to backend:', data.message);
          break;
          
        case 'price_update':
          console.log('📈 Price update received:', data.data || data);
          // Update the price store with real-time data
          if (data.data && typeof data.data === 'object') {
            updatePrices(data.data);
            setConnectionStatus(true);
          }
          break;
          
        case 'new_signal':
          if (data.signal) {
            setActiveSignal(data.signal);
            addAlert({
              type: 'signal',
              title: 'New Trading Signal',
              message: `${data.signal.signal_type || 'Unknown'} signal for ${data.signal.symbol || 'Unknown'}`,
              severity: 'info'
            });
          }
          break;
          
        case 'signal_filled':
          if (data.signal) {
            addHistoricalSignal(data.signal);
            addAlert({
              type: 'trade',
              title: 'Signal Filled',
              message: `${data.signal.signal_type || 'Unknown'} signal filled at ${data.signal.entry_price || 'Unknown'}`,
              severity: 'success'
            });
          }
          break;
          
        case 'circuit_breaker':
          addAlert({
            type: 'risk',
            title: 'Circuit Breaker Activated',
            message: 'Daily loss limit reached. Trading halted.',
            severity: 'error'
          });
          break;
          
        case 'risk_update':
          if (data.metrics) {
            updateRiskMetrics(data.metrics);
          }
          break;
          
        case 'smc_update':
          if (data.smc_data) {
            updateSMCData(data.smc_data);
          }
          break;
          
        case 'mtf_update':
          if (data.mtf_data) {
            updateMTFData(data.mtf_data);
          }
          break;
          
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error, data);
    }
  };

  const { connected } = useWebSocket(handleWebSocketMessage);

  // Update price store connection status when WebSocket status changes
  React.useEffect(() => {
    setConnectionStatus(connected);
  }, [connected, setConnectionStatus]);

  const getBannerConfig = () => {
    if (backendStatus === 'checking') {
      return {
        color: 'var(--accent-blue)',
        icon: Info,
        message: '🔄 Checking backend connection...'
      };
    } else if (backendStatus === 'disconnected') {
      return {
        color: 'var(--accent-red)',
        icon: AlertTriangle,
        message: '⚠️ DEMO MODE — Backend disconnected. Connect backend at localhost:8000 for live data'
      };
    } else if (!connected) {
      return {
        color: 'var(--accent-yellow)',
        icon: AlertTriangle,
        message: '⚠️ WebSocket disconnected — Reconnecting for real-time updates...'
      };
    }
    // If backend is connected AND WebSocket is connected, no banner (live mode)
    return null;
  };

  const bannerConfig = getBannerConfig();

  return (
    <div className="trading-terminal" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Status Banner */}
      {bannerConfig && showDemoBanner && (
        <div 
          data-testid="status-banner" 
          className="flex items-center justify-between px-4 py-2" 
          style={{ backgroundColor: bannerConfig.color, color: '#000' }}
        >
          <div className="flex items-center gap-2">
            <bannerConfig.icon className="w-4 h-4" />
            <span className="text-sm font-medium">
              {bannerConfig.message}
            </span>
          </div>
          <button
            data-testid="dismiss-banner"
            onClick={() => setShowDemoBanner(false)}
            className="text-xs font-medium px-3 py-1 rounded hover:bg-black/10 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <Header backendStatus={backendStatus} />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Watchlist */}
        <Watchlist />

        {/* Center: Chart + Signal Panel */}
        <div className="flex-1 flex overflow-hidden">
          <ChartPanel />
          <SignalPanel />
        </div>
      </div>

      {/* Bottom Panel */}
      <BottomPanel />
    </div>
  );
}

export default App;