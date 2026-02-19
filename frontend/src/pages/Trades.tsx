import { useState, useEffect } from 'react'
import api from '../services/api'

interface Trade {
  id: number
  bot_id: number
  bot_name: string | null
  exchange: string
  symbol: string
  side: string
  order_type: string
  amount: number
  price: number | null
  filled_amount: number
  filled_price: number | null
  status: string
  fee: number
  fee_currency: string | null
  created_at: string
  executed_at: string | null
}

interface TradeSummary {
  total_trades: number
  total_buy: number
  total_sell: number
  total_volume: number
  total_fees: number
  total_pnl: number
  win_rate: number
}

export default function Trades() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [summary, setSummary] = useState<TradeSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [botFilter, setBotFilter] = useState<number | null>(null)

  const fetchTrades = async () => {
    try {
      const params = new URLSearchParams()
      if (botFilter) params.append('bot_id', botFilter.toString())
      params.append('limit', '50')

      const [tradesRes, summaryRes] = await Promise.all([
        api.get<Trade[]>(`/trades?${params}`),
        api.get<TradeSummary>(`/trades/summary${botFilter ? `?bot_id=${botFilter}` : ''}`),
      ])
      
      setTrades(tradesRes.data)
      setSummary(summaryRes.data)
      setError('')
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Please login to view trade history')
      } else {
        setError('Failed to fetch trades')
      }
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTrades()
  }, [botFilter])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading trades...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">📊 Trade History</h2>
        <div className="flex items-center gap-2">
          <label className="text-gray-400 text-sm">Filter by Bot:</label>
          <select
            value={botFilter || ''}
            onChange={(e) => setBotFilter(e.target.value ? parseInt(e.target.value) : null)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500"
          >
            <option value="">All Bots</option>
            {/* TODO: Populate bot options dynamically */}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-xs mb-1">Total Trades</div>
            <div className="text-xl font-bold text-white">{summary.total_trades}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-xs mb-1">Buy Orders</div>
            <div className="text-xl font-bold text-green-400">{summary.total_buy}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-xs mb-1">Sell Orders</div>
            <div className="text-xl font-bold text-red-400">{summary.total_sell}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-xs mb-1">Total Volume</div>
            <div className="text-xl font-bold text-white">{summary.total_volume.toFixed(4)}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-xs mb-1">Total Fees</div>
            <div className="text-xl font-bold text-gray-400">${summary.total_fees.toFixed(2)}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-400 text-xs mb-1">Total P&L</div>
            <div className={`text-xl font-bold ${summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Trades Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-800 text-gray-400 text-sm">
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Bot</th>
              <th className="px-4 py-3 text-left">Symbol</th>
              <th className="px-4 py-3 text-left">Side</th>
              <th className="px-4 py-3 text-right">Amount</th>
              <th className="px-4 py-3 text-right">Price</th>
              <th className="px-4 py-3 text-right">Fee</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => {
              const sideColor = trade.side === 'buy' ? 'text-green-400' : 'text-red-400'
              const statusColor = trade.status === 'filled' ? 'text-green-400' : 
                                 trade.status === 'failed' ? 'text-red-400' : 
                                 'text-gray-400'
              
              const date = new Date(trade.created_at)
              const dateStr = date.toLocaleDateString()
              const timeStr = date.toLocaleTimeString()
              
              return (
                <tr
                  key={trade.id}
                  className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-white text-sm">{dateStr}</div>
                    <div className="text-gray-500 text-xs">{timeStr}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-white text-sm">{trade.bot_name || `Bot #${trade.bot_id}`}</div>
                    <div className="text-gray-500 text-xs">{trade.exchange}</div>
                  </td>
                  <td className="px-4 py-3 text-white font-mono text-sm">{trade.symbol}</td>
                  <td className={`px-4 py-3 ${sideColor} font-semibold uppercase text-sm`}>
                    {trade.side}
                  </td>
                  <td className="px-4 py-3 text-right text-white">{trade.filled_amount.toFixed(6)}</td>
                  <td className="px-4 py-3 text-right text-white">
                    ${trade.filled_price ? trade.filled_price.toFixed(2) : trade.price?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400 text-sm">
                    ${trade.fee.toFixed(2)} {trade.fee_currency || ''}
                  </td>
                  <td className={`px-4 py-3 ${statusColor} uppercase text-sm`}>
                    {trade.status}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {trades.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No trades yet. Start a bot to see trade history!
          </div>
        )}
      </div>
    </div>
  )
}
