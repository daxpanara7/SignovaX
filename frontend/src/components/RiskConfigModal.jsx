import React, { useState, useEffect } from 'react'
import { X, Save, AlertTriangle, Shield, Brain, Globe, DollarSign } from 'lucide-react'
import { useRiskStore } from '../stores/riskStore'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

const RiskConfigModal = ({ isOpen, onClose }) => {
  const {
    riskPerTrade,
    maxDailyLoss,
    accountBalance,
    circuitBreakerEnabled,
    mlFilterEnabled,
    sessionFilterEnabled,
    updateRiskSettings,
    riskLevel
  } = useRiskStore()

  const [formData, setFormData] = useState({
    riskPerTrade: riskPerTrade,
    maxDailyLoss: maxDailyLoss,
    accountBalance: accountBalance,
    circuitBreakerEnabled: circuitBreakerEnabled,
    mlFilterEnabled: mlFilterEnabled,
    sessionFilterEnabled: sessionFilterEnabled
  })

  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setFormData({
        riskPerTrade,
        maxDailyLoss,
        accountBalance,
        circuitBreakerEnabled,
        mlFilterEnabled,
        sessionFilterEnabled
      })
      setHasChanges(false)
    }
  }, [isOpen, riskPerTrade, maxDailyLoss, accountBalance, circuitBreakerEnabled, mlFilterEnabled, sessionFilterEnabled])

  useEffect(() => {
    const hasFormChanges = 
      formData.riskPerTrade !== riskPerTrade ||
      formData.maxDailyLoss !== maxDailyLoss ||
      formData.accountBalance !== accountBalance ||
      formData.circuitBreakerEnabled !== circuitBreakerEnabled ||
      formData.mlFilterEnabled !== mlFilterEnabled ||
      formData.sessionFilterEnabled !== sessionFilterEnabled

    setHasChanges(hasFormChanges)
  }, [formData, riskPerTrade, maxDailyLoss, accountBalance, circuitBreakerEnabled, mlFilterEnabled, sessionFilterEnabled])

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSave = () => {
    // Validation
    if (formData.riskPerTrade <= 0 || formData.riskPerTrade > 10) {
      toast.error('Risk per trade must be between 0.1% and 10%')
      return
    }

    if (formData.maxDailyLoss <= 0 || formData.maxDailyLoss > 20) {
      toast.error('Max daily loss must be between 0.1% and 20%')
      return
    }

    if (formData.accountBalance <= 0) {
      toast.error('Account balance must be greater than 0')
      return
    }

    // Save settings
    updateRiskSettings(formData)
    
    // Save to localStorage for persistence
    localStorage.setItem('riskSettings', JSON.stringify(formData))
    
    toast.success('Risk settings saved successfully')
    onClose()
  }

  const handleReset = () => {
    const defaultSettings = {
      riskPerTrade: 2.0,
      maxDailyLoss: 6.0,
      accountBalance: 10000,
      circuitBreakerEnabled: true,
      mlFilterEnabled: true,
      sessionFilterEnabled: true
    }
    
    setFormData(defaultSettings)
  }

  const calculatePositionSize = () => {
    const riskAmount = formData.accountBalance * (formData.riskPerTrade / 100)
    return riskAmount
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

  const Slider = ({ label, value, onChange, min, max, step, suffix = '%', icon: Icon }) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {Icon && <Icon className="w-4 h-4 text-dark-muted" />}
          <label className="text-sm text-dark-text">{label}</label>
        </div>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
            className="w-16 px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text text-sm text-right focus:outline-none focus:border-bull"
            min={min}
            max={max}
            step={step}
          />
          <span className="text-sm text-dark-muted">{suffix}</span>
        </div>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer slider"
      />
    </div>
  )

  const Toggle = ({ label, checked, onChange, icon: Icon, description }) => (
    <div className="flex items-center justify-between p-3 bg-dark-bg border border-dark-border rounded-lg">
      <div className="flex items-center space-x-3">
        {Icon && <Icon className="w-5 h-5 text-dark-muted" />}
        <div>
          <div className="text-sm text-dark-text font-medium">{label}</div>
          {description && (
            <div className="text-xs text-dark-muted">{description}</div>
          )}
        </div>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-bull' : 'bg-dark-border'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  )

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-2xl mx-4 bg-dark-surface border border-dark-border rounded-lg shadow-xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-dark-border">
            <div>
              <h2 className="text-xl font-semibold text-dark-text">Risk Management Settings</h2>
              <p className="text-sm text-dark-muted mt-1">Configure your trading risk parameters</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
                riskLevel === 'LOW' ? 'bg-bull/20 text-bull' :
                riskLevel === 'MEDIUM' ? 'bg-warning-500/20 text-warning-500' :
                riskLevel === 'HIGH' ? 'bg-orange-500/20 text-orange-500' :
                'bg-bear/20 text-bear'
              }`}>
                <AlertTriangle className="w-4 h-4" />
                <span>{riskLevel} RISK</span>
              </div>
              <button
                onClick={onClose}
                className="text-dark-muted hover:text-dark-text transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
            {/* Account Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-dark-text flex items-center space-x-2">
                <DollarSign className="w-5 h-5" />
                <span>Account Settings</span>
              </h3>
              
              <div className="space-y-2">
                <label className="text-sm text-dark-text">Account Balance</label>
                <div className="flex items-center space-x-2">
                  <span className="text-dark-muted">$</span>
                  <input
                    type="number"
                    value={formData.accountBalance}
                    onChange={(e) => handleInputChange('accountBalance', parseFloat(e.target.value) || 0)}
                    className="flex-1 px-3 py-2 bg-dark-bg border border-dark-border rounded text-dark-text focus:outline-none focus:border-bull"
                    min="1"
                    step="100"
                  />
                </div>
              </div>
            </div>

            {/* Risk Parameters */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-dark-text flex items-center space-x-2">
                <Shield className="w-5 h-5" />
                <span>Risk Parameters</span>
              </h3>
              
              <Slider
                label="Risk Per Trade"
                value={formData.riskPerTrade}
                onChange={(value) => handleInputChange('riskPerTrade', value)}
                min={0.1}
                max={10}
                step={0.1}
                suffix="%"
                icon={AlertTriangle}
              />

              <Slider
                label="Max Daily Loss"
                value={formData.maxDailyLoss}
                onChange={(value) => handleInputChange('maxDailyLoss', value)}
                min={0.1}
                max={20}
                step={0.1}
                suffix="%"
                icon={Shield}
              />

              {/* Position Size Preview */}
              <div className="p-3 bg-dark-bg border border-dark-border rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-dark-muted">Max Position Size:</span>
                  <span className="text-sm font-medium text-dark-text">
                    ${calculatePositionSize().toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Safety Features */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-dark-text">Safety Features</h3>
              
              <Toggle
                label="Circuit Breaker"
                checked={formData.circuitBreakerEnabled}
                onChange={(value) => handleInputChange('circuitBreakerEnabled', value)}
                icon={AlertTriangle}
                description="Stop trading when daily loss limit is reached"
              />

              <Toggle
                label="ML Signal Filter"
                checked={formData.mlFilterEnabled}
                onChange={(value) => handleInputChange('mlFilterEnabled', value)}
                icon={Brain}
                description="Only trade signals approved by ML model"
              />

              <Toggle
                label="Session Filter"
                checked={formData.sessionFilterEnabled}
                onChange={(value) => handleInputChange('sessionFilterEnabled', value)}
                icon={Globe}
                description="Filter signals based on trading session performance"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-dark-border">
            <button
              onClick={handleReset}
              className="px-4 py-2 text-dark-muted hover:text-dark-text transition-colors"
            >
              Reset to Defaults
            </button>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-dark-muted hover:text-dark-text transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges}
                className={`flex items-center space-x-2 px-4 py-2 rounded font-medium transition-colors ${
                  hasChanges
                    ? 'bg-bull text-white hover:bg-bull/90'
                    : 'bg-dark-border text-dark-muted cursor-not-allowed'
                }`}
              >
                <Save className="w-4 h-4" />
                <span>Save Settings</span>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

export default RiskConfigModal