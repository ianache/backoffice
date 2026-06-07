import { config } from '../config/index.js'

// Module-level singleton token cache — refreshed only when < 30s remain on expiry
let _adminToken: string | null = null
let _tokenExpiry: number = 0

export async function getAdminToken(): Promise<string> {
  const now = Date.now() / 1000
  if (_adminToken && _tokenExpiry - now > 30) return _adminToken

  const params = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: config.keycloakAdmin.clientId,
    client_secret: config.keycloakAdmin.clientSecret,
  })
  const res = await fetch(
    `${config.keycloak.url}/realms/${config.keycloak.realm}/protocol/openid-connect/token`,
    { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: params }
  )
  if (!res.ok) throw new Error(`Keycloak admin token failed: ${res.status}`)
  const data = await res.json() as { access_token: string; expires_in: number }
  _adminToken = data.access_token
  _tokenExpiry = now + data.expires_in
  return _adminToken
}

export async function kcAdminFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = await getAdminToken()
  const base = `${config.keycloak.url}/admin/realms/${config.keycloak.realm}`
  return fetch(`${base}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })
}
