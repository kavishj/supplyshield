import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Auth removal switch.
 * Set VITE_AUTH_ENABLED=false in .env → login screen is skipped entirely,
 * every route is accessible, no token is required by the BFF.
 *
 * To remove auth permanently:
 *   1. Delete this file.
 *   2. Delete src/components/ProtectedRoute.jsx.
 *   3. Remove <ProtectedRoute> wrappers from App.jsx.
 *   4. Set AUTH_REQUIRED=false in bff/.env (or remove the dependency).
 */
const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED !== 'false'

export const useAuthStore = create(
  persist(
    (set) => ({
      // When auth is disabled, start in authenticated state so nothing blocks.
      isAuthenticated: !AUTH_ENABLED,
      token:           null,
      authEnabled:     AUTH_ENABLED,

      /** Called after successful OTP verification. */
      login: (token) => set({ isAuthenticated: true, token }),

      /** Clears session — call on logout or token expiry. */
      logout: () => set({ isAuthenticated: false, token: null }),
    }),
    {
      name:    'supplyshield-auth',   // localStorage key
      // Only persist token + isAuthenticated — authEnabled is derived from env
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        token:           state.token,
      }),
    }
  )
)
