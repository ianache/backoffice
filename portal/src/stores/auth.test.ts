import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Set up sessionStorage globally before any module evaluation
globalThis.sessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn(),
  length: 0,
} as unknown as Storage

import { setActivePinia, createPinia } from 'pinia'
import keycloak from '../plugins/keycloak'

// Dynamically import the store so sessionStorage is already defined on globalThis
const { useAuthStore } = await import('./auth')

vi.mock('../plugins/keycloak', () => {
  return {
    default: {
      init: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
      updateToken: vi.fn(),
      token: 'mock-token',
      realmAccess: { roles: ['User'] },
      tokenParsed: { preferred_username: 'test-user', email: 'test@example.com', sub: 'mock-sub-123' },
    },
  }
})

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('populates store on successful authentication', async () => {
    vi.mocked(keycloak.init).mockResolvedValue(true)
    const store = useAuthStore()
    
    await store.init()
    
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('mock-token')
    expect(store.user).toEqual({ name: 'test-user', email: 'test@example.com', sub: 'mock-sub-123' })
    expect(store.roles).toEqual(['User'])
    expect(store.isLoading).toBe(false)
  })

  it('clears auth state when Keycloak init returns false (unauthenticated)', async () => {
    vi.mocked(keycloak.init).mockResolvedValue(false)
    const store = useAuthStore()
    
    // Simulate persisted state being true initially
    store.isAuthenticated = true
    store.token = 'old-token'
    store.user = { name: 'old-user', email: 'old@example.com', sub: 'old-sub' }
    store.roles = ['OldRole']
    
    await store.init()
    
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.roles).toEqual([])
    expect(store.isLoading).toBe(false)
  })

  it('clears auth state when Keycloak init throws an error', async () => {
    vi.mocked(keycloak.init).mockRejectedValue(new Error('Network Error'))
    const store = useAuthStore()
    
    // Simulate persisted state being true initially
    store.isAuthenticated = true
    store.token = 'old-token'
    store.user = { name: 'old-user', email: 'old@example.com', sub: 'old-sub' }
    store.roles = ['OldRole']
    
    await store.init()
    
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.roles).toEqual([])
    expect(store.isLoading).toBe(false)
  })

  describe('loginWithCredentials()', () => {
    beforeEach(() => {
      vi.stubGlobal('fetch', vi.fn())
    })

    afterEach(() => {
      vi.unstubAllGlobals()
    })

    it('throws AUTH_ERR_INVALID_CREDENTIALS on invalid request status', async () => {
      const { AUTH_ERR_INVALID_CREDENTIALS } = await import('./auth')
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 401,
      } as Response)

      const store = useAuthStore()
      await expect(store.loginWithCredentials('test@example.com', 'wrong-pass'))
        .rejects.toThrow(AUTH_ERR_INVALID_CREDENTIALS)
    })

    it('throws AUTH_ERR_FAILED_AFTER_EXCHANGE on Keycloak post-exchange failure', async () => {
      const { AUTH_ERR_FAILED_AFTER_EXCHANGE } = await import('./auth')
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: async () => ({
          access_token: 'new-acc',
          refresh_token: 'new-ref',
          id_token: 'new-id',
        }),
      } as Response)

      vi.mocked(keycloak.init).mockResolvedValue(false) // authentication fails after exchange

      const store = useAuthStore()
      await expect(store.loginWithCredentials('test@example.com', 'correct-pass'))
        .rejects.toThrow(AUTH_ERR_FAILED_AFTER_EXCHANGE)
    })
  })
})

