import { BrowserRouter, Routes, Route } from 'react-router-dom'

function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-green-400 mb-2">💹 Crypto Dash</h1>
        <p className="text-gray-400">Dashboard — Coming Soon</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/portfolio" element={<div className="p-8 text-white">Portfolio</div>} />
        <Route path="/alerts" element={<div className="p-8 text-white">Alerts</div>} />
        <Route path="/signals" element={<div className="p-8 text-white">Signals</div>} />
        <Route path="/login" element={<div className="p-8 text-white">Login</div>} />
      </Routes>
    </BrowserRouter>
  )
}
