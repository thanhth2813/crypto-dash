import { useState, useEffect } from 'react'
import api from '../services/api'
import BotChart from '../components/BotChart'

interface Bot {
  id: number
  name: string
  strategy: string
  exchange: string
  symbol: string
  status: string
  paper_mode: boolean
  total_invested: number
  total_pnl: number
  created_at: string
  started_at: string | null
}

export default function Bots() {
  const [bots, setBots] = useState<Bot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [expandedBotId, setExpandedBotId] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    strategy: 'dca',
    exchange: 'paper',
    symbol: 'BTCUSDT',
    paper_mode: true,
    config: '{}',
    // DCA fields
    amount_per_buy: '33',
    interval_minutes: '60',
    max_buys: '100',
    // Grid fields
    upper_price: '',
    lower_price: '',
    grid_count: '10',
    amount_per_grid: '10',
    // Signal fields
    signal_amount: '33',
    coin_id: 'bitcoin',
  })

  const fetchBots = async () => {
    try {
      const { data } = await api.get<Bot[]>('/bots')
      setBots(data)
      setError('')
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Please login to view bots')
      } else {
        setError('Failed to fetch bots')
      }
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBots()
  }, [])

  const buildConfig = () => {
    if (formData.strategy === 'dca') {
      return {
        symbol: formData.symbol.toUpperCase(),
        amount_per_buy: parseFloat(formData.amount_per_buy) || 33,
        interval_minutes: parseInt(formData.interval_minutes) || 60,
        max_buys: parseInt(formData.max_buys) || 100,
      }
    }
    if (formData.strategy === 'grid') {
      return {
        symbol: formData.symbol.toUpperCase(),
        upper_price: parseFloat(formData.upper_price) || 0,
        lower_price: parseFloat(formData.lower_price) || 0,
        grid_count: parseInt(formData.grid_count) || 10,
        amount_per_grid: parseFloat(formData.amount_per_grid) || 10,
      }
    }
    if (formData.strategy === 'signal') {
      return {
        symbol: formData.symbol.toUpperCase(),
        coin_id: formData.coin_id || 'bitcoin',
        amount: parseFloat(formData.signal_amount) || 33,
      }
    }
    return {}
  }

  const handleCreateBot = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const config = buildConfig()

      await api.post('/bots', {
        name: formData.name,
        strategy: formData.strategy,
        exchange: formData.exchange,
        symbol: formData.symbol.toUpperCase(),
        paper_mode: formData.paper_mode,
        config,
      })
      setFormData({
        name: '', strategy: 'dca', exchange: 'paper', symbol: 'BTCUSDT', paper_mode: true, config: '{}',
        amount_per_buy: '33', interval_minutes: '60', max_buys: '100',
        upper_price: '', lower_price: '', grid_count: '10', amount_per_grid: '10',
        signal_amount: '33', coin_id: 'bitcoin',
      })
      setShowCreateForm(false)
      await fetchBots()
    } catch (err) {
      alert('Failed to create bot')
      console.error(err)
    }
  }

  const handleStartBot = async (id: number) => {
    try {
      await api.post(`/bots/${id}/start`)
      await fetchBots()
    } catch (err) {
      alert('Failed to start bot')
      console.error(err)
    }
  }

  const handleStopBot = async (id: number) => {
    try {
      await api.post(`/bots/${id}/stop`)
      await fetchBots()
    } catch (err) {
      alert('Failed to stop bot')
      console.error(err)
    }
  }

  const handleDeleteBot = async (id: number) => {
    if (!confirm('Delete this bot?')) return
    try {
      await api.delete(`/bots/${id}`)
      await fetchBots()
    } catch (err) {
      alert('Failed to delete bot')
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading bots...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">🤖 Trading Bots</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-green-500 hover:bg-green-400 text-black font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {showCreateForm ? 'Cancel' : '+ Create Bot'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Create Bot Form */}
      {showCreateForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Create New Bot</h3>
          <form onSubmit={handleCreateBot} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Bot Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
              />
              <select
                value={formData.strategy}
                onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
              >
                <option value="dca">DCA (Dollar Cost Average)</option>
                <option value="grid">Grid Trading</option>
                <option value="signal">Signal-based</option>
              </select>
              <select
                value={formData.exchange}
                onChange={(e) => setFormData({ ...formData, exchange: e.target.value })}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
              >
                <option value="paper">Paper Trading</option>
                <option value="binance">Binance</option>
              </select>
              <input
                type="text"
                placeholder="Symbol (e.g., BTCUSDT)"
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                required
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.paper_mode}
                onChange={(e) => setFormData({ ...formData, paper_mode: e.target.checked })}
                className="w-4 h-4"
              />
              <label className="text-gray-400 text-sm">Paper Mode (simulated trading)</label>
            </div>

            {/* Strategy-specific config fields */}
            {formData.strategy === 'dca' && (
              <div className="border border-gray-700 rounded-lg p-4 space-y-3">
                <h4 className="text-sm font-semibold text-green-400">💰 DCA Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Amount per Buy (USDT)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="1"
                      placeholder="33"
                      value={formData.amount_per_buy}
                      onChange={(e) => setFormData({ ...formData, amount_per_buy: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Interval (minutes)</label>
                    <input
                      type="number"
                      min="1"
                      placeholder="60"
                      value={formData.interval_minutes}
                      onChange={(e) => setFormData({ ...formData, interval_minutes: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Max Buys</label>
                    <input
                      type="number"
                      min="1"
                      placeholder="100"
                      value={formData.max_buys}
                      onChange={(e) => setFormData({ ...formData, max_buys: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Total budget: ${((parseFloat(formData.amount_per_buy) || 0) * (parseInt(formData.max_buys) || 0)).toFixed(2)} USDT
                </p>
              </div>
            )}

            {formData.strategy === 'grid' && (
              <div className="border border-gray-700 rounded-lg p-4 space-y-3">
                <h4 className="text-sm font-semibold text-blue-400">📊 Grid Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Upper Price (USDT)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g., 70000"
                      value={formData.upper_price}
                      onChange={(e) => setFormData({ ...formData, upper_price: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Lower Price (USDT)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g., 60000"
                      value={formData.lower_price}
                      onChange={(e) => setFormData({ ...formData, lower_price: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Grid Count</label>
                    <input
                      type="number"
                      min="2"
                      placeholder="10"
                      value={formData.grid_count}
                      onChange={(e) => setFormData({ ...formData, grid_count: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Amount per Grid (USDT)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="1"
                      placeholder="10"
                      value={formData.amount_per_grid}
                      onChange={(e) => setFormData({ ...formData, amount_per_grid: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Total budget: ${((parseFloat(formData.amount_per_grid) || 0) * (parseInt(formData.grid_count) || 0)).toFixed(2)} USDT
                </p>
              </div>
            )}

            {formData.strategy === 'signal' && (
              <div className="border border-gray-700 rounded-lg p-4 space-y-3">
                <h4 className="text-sm font-semibold text-purple-400">📈 Signal Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Amount per Trade (USDT)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="1"
                      placeholder="33"
                      value={formData.signal_amount}
                      onChange={(e) => setFormData({ ...formData, signal_amount: e.target.value })}
                      required
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Coin ID (CoinGecko)</label>
                    <select
                      value={formData.coin_id}
                      onChange={(e) => setFormData({ ...formData, coin_id: e.target.value })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    >
                      <option value="bitcoin">Bitcoin (BTC)</option>
                      <option value="ethereum">Ethereum (ETH)</option>
                      <option value="solana">Solana (SOL)</option>
                      <option value="binancecoin">BNB</option>
                      <option value="cardano">Cardano (ADA)</option>
                    </select>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Bot will auto-trade when RSI+EMA signals BUY or SELL
                </p>
              </div>
            )}
            <button
              type="submit"
              className="w-full bg-green-500 hover:bg-green-400 text-black font-semibold py-2 rounded-lg transition-colors"
            >
              Create Bot
            </button>
          </form>
        </div>
      )}

      {/* Bots Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-800 text-gray-400 text-sm">
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Strategy</th>
              <th className="px-4 py-3 text-left">Symbol</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Invested</th>
              <th className="px-4 py-3 text-right">P&L</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {bots.map((bot) => {
              const pnlColor = bot.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
              const statusColor = bot.status === 'running' ? 'text-green-400' : 
                                 bot.status === 'error' ? 'text-red-400' : 
                                 'text-gray-400'
              const isExpanded = expandedBotId === bot.id
              
              return (
                <>
                  <tr
                    key={bot.id}
                    className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors cursor-pointer"
                    onClick={() => setExpandedBotId(isExpanded ? null : bot.id)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                        <div>
                          <div className="text-white font-medium">{bot.name}</div>
                          <div className="text-gray-500 text-xs">{bot.exchange} {bot.paper_mode && '(Paper)'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-white uppercase text-sm">{bot.strategy}</td>
                    <td className="px-4 py-3 text-gray-400 font-mono text-sm">{bot.symbol}</td>
                    <td className={`px-4 py-3 ${statusColor} font-semibold uppercase text-sm`}>
                      {bot.status}
                    </td>
                    <td className="px-4 py-3 text-right text-white">${bot.total_invested.toFixed(2)}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${pnlColor}`}>
                      {bot.total_pnl >= 0 ? '+' : ''}${bot.total_pnl.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                      {bot.status !== 'running' && (
                        <button
                          onClick={() => handleStartBot(bot.id)}
                          className="text-green-400 hover:text-green-300 text-sm"
                        >
                          Start
                        </button>
                      )}
                      {bot.status === 'running' && (
                        <button
                          onClick={() => handleStopBot(bot.id)}
                          className="text-yellow-400 hover:text-yellow-300 text-sm"
                        >
                          Stop
                        </button>
                      )}
                      {bot.status !== 'running' && (
                        <button
                          onClick={() => handleDeleteBot(bot.id)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr key={`${bot.id}-details`} className="border-t border-gray-800">
                      <td colSpan={7} className="px-4 py-6 bg-gray-950">
                        <BotChart botId={bot.id} botName={bot.name} />
                      </td>
                    </tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>

        {bots.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No bots yet. Create your first bot to start automated trading!
          </div>
        )}
      </div>
    </div>
  )
}
