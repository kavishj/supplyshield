/**
 * Supplier-portal API calls.
 *
 * Supplier endpoints use the supplier JWT.
 * Admin endpoints that manage supplier accounts use the regular admin
 * JWT and are exported from bff.js — see those exports below the class.
 */
import axios from 'axios'
import { useSupplierAuthStore } from '../stores/supplierAuthStore'

const http = axios.create({ baseURL: '/api/supplier-portal' })

// Inject supplier Bearer token on every request
http.interceptors.request.use((config) => {
  const { token } = useSupplierAuthStore.getState()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 clear supplier session
http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useSupplierAuthStore.getState().logout()
    }
    return Promise.reject(err)
  }
)

// ── Supplier auth ─────────────────────────────────────────────────────────────
export const apiSupplierLogin = (username, password) =>
  http.post('/auth/login', { username, password })

// ── Supplier portal (supplier JWT) ───────────────────────────────────────────
export const apiGetMyNotifications = ()       => http.get('/notifications')
export const apiMarkNotifRead      = (id)     => http.put(`/notifications/${id}/read`)

export const apiUploadDocument = (notification_id, file, note = '') => {
  const fd = new FormData()
  fd.append('notification_id', notification_id)
  fd.append('note', note)
  fd.append('file', file)
  return http.post('/documents', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
