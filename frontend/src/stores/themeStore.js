import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useThemeStore = create(
  persist(
    (set) => ({
      dark: false,
      toggle: () => set(s => ({ dark: !s.dark })),
    }),
    { name: 'supplyshield-theme' }
  )
)
