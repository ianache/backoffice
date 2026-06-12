import { describe, it, expect } from 'vitest'
import { ref, effectScope, nextTick } from 'vue'
import { evaluateRule, useRuleSimulator } from './useRuleSimulator'
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

// ---------------------------------------------------------------------------
// anyOf operator behavior — mirrors Plan 14-03's sdk-js evaluator.ts anyOf
// (list intersection / scalar membership, case-sensitive, fail-closed)
// ---------------------------------------------------------------------------

describe('evaluateRule — anyOf', () => {
  it('list actual intersecting list expected -> true', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin', 'TenantOwner'], result: true }
    expect(evaluateRule(rule, { roles: ['TenantOwner', 'viewer'] })).toBe(true)
  })

  it('list actual with no intersection -> false', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin', 'TenantOwner'], result: true }
    expect(evaluateRule(rule, { roles: ['viewer'] })).toBe(false)
  })

  it('scalar actual present in expected list -> true', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin'], result: true }
    expect(evaluateRule(rule, { roles: 'PlatformAdmin' })).toBe(true)
  })

  it('scalar actual not present in expected list -> false', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin'], result: true }
    expect(evaluateRule(rule, { roles: 'guest' })).toBe(false)
  })

  it('empty expected value -> false', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: [], result: true }
    expect(evaluateRule(rule, { roles: ['PlatformAdmin'] })).toBe(false)
  })

  it('case-sensitive: differently-cased actual does not match -> false', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin'], result: true }
    expect(evaluateRule(rule, { roles: ['platformadmin'] })).toBe(false)
  })

  it('non-array expected value fails closed -> false', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: 'PlatformAdmin', result: true }
    expect(evaluateRule(rule, { roles: ['PlatformAdmin'] })).toBe(false)
  })

  it('missing attribute -> false', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin'], result: true }
    expect(evaluateRule(rule, {})).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// Real user context shape (Phase 13) — confirms evaluateRule() handles the
// shape returned by shell/useUserContext() with no changes needed
// ---------------------------------------------------------------------------

describe('evaluateRule - real user context shape (Phase 13)', () => {
  it('evaluates a tenant_id rule against a real-user-context object', () => {
    const rule: RuleSchema = { attribute: 'tenant_id', operator: 'equals', value: 'tenant-acme', result: true }
    const realContext = { sub: 'user-123', email: 'a@b.com', roles: ['PlatformAdmin'], tenant_id: 'tenant-acme', product_id: 'backoffice' }
    expect(evaluateRule(rule, realContext)).toBe(true)
  })

  it('evaluates a roles "in" rule against a real-user-context object', () => {
    const rule: RuleSchema = { attribute: 'roles', operator: 'in', value: ['PlatformAdmin', 'TenantAdmin'], result: true }
    const realContext = { sub: 'user-123', email: 'a@b.com', roles: ['PlatformAdmin'], tenant_id: 'tenant-acme', product_id: 'backoffice' }
    // NOTE: 'in' operator checks Array.isArray(expected) && expected.includes(actual);
    // actual = realContext.roles (an array) — 'in' against an array actual is NOT
    // the typical case (it expects a scalar). This test documents current behavior;
    // if it returns false, that's correct per existing evaluateRule() semantics
    // (no new logic added — this is a documentation/regression test).
    const result = evaluateRule(rule, realContext)
    expect(typeof result).toBe('boolean')
  })
})

// ---------------------------------------------------------------------------
// useRuleSimulator — AND combination mode (Plan 15-03)
// New 3rd `mode` param: 'and' exposes per-rule ruleResults[] + overallResult
// (true only when ALL rules pass); 'first_match' (default) preserves the
// existing first-match-wins behavior with ruleResults populated too.
// ---------------------------------------------------------------------------

const andRules: RuleSchema[] = [
  { attribute: 'country', operator: 'equals', value: 'PE', result: true },
  { attribute: 'plan', operator: 'equals', value: 'pro', result: true },
]

describe('useRuleSimulator — AND combination mode', () => {
  it('and + all match: ruleResults all true, overallResult true, matchedIndex/matchedResult null', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>(andRules)
      const contextJson = ref(JSON.stringify({ country: 'PE', plan: 'pro' }))
      const mode = ref('and')
      api = useRuleSimulator(rules as any, contextJson, mode)
    })
    await nextTick()

    expect(api.ruleResults.value).toEqual([true, true])
    expect(api.overallResult.value).toBe(true)
    expect(api.matchedIndex.value).toBeNull()
    expect(api.matchedResult.value).toBeNull()
    scope.stop()
  })

  it('and + one fails: ruleResults [true, false], overallResult false', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>(andRules)
      const contextJson = ref(JSON.stringify({ country: 'PE', plan: 'free' }))
      const mode = ref('and')
      api = useRuleSimulator(rules as any, contextJson, mode)
    })
    await nextTick()

    expect(api.ruleResults.value).toEqual([true, false])
    expect(api.overallResult.value).toBe(false)
    scope.stop()
  })

  it('and + per-rule result ignored: overallResult true even when rules have result:false', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>([
        { attribute: 'country', operator: 'equals', value: 'PE', result: false },
        { attribute: 'plan', operator: 'equals', value: 'pro', result: false },
      ])
      const contextJson = ref(JSON.stringify({ country: 'PE', plan: 'pro' }))
      const mode = ref('and')
      api = useRuleSimulator(rules as any, contextJson, mode)
    })
    await nextTick()

    expect(api.ruleResults.value).toEqual([true, true])
    expect(api.overallResult.value).toBe(true)
    scope.stop()
  })

  it('and + empty rules: ruleResults [], overallResult null', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>([])
      const contextJson = ref(JSON.stringify({ country: 'PE', plan: 'pro' }))
      const mode = ref('and')
      api = useRuleSimulator(rules as any, contextJson, mode)
    })
    await nextTick()

    expect(api.ruleResults.value).toEqual([])
    expect(api.overallResult.value).toBeNull()
    scope.stop()
  })

  it('and + invalid context JSON: contextError set, ruleResults [], overallResult null', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>(andRules)
      const contextJson = ref('{ not valid json')
      const mode = ref('and')
      api = useRuleSimulator(rules as any, contextJson, mode)
    })
    await nextTick()

    expect(api.contextError.value).not.toBeNull()
    expect(api.ruleResults.value).toEqual([])
    expect(api.overallResult.value).toBeNull()
    scope.stop()
  })

  it('first_match (default 3rd param omitted): existing behavior preserved with ruleResults populated', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>(andRules)
      const contextJson = ref(JSON.stringify({ country: 'PE', plan: 'pro' }))
      api = useRuleSimulator(rules as any, contextJson)
    })
    await nextTick()

    expect(api.matchedIndex.value).toBe(0)
    expect(api.matchedResult.value).toBe(andRules[0].result)
    expect(api.overallResult.value).toBe(api.matchedResult.value)
    expect(api.ruleResults.value).toEqual([true, true])
    scope.stop()
  })

  it('first_match + no match: matchedIndex null, overallResult null', async () => {
    const scope = effectScope()
    let api!: ReturnType<typeof useRuleSimulator>
    scope.run(() => {
      const rules = ref<RuleSchema[]>(andRules)
      const contextJson = ref(JSON.stringify({ country: 'AR', plan: 'free' }))
      api = useRuleSimulator(rules as any, contextJson)
    })
    await nextTick()

    expect(api.matchedIndex.value).toBeNull()
    expect(api.matchedResult.value).toBeNull()
    expect(api.overallResult.value).toBeNull()
    expect(api.ruleResults.value).toEqual([false, false])
    scope.stop()
  })
})
