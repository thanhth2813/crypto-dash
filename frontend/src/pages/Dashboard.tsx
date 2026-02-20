import { useState, useEffect, useRef } from 'react'
import api from '../services/api'

interface CoinPrice {
  coin_id: string
  symbol: string
  price: number
  ts: string
}

interface WSPriceUpdate {
  type: string
  symbol: string
  price: number
  open: number
  high: number
  low: number
  volume: number
  timestamp: number
}

interface PriceChange {
  [symbol: string]: 'up' | 'down' | null
}

export default function Dashboard() {
  const [prices, setPrices] = useState<CoinPrice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [priceChanges, setPriceChanges] = useState<PriceChange>({})
  const wsRef = useRef<WebSocket | null>(null)
  const priceMapRef = useRef<Map<string, number>>(new Map())

  // Fetch initial prices via REST API
  const fetchPrices = async () => {
    try {
      const { data } = await api.get<CoinPrice[]>('/market/prices')
      const topPrices = data.slice(0, 20)
      setPrices(topPrices)
      
      // Initialize price map for change detection
      topPrices.forEach(coin => {
        priceMapRef.current.set(coin.symbol.toUpperCase(), coin.price)
      })
      
      setLastUpdate(new Date())
      setError('')
    } catch (err) {
      setError('Failed to fetch market prices')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Connect to WebSocket for real-time updates
  const connectWebSocket = () => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    const wsUrl = `${wsProtocol}//${wsHost}/ws/prices`
    
    console.log('Connecting to WebSocket:', wsUrl)
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      setWsConnected(true)
      setError('')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSPriceUpdate
        
        if (data.type === 'connected') {
          console.log('WebSocket handshake:', data)
          return
        }
        
        if (data.type === 'price_update') {
          updatePrice(data)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected - reconnecting in 5s...')
      setWsConnected(false)
      
      // Reconnect after 5 seconds
      setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connectWebSocket()
        }
      }, 5000)
    }
  }

  // Update price from WebSocket feed
  const updatePrice = (data: WSPriceUpdate) => {
    const symbol = data.symbol
    const newPrice = data.price
    const oldPrice = priceMapRef.current.get(symbol)
    
    // Detect price change direction
    if (oldPrice !== undefined && oldPrice !== newPrice) {
      const direction = newPrice > oldPrice ? 'up' : 'down'
      
      // Flash animation
      setPriceChanges(prev => ({ ...prev, [symbol]: direction }))
      
      // Clear flash after 1 second
      setTimeout(() => {
        setPriceChanges(prev => {
          const updated = { ...prev }
          if (updated[symbol] === direction) {
            updated[symbol] = null
          }
          return updated
        })
      }, 1000)
    }
    
    // Update price map
    priceMapRef.current.set(symbol, newPrice)
    
    // Update prices array
    setPrices(prev => {
      return prev.map(coin => {
        const coinSymbol = `${coin.symbol.toUpperCase()}USDT`
        if (coinSymbol === symbol) {
          return { ...coin, price: newPrice }
        }
        return coin
      })
    })
    
    setLastUpdate(new Date())
  }

  useEffect(() => {
    // Fetch initial prices
    fetchPrices()
    
    // Connect to WebSocket
    connectWebSocket()
    
    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
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
        <div className="flex items-center gap-4">
          {/* WebSocket Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            <span className="text-sm text-gray-400">
              {wsConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
          
          {lastUpdate && (
            <div className="text-sm text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </div>
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
            {prices.map((coin, idx) => {
              const wsSymbol = `${coin.symbol.toUpperCase()}USDT`
              const change = priceChanges[wsSymbol]
              
              return (
                <tr
                  key={coin.coin_id}
                  className={`border-t border-gray-800 hover:bg-gray-800/50 transition-all duration-300 ${
                    change === 'up' ? 'bg-green-900/20' : 
                    change === 'down' ? 'bg-red-900/20' : ''
                  }`}
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
                    <span className={`font-semibold transition-colors duration-300 ${
                      change === 'up' ? 'text-green-400' : 
                      change === 'down' ? 'text-red-400' : 
                      'text-white'
                    }`}>
                      ${coin.price.toLocaleString(undefined, { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                      })}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {prices.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            No market data available
          </div>
        )}
      </div>

      {/* Real-time Status Info */}
      <div className="mt-6 bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">📡 Real-time Feed</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{prices.length}</div>
            <div className="text-sm text-gray-400">Coins Tracked</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {wsConnected ? '🟢 Live' : '🔴 Offline'}
            </div>
            <div className="text-sm text-gray-400">Connection Status</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">Binance</div>
            <div className="text-sm text-gray-400">Data Source</div>
          </div>
        </div>
      </div>
    </div>
  )
}
