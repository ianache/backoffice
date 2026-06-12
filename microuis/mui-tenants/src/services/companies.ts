import api from 'shell/api'

export interface Company {
  id: string
  name: string
  status: 'active' | 'inactive'
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface CompanyPayload {
  id: string
  name: string
  status: 'active' | 'inactive'
  tenant_id: string
}

// id (slug) and tenant_id are immutable after creation — backend CompanyUpdate excludes both
export type CompanyUpdatePayload = Partial<Pick<CompanyPayload, 'name' | 'status'>>

// Default '' = ALL statuses (admin view shows inactive too, like ProductsView)
export async function listCompanies(statusFilter: string = ''): Promise<Company[]> {
  const { data } = await api.get('/companies/', {
    params: statusFilter ? { status: statusFilter } : {},
  })
  // Backend returns a plain array (List[CompanyResponse]); tolerate {items} wrappers
  return Array.isArray(data) ? data : (data.items ?? [])
}

export async function createCompany(payload: CompanyPayload): Promise<Company> {
  const { data } = await api.post('/companies/', payload)
  return data
}

export async function updateCompany(id: string, payload: CompanyUpdatePayload): Promise<Company> {
  const { data } = await api.patch(`/companies/${id}`, payload)
  return data
}
