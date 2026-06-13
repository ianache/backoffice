import api from 'shell/api'

export interface AuditLogEntry {
  id: number
  created_at: string
  tenant_id: string | null
  user_id: string
  user_email: string | null
  action_type: string
  environment: string
  target_type: string
  target_id: string
  client_ip: string | null
  user_agent: string | null
}

export interface AuditLogFilters {
  environment?: string
  action_type?: string
  user_id?: string
  start_date?: string
  end_date?: string
  page?: number
  limit?: number
}

export interface AuditLogListResult {
  items: AuditLogEntry[]
  total: number
  page: number
  limit: number
}

export interface AuditLogDiff {
  id: number
  action_type: string
  target_type: string
  target_id: string
  diff: {
    added: Record<string, unknown>
    removed: Record<string, unknown>
    modified: Record<string, { before: unknown; after: unknown }>
  }
}

export async function listAuditLogs(filters: AuditLogFilters = {}): Promise<AuditLogListResult> {
  const params: Record<string, string | number> = {}
  if (filters.environment) params.environment = filters.environment
  if (filters.action_type) params.action_type = filters.action_type
  if (filters.user_id) params.user_id = filters.user_id
  if (filters.start_date) params.start_date = filters.start_date
  if (filters.end_date) params.end_date = filters.end_date
  params.page = filters.page ?? 1
  params.limit = filters.limit ?? 25

  const { data } = await api.get('/audit-logs/', { params })
  return data
}

export async function getAuditLogDiff(id: number): Promise<AuditLogDiff> {
  const { data } = await api.get(`/audit-logs/${id}/diff`)
  return data
}
