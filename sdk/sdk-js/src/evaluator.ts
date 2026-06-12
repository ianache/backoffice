/**
 * Local (DB-free) flag evaluation engine for @backoffice/sdk-js.
 *
 * Mirrors the canonical backend OPERATORS table and _evaluate_rule()/evaluate_flag()
 * logic in backend/app/domains/feature_flags/service.py (Plan 01), and the
 * useRuleSimulator.ts operator semantics (Plan 04), including greaterThan/lessThan
 * Number() coercion and fail-closed behavior on exceptions.
 */
import type { FlagEntry, RuleSchema, UserContext } from './types'

export const OPERATORS: Record<string, (actual: unknown, expected: unknown) => boolean> = {
  equals: (actual, expected) => actual === expected,
  in: (actual, expected) => Array.isArray(expected) && expected.includes(actual),
  notIn: (actual, expected) => Array.isArray(expected) && !expected.includes(actual),
  contains: (actual, expected) => String(actual).includes(String(expected)),
  regex: (actual, expected) => new RegExp(String(expected)).test(String(actual)),
  greaterThan: (actual, expected) => Number(actual) > Number(expected),
  lessThan: (actual, expected) => Number(actual) < Number(expected),
  anyOf: (actual, expected) => {
    if (Array.isArray(actual)) {
      const expectedArr = Array.isArray(expected) ? expected : []
      return actual.some((v) => expectedArr.includes(v))
    }
    return Array.isArray(expected) && expected.includes(actual)
  },
}

/**
 * Port of backend `_evaluate_rule()`.
 * - Missing/null attribute → false
 * - Unknown operator → false
 * - Any exception during operator evaluation → false (fail-closed)
 * - greaterThan/lessThan use Number() coercion; NaN comparisons are always false
 */
export function evaluateRule(rule: RuleSchema, user: UserContext): boolean {
  const actual = user[rule.attribute]
  if (actual === undefined || actual === null) return false

  const fn = OPERATORS[rule.operator]
  if (!fn) return false

  try {
    return Boolean(fn(actual, rule.value))
  } catch {
    return false
  }
}

/**
 * Port of backend `evaluate_flag()` for a single bootstrap-inlined flag entry.
 * - `enabled: false` → always false
 * - Company-scope target guard (TGT-03): when `scope === 'company'` and
 *   `entry.company_id` is non-null, the entry only applies if
 *   `user.company_id === entry.company_id` — otherwise false (fail-closed).
 *   Legacy entries with `company_id` null/undefined skip this check.
 *   Tenant/product targeting is enforced upstream by bootstrap filtering
 *   (by SDK client identity), not here.
 * - First matching rule wins → returns `rule.result ?? entry.default_val`
 * - rule_based segments: any matching condition → true
 * - manual segments: user id (id/sub/user_id) present in `members[]` → true
 * - No match → `entry.default_val`
 */
export function evaluateFlag(entry: FlagEntry, user: UserContext): boolean {
  if (!entry.enabled) return false

  if (entry.scope === 'company' && entry.company_id != null) {
    if (user.company_id !== entry.company_id) return false
  }

  for (const rule of entry.rules) {
    if (evaluateRule(rule, user)) return Boolean(rule.result ?? entry.default_val)
  }

  const userId = user.id ?? user.sub ?? user.user_id
  for (const seg of entry.segments) {
    if (seg.type === 'rule_based' && seg.conditions.some((c) => evaluateRule(c, user))) return true
    if (seg.type === 'manual' && userId && seg.members.includes(String(userId))) return true
  }

  return entry.default_val
}
