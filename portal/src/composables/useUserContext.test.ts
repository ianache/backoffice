import { describe, it, expect, beforeEach, vi } from 'vitest'

globalThis.sessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn(),
  length: 0,
} as unknown as Storage

import { setActivePinia, createPinia } from 'pinia'
const { useAuthStore } = await import('../stores/auth')
const { useUserContext } = await import('./useUserContext')

describe('useUserContext', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('returns mapped real-user context when authenticated', () => {
    const authStore = useAuthStore()
    authStore.$patch({
      isAuthenticated: true,
      user: { name: 'Test User', email: 'a@b.com', sub: 'user-123' },
      roles: ['PlatformAdmin'],
    })

    const ctx = useUserContext()

    expect(ctx.sub).toBe('user-123')
    expect(ctx.email).toBe('a@b.com')
    expect(ctx.roles).toEqual(['PlatformAdmin'])
    expect(ctx.product_id).toBe('backoffice')
    expect(typeof ctx.tenant_id).toBe('string')
  })

  it('returns empty defaults when unauthenticated (no throw)', () => {
    const ctx = useUserContext()

    expect(ctx.sub).toBe('')
    expect(ctx.email).toBe('')
    expect(ctx.roles).toEqual([])
    expect(ctx.product_id).toBe('backoffice')
  })
})
