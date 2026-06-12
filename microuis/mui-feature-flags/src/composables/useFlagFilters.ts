// Client-side filter logic for the /flags table (FLT-01..FLT-05).
// applyFlagFilters is pure and dependency-free for direct vitest unit testing
// (flagFormModel.ts precedent); useFlagFilters wraps it in reactive refs.

import { ref, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import type { FeatureFlag } from '../services/flags'

export interface FlagFilterState {
  status: 'all' | 'enabled' | 'disabled'
  tag: string // '' = any tag
  complexity: 'all' | 'complex' | 'simple'
  environment: string // '' = all; else exact match on flag.environment
  scopeTarget: '' | 'global' | 'tenant' | 'product' | 'company' // '' = all
}

export const EMPTY_FILTERS: FlagFilterState = {
  status: 'all',
  tag: '',
  complexity: 'all',
  environment: '',
  scopeTarget: '',
}

/**
 * Pure, dependency-free predicate application (AND across dimensions).
 */
export function applyFlagFilters(flags: FeatureFlag[], f: FlagFilterState): FeatureFlag[] {
  return flags.filter((flag) => {
    if (f.status === 'enabled' && flag.enabled !== true) return false
    if (f.status === 'disabled' && flag.enabled !== false) return false

    if (f.tag && !flag.tags.includes(f.tag)) return false

    if (f.complexity === 'complex' && flag.complex !== true) return false
    if (f.complexity === 'simple' && flag.complex !== false) return false

    if (f.environment && flag.environment !== f.environment) return false

    if (f.scopeTarget && flag.scope !== f.scopeTarget) return false

    return true
  })
}

export function useFlagFilters(flags: Readonly<Ref<FeatureFlag[]>>): {
  filters: Ref<FlagFilterState>
  filteredFlags: ComputedRef<FeatureFlag[]>
  availableTags: ComputedRef<string[]>
  hasActiveFilters: ComputedRef<boolean>
  clearFilters: () => void
} {
  const filters = ref<FlagFilterState>({ ...EMPTY_FILTERS })

  const filteredFlags = computed(() => applyFlagFilters(flags.value, filters.value))

  const availableTags = computed(() => {
    const tagSet = new Set<string>()
    for (const flag of flags.value) {
      for (const tag of flag.tags) {
        tagSet.add(tag)
      }
    }
    return Array.from(tagSet).sort()
  })

  const hasActiveFilters = computed(() => {
    const f = filters.value
    return (
      f.status !== EMPTY_FILTERS.status ||
      f.tag !== EMPTY_FILTERS.tag ||
      f.complexity !== EMPTY_FILTERS.complexity ||
      f.environment !== EMPTY_FILTERS.environment ||
      f.scopeTarget !== EMPTY_FILTERS.scopeTarget
    )
  })

  const clearFilters = () => {
    filters.value = { ...EMPTY_FILTERS }
  }

  return {
    filters,
    filteredFlags,
    availableTags,
    hasActiveFilters,
    clearFilters,
  }
}
