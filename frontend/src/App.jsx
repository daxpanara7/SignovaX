import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Signals from './pages/Signals'
import Backtest from './pages/Backtest'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/backtest" element={<Backtest />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App