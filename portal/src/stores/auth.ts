import { defineStore } from 'pinia'
import { ref } from 'vue'
import keycloak from '../plugins/keycloak'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const token = ref<string | null>(null)
  const user = ref<{ name: string; email: string } | null>(null)
  const roles = ref<string[]>([])
  const isLoading = ref(true)

  let refreshInterval: ReturnType<typeof setInterval> | null = null

  const hasRole = (role: string) => roles.value.includes(role)

  async function init(): Promise<void> {
    isLoading.value = true
    try {
      const authenticated = await keycloak.init({
        onLoad: 'check-sso',
        checkLoginIframe: false,
      })
      if (authenticated) {
        _populate()
        // Refresh access token every 30s — prevent expiry mid-session
        refreshInterval = setInterval(async () => {
          try {
            const refreshed = await keycloak.updateToken(60)
            if (refreshed) token.value = keycloak.token ?? null
          } catch {
            logout()
          }
        }, 30_000)
      } else {
        _clear()
      }
    } catch (error) {
      console.error('Keycloak initialization failed:', error)
      _clear()
    } finally {
      isLoading.value = false
    }
  }

  function _populate(): void {
    isAuthenticated.value = true
    token.value = keycloak.token ?? null
    roles.value = keycloak.realmAccess?.roles ?? []
    user.value = {
      name: keycloak.tokenParsed?.preferred_username ?? '',
      email: keycloak.tokenParsed?.email ?? '',
    }
  }

  function _clear(): void {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
    isAuthenticated.value = false
    token.value = null
    user.value = null
    roles.value = []
  }

  function login(): void {
    keycloak.login()
  }

  async function loginWithCredentials(email: string, password: string): Promise<void> {
    isLoading.value = true
    try {
      const response = await fetch(`${import.meta.env.VITE_KEYCLOAK_URL}/realms/${import.meta.env.VITE_KEYCLOAK_REALM}/protocol/openid-connect/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          client_id: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
          grant_type: 'password',
          username: email,
          password: password,
        })
      })

      if (!response.ok) {
        throw new Error('Invalid email or password')
      }

      const data = await response.json()
      
      // Initialize keycloak with the obtained tokens
      const authenticated = await keycloak.init({
        onLoad: 'check-sso',
        checkLoginIframe: false,
        token: data.access_token,
        refreshToken: data.refresh_token,
        idToken: data.id_token
      })

      if (authenticated) {
        _populate()
        // Start refresh interval
        if (refreshInterval) clearInterval(refreshInterval)
        refreshInterval = setInterval(async () => {
          try {
            const refreshed = await keycloak.updateToken(60)
            if (refreshed) token.value = keycloak.token ?? null
          } catch {
            logout()
          }
        }, 30_000)
      } else {
        throw new Error('Authentication failed after token exchange')
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      _clear()
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function logout(): void {
    _clear()
    keycloak.logout()
  }

  return { isAuthenticated, token, user, roles, isLoading, hasRole, init, login, loginWithCredentials, logout }
}, {
  persist: {
    pick: ['token', 'user', 'roles', 'isAuthenticated'],
    storage: sessionStorage,
  },
})
