import { ref, watchEffect } from 'vue'
import type { Ref } from 'vue'
import type { RuleSchema } from '../services/flags'

// ---------------------------------------------------------------------------
// Operator dispatch — direct TypeScript port of OPERATORS dict in service.py
// ---------------------------------------------------------------------------

type OperatorFn = (actual: unknown, expected: unknown) => boolean

export const OPERATORS: Record<string, OperatorFn> = {
  equals:   (actual, expected) => actual === expected,
  in:       (actual, expected) => Array.isArray(expected) && expected.includes(actual),
  notIn:    (actual, expected) => Array.isArray(expected) && !expected.includes(actual),
  contains: (actual, expected) => String(actual).includes(String(expected)),
  regex:    (actual, expected) => {
    try {
      return new RegExp(String(expected)).test(String(actual))
    } catch {
      return false
    }
  },
  greaterThan: (actual, expected) => Number(actual) > Number(expected),
  lessThan:    (actual, expected) => Number(actual) < Number(expected),
}

// ---------------------------------------------------------------------------
// evaluateRule — port of _evaluate_rule() from service.py
// ---------------------------------------------------------------------------

export function evaluateRule(rule: RuleSchema, user: Record<string, unknown>): boolean {
  const actual = user[rule.attribute]
  if (actual === undefined || actual === null) return false
  const fn = OPERATORS[rule.operator]
  if (!fn) return false
  try {
    return fn(actual, rule.value)
  } catch {
    return false
  }
}

// ---------------------------------------------------------------------------
// useRuleSimulator composable
// ---------------------------------------------------------------------------

export function useRuleSimulator(
  rules: Readonly<Ref<RuleSchema[]>>,
  contextJson: Ref<string>,
) {
  const matchedIndex  = ref<number | null>(null)
  const matchedResult = ref<boolean | null>(null)
  const contextError  = ref<string | null>(null)

  watchEffect(() => {
    // Reset state on every evaluation run
    matchedIndex.value  = null
    matchedResult.value = null
    contextError.value  = null

    // Parse context JSON
    let user: Record<string, unknown> = {}
    try {
      const parsed = JSON.parse(contextJson.value || '{}')
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        contextError.value = 'Context must be a JSON object'
        return
      }
      user = parsed
    } catch (err) {
      contextError.value = err instanceof Error ? err.message : 'Invalid JSON'
      return
    }

    // First-match-wins loop
    const ruleList = rules.value
    for (let i = 0; i < ruleList.length; i++) {
      if (evaluateRule(ruleList[i], user)) {
        matchedIndex.value  = i
        matchedResult.value = ruleList[i].result
        return
      }
    }
    // No rule matched
  })

  return { matchedIndex, matchedResult, contextError }
}
