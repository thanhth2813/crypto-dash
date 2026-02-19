import { useState, useEffect } from 'react'
import api from '../services/api'

interface Holding {
  id: number
  coin_id: string
  symbol: string
  amount: number
  buy_price: number
  current_price: number
  pnl: number
}

interface Summary {
  total_invested: number
  total_value: number
  total_pnl: number
}

export default function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    coin_id: '',
    symbol: '',
    amount: '',
    buy_price: '',
  })

  const fetchPortfolio = async () => {
    try {
      const [holdingsRes, summaryRes] = await Promise.all([
        api.get<Holding[]>('/portfolio'),
        api.get<Summary>('/portfolio/summary'),
      ])
      setHoldings(holdingsRes.data)
      setSummary(summaryRes.data)
      setError('')
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Please login to view portfolio')
      } else {
        setError('Failed to fetch portfolio')
      }
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/portfolio', {
        coin_id: formData.coin_id,
        symbol: formData.symbol.toUpperCase(),
        amount: parseFloat(formData.amount),
        buy_price: parseFloat(formData.buy_price),
      })
      setFormData({ coin_id: '', symbol: '', amount: '', buy_price: '' })
      setShowAddForm(false)
      await fetchPortfolio()
    } catch (err) {
      alert('Failed to add holding')
      console.error(err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this holding?')) return
    try {
      await api.delete(`/portfolio/${id}`)
      await fetchPortfolio()
    } catch (err) {
      alert('Failed to delete holding')
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading portfolio...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">💼 Portfolio</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-green-500 hover:bg-green-400 text-black font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {showAddForm ? 'Cancel' : '+ Add Holding'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-sm mb-1">Total Invested</div>
            <div className="text-2xl font-bold text-white">
              ${summary.total_invested.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-sm mb-1">Current Value</div>
            <div className="text-2xl font-bold text-white">
              ${summary.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-sm mb-1">Total P&L</div>
            <div className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              <span className="text-sm ml-2">
                ({summary.total_invested > 0 ? ((summary.total_pnl / summary.total_invested) * 100).toFixed(2) : '0.00'}%)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Add Holding Form */}
      {showAddForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Add New Holding</h3>
          <form onSubmit={handleAddHolding} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Coin ID (e.g., bitcoin)"
              value={formData.coin_id}
              onChange={(e) => setFormData({ ...formData, coin_id: e.target.value })}
              required
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
            />
            <input
              type="text"
              placeholder="Symbol (e.g., BTC)"
              value={formData.symbol}
              onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
              required
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
            />
            <input
              type="number"
              step="any"
              placeholder="Amount"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
            />
            <input
              type="number"
              step="any"
              placeholder="Buy Price (USD)"
              value={formData.buy_price}
              onChange={(e) => setFormData({ ...formData, buy_price: e.target.value })}
              required
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
            />
            <button
              type="submit"
              className="bg-green-500 hover:bg-green-400 text-black font-semibold py-2 rounded-lg transition-colors md:col-span-4"
            >
              Add Holding
            </button>
          </form>
        </div>
      )}

      {/* Holdings Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-800 text-gray-400 text-sm">
              <th className="px-4 py-3 text-left">Coin</th>
              <th className="px-4 py-3 text-right">Amount</th>
              <th className="px-4 py-3 text-right">Buy Price</th>
              <th className="px-4 py-3 text-right">Current Price</th>
              <th className="px-4 py-3 text-right">Value</th>
              <th className="px-4 py-3 text-right">P&L</th>
              <th className="px-4 py-3 text-right">P&L %</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => {
              const value = h.amount * h.current_price
              const pnlPercent = h.buy_price > 0 ? ((h.current_price - h.buy_price) / h.buy_price) * 100 : 0
              return (
                <tr
                  key={h.id}
                  className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-white font-medium capitalize">{h.coin_id.replace(/-/g, ' ')}</div>
                    <div className="text-gray-500 text-xs uppercase font-mono">{h.symbol}</div>
                  </td>
                  <td className="px-4 py-3 text-right text-white">{h.amount.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">${h.buy_price.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-white">${h.current_price.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-white font-semibold">${value.toFixed(2)}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${h.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {h.pnl >= 0 ? '+' : ''}${h.pnl.toFixed(2)}
                  </td>
                  <td className={`px-4 py-3 text-right ${pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(h.id)}
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

        {holdings.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No holdings yet. Add your first holding to track P&L!
          </div>
        )}
      </div>

      {/* Pie Chart placeholder */}
      {holdings.length > 0 && (
        <div className="mt-6 bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Portfolio Allocation</h3>
          <div className="text-gray-500 text-center py-12">
            Pie chart coming soon — use recharts PieChart component
          </div>
        </div>
      )}
    </div>
  )
}
