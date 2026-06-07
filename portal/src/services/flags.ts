import api from './api'

export interface RuleSchema {
  attribute: string
  operator: string  // 'equals' | 'in' | 'notIn' | 'contains' | 'regex'
  value: any
  result: boolean
}

export interface FeatureFlag {
  id: number
  name: string
  description: string | null
  scope: string           // 'global' | 'tenant' | 'product' | 'company'
  tenant_id: string | null
  product_id: string | null
  company_id: string | null
  enabled: boolean
  default_val: boolean
  complex: boolean
  ttl: number | null
  environment: string     // 'production' | 'staging' | 'development'
  rollout: number         // 0-100 display only in Phase 4 (FLAG-07 deferred)
  rules: RuleSchema[]
  tags: string[]
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface FlagPayload {
  name: string
  description?: string
  scope: string
  tenant_id?: string
  product_id?: string
  company_id?: string
  enabled?: boolean
  default_val?: boolean
  complex?: boolean
  ttl?: number
  environment?: string
  rollout?: number
  rules?: RuleSchema[]
  tags?: string[]
}

export interface FlagFilters {
  scope?: string
  q?: string
}

export interface Segment {
  id: number
  name: string
  description: string | null
  tenant_id: string | null
  members: string[]       // array of user UUIDs
  created_at: string
  updated_at: string
}

export interface SegmentPayload {
  name: string
  description?: string
  tenant_id?: string
  members?: string[]
}

// Flags

export async function list(filters?: FlagFilters): Promise<FeatureFlag[]> {
  const { data } = await api.get('/flags/', { params: filters })
  return data
}

export async function create(payload: FlagPayload): Promise<FeatureFlag> {
  const { data } = await api.post('/flags/', payload)
  return data
}

export async function update(id: number, payload: Partial<FlagPayload>): Promise<FeatureFlag> {
  const { data } = await api.patch(`/flags/${id}`, payload)
  return data
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/flags/${id}`)
}

export async function setEnabled(id: number, enabled: boolean): Promise<void> {
  const endpoint = enabled ? `/flags/${id}/enable` : `/flags/${id}/disable`
  await api.post(endpoint)
}

// Segments (FLAG-06)

export async function listSegments(tenantId?: string): Promise<Segment[]> {
  const { data } = await api.get('/flags/segments/', { params: tenantId ? { tenant_id: tenantId } : {} })
  return data
}

export async function createSegment(payload: SegmentPayload): Promise<Segment> {
  const { data } = await api.post('/flags/segments/', payload)
  return data
}
