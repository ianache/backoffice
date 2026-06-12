/**
 * Shared TypeScript contracts for @backoffice/sdk-js.
 *
 * These types mirror the backend SDK bootstrap response
 * (backend/app/domains/sdk/service.py bootstrap_flags(), Plan 11-06)
 * and are consumed directly by Plans 07/08 (sdk-js client/WS/telemetry).
 */

export interface RuleSchema {
  attribute: string
  operator: string
  value: unknown
  result?: boolean
}

export interface BootstrapSegment {
  id: number
  type: string
  conditions: RuleSchema[]
  members: string[]
}

export interface FlagEntry {
  enabled: boolean
  rules: RuleSchema[]
  segments: BootstrapSegment[]
  default_val: boolean
  scope: string
  tenant_id?: string | null
  product_id?: string | null
  company_id?: string | null
}

export type BootstrapResponse = Record<string, FlagEntry>

export interface UserContext {
  id?: string
  sub?: string
  user_id?: string
  [key: string]: unknown
}

export interface EvalEventItem {
  flag_key: string
  result: boolean
  evaluated_at: string
  user_id: string
}
