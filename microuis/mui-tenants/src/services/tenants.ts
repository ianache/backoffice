import api from 'shell/api'

export interface Tenant {
  id: number
  name: string
  country: string
  status: 'active' | 'suspended'
  owner?: string
  default_language: string
  default_currency: string
  default_units: string
  logo_url?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  font_family?: string
  font_weight?: string
  domain?: string
  products: string[]
  created_at: string
}

export interface TenantFilters {
  status?: string
  country?: string
  q?: string
}

export type TenantPayload = Omit<Tenant, 'id' | 'created_at'>

export async function list(filters?: TenantFilters): Promise<Tenant[]> {
  const { data } = await api.get('/tenants/', { params: filters })
  return data
}

export async function create(payload: TenantPayload): Promise<Tenant> {
  const { data } = await api.post('/tenants/', payload)
  return data
}

export async function update(id: number, payload: Partial<TenantPayload>): Promise<Tenant> {
  const { data } = await api.patch(`/tenants/${id}`, payload)
  return data
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/tenants/${id}`)
}

// Product subscriptions live in tenant_subscriptions (since b003) and are managed
// via dedicated endpoints — the products array in create/update payloads is ignored
// by the backend schemas.
export async function subscribeProduct(tenantId: number, productId: string): Promise<void> {
  await api.post(`/tenants/${tenantId}/products/${productId}`)
}

export async function unsubscribeProduct(tenantId: number, productId: string): Promise<void> {
  await api.delete(`/tenants/${tenantId}/products/${productId}`)
}
