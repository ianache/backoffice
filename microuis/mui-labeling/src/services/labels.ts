import api from 'shell/api'

export interface Namespace {
  id: string
  strategy: 'eager' | 'lazy'
  description: string | null
  created_at: string
  updated_at: string
}

export interface NamespacePayload {
  id: string
  strategy?: 'eager' | 'lazy'
  description?: string
}

export interface LocalizedLabel {
  id: number
  tenant_id: string
  company_id: string | null
  product_id: string | null
  namespace: string
  locale: 'es_PE' | 'en_US'
  label_key: string
  label_value: string
  label_type: string | null
  params: string[]
  description: string | null
  version: number
  created_at: string
  updated_at: string
}

export interface LabelCreatePayload {
  tenant_id: string
  company_id?: string | null
  product_id?: string | null
  namespace: string
  label_key: string
  label_type?: string | null
  params?: string[]
  description?: string | null
  values: Record<string, string>
}

export interface LabelUpdatePayload {
  label_type?: string | null
  params?: string[]
  description?: string | null
  values?: Record<string, string>
  version: number
}

export interface LabelValuePayload {
  locale: string
  label_value: string
  version: number
}

export interface RestorePayload {
  tenant_id: string
  company_id?: string | null
  product_id?: string | null
  namespace: string
  locale: string
  label_key: string
}

export interface MissingLabelReport {
  id: number
  tenant_id: string
  company_id: string | null
  product_id: string | null
  namespace: string
  label_key: string
  locale: string
  hits: number
  created_at: string
  last_reported_at: string
}

export interface KeysFilter {
  tenant_id: string
  company_id?: string
  product_id?: string
  namespace?: string
}

// Namespaces (RF-02)

export async function listNamespaces(): Promise<Namespace[]> {
  const { data } = await api.get('/labels/namespaces')
  return data
}

export async function createNamespace(payload: NamespacePayload): Promise<Namespace> {
  const { data } = await api.post('/labels/namespaces', payload)
  return data
}

export async function updateNamespace(id: string, payload: Partial<NamespacePayload>): Promise<Namespace> {
  const { data } = await api.patch(`/labels/namespaces/${id}`, payload)
  return data
}

export async function deleteNamespace(id: string): Promise<void> {
  await api.delete(`/labels/namespaces/${id}`)
}

// Keys (RF-03/RF-04)

export async function listKeys(filters: KeysFilter): Promise<LocalizedLabel[]> {
  const { data } = await api.get('/labels/keys', { params: filters })
  return data
}

export async function createKey(payload: LabelCreatePayload): Promise<LocalizedLabel[]> {
  const { data } = await api.post('/labels/keys', payload)
  return data
}

export async function updateKey(id: number, payload: LabelUpdatePayload): Promise<LocalizedLabel> {
  const { data } = await api.patch(`/labels/keys/${id}`, payload)
  return data
}

export async function updateKeyValue(id: number, payload: LabelValuePayload): Promise<LocalizedLabel> {
  const { data } = await api.patch(`/labels/keys/${id}/value`, payload)
  return data
}

export async function deleteKey(id: number): Promise<void> {
  await api.delete(`/labels/keys/${id}`)
}

export async function restoreOverride(payload: RestorePayload): Promise<void> {
  await api.post('/labels/keys/restore', payload)
}

// Missing label reports (RF-06)

export async function listMissingLabels(tenantId: string): Promise<MissingLabelReport[]> {
  const { data } = await api.get('/labels/missing', { params: { tenant_id: tenantId } })
  return data
}
