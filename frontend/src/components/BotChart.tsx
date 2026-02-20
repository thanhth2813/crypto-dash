import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Scatter, ScatterChart, ZAxis } from 'recharts'
import api from '../services/api'

interface Trade {
  id: number
  bot_id: number
  symbol: string
  side: string
  amount: number
  price: number
  filled_price: number
  status: string
  created_at: string
}

interface ChartDataPoint {
  timestamp: string
  pnl: number
  invested: number
}

interface BotChartProps {
  botId: number
  botName: string
}

export default function BotChart({ botId, botName }: BotChartProps) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalTrades: 0,
    winRate: 0,
    avgProfit: 0,
    totalPnL: 0,
  })

  useEffect(() => {
    fetchTrades()
  }, [botId])

  const fetchTrades = async () => {
    try {
      const { data } = await api.get<{ trades: Trade[] }>(`/trades?bot_id=${botId}`)
      const botTrades = data.trades || []
      setTrades(botTrades)
      
      // Calculate P&L over time
      const dataPoints: ChartDataPoint[] = []
      let cumulativePnL = 0
      let totalInvested = 0
      
      botTrades.forEach((trade) => {
        const cost = trade.filled_price * trade.amount
        
        if (trade.side === 'BUY') {
          cumulativePnL -= cost // spent money
          totalInvested += cost
        } else {
          cumulativePnL += cost // received money
        }
        
        dataPoints.push({
          timestamp: new Date(trade.created_at).toLocaleTimeString(),
          pnl: parseFloat(cumulativePnL.toFixed(2)),
          invested: parseFloat(totalInvested.toFixed(2)),
        })
      })
      
      setChartData(dataPoints)
      
      // Calculate stats
      const profitable = botTrades.filter((t, idx) => {
        if (idx === 0) return false
        const prevTrade = botTrades[idx - 1]
        if (t.side === 'SELL' && prevTrade.side === 'BUY') {
          return t.filled_price > prevTrade.filled_price
        }
        return false
      }).length
      
      const sellTrades = botTrades.filter(t => t.side === 'SELL').length
      const winRate = sellTrades > 0 ? (profitable / sellTrades) * 100 : 0
      const avgProfit = botTrades.length > 0 ? cumulativePnL / botTrades.length : 0
      
      setStats({
        totalTrades: botTrades.length,
        winRate: parseFloat(winRate.toFixed(2)),
        avgProfit: parseFloat(avgProfit.toFixed(2)),
        totalPnL: parseFloat(cumulativePnL.toFixed(2)),
      })
      
    } catch (err) {
      console.error('Failed to fetch trades:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-8 text-gray-400">
        Loading performance data...
      </div>
    )
  }

  if (trades.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        No trades yet. Start the bot to see performance data.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.totalTrades}</div>
          <div className="text-sm text-gray-400">Total Trades</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{stats.winRate}%</div>
          <div className="text-sm text-gray-400">Win Rate</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className={`text-2xl font-bold ${stats.avgProfit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            ${stats.avgProfit.toFixed(2)}
          </div>
          <div className="text-sm text-gray-400">Avg Profit/Trade</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className={`text-2xl font-bold ${stats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.totalPnL >= 0 ? '+' : ''}${stats.totalPnL.toFixed(2)}
          </div>
          <div className="text-sm text-gray-400">Total P&L</div>
        </div>
      </div>

      {/* P&L Chart */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h4 className="text-white font-semibold mb-4">📈 P&L Over Time</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="timestamp" 
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
            />
            <YAxis 
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="pnl" 
              stroke="#10B981" 
              strokeWidth={2}
              name="P&L ($)"
              dot={{ fill: '#10B981', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Trade Markers Chart */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h4 className="text-white font-semibold mb-4">💹 Trade History</h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {trades.map((trade, idx) => {
            const isBuy = trade.side === 'BUY'
            const bgColor = isBuy ? 'bg-green-900/20' : 'bg-red-900/20'
            const dotColor = isBuy ? 'bg-green-400' : 'bg-red-400'
            const textColor = isBuy ? 'text-green-400' : 'text-red-400'
            
            return (
              <div 
                key={trade.id}
                className={`${bgColor} border border-gray-700 rounded-lg p-3 flex items-center justify-between`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${dotColor}`} />
                  <div>
                    <div className={`font-semibold ${textColor}`}>
                      {trade.side} {trade.amount.toFixed(8)} {trade.symbol.replace('USDT', '')}
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(trade.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-semibold">
                    ${trade.filled_price.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-400">
                    ${(trade.filled_price * trade.amount).toFixed(2)}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
