import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

/**
 * Wraps any route that requires authentication.
 *
 * Auth removal: delete this file and remove <ProtectedRoute> wrappers in App.jsx.
 * The VITE_AUTH_ENABLED=false switch in .env already makes isAuthenticated=true
 * by default, so the redirect never fires — but this component can stay in place
 * until you're ready to delete it.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}
