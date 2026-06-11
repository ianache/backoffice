import api from 'shell/api'

export interface Product {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive'
  labels: string[]
  created_at: string
  updated_at: string
}

export interface ProductPayload {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive'
  labels: string[]
}

// id (slug) is immutable after creation — backend ProductUpdate has no id field
export type ProductUpdatePayload = Partial<Omit<ProductPayload, 'id'>>

// Default 'active' keeps TenantForm's product-access list behavior; pass '' for the full catalog
export async function listProducts(statusFilter: string = 'active'): Promise<Product[]> {
  const { data } = await api.get('/products/', {
    params: statusFilter ? { status: statusFilter } : {},
  })
  // Backend returns a plain array (List[ProductResponse]); tolerate {items} wrappers
  return Array.isArray(data) ? data : (data.items ?? [])
}

export async function createProduct(payload: ProductPayload): Promise<Product> {
  const { data } = await api.post('/products/', payload)
  return data
}

export async function updateProduct(id: string, payload: ProductUpdatePayload): Promise<Product> {
  const { data } = await api.patch(`/products/${id}`, payload)
  return data
}
