import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Suppress the "ResizeObserver loop completed with undelivered notifications" error.
// This is a benign browser quirk that fires when ResizeObserver callbacks trigger
// layout changes faster than the browser can deliver them (e.g. Ctrl+- zoom).
// It does NOT indicate a real problem and never appears in production builds.
const _origError = window.onerror;
window.onerror = (msg, ...args) => {
  if (typeof msg === 'string' && msg.includes('ResizeObserver loop')) return true;
  return _origError ? _origError(msg, ...args) : false;
};
// Also suppress the react-scripts dev overlay version
const _origConsoleError = console.error;
console.error = (...args) => {
  if (args[0] && String(args[0]).includes('ResizeObserver loop')) return;
  _origConsoleError(...args);
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);