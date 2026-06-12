import api from 'shell/api'

// Lightweight lookup catalogs for FlagForm scope-target comboboxes (TGT-01).
// mui-feature-flags creates its own HTTP services rather than sharing stores
// with other remotes (per 14-CONTEXT.md).

export interface LookupOption {
  id: string
  name: string
}

// GET /products/?status=active -> [{id: slug, name, ...}] -> {id, name}
export async function listProductsLookup(): Promise<LookupOption[]> {
  const { data } = await api.get('/products/', { params: { status: 'active' } })
  const items = Array.isArray(data) ? data : (data.items ?? [])
  return items.map((p: any) => ({ id: p.id, name: p.name }))
}

// GET /companies/?status=active -> [{id: slug, name, tenant_id, ...}] -> {id, name}
export async function listCompaniesLookup(): Promise<LookupOption[]> {
  const { data } = await api.get('/companies/', { params: { status: 'active' } })
  const items = Array.isArray(data) ? data : (data.items ?? [])
  return items.map((c: any) => ({ id: c.id, name: c.name }))
}

// GET /tenants/ -> [{id: number, name, ...}] -> {id: String(id), name}
// PlatformAdmin-only BFF route — callers should catch errors and fall back
// to the logged-in user's own tenant via useUserContext().
export async function listTenantsLookup(): Promise<LookupOption[]> {
  const { data } = await api.get('/tenants/')
  const items = Array.isArray(data) ? data : (data.items ?? [])
  return items.map((t: any) => ({ id: String(t.id), name: t.name }))
}
