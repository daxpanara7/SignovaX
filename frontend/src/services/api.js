import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      // Could redirect to login here
    }
    return Promise.reject(error);
  }
);

// Authentication
export const login = async (username, password) => {
  try {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('auth_token');
};

// Data Management
export const fetchData = async (symbol, timeframe, limit = 500) => {
  try {
    const response = await api.get('/data/ohlcv', {
      params: { symbol, timeframe, limit }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch data:', error);
    return null;
  }
};

export const fetchMultiTimeframeData = async (symbol, timeframes) => {
  try {
    const response = await api.post('/data/multi-timeframe', {
      symbol,
      timeframes
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch multi-timeframe data:', error);
    return null;
  }
};

// Analysis & Signals
export const analyzeMarket = async (symbol, timeframe) => {
  try {
    const response = await api.post('/analysis/analyze', {
      symbol,
      timeframe
    });
    return response.data;
  } catch (error) {
    console.error('Failed to analyze market:', error);
    return null;
  }
};

export const fetchSignals = async (symbol = null, limit = 50) => {
  try {
    const params = { limit };
    if (symbol) params.symbol = symbol;
    
    const response = await api.get('/signals/current', { params });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch signals:', error);
    return null;
  }
};

export const generateSignal = async (symbol, timeframe) => {
  try {
    const response = await api.post('/signals/generate', {
      symbol,
      timeframe
    });
    return response.data;
  } catch (error) {
    console.error('Failed to generate signal:', error);
    return null;
  }
};

// MTF Confluence Analysis
export const analyzeMTFConfluence = async (symbol, timeframes) => {
  try {
    const response = await api.post('/mtf/analyze', {
      symbol,
      timeframes
    });
    return response.data;
  } catch (error) {
    console.error('Failed to analyze MTF confluence:', error);
    return null;
  }
};

// Precise SMC Analysis
export const analyzeSMC = async (symbol, timeframe) => {
  try {
    const response = await api.post('/smc/analyze', {
      symbol,
      timeframe
    });
    return response.data;
  } catch (error) {
    console.error('Failed to analyze SMC:', error);
    return null;
  }
};

export const fetchOrderBlocks = async (symbol, timeframe) => {
  try {
    const response = await api.get('/smc/order-blocks', {
      params: { symbol, timeframe }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch order blocks:', error);
    return null;
  }
};

export const fetchFVGs = async (symbol, timeframe) => {
  try {
    const response = await api.get('/smc/fvg', {
      params: { symbol, timeframe }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch FVGs:', error);
    return null;
  }
};

export const fetchLiquidityZones = async (symbol, timeframe) => {
  try {
    const response = await api.get('/smc/liquidity', {
      params: { symbol, timeframe }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch liquidity zones:', error);
    return null;
  }
};

// Risk Management
export const fetchRiskStatus = async () => {
  try {
    const response = await api.get('/risk/status');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch risk status:', error);
    return null;
  }
};

export const calculatePositionSize = async (entry, stopLoss, riskPercent) => {
  try {
    const response = await api.get('/risk/position-size', {
      params: { entry, sl: stopLoss, risk_pct: riskPercent }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to calculate position size:', error);
    return null;
  }
};

export const validateSignal = async (signal) => {
  try {
    const response = await api.post('/risk/validate', signal);
    return response.data;
  } catch (error) {
    console.error('Failed to validate signal:', error);
    return null;
  }
};

// Backtesting
export const runBacktest = async (config) => {
  try {
    const response = await api.post('/backtest/run', config);
    return response.data;
  } catch (error) {
    console.error('Failed to run backtest:', error);
    return null;
  }
};

export const runAdvancedBacktest = async (config) => {
  try {
    const response = await api.post('/advanced-backtest/run', config);
    return response.data;
  } catch (error) {
    console.error('Failed to run advanced backtest:', error);
    return null;
  }
};

export const runWalkForwardTest = async (config) => {
  try {
    const response = await api.post('/advanced-backtest/walkforward', config);
    return response.data;
  } catch (error) {
    console.error('Failed to run walk-forward test:', error);
    return null;
  }
};

export const runMonteCarloSimulation = async (config) => {
  try {
    const response = await api.post('/advanced-backtest/montecarlo', config);
    return response.data;
  } catch (error) {
    console.error('Failed to run Monte Carlo simulation:', error);
    return null;
  }
};

export const fetchBacktestResults = async (resultId) => {
  try {
    const response = await api.get(`/advanced-backtest/results/${resultId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch backtest results:', error);
    return null;
  }
};

// ML Signal Filter
export const trainMLFilter = async (config) => {
  try {
    const response = await api.post('/ml/train', config);
    return response.data;
  } catch (error) {
    console.error('Failed to train ML filter:', error);
    return null;
  }
};

export const filterSignal = async (signal) => {
  try {
    const response = await api.post('/ml/filter', signal);
    return response.data;
  } catch (error) {
    console.error('Failed to filter signal:', error);
    return null;
  }
};

export const getMLMetrics = async () => {
  try {
    const response = await api.get('/ml/metrics');
    return response.data;
  } catch (error) {
    console.error('Failed to get ML metrics:', error);
    return null;
  }
};

// Session Management
export const fetchSessionData = async (date = null) => {
  try {
    const params = date ? { date } : {};
    const response = await api.get('/sessions/data', { params });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch session data:', error);
    return null;
  }
};

export const fetchSessionHeatmap = async (symbol, days = 30) => {
  try {
    const response = await api.get('/sessions/heatmap', {
      params: { symbol, days }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch session heatmap:', error);
    return null;
  }
};

// Alert System
export const fetchAlerts = async (limit = 50) => {
  try {
    const response = await api.get('/alerts/list', {
      params: { limit }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch alerts:', error);
    return null;
  }
};

export const createAlert = async (alert) => {
  try {
    const response = await api.post('/alerts/create', alert);
    return response.data;
  } catch (error) {
    console.error('Failed to create alert:', error);
    return null;
  }
};

export const updateAlertSettings = async (settings) => {
  try {
    const response = await api.post('/alerts/settings', settings);
    return response.data;
  } catch (error) {
    console.error('Failed to update alert settings:', error);
    return null;
  }
};

export const testAlert = async (type, message) => {
  try {
    const response = await api.post('/alerts/test', { type, message });
    return response.data;
  } catch (error) {
    console.error('Failed to test alert:', error);
    return null;
  }
};

// Health Check
export const checkHealth = async () => {
  try {
    // Use the correct health endpoint (not under /api)
    const response = await axios.get(`${BACKEND_URL}/health`, {
      timeout: 5000
    });
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
};

export default api;
