<template>
  <div
    class="rule-simulator flex flex-col h-full bg-white rounded-xl border border-outline-variant shadow-sm overflow-hidden"
  >
    <!-- Header -->
    <div class="px-4 py-3 border-b border-outline-variant flex items-center gap-2">
      <span class="material-symbols-outlined text-primary text-lg">play_circle</span>
      <span class="text-sm font-semibold text-on-surface">Live Simulator</span>

      <!-- Result badge: shown only when no contextError -->
      <div
        v-if="!contextError && overallResult !== null"
        :class="[
          'ml-auto px-2 py-0.5 rounded font-label-md text-label-md uppercase',
          overallResult
            ? 'bg-green-100 text-green-700'
            : 'bg-error-container text-on-error-container',
        ]"
      >
        {{ overallResult ? 'Passing' : 'Failing' }}
      </div>
      <div
        v-else-if="!contextError && overallResult === null && rules.length > 0"
        class="ml-auto px-2 py-0.5 rounded font-label-md text-label-md uppercase bg-surface-container text-on-surface-variant"
      >
        No match
      </div>
    </div>

    <!-- Context JSON textarea -->
    <div class="p-4 flex-shrink-0">
      <div class="flex items-center justify-between mb-1">
        <label class="text-xs font-medium text-on-surface-variant">Test Context</label>
        <label
          class="flex items-center gap-1.5 text-xs text-on-surface-variant cursor-pointer select-none"
        >
          <input
            type="checkbox"
            :checked="useRealContext"
            @change="toggleRealContext"
            class="accent-primary"
          />
          Use my real context
        </label>
      </div>
      <textarea
        v-model="contextJson"
        rows="6"
        :readonly="useRealContext"
        class="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface-container text-sm font-mono text-on-surface outline-none focus:border-primary resize-none transition-colors"
        :class="{ 'border-error': contextError, 'bg-surface-container-high': useRealContext }"
        placeholder='{"country": "PE"}'
        spellcheck="false"
      />
      <p v-if="contextError" class="mt-1 text-xs text-[color:var(--error)]">{{ contextError }}</p>
      <button
        type="button"
        :disabled="!!contextError"
        @click="emit('save-test-context', contextJson)"
        class="mt-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary text-on-primary hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Save Test Context
      </button>
    </div>

    <!-- First-match mode: Matched rule highlight -->
    <div v-if="effectiveMode !== 'and'" class="px-4 pb-4 flex-1 overflow-auto">
      <label class="text-xs font-medium text-on-surface-variant mb-2 block">Matched Rule</label>
      <div
        v-if="matchedIndex !== null"
        class="p-3 rounded-lg bg-primary-container border border-primary"
      >
        <p class="text-sm font-semibold text-on-primary-container">Rule {{ matchedIndex + 1 }}</p>
        <p class="text-xs text-on-primary-container opacity-80 mt-1">
          Result: <strong>{{ String(matchedResult) }}</strong>
        </p>
        <div
          v-if="matchedRule?.operator === 'anyOf' && Array.isArray(matchedRule.value)"
          class="flex flex-wrap gap-1 mt-2"
        >
          <span
            v-for="(v, i) in matchedRule.value"
            :key="i"
            class="bg-primary-container text-on-primary-container text-[11px] font-medium px-2 py-0.5 rounded-full"
            >{{ v }}</span
          >
        </div>
      </div>
      <div v-else-if="rules.length === 0" class="text-xs text-on-surface-variant italic">
        Add rules to start simulation
      </div>
      <div v-else-if="!contextError" class="text-xs text-on-surface-variant italic">
        No rule matched — flag returns default value
      </div>
    </div>

    <!-- AND mode: per-rule pass/fail list -->
    <div v-else class="px-4 pb-4 flex-1 overflow-auto">
      <label class="text-xs font-medium text-on-surface-variant mb-2 block">Rules (ALL must match)</label>
      <div v-if="rules.length === 0" class="text-xs text-on-surface-variant italic">
        Add rules to start simulation
      </div>
      <div v-else class="space-y-2">
        <div
          v-for="(rule, i) in rules"
          :key="rule._id"
          class="flex items-center gap-2 p-2 rounded-lg bg-surface-container"
        >
          <span
            :class="[
              'material-symbols-outlined text-base',
              ruleResults[i] ? 'text-green-700' : 'text-error',
            ]"
          >
            {{ ruleResults[i] ? 'check_circle' : 'cancel' }}
          </span>
          <span class="text-sm text-on-surface">Rule {{ i + 1 }}</span>
        </div>
        <p v-if="overallResult === false" class="text-xs text-on-surface-variant italic mt-2">
          Not all rules match — flag evaluates false
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { useRuleSimulator } from '../../composables/useRuleSimulator'
import type { RuleSchema } from '../../services/flags'
import { useUserContext } from 'shell/useUserContext'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

const props = defineProps<{
  rules: (RuleSchema & { _id: string })[]
  mode?: 'flag' | 'segment'
  testContext?: string | null
  combinationMode?: string
}>()

// ---------------------------------------------------------------------------
// Emits
// ---------------------------------------------------------------------------

const emit = defineEmits<{
  'save-test-context': [json: string]
}>()

// ---------------------------------------------------------------------------
// Internal state
// ---------------------------------------------------------------------------

const PLACEHOLDER_CONTEXT = '{\n  "country": "PE",\n  "plan": "pro"\n}'

const contextJson = ref(props.testContext || PLACEHOLDER_CONTEXT)

// ---------------------------------------------------------------------------
// Real-context toggle (SIM-03) — defaults OFF on every mount, never persisted
// ---------------------------------------------------------------------------

const useRealContext = ref(false)
let previousContextJson = ''

const realContextJson = computed(() => {
  const ctx = useUserContext()
  return JSON.stringify(
    {
      sub: ctx.sub,
      email: ctx.email,
      roles: ctx.roles,
      tenant_id: ctx.tenant_id,
      product_id: ctx.product_id,
    },
    null,
    2,
  )
})

function toggleRealContext(): void {
  if (!useRealContext.value) {
    // Turning ON — save current value, switch to real context
    previousContextJson = contextJson.value
    contextJson.value = realContextJson.value
    useRealContext.value = true
  } else {
    // Turning OFF — restore previous value
    contextJson.value = previousContextJson
    useRealContext.value = false
  }
}

// Compute rules without _id for simulator (strip local _id field)
const strippedRules = computed<RuleSchema[]>(() =>
  props.rules.map(({ _id: _ignored, ...r }) => r as RuleSchema),
)

// Effective combination mode — defaults to 'first_match' when unset (legacy flags)
const effectiveMode = computed(() => props.combinationMode ?? 'first_match')

// Cast as Readonly<Ref> to satisfy composable signature while avoiding
// deep-readonly mismatch from Vue's readonly() wrapper
const { matchedIndex, matchedResult, ruleResults, overallResult, contextError } = useRuleSimulator(
  strippedRules as unknown as Readonly<Ref<RuleSchema[]>>,
  contextJson,
  effectiveMode,
)

// Matched rule object (with original _id) for Matched Rule panel display
const matchedRule = computed(() =>
  matchedIndex.value !== null ? props.rules[matchedIndex.value] : null,
)
</script>
