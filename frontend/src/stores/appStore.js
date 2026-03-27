/**
 * Global app state — company profile, onboarding status, agent health.
 * NOT persisted to localStorage (fetched fresh on every app load).
 */
import { create } from 'zustand'
import { apiProfileStatus, apiGetProfile } from '../api/bff'

export const useAppStore = create((set) => ({
  profile:            null,
  onboardingComplete: null,   // null = not yet checked

  /** Called once after authentication to bootstrap app state. */
  async bootstrap() {
    try {
      const [statusRes, profileRes] = await Promise.all([
        apiProfileStatus(),
        apiGetProfile(),
      ])
      set({
        onboardingComplete: statusRes.data.onboarding_complete,
        profile:            profileRes.data,
      })
    } catch {
      set({ onboardingComplete: false, profile: null })
    }
  },

  setProfile(profile) {
    set({ profile, onboardingComplete: true })
  },
}))
