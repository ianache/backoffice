import { describe, it, expect, vi, beforeEach } from 'vitest'

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
      tokenParsed: { preferred_username: 'test-user', email: 'test@example.com' },
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
    expect(store.user).toEqual({ name: 'test-user', email: 'test@example.com' })
    expect(store.roles).toEqual(['User'])
    expect(store.isLoading).toBe(false)
  })

  it('clears auth state when Keycloak init returns false (unauthenticated)', async () => {
    vi.mocked(keycloak.init).mockResolvedValue(false)
    const store = useAuthStore()
    
    // Simulate persisted state being true initially
    store.isAuthenticated = true
    store.token = 'old-token'
    store.user = { name: 'old-user', email: 'old@example.com' }
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
    store.user = { name: 'old-user', email: 'old@example.com' }
    store.roles = ['OldRole']
    
    await store.init()
    
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.roles).toEqual([])
    expect(store.isLoading).toBe(false)
  })
})
