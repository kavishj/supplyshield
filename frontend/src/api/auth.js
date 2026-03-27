import axios from 'axios'

// All requests go through Vite's proxy (/api → http://localhost:8006)
// so no port is ever hard-coded in application code.
const http = axios.create({ baseURL: '/api' })

/**
 * Step 1 — verify username + password.
 * Returns { success: true, requires_setup: bool }
 */
export const apiLogin = (username, password) =>
  http.post('/auth/login', { username, password })

/**
 * Step 2 — verify TOTP code, receive JWT.
 * Returns { success: true, token: string }
 */
export const apiVerifyOtp = (otp_code) =>
  http.post('/auth/verify-otp', { otp_code })

/**
 * Returns the URL for the TOTP QR code PNG.
 * Used as an <img src="..."> — no axios needed.
 */
export const getQrCodeUrl = () => '/api/auth/qr-code'

/**
 * Re-validate a stored JWT on page load.
 * Returns { authenticated: true, username: string }
 */
export const apiGetMe = (token) =>
  http.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
