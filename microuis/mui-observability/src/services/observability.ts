import api from 'shell/api'

export interface ServiceHealthSample {
  id: number
  checked_at: string
  service_name: string
  status: 'UP' | 'DEGRADED' | 'DOWN'
  latency_ms: number | null
  details: string | null
}

export interface ServiceHealthListResponse {
  items: ServiceHealthSample[]
}

export interface LatencyTrendHistoryPoint {
  ts: string
  avg_latency_ms: number | null
}

export interface ServiceMetrics {
  service_name: string
  uptime_pct: number
  error_rate_pct: number
  p95_latency_ms: number | null
  p99_latency_ms: number | null
  sample_count: number
  history: LatencyTrendHistoryPoint[]
}

export interface MetricsResponse {
  items: ServiceMetrics[]
  range: '24h' | '7d' | '30d'
}

export async function fetchServices(): Promise<ServiceHealthListResponse> {
  const { data } = await api.get<ServiceHealthListResponse>('/observability/health/services')
  return data
}

export async function fetchMetrics(range: '24h' | '7d' | '30d'): Promise<MetricsResponse> {
  const { data } = await api.get<MetricsResponse>('/observability/metrics', {
    params: { range }
  })
  return data
}
