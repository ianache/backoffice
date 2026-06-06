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
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
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
      }
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

  function login(): void {
    keycloak.login()
  }

  function logout(): void {
    if (refreshInterval) clearInterval(refreshInterval)
    isAuthenticated.value = false
    token.value = null
    user.value = null
    roles.value = []
    keycloak.logout()
  }

  return { isAuthenticated, token, user, roles, isLoading, hasRole, init, login, logout }
}, {
  persist: {
    pick: ['token', 'user', 'roles', 'isAuthenticated'],
    storage: sessionStorage,
  },
})
