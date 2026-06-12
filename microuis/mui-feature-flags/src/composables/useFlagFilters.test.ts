import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import {
  applyFlagFilters,
  useFlagFilters,
  EMPTY_FILTERS,
  type FlagFilterState,
} from './useFlagFilters'
import type { FeatureFlag } from '../services/flags'

// ---------------------------------------------------------------------------
// Test helper
// ---------------------------------------------------------------------------

function makeFlag(overrides: Partial<FeatureFlag> = {}): FeatureFlag {
  return {
    id: 1,
    name: 'test-flag',
    description: null,
    scope: 'global',
    tenant_id: null,
    product_id: null,
    company_id: null,
    enabled: true,
    default_val: false,
    complex: false,
    ttl: null,
    environment: 'production',
    rollout: 100,
    rules: [],
    tags: [],
    test_context: null,
    created_by: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// applyFlagFilters — pure predicate application (AND across dimensions)
// ---------------------------------------------------------------------------

describe('applyFlagFilters', () => {
  it('EMPTY_FILTERS returns all flags', () => {
    const flags = [makeFlag({ id: 1 }), makeFlag({ id: 2, enabled: false })]
    expect(applyFlagFilters(flags, EMPTY_FILTERS)).toEqual(flags)
  })

  it('status enabled keeps only enabled:true', () => {
    const flags = [
      makeFlag({ id: 1, enabled: true }),
      makeFlag({ id: 2, enabled: false }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, status: 'enabled' })
    expect(result.map((f) => f.id)).toEqual([1])
  })

  it('status disabled keeps only enabled:false', () => {
    const flags = [
      makeFlag({ id: 1, enabled: true }),
      makeFlag({ id: 2, enabled: false }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, status: 'disabled' })
    expect(result.map((f) => f.id)).toEqual([2])
  })

  it('tag filter keeps only flags whose tags include the selected tag, excluding flags with empty tags', () => {
    const flags = [
      makeFlag({ id: 1, tags: ['beta', 'alpha'] }),
      makeFlag({ id: 2, tags: ['alpha'] }),
      makeFlag({ id: 3, tags: [] }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, tag: 'beta' })
    expect(result.map((f) => f.id)).toEqual([1])
  })

  it('complexity complex keeps only flag.complex === true', () => {
    const flags = [
      makeFlag({ id: 1, complex: true }),
      makeFlag({ id: 2, complex: false }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, complexity: 'complex' })
    expect(result.map((f) => f.id)).toEqual([1])
  })

  it('complexity simple keeps only flag.complex === false', () => {
    const flags = [
      makeFlag({ id: 1, complex: true }),
      makeFlag({ id: 2, complex: false }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, complexity: 'simple' })
    expect(result.map((f) => f.id)).toEqual([2])
  })

  it('environment staging keeps only environment === staging', () => {
    const flags = [
      makeFlag({ id: 1, environment: 'production' }),
      makeFlag({ id: 2, environment: 'staging' }),
      makeFlag({ id: 3, environment: 'development' }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, environment: 'staging' })
    expect(result.map((f) => f.id)).toEqual([2])
  })

  it('scopeTarget global/tenant/product/company each keep only matching flag.scope (4 buckets)', () => {
    const flags = [
      makeFlag({ id: 1, scope: 'global' }),
      makeFlag({ id: 2, scope: 'tenant' }),
      makeFlag({ id: 3, scope: 'product' }),
      makeFlag({ id: 4, scope: 'company' }),
    ]

    expect(applyFlagFilters(flags, { ...EMPTY_FILTERS, scopeTarget: 'global' }).map((f) => f.id)).toEqual([1])
    expect(applyFlagFilters(flags, { ...EMPTY_FILTERS, scopeTarget: 'tenant' }).map((f) => f.id)).toEqual([2])
    expect(applyFlagFilters(flags, { ...EMPTY_FILTERS, scopeTarget: 'product' }).map((f) => f.id)).toEqual([3])
    expect(applyFlagFilters(flags, { ...EMPTY_FILTERS, scopeTarget: 'company' }).map((f) => f.id)).toEqual([4])
  })

  it('dimensions combine with AND: status enabled + environment production excludes an enabled staging flag', () => {
    const flags = [
      makeFlag({ id: 1, enabled: true, environment: 'production' }),
      makeFlag({ id: 2, enabled: true, environment: 'staging' }),
      makeFlag({ id: 3, enabled: false, environment: 'production' }),
    ]
    const result = applyFlagFilters(flags, { ...EMPTY_FILTERS, status: 'enabled', environment: 'production' })
    expect(result.map((f) => f.id)).toEqual([1])
  })
})

// ---------------------------------------------------------------------------
// useFlagFilters — composable wrapper
// ---------------------------------------------------------------------------

describe('useFlagFilters', () => {
  it('availableTags returns unique sorted tags across flags', () => {
    const flags = ref<FeatureFlag[]>([
      makeFlag({ id: 1, tags: ['beta', 'alpha'] }),
      makeFlag({ id: 2, tags: ['alpha', 'gamma'] }),
      makeFlag({ id: 3, tags: [] }),
    ])
    const { availableTags } = useFlagFilters(flags)
    expect(availableTags.value).toEqual(['alpha', 'beta', 'gamma'])
  })

  it('hasActiveFilters is false initially, true after setting filters.value.status', () => {
    const flags = ref<FeatureFlag[]>([makeFlag()])
    const { filters, hasActiveFilters } = useFlagFilters(flags)
    expect(hasActiveFilters.value).toBe(false)

    filters.value.status = 'enabled'
    expect(hasActiveFilters.value).toBe(true)
  })

  it('clearFilters restores EMPTY_FILTERS and filteredFlags returns all', () => {
    const flags = ref<FeatureFlag[]>([
      makeFlag({ id: 1, enabled: true }),
      makeFlag({ id: 2, enabled: false }),
    ])
    const { filters, filteredFlags, clearFilters, hasActiveFilters } = useFlagFilters(flags)

    filters.value.status = 'enabled'
    expect(filteredFlags.value.map((f) => f.id)).toEqual([1])

    clearFilters()
    expect(filters.value).toEqual(EMPTY_FILTERS)
    expect(hasActiveFilters.value).toBe(false)
    expect(filteredFlags.value.map((f) => f.id)).toEqual([1, 2])
  })

  it('clearFilters does not mutate EMPTY_FILTERS', () => {
    const flags = ref<FeatureFlag[]>([makeFlag()])
    const { filters, clearFilters } = useFlagFilters(flags)

    filters.value.status = 'enabled'
    clearFilters()

    const snapshot: FlagFilterState = { ...EMPTY_FILTERS }
    expect(EMPTY_FILTERS).toEqual(snapshot)
    expect(EMPTY_FILTERS.status).toBe('all')
  })

  it('filteredFlags recomputes when the source flags ref changes', () => {
    const flags = ref<FeatureFlag[]>([makeFlag({ id: 1, enabled: true })])
    const { filteredFlags } = useFlagFilters(flags)

    expect(filteredFlags.value.map((f) => f.id)).toEqual([1])

    flags.value = [makeFlag({ id: 1, enabled: true }), makeFlag({ id: 2, enabled: true })]
    expect(filteredFlags.value.map((f) => f.id)).toEqual([1, 2])
  })
})
