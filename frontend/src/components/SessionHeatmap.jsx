import React, { useState } from 'react'
import { Info } from 'lucide-react'

const SessionHeatmap = () => {
  const [hoveredCell, setHoveredCell] = useState(null)

  // Mock session performance data
  const sessionData = {
    monday: {
      asia: { winRate: 65, avgR: 1.2, totalTrades: 8 },
      london: { winRate: 78, avgR: 1.8, totalTrades: 15 },
      new_york: { winRate: 72, avgR: 1.5, totalTrades: 12 }
    },
    tuesday: {
      asia: { winRate: 58, avgR: 0.9, totalTrades: 6 },
      london: { winRate: 82, avgR: 2.1, totalTrades: 18 },
      new_york: { winRate: 69, avgR: 1.4, totalTrades: 11 }
    },
    wednesday: {
      asia: { winRate: 71, avgR: 1.6, totalTrades: 9 },
      london: { winRate: 75, avgR: 1.7, totalTrades: 14 },
      new_york: { winRate: 77, avgR: 1.9, totalTrades: 13 }
    },
    thursday: {
      asia: { winRate: 62, avgR: 1.1, totalTrades: 7 },
      london: { winRate: 85, avgR: 2.3, totalTrades: 20 },
      new_york: { winRate: 74, avgR: 1.6, totalTrades: 16 }
    },
    friday: {
      asia: { winRate: 55, avgR: 0.8, totalTrades: 5 },
      london: { winRate: 68, avgR: 1.3, totalTrades: 12 },
      new_york: { winRate: 71, avgR: 1.5, totalTrades: 14 }
    },
    saturday: {
      asia: { winRate: 45, avgR: 0.6, totalTrades: 3 },
      london: { winRate: 52, avgR: 0.9, totalTrades: 4 },
      new_york: { winRate: 48, avgR: 0.7, totalTrades: 2 }
    },
    sunday: {
      asia: { winRate: 41, avgR: 0.5, totalTrades: 2 },
      london: { winRate: 47, avgR: 0.8, totalTrades: 3 },
      new_york: { winRate: 44, avgR: 0.6, totalTrades: 1 }
    }
  }

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  const sessions = [
    { key: 'asia', label: 'Asia', time: '00:00-08:00 UTC', icon: '🌏' },
    { key: 'london', label: 'London', time: '07:00-16:00 UTC', icon: '🇬🇧' },
    { key: 'new_york', label: 'New York', time: '12:00-21:00 UTC', icon: '🇺🇸' }
  ]

  const getIntensityColor = (winRate) => {
    if (winRate >= 80) return 'bg-bull/80'
    if (winRate >= 70) return 'bg-bull/60'
    if (winRate >= 60) return 'bg-bull/40'
    if (winRate >= 50) return 'bg-bull/20'
    if (winRate >= 40) return 'bg-bear/20'
    if (winRate >= 30) return 'bg-bear/40'
    return 'bg-bear/60'
  }

  const getTextColor = (winRate) => {
    if (winRate >= 60) return 'text-white'
    return 'text-dark-text'
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-dark-text font-semibold">Session Performance</h3>
          <p className="text-xs text-dark-muted">Win rate by day and session</p>
        </div>
        <div className="flex items-center space-x-1 text-dark-muted">
          <Info className="w-4 h-4" />
          <span className="text-xs">Hover for details</span>
        </div>
      </div>

      {/* Heatmap */}
      <div className="space-y-3">
        {/* Session Headers */}
        <div className="grid grid-cols-8 gap-1">
          <div></div> {/* Empty corner */}
          {sessions.map((session) => (
            <div key={session.key} className="text-center">
              <div className="text-lg mb-1">{session.icon}</div>
              <div className="text-xs text-dark-text font-medium">{session.label}</div>
              <div className="text-xs text-dark-muted">{session.time}</div>
            </div>
          ))}
        </div>

        {/* Heatmap Grid */}
        <div className="space-y-1">
          {days.map((day, dayIndex) => {
            const dayKey = day.toLowerCase()
            return (
              <div key={day} className="grid grid-cols-8 gap-1">
                {/* Day Label */}
                <div className="flex items-center justify-end pr-2">
                  <span className="text-xs text-dark-text font-medium">{day.slice(0, 3)}</span>
                </div>

                {/* Session Cells */}
                {sessions.map((session) => {
                  const data = sessionData[dayKey]?.[session.key]
                  const cellKey = `${dayKey}-${session.key}`
                  
                  return (
                    <div
                      key={session.key}
                      className={`relative h-12 rounded border border-dark-border cursor-pointer transition-all hover:scale-105 ${
                        data ? getIntensityColor(data.winRate) : 'bg-dark-bg'
                      }`}
                      onMouseEnter={() => setHoveredCell({ day, session: session.label, data })}
                      onMouseLeave={() => setHoveredCell(null)}
                    >
                      {data && (
                        <div className={`absolute inset-0 flex flex-col items-center justify-center ${getTextColor(data.winRate)}`}>
                          <div className="text-xs font-bold">{data.winRate}%</div>
                          <div className="text-xs opacity-75">{data.totalTrades}</div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-dark-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-dark-muted">Win Rate:</span>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-bear/60 rounded"></div>
              <span className="text-xs text-dark-muted">Low</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-bull/40 rounded"></div>
              <span className="text-xs text-dark-muted">Med</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-bull/80 rounded"></div>
              <span className="text-xs text-dark-muted">High</span>
            </div>
          </div>
          
          <div className="text-xs text-dark-muted">
            Numbers show trades count
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCell && hoveredCell.data && (
        <div className="absolute z-50 bg-dark-surface border border-dark-border rounded-lg p-3 shadow-xl pointer-events-none"
             style={{
               position: 'fixed',
               top: '50%',
               left: '50%',
               transform: 'translate(-50%, -50%)'
             }}>
          <div className="text-sm font-semibold text-dark-text mb-2">
            {hoveredCell.day} - {hoveredCell.session}
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between space-x-4">
              <span className="text-dark-muted">Win Rate:</span>
              <span className={`font-medium ${
                hoveredCell.data.winRate >= 60 ? 'text-bull' : 'text-bear'
              }`}>
                {hoveredCell.data.winRate}%
              </span>
            </div>
            <div className="flex justify-between space-x-4">
              <span className="text-dark-muted">Avg R:</span>
              <span className="text-dark-text font-medium">
                {hoveredCell.data.avgR.toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between space-x-4">
              <span className="text-dark-muted">Total Trades:</span>
              <span className="text-dark-text font-medium">
                {hoveredCell.data.totalTrades}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SessionHeatmap