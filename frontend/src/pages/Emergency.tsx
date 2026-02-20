import { useState, useEffect } from 'react'
import api from '../services/api'

interface SystemStatus {
  running_bots: number
  error_bots: number
  total_exposure: number
  scheduler_active: boolean
  status_breakdown: Record<string, number>
  circuit_breakers: {
    max_exposure_triggered: boolean
    error_rate_triggered: boolean
  }
  running_bot_details: Array<{
    id: number
    name: string
    strategy: string
    symbol: string
    invested: number
    pnl: number
  }>
}

export default function Emergency() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [stopping, setStopping] = useState(false)

  const fetchStatus = async () => {
    try {
      const { data } = await api.get<SystemStatus>('/emergency/status')
      setStatus(data)
      setError('')
    } catch (err: any) {
      setError('Failed to fetch system status')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const handleStopAll = async () => {
    if (!confirm('⚠️ STOP ALL BOTS? This will immediately halt all trading!')) return

    setStopping(true)
    try {
      const { data } = await api.post('/emergency/stop-all', {
        reason: 'Manual emergency stop via dashboard',
      })
      alert(`✅ Stopped ${data.stopped_count} bots\n${data.failed_count > 0 ? `⚠️ Failed: ${data.failed_count}` : ''}`)
      await fetchStatus()
    } catch (err: any) {
      alert(`❌ Failed to stop bots: ${err.response?.data?.detail || err.message}`)
    } finally {
      setStopping(false)
    }
  }

  const handleStopBot = async (botId: number, botName: string) => {
    if (!confirm(`Stop bot "${botName}"?`)) return

    try {
      await api.post(`/emergency/stop/${botId}`, {
        reason: 'Manual stop via emergency dashboard',
      })
      alert(`✅ Bot "${botName}" stopped`)
      await fetchStatus()
    } catch (err: any) {
      alert(`❌ Failed to stop bot: ${err.response?.data?.detail || err.message}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading system status...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">🚨 Emergency Controls</h2>
        <button
          onClick={handleStopAll}
          disabled={stopping || status?.running_bots === 0}
          className="bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold px-6 py-3 rounded-lg transition-colors"
        >
          {stopping ? 'STOPPING...' : '🛑 STOP ALL BOTS'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <div className="text-3xl font-bold text-green-400">{status?.running_bots || 0}</div>
          <div className="text-sm text-gray-400 mt-1">Running Bots</div>
        </div>
        
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <div className="text-3xl font-bold text-red-400">{status?.error_bots || 0}</div>
          <div className="text-sm text-gray-400 mt-1">Error Bots</div>
        </div>
        
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <div className="text-3xl font-bold text-white">${status?.total_exposure.toFixed(2) || '0.00'}</div>
          <div className="text-sm text-gray-400 mt-1">Total Exposure</div>
        </div>
        
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <div className="text-3xl font-bold text-blue-400">
            {status?.scheduler_active ? '🟢' : '🔴'}
          </div>
          <div className="text-sm text-gray-400 mt-1">Scheduler Status</div>
        </div>
      </div>

      {/* Circuit Breakers */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">⚡ Circuit Breakers</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between bg-gray-800 rounded-lg p-4">
            <span className="text-gray-300">Max Exposure Limit</span>
            <span className={status?.circuit_breakers.max_exposure_triggered ? 'text-red-400 font-bold' : 'text-green-400'}>
              {status?.circuit_breakers.max_exposure_triggered ? '🔴 TRIGGERED' : '🟢 OK'}
            </span>
          </div>
          <div className="flex items-center justify-between bg-gray-800 rounded-lg p-4">
            <span className="text-gray-300">Error Rate Monitor</span>
            <span className={status?.circuit_breakers.error_rate_triggered ? 'text-red-400 font-bold' : 'text-green-400'}>
              {status?.circuit_breakers.error_rate_triggered ? '🔴 TRIGGERED' : '🟢 OK'}
            </span>
          </div>
        </div>
      </div>

      {/* Running Bots Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">Running Bots</h3>
        </div>
        
        {status?.running_bot_details && status.running_bot_details.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="bg-gray-800 text-gray-400 text-sm">
                <th className="px-4 py-3 text-left">Bot Name</th>
                <th className="px-4 py-3 text-left">Strategy</th>
                <th className="px-4 py-3 text-left">Symbol</th>
                <th className="px-4 py-3 text-right">Invested</th>
                <th className="px-4 py-3 text-right">P&L</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {status.running_bot_details.map((bot) => (
                <tr key={bot.id} className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors">
                  <td className="px-4 py-3 text-white font-medium">{bot.name}</td>
                  <td className="px-4 py-3 text-gray-400 uppercase text-sm">{bot.strategy}</td>
                  <td className="px-4 py-3 text-gray-400 font-mono text-sm">{bot.symbol}</td>
                  <td className="px-4 py-3 text-right text-white">${bot.invested.toFixed(2)}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${bot.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {bot.pnl >= 0 ? '+' : ''}${bot.pnl.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleStopBot(bot.id, bot.name)}
                      className="text-red-400 hover:text-red-300 text-sm font-semibold"
                    >
                      STOP
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-12 text-gray-500">
            No bots currently running
          </div>
        )}
      </div>

      {/* Status Breakdown */}
      {status?.status_breakdown && Object.keys(status.status_breakdown).length > 0 && (
        <div className="mt-6 bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Bot Status Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(status.status_breakdown).map(([status, count]) => (
              <div key={status} className="text-center">
                <div className="text-2xl font-bold text-white">{count}</div>
                <div className="text-sm text-gray-400 capitalize">{status}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
