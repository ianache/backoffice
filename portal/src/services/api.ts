import axios from 'axios'
import keycloak from '../plugins/keycloak'

const api = axios.create({
  baseURL: import.meta.env.VITE_BFF_URL as string,
  withCredentials: false,
})

api.interceptors.request.use(async (config) => {
  // Refresh if token expires within 30 seconds (skip in E2E mode where Keycloak is bypassed)
  if (import.meta.env.VITE_E2E_SKIP_AUTH !== 'true') {
    try {
      await keycloak.updateToken(30)
    } catch {
      // Token refresh failed — Keycloak will handle redirect
    }
  }
  if (keycloak.token) {
    config.headers.Authorization = `Bearer ${keycloak.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && import.meta.env.VITE_E2E_SKIP_AUTH !== 'true') {
      keycloak.login()
    }
    return Promise.reject(error)
  }
)

export default api
