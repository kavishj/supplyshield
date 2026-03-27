import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAppStore }  from './stores/appStore'
import { useAuthStore } from './stores/authStore'
import { useThemeStore } from './stores/themeStore'
import { ToastProvider } from './contexts/ToastContext'
import ProtectedRoute   from './components/ProtectedRoute'
import Layout           from './components/Layout'

// Pages
import Login             from './pages/Login'
import Onboarding        from './pages/Onboarding'
import MySuppliers       from './pages/MySuppliers'
import SupplierAnalysis  from './pages/SupplierAnalysis'
import RiskRecommendations from './pages/RiskRecommendations'
import PortfolioDashboard  from './pages/PortfolioDashboard'
import AuditLog            from './pages/AuditLog'
import SupplierActions     from './pages/SupplierActions'
import SupplierLogin       from './pages/SupplierLogin'
import SupplierPortal      from './pages/SupplierPortal'
import SupplierProtectedRoute from './components/SupplierProtectedRoute'

/**
 * AuthenticatedApp — bootstraps profile state after auth,
 * then enforces the onboarding gate.
 *
 * Onboarding gate: if profile is not yet saved, send user to /onboarding.
 * Once saved, /onboarding can still be reached from the Profile link in the nav.
 *
 * Auth removal: set VITE_AUTH_ENABLED=false in .env OR remove <ProtectedRoute>
 * wrappers below. The gate logic lives entirely in ProtectedRoute + authStore.
 */
function AuthenticatedApp() {
  const bootstrap          = useAppStore(s => s.bootstrap)
  const isAuthenticated    = useAuthStore(s => s.isAuthenticated)
  const onboardingComplete = useAppStore(s => s.onboardingComplete)

  useEffect(() => {
    if (isAuthenticated) bootstrap()
  }, [isAuthenticated, bootstrap])

  return (
    <Routes>
      {/* ── Public ───────────────────────────────────────────────────── */}
      <Route path="/login" element={<Login />} />

      {/* ── Protected app shell ──────────────────────────────────────── */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        {/* Root → onboarding (first time) or suppliers (returning) */}
        <Route index element={
          onboardingComplete === false
            ? <Navigate to="/onboarding" replace />
            : <Navigate to="/suppliers"  replace />
        } />

        {/* Company setup — always accessible via Profile link */}
        <Route path="onboarding"      element={<Onboarding />} />

        {/* Main app pages */}
        <Route path="suppliers"       element={<MySuppliers />} />
        <Route path="analysis"        element={<SupplierAnalysis />} />
        <Route path="recommendations" element={<RiskRecommendations />} />
        <Route path="dashboard"       element={<PortfolioDashboard />} />
        <Route path="audit-log"       element={<AuditLog />} />
        <Route path="supplier-actions" element={<SupplierActions />} />
      </Route>

      {/* ── Supplier portal (standalone, no admin Layout) ─────────── */}
      <Route path="/supplier-login"  element={<SupplierLogin />} />
      <Route
        path="/supplier-portal"
        element={
          <SupplierProtectedRoute>
            <SupplierPortal />
          </SupplierProtectedRoute>
        }
      />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  const dark = useThemeStore(s => s.dark)

  // Sync dark class on <html> whenever theme changes
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthenticatedApp />
      </ToastProvider>
    </BrowserRouter>
  )
}
