import api from 'shell/api'

export interface Product {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive'
  labels?: string[]
}

export interface ProductListResponse {
  items: Product[]
  total: number
}

export async function listProducts(statusFilter = 'active'): Promise<Product[]> {
  const { data } = await api.get<ProductListResponse>('/products/', {
    params: { status: statusFilter },
  })
  return data.items ?? []
}
