import axios from 'axios'
import keycloak from '../plugins/keycloak'

const api = axios.create({
  baseURL: import.meta.env.VITE_BFF_URL as string,
  withCredentials: false,
})

api.interceptors.request.use(async (config) => {
  // Refresh if token expires within 30 seconds
  try {
    await keycloak.updateToken(30)
  } catch {
    // Token refresh failed — Keycloak will handle redirect
  }
  if (keycloak.token) {
    config.headers.Authorization = `Bearer ${keycloak.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      keycloak.login()
    }
    return Promise.reject(error)
  }
)

export default api
