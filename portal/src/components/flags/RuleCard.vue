<template>
  <div class="group">
    <div
      class="rule-card relative flex rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm overflow-hidden"
    >
      <!-- Drag handle: left edge, visible on hover, only this triggers drag -->
      <div
        class="drag-handle flex items-center justify-center w-8 bg-primary-container cursor-grab active:cursor-grabbing flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <span class="material-symbols-outlined text-on-primary-container text-sm">drag_indicator</span>
      </div>

      <!-- Card body -->
      <div class="flex-1 p-4">
        <!-- Header row: "Rule N" title + delete button -->
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-semibold text-on-surface">Rule {{ index + 1 }}</span>
          <button
            type="button"
            @click="emit('delete')"
            class="flex items-center justify-center w-7 h-7 rounded-lg text-on-surface-variant hover:bg-error-container hover:text-on-error-container transition-colors"
          >
            <span class="material-symbols-outlined text-sm">delete</span>
          </button>
        </div>

        <!-- Fields row: attribute | operator | value | result -->
        <div class="grid grid-cols-4 gap-3 items-start">
          <!-- Attribute: free-text input -->
          <div>
            <label class="form-label">Attribute</label>
            <input
              type="text"
              :value="rule.attribute"
              @input="emit('update', { ...rule, attribute: ($event.target as HTMLInputElement).value })"
              placeholder="e.g. country"
              class="form-input"
            />
          </div>

          <!-- Operator: select with 5 options -->
          <div>
            <label class="form-label">Operator</label>
            <select
              :value="rule.operator"
              @change="onOperatorChange(($event.target as HTMLSelectElement).value)"
              class="form-input"
            >
              <option v-for="op in OPERATORS" :key="op" :value="op">{{ op }}</option>
            </select>
          </div>

          <!-- Value: ChipTagInput for in/notIn, plain text for others -->
          <div>
            <label class="form-label">Value</label>
            <ChipTagInput
              v-if="isArrayOperator(rule.operator)"
              :modelValue="Array.isArray(rule.value) ? rule.value : []"
              @update:modelValue="emit('update', { ...rule, value: $event })"
            />
            <input
              v-else
              type="text"
              :value="Array.isArray(rule.value) ? rule.value.join(', ') : (rule.value ?? '')"
              @input="emit('update', { ...rule, value: ($event.target as HTMLInputElement).value })"
              placeholder="value"
              class="form-input"
            />
          </div>

          <!-- Result: boolean toggle true/false -->
          <div>
            <label class="form-label">Result</label>
            <div class="flex items-center gap-2 mt-1">
              <button
                type="button"
                @click="emit('update', { ...rule, result: !rule.result })"
                :class="[
                  'px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors',
                  rule.result
                    ? 'bg-primary text-on-primary border-primary'
                    : 'bg-surface-container border-outline-variant text-on-surface-variant',
                ]"
              >
                {{ rule.result ? 'true' : 'false' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RuleSchema } from '../../services/flags'
import ChipTagInput from './ChipTagInput.vue'

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  rule: RuleSchema & { _id: string }
  index: number
}>()

const emit = defineEmits<{
  update: [rule: RuleSchema & { _id: string }]
  delete: []
}>()

// ---------------------------------------------------------------------------
// Operator constants
// ---------------------------------------------------------------------------

const OPERATORS = ['equals', 'in', 'notIn', 'contains', 'regex'] as const

const isArrayOperator = (op: string): boolean => op === 'in' || op === 'notIn'

// ---------------------------------------------------------------------------
// Operator change handler — coerces value type when switching operator family
// ---------------------------------------------------------------------------

function onOperatorChange(newOp: string): void {
  let newValue: unknown = props.rule.value

  if (isArrayOperator(newOp) && !Array.isArray(props.rule.value)) {
    // Switching TO array operator: wrap scalar into array (or empty array)
    newValue = props.rule.value ? [String(props.rule.value)] : []
  } else if (!isArrayOperator(newOp) && Array.isArray(props.rule.value)) {
    // Switching AWAY from array operator: join array into comma-separated string
    newValue = (props.rule.value as string[]).join(', ')
  }

  emit('update', { ...props.rule, operator: newOp, value: newValue })
}
</script>

<style scoped>
.form-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border-radius: var(--rounded-lg);
  border: 1px solid var(--outline-variant);
  background: var(--surface-container-lowest);
  color: var(--on-surface);
  font-size: 0.875rem;
  font-family: var(--font-family-sans);
  outline: none;
  transition: border-color 0.15s;
}

.form-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 15%, transparent);
}
</style>
