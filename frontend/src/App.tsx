import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Bots from './pages/Bots'
import Trades from './pages/Trades'
import Alerts from './pages/Alerts'
import Signals from './pages/Signals'
import Emergency from './pages/Emergency'
import Login from './pages/Login'
import Register from './pages/Register'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected — wrapped in AppLayout sidebar */}
      <Route element={<PrivateRoute><AppLayout /></PrivateRoute>}>
        <Route path="/"          element={<Dashboard />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/bots"      element={<Bots />} />
        <Route path="/trades"    element={<Trades />} />
        <Route path="/alerts"    element={<Alerts />} />
        <Route path="/signals"   element={<Signals />} />
        <Route path="/emergency" element={<Emergency />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
