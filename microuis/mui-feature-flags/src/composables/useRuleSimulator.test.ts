import { describe, it, expect } from 'vitest'
import { evaluateRule } from './useRuleSimulator'
import type { RuleSchema } from '../services/flags'

// ---------------------------------------------------------------------------
// greaterThan / lessThan operator behavior — mirrors Plan 01's backend
// OPERATORS table (backend/app/domains/feature_flags/service.py) test fixtures
// ---------------------------------------------------------------------------

describe('evaluateRule - greaterThan / lessThan', () => {
  it('greaterThan: numeric actual > numeric expected -> true', () => {
    const rule: RuleSchema = { attribute: 'ltv', operator: 'greaterThan', value: 500, result: true }
    expect(evaluateRule(rule, { ltv: 600 })).toBe(true)
  })

  it('greaterThan: numeric actual <= numeric expected -> false', () => {
    const rule: RuleSchema = { attribute: 'ltv', operator: 'greaterThan', value: 500, result: true }
    expect(evaluateRule(rule, { ltv: 400 })).toBe(false)
  })

  it('greaterThan: numeric strings coerced via Number() -> true', () => {
    const rule: RuleSchema = { attribute: 'ltv', operator: 'greaterThan', value: '500', result: true }
    expect(evaluateRule(rule, { ltv: '600' })).toBe(true)
  })

  it('greaterThan: non-numeric actual fails closed (NaN > NaN -> false)', () => {
    const rule: RuleSchema = { attribute: 'plan', operator: 'greaterThan', value: 500, result: true }
    expect(evaluateRule(rule, { plan: 'enterprise' })).toBe(false)
  })

  it('lessThan: numeric actual < numeric expected -> true', () => {
    const rule: RuleSchema = { attribute: 'ltv', operator: 'lessThan', value: 500, result: true }
    expect(evaluateRule(rule, { ltv: 100 })).toBe(true)
  })

  it('lessThan: missing attribute -> false', () => {
    const rule: RuleSchema = { attribute: 'ltv', operator: 'lessThan', value: 500, result: true }
    expect(evaluateRule(rule, {})).toBe(false)
  })
})
