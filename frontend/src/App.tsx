import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import { NAV } from './nav'
import Shell from './Shell'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Signup from './pages/Signup'
import VerifyEmail from './pages/VerifyEmail'
import {
  Assistant, Audit, Billing, Catalog, Customers, Insights, Invoices, Payments, Reconciliation, Subscriptions,
} from './pages/Modules'

const PAGES: Record<string, JSX.Element> = {
  '/': <Dashboard />,
  '/customers': <Customers />,
  '/subscriptions': <Subscriptions />,
  '/billing': <Billing />,
  '/invoices': <Invoices />,
  '/payments': <Payments />,
  '/reconciliation': <Reconciliation />,
  '/insights': <Insights />,
  '/assistant': <Assistant />,
  '/catalog': <Catalog />,
  '/audit': <Audit />,
}

export default function App() {
  const { role, loading } = useAuth()
  if (loading) return <div className="login"><p className="muted">Loading…</p></div>
  if (!role) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }
  // Only routes in the signed-in role's nav exist; the backend must still enforce this.
  return (
    <Routes>
      <Route element={<Shell />}>
        {NAV[role].map(({ to }) => <Route key={to} path={to} element={PAGES[to]} />)}
      </Route>
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
