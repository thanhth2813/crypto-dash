import { useState, useEffect } from 'react'
import api from '../services/api'

interface Alert {
  id: number
  user_id: number
  coin_id: string
  symbol: string
  target_price: number
  condition: string
  is_active: boolean
  triggered_at: string | null
  created_at: string
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({
    coin_id: 'bitcoin',
    symbol: 'BTC',
    target_price: '',
    condition: 'above',
  })

  const fetchAlerts = async () => {
    try {
      const { data } = await api.get<Alert[]>('/alerts')
      setAlerts(data)
      setError('')
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Please login to view alerts')
      } else {
        setError('Failed to fetch alerts')
      }
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlerts()
  }, [])

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/alerts', {
        coin_id: formData.coin_id,
        symbol: formData.symbol.toUpperCase(),
        target_price: parseFloat(formData.target_price),
        condition: formData.condition,
      })
      setFormData({ coin_id: 'bitcoin', symbol: 'BTC', target_price: '', condition: 'above' })
      setShowCreateForm(false)
      await fetchAlerts()
    } catch (err) {
      alert('Failed to create alert')
      console.error(err)
    }
  }

  const handleDeleteAlert = async (id: number) => {
    if (!confirm('Delete this alert?')) return
    try {
      await api.delete(`/alerts/${id}`)
      await fetchAlerts()
    } catch (err) {
      alert('Failed to delete alert')
      console.error(err)
    }
  }

  const handleToggleAlert = async (id: number, currentStatus: boolean) => {
    try {
      await api.patch(`/alerts/${id}`, {
        is_active: !currentStatus,
      })
      await fetchAlerts()
    } catch (err) {
      alert('Failed to toggle alert')
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading alerts...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">🔔 Price Alerts</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-green-500 hover:bg-green-400 text-black font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {showCreateForm ? 'Cancel' : '+ Create Alert'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Create Alert Form */}
      {showCreateForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Create New Alert</h3>
          <form onSubmit={handleCreateAlert} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Coin ID</label>
                <input
                  type="text"
                  placeholder="e.g., bitcoin"
                  value={formData.coin_id}
                  onChange={(e) => setFormData({ ...formData, coin_id: e.target.value })}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Symbol</label>
                <input
                  type="text"
                  placeholder="e.g., BTC"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Target Price</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="e.g., 50000"
                  value={formData.target_price}
                  onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Condition</label>
                <select
                  value={formData.condition}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                >
                  <option value="above">Above</option>
                  <option value="below">Below</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              className="w-full bg-green-500 hover:bg-green-400 text-black font-semibold py-2 rounded-lg transition-colors"
            >
              Create Alert
            </button>
          </form>
        </div>
      )}

      {/* Alerts Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-800 text-gray-400 text-sm">
              <th className="px-4 py-3 text-left">Coin</th>
              <th className="px-4 py-3 text-left">Condition</th>
              <th className="px-4 py-3 text-right">Target Price</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Created</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => {
              const statusColor = alert.triggered_at
                ? 'text-yellow-400'
                : alert.is_active
                  ? 'text-green-400'
                  : 'text-gray-500'
              const statusText = alert.triggered_at
                ? '🟡 Triggered'
                : alert.is_active
                  ? '🟢 Active'
                  : '⚪ Paused'

              return (
                <tr
                  key={alert.id}
                  className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-white font-medium capitalize">{alert.coin_id.replace(/-/g, ' ')}</div>
                    <div className="text-gray-500 text-xs uppercase">{alert.symbol}</div>
                  </td>
                  <td className="px-4 py-3 text-white capitalize">{alert.condition}</td>
                  <td className="px-4 py-3 text-right text-white font-semibold">
                    ${alert.target_price.toLocaleString()}
                  </td>
                  <td className={`px-4 py-3 ${statusColor} font-semibold text-sm`}>{statusText}</td>
                  <td className="px-4 py-3 text-gray-400 text-sm">
                    {new Date(alert.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      onClick={() => handleToggleAlert(alert.id, alert.is_active)}
                      className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      {alert.is_active ? 'Pause' : 'Resume'}
                    </button>
                    <button
                      onClick={() => handleDeleteAlert(alert.id)}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {alerts.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No alerts yet. Create your first price alert to get notified when targets are reached!
          </div>
        )}
      </div>
    </div>
  )
}
