import { Navigate } from 'react-router-dom'
import { useSupplierAuthStore } from '../stores/supplierAuthStore'

export default function SupplierProtectedRoute({ children }) {
  const isLoggedIn = useSupplierAuthStore(s => s.isLoggedIn)
  return isLoggedIn ? children : <Navigate to="/supplier-login" replace />
}
