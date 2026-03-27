import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useSupplierAuthStore = create(
  persist(
    (set) => ({
      token:           null,
      supplierId:      null,
      supplierName:    null,
      supplierCountry: null,
      username:        null,
      contactName:     null,
      isLoggedIn:      false,

      login: (data) => set({
        token:           data.token,
        supplierId:      data.supplier_id,
        supplierName:    data.supplier_name,
        supplierCountry: data.supplier_country,
        username:        data.username,
        contactName:     data.contact_name,
        isLoggedIn:      true,
      }),

      logout: () => set({
        token: null, supplierId: null, supplierName: null,
        supplierCountry: null, username: null, contactName: null,
        isLoggedIn: false,
      }),
    }),
    { name: 'supplyshield-supplier-auth' }
  )
)
