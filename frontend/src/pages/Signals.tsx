import { useState } from 'react'
import api from '../services/api'

interface Signal {
  coin_id: string
  symbol: string
  signal: string
  rsi: number
  rsi_signal: string
  ema_short: number
  ema_long: number
  ema_signal: string
}

const POPULAR_COINS = [
  { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin' },
  { id: 'ethereum', symbol: 'ETH', name: 'Ethereum' },
  { id: 'binancecoin', symbol: 'BNB', name: 'Binance Coin' },
  { id: 'cardano', symbol: 'ADA', name: 'Cardano' },
  { id: 'solana', symbol: 'SOL', name: 'Solana' },
  { id: 'ripple', symbol: 'XRP', name: 'Ripple' },
  { id: 'polkadot', symbol: 'DOT', name: 'Polkadot' },
  { id: 'dogecoin', symbol: 'DOGE', name: 'Dogecoin' },
]

export default function Signals() {
  const [selectedCoin, setSelectedCoin] = useState('bitcoin')
  const [signal, setSignal] = useState<Signal | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchSignal = async (coinId: string) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get<Signal>(`/signals/${coinId}`)
      setSignal(data)
    } catch (err: any) {
      setError('Failed to fetch signal')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCoinSelect = (coinId: string) => {
    setSelectedCoin(coinId)
    fetchSignal(coinId)
  }

  const getSignalColor = (sig: string) => {
    if (sig === 'BUY' || sig === 'OVERSOLD') return 'text-green-400'
    if (sig === 'SELL' || sig === 'OVERBOUGHT') return 'text-red-400'
    return 'text-gray-400'
  }

  const getSignalIcon = (sig: string) => {
    if (sig === 'BUY' || sig === 'OVERSOLD') return '🟢'
    if (sig === 'SELL' || sig === 'OVERBOUGHT') return '🔴'
    return '🟡'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">📈 Trading Signals</h2>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Coin Selector */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Select Coin</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {POPULAR_COINS.map((coin) => (
            <button
              key={coin.id}
              onClick={() => handleCoinSelect(coin.id)}
              className={`p-4 rounded-lg text-left transition-all ${
                selectedCoin === coin.id
                  ? 'bg-green-500/20 border-2 border-green-500 text-green-400'
                  : 'bg-gray-800 border-2 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white'
              }`}
            >
              <div className="font-semibold">{coin.symbol}</div>
              <div className="text-xs opacity-75">{coin.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Signal Display */}
      {loading && (
        <div className="text-center py-12 text-gray-400">
          Loading signal...
        </div>
      )}

      {signal && !loading && (
        <div className="space-y-6">
          {/* Overall Signal */}
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">{getSignalIcon(signal.signal)}</div>
              <div className={`text-4xl font-bold mb-2 ${getSignalColor(signal.signal)}`}>
                {signal.signal}
              </div>
              <div className="text-gray-400">
                {signal.symbol} Overall Signal
              </div>
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* RSI */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">📊 RSI (Relative Strength Index)</h3>
              
              <div className="mb-4">
                <div className="flex justify-between mb-2">
                  <span className="text-gray-400">Value</span>
                  <span className="text-white font-semibold">{signal.rsi.toFixed(2)}</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      signal.rsi < 30
                        ? 'bg-green-500'
                        : signal.rsi > 70
                          ? 'bg-red-500'
                          : 'bg-yellow-500'
                    }`}
                    style={{ width: `${signal.rsi}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0 (Oversold)</span>
                  <span>50</span>
                  <span>100 (Overbought)</span>
                </div>
              </div>

              <div className={`text-center text-xl font-bold ${getSignalColor(signal.rsi_signal)}`}>
                {signal.rsi_signal}
              </div>
              <div className="text-center text-gray-400 text-sm mt-2">
                {signal.rsi < 30 && '⬇️ Price may be oversold - potential buy opportunity'}
                {signal.rsi > 70 && '⬆️ Price may be overbought - potential sell signal'}
                {signal.rsi >= 30 && signal.rsi <= 70 && '➡️ Neutral - no clear signal'}
              </div>
            </div>

            {/* EMA */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">📉 EMA (Exponential Moving Average)</h3>
              
              <div className="space-y-3 mb-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">EMA Short (12-day)</span>
                  <span className="text-white font-semibold">${signal.ema_short.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">EMA Long (26-day)</span>
                  <span className="text-white font-semibold">${signal.ema_long.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Crossover</span>
                  <span className={`font-semibold ${
                    signal.ema_short > signal.ema_long ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {signal.ema_short > signal.ema_long ? 'Bullish ⬆️' : 'Bearish ⬇️'}
                  </span>
                </div>
              </div>

              <div className={`text-center text-xl font-bold ${getSignalColor(signal.ema_signal)}`}>
                {signal.ema_signal}
              </div>
              <div className="text-center text-gray-400 text-sm mt-2">
                {signal.ema_short > signal.ema_long && '🚀 Short EMA above Long EMA - uptrend'}
                {signal.ema_short <= signal.ema_long && '📉 Short EMA below Long EMA - downtrend'}
              </div>
            </div>
          </div>

          {/* Strategy Recommendation */}
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">💡 Recommendation</h3>
            <div className="text-gray-300 leading-relaxed">
              {signal.signal === 'BUY' && (
                <div className="text-green-400">
                  ✅ <strong>BUY Signal Detected:</strong> Both RSI and EMA indicators suggest a buying opportunity. 
                  Consider entering a position or adding to existing holdings. Always use stop-loss orders.
                </div>
              )}
              {signal.signal === 'SELL' && (
                <div className="text-red-400">
                  ⚠️ <strong>SELL Signal Detected:</strong> Both RSI and EMA indicators suggest selling pressure. 
                  Consider taking profits or reducing position size. Protect your downside.
                </div>
              )}
              {signal.signal === 'NEUTRAL' && (
                <div className="text-gray-400">
                  ⏸️ <strong>Neutral Signal:</strong> Mixed signals from RSI and EMA. 
                  Consider waiting for a clearer trend before making trading decisions.
                </div>
              )}
            </div>
            <div className="mt-4 text-sm text-gray-500">
              ⚠️ This is not financial advice. Always do your own research and consider your risk tolerance.
            </div>
          </div>
        </div>
      )}

      {!signal && !loading && (
        <div className="text-center py-12 text-gray-500">
          Select a coin to view trading signals
        </div>
      )}
    </div>
  )
}
