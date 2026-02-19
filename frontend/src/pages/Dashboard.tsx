import { useState, useEffect } from 'react'
import api from '../services/api'

interface CoinPrice {
  coin_id: string
  symbol: string
  price: number
  ts: string
}

export default function Dashboard() {
  const [prices, setPrices] = useState<CoinPrice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchPrices = async () => {
    try {
      const { data } = await api.get<CoinPrice[]>('/market/prices')
      setPrices(data.slice(0, 20)) // top 20
      setLastUpdate(new Date())
      setError('')
    } catch (err) {
      setError('Failed to fetch market prices')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPrices()

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchPrices, 30000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading market data...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">📊 Market Overview</h2>
        <div className="text-sm text-gray-500">
          {lastUpdate && (
            <>
              Last update: {lastUpdate.toLocaleTimeString()}
              <span className="ml-2 text-green-400">● Auto-refresh 30s</span>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Top 20 Coins Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-800 text-gray-400 text-sm">
              <th className="px-4 py-3 text-left">#</th>
              <th className="px-4 py-3 text-left">Coin</th>
              <th className="px-4 py-3 text-left">Symbol</th>
              <th className="px-4 py-3 text-right">Price (USD)</th>
            </tr>
          </thead>
          <tbody>
            {prices.map((coin, idx) => (
              <tr
                key={coin.coin_id}
                className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors"
              >
                <td className="px-4 py-3 text-gray-500 text-sm">{idx + 1}</td>
                <td className="px-4 py-3 text-white font-medium capitalize">
                  {coin.coin_id.replace(/-/g, ' ')}
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-300 uppercase font-mono text-sm">
                    {coin.symbol}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-white font-semibold">
                    ${coin.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {prices.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No market data available
          </div>
        )}
      </div>

      {/* Chart placeholder — can be enhanced with recharts */}
      <div className="mt-6 bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Price Chart</h3>
        <div className="text-gray-500 text-center py-12">
          Chart coming soon — use recharts or chart.js for price history visualization
        </div>
      </div>
    </div>
  )
}
