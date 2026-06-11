/**
 * useUserContext — Exposes the logged-in user's real context to remote MUIs
 * via Module Federation, for the Live Simulator "use my real context" toggle (Phase 13).
 *
 * Returned keys match feature-flag/segment rule attribute names directly
 * (sub, roles, tenant_id, product_id) — not the raw JWT/authStore shape.
 * Always reads the live Pinia auth store — no caching, no async init.
 */
import { useAuthStore } from '../stores/auth'

export interface UserContext {
  sub: string
  email: string
  roles: string[]
  tenant_id: string
  product_id: string
}

export function useUserContext(): UserContext {
  const authStore = useAuthStore()
  return {
    sub: authStore.user?.sub ?? '',
    email: authStore.user?.email ?? '',
    roles: authStore.roles,
    tenant_id: import.meta.env.VITE_BO_TENANT_ID ?? '',
    product_id: 'backoffice',
  }
}
