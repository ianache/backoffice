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
        v-if="!contextError && matchedResult !== null"
        :class="[
          'ml-auto px-2 py-0.5 rounded font-label-md text-label-md uppercase',
          matchedResult
            ? 'bg-green-100 text-green-700'
            : 'bg-error-container text-on-error-container',
        ]"
      >
        {{ matchedResult ? 'Passing' : 'Failing' }}
      </div>
      <div
        v-else-if="!contextError && matchedResult === null && rules.length > 0"
        class="ml-auto px-2 py-0.5 rounded font-label-md text-label-md uppercase bg-surface-container text-on-surface-variant"
      >
        No match
      </div>
    </div>

    <!-- Context JSON textarea -->
    <div class="p-4 flex-shrink-0">
      <label class="text-xs font-medium text-on-surface-variant mb-1 block">Test Context</label>
      <textarea
        v-model="contextJson"
        rows="6"
        class="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface-container text-sm font-mono text-on-surface outline-none focus:border-primary resize-none transition-colors"
        :class="{ 'border-error': contextError }"
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

    <!-- Matched rule highlight -->
    <div class="px-4 pb-4 flex-1 overflow-auto">
      <label class="text-xs font-medium text-on-surface-variant mb-2 block">Matched Rule</label>
      <div
        v-if="matchedIndex !== null"
        class="p-3 rounded-lg bg-primary-container border border-primary"
      >
        <p class="text-sm font-semibold text-on-primary-container">Rule {{ matchedIndex + 1 }}</p>
        <p class="text-xs text-on-primary-container opacity-80 mt-1">
          Result: <strong>{{ String(matchedResult) }}</strong>
        </p>
      </div>
      <div v-else-if="rules.length === 0" class="text-xs text-on-surface-variant italic">
        Add rules to start simulation
      </div>
      <div v-else-if="!contextError" class="text-xs text-on-surface-variant italic">
        No rule matched — flag returns default value
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { useRuleSimulator } from '../../composables/useRuleSimulator'
import type { RuleSchema } from '../../services/flags'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

const props = defineProps<{
  rules: (RuleSchema & { _id: string })[]
  mode?: 'flag' | 'segment'
  testContext?: string | null
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

// Compute rules without _id for simulator (strip local _id field)
const strippedRules = computed<RuleSchema[]>(() =>
  props.rules.map(({ _id: _ignored, ...r }) => r as RuleSchema),
)

// Cast as Readonly<Ref> to satisfy composable signature while avoiding
// deep-readonly mismatch from Vue's readonly() wrapper
const { matchedIndex, matchedResult, contextError } = useRuleSimulator(
  strippedRules as unknown as Readonly<Ref<RuleSchema[]>>,
  contextJson,
)
</script>
