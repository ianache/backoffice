import api from 'shell/api'

// KcUser maps the Keycloak UserRepresentation as returned by GET /users
export interface KcUser {
  id: string              // Keycloak UUID
  username: string
  email: string
  first_name: string
  last_name: string
  enabled: boolean
  tenant_id: string       // from attributes.tenant_id[0]
  tenant_role: string | null  // e.g., "TenantAdmin" — derived from realm roles
  product_roles: Record<string, string>  // { productId: roleName }
  created_timestamp: number
}

// Payload for creating or updating a user
export interface UserPayload {
  email: string
  first_name: string
  last_name: string
  tenant_role: string
  product_roles: Record<string, string>  // { productId: roleName | '' }
}

// Single audit log entry for a user
export interface UserEventRecord {
  id: number
  keycloak_user_id: string
  actor_sub: string
  action: string            // user.created, user.updated, user.enabled, user.disabled, user.roles_changed, user.mfa_reset
  context: Record<string, unknown> | null
  created_at: string        // ISO date string
}

export interface UserFilters {
  enabled?: boolean
}

// List all users in the caller's tenant (BFF injects tenant context from JWT)
export async function list(filters?: UserFilters): Promise<KcUser[]> {
  const { data } = await api.get('/users/', { params: filters })
  return data
}

// Create a new user in Keycloak with tenant assignment and initial role
export async function create(payload: UserPayload): Promise<KcUser> {
  const { data } = await api.post('/users/', payload)
  return data
}

// Update user profile and/or roles
export async function update(id: string, payload: Partial<UserPayload>): Promise<KcUser> {
  const { data } = await api.patch(`/users/${id}`, payload)
  return data
}

// Enable or disable a user (blocks login when disabled)
export async function setEnabled(id: string, enabled: boolean): Promise<void> {
  const endpoint = enabled ? `/users/${id}/enable` : `/users/${id}/disable`
  await api.post(endpoint)
}

// Remove all OTP and WebAuthn credentials, forcing re-enrollment on next login
export async function resetMfa(id: string): Promise<void> {
  await api.post(`/users/${id}/reset-mfa`)
}

// Load chronological audit events for a specific user
export async function listEvents(id: string): Promise<UserEventRecord[]> {
  const { data } = await api.get(`/users/${id}/events`)
  return data
}
