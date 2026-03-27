/**
 * All HTTP calls to the BFF.
 * Every call goes through /api (Vite proxy → localhost:8006).
 * Token is injected from the Zustand auth store.
 */
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const http = axios.create({ baseURL: '/api' })

// Inject Bearer token from Zustand store on every request
http.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear auth and let the router redirect to /login
http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(err)
  }
)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const apiLogin       = (username, password) => http.post('/auth/login', { username, password })
export const apiVerifyOtp   = (otp_code)           => http.post('/auth/verify-otp', { otp_code })
export const apiGetMe       = ()                   => http.get('/auth/me')
export const getQrCodeUrl   = ()                   => '/api/auth/qr-code'

// ── Health ────────────────────────────────────────────────────────────────────
export const apiHealth = () => http.get('/health')

// ── Company Profile ───────────────────────────────────────────────────────────
export const apiGetProfile    = ()       => http.get('/profile')
export const apiProfileStatus = ()       => http.get('/profile/status')
export const apiSaveProfile   = (data)   => http.post('/profile', data)

// ── Onboarded Suppliers ───────────────────────────────────────────────────────
export const apiGetSuppliers    = ()           => http.get('/suppliers/onboarded')
export const apiSaveSupplier    = (data)       => http.post('/suppliers/onboarded', data)
export const apiDeleteSupplier  = (id)         => http.delete(`/suppliers/onboarded/${id}`)
export const apiExcelUpload     = (file)       => {
  const fd = new FormData()
  fd.append('file', file)
  return http.post('/suppliers/excel-upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const getTemplateUrl = () => '/api/suppliers/excel-template'

// ── Audit Log ─────────────────────────────────────────────────────────────────
export const apiAuditLog = () => http.get('/audit-log')

// ── Portfolio ─────────────────────────────────────────────────────────────────
export const apiPortfolio      = () => http.get('/portfolio')
export const apiRiskySuppliers = () => http.get('/risky-suppliers')

// ── Analysis ─────────────────────────────────────────────────────────────────
export const apiAnalyze   = (payload) => http.post('/analyze',   payload, { timeout: 140000 })
export const apiRecommend = (payload) => http.post('/recommend', payload, { timeout: 140000 })

// ── Recommendations ───────────────────────────────────────────────────────────
export const apiGetRecommendation    = (name)    => http.get(`/recommendations/${encodeURIComponent(name)}`)
export const apiUpdateActionStatus   = (name, action_id, completed) =>
  http.post(`/recommendations/${encodeURIComponent(name)}/action-status`, { action_id, completed })

// ── Supplier Portal (admin side) ──────────────────────────────────────────────
export const apiGetSupplierAccountStatus  = (id)   => http.get(`/supplier-portal/accounts/${id}/status`)
export const apiCreateSupplierAccount     = (data)  => http.post('/supplier-portal/accounts', data)
export const apiNotifySupplier            = (data)  => http.post('/supplier-portal/notify', data)
export const apiGetSupplierActionLog      = ()      => http.get('/supplier-portal/action-log')
export const apiMarkActionLogSeen         = ()      => http.put('/supplier-portal/action-log/mark-seen')
export const getDocumentDownloadUrl       = (docId) => `/api/supplier-portal/documents/${docId}`

// ── PDF ───────────────────────────────────────────────────────────────────────
export const apiGeneratePdf = async (result) => {
  const res = await http.post('/pdf/generate', result, { responseType: 'blob' })
  return res.data  // Blob
}
