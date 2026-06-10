<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Segment, SegmentPayload, RuleSchema } from '../../services/flags'
import RuleCard from './RuleCard.vue'

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  segment?: Segment
}>()

const emit = defineEmits<{
  save: [payload: SegmentPayload]
  cancel: []
}>()

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

type RuleWithId = RuleSchema & { _id: string }

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------

const form = ref<{
  name: string
  description: string
  type: 'manual' | 'rule_based'
  membersText: string
  conditions: RuleWithId[]
}>({
  name: '',
  description: '',
  type: 'manual',
  membersText: '',
  conditions: [],
})

// Populate form when segment prop changes (edit mode)
watch(
  () => props.segment,
  (seg) => {
    if (seg) {
      form.value = {
        name: seg.name,
        description: seg.description ?? '',
        type: seg.type ?? 'manual',
        membersText: (seg.members ?? []).join('\n'),
        conditions: (seg.conditions ?? []).map((c) => ({ ...c, _id: crypto.randomUUID() })),
      }
    } else {
      reset()
    }
  },
  { immediate: true }
)

// ---------------------------------------------------------------------------
// Condition helpers (rule_based)
// ---------------------------------------------------------------------------

function addCondition(): void {
  form.value.conditions.push({
    _id: crypto.randomUUID(),
    attribute: '',
    operator: 'equals',
    value: '',
    // result is unused by resolve_segment_members() — defaulted to true
    result: true,
  })
}

function updateCondition(index: number, rule: RuleWithId): void {
  form.value.conditions[index] = rule
}

function removeCondition(index: number): void {
  form.value.conditions.splice(index, 1)
}

// ---------------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------------

function handleSubmit(): void {
  const payload: SegmentPayload = {
    name: form.value.name.trim(),
    description: form.value.description.trim() || undefined,
    type: form.value.type,
    members: [],
    conditions: [],
  }

  if (form.value.type === 'manual') {
    // Parse newline or comma-separated UUIDs
    payload.members = form.value.membersText
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter(Boolean)
    payload.conditions = []
  } else {
    // rule_based — strip internal _id before sending; result defaults to true
    // (unused by resolve_segment_members(), only the boolean evaluation of
    // _evaluate_rule(c, user) is checked)
    payload.conditions = form.value.conditions.map(({ _id, ...rest }) => ({ ...rest, result: rest.result ?? true }))
    payload.members = []
  }

  emit('save', payload)
}

// ---------------------------------------------------------------------------
// Expose reset for parent to call after save
// ---------------------------------------------------------------------------

function reset(): void {
  form.value = {
    name: '',
    description: '',
    type: 'manual',
    membersText: '',
    conditions: [],
  }
}

defineExpose({ reset })
</script>

<template>
  <form
    @submit.prevent="handleSubmit"
    class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 flex flex-col gap-4"
  >
    <h3 class="text-base font-semibold text-on-surface">
      {{ segment ? 'Edit Segment' : 'Create Segment' }}
    </h3>

    <!-- Name -->
    <div>
      <label class="form-label">Name <span class="text-error">*</span></label>
      <input
        v-model="form.name"
        type="text"
        required
        placeholder="e.g. beta-users"
        class="form-input"
      />
    </div>

    <!-- Description -->
    <div>
      <label class="form-label">Description</label>
      <input
        v-model="form.description"
        type="text"
        placeholder="Optional description"
        class="form-input"
      />
    </div>

    <!-- Type select -->
    <div>
      <label class="form-label">Type</label>
      <select v-model="form.type" class="form-input">
        <option value="manual">Manual (member UUIDs)</option>
        <option value="rule_based">Rule-based (conditions)</option>
      </select>
    </div>

    <!-- Manual: member UUIDs textarea -->
    <div v-if="form.type === 'manual'">
      <label class="form-label">Member UUIDs</label>
      <textarea
        v-model="form.membersText"
        rows="4"
        placeholder="One UUID per line, or comma-separated"
        class="form-input font-mono text-xs"
      />
      <p class="mt-1 text-xs text-on-surface-variant">
        Enter user UUIDs separated by newlines or commas.
      </p>
    </div>

    <!-- Rule-based: RuleCard list (mode="segment" hides Result column) -->
    <template v-if="form.type === 'rule_based'">
      <div class="flex flex-col gap-3">
        <label class="form-label">Conditions</label>

        <div
          v-for="(rule, index) in form.conditions"
          :key="rule._id"
        >
          <RuleCard
            :rule="rule"
            :index="index"
            mode="segment"
            @update="updateCondition(index, $event)"
            @delete="removeCondition(index)"
          />
        </div>

        <button
          type="button"
          @click="addCondition"
          class="flex items-center gap-2 self-start px-3 py-2 rounded-lg border border-dashed border-outline text-on-surface-variant hover:border-primary hover:text-primary transition-colors text-sm"
        >
          <span class="material-symbols-outlined text-[18px]">add</span>
          Add Condition
        </button>

        <p v-if="form.conditions.length === 0" class="text-xs text-on-surface-variant">
          No conditions added. Add at least one condition for a rule-based segment.
        </p>
      </div>
    </template>

    <!-- Actions -->
    <div class="flex items-center justify-end gap-3 pt-2 border-t border-outline-variant">
      <button
        type="button"
        @click="emit('cancel')"
        class="px-4 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-high transition-colors"
      >
        Cancel
      </button>
      <button
        type="submit"
        class="px-4 py-2 rounded-lg text-sm font-medium bg-primary text-on-primary hover:opacity-90 transition-opacity"
      >
        {{ segment ? 'Save Changes' : 'Create Segment' }}
      </button>
    </div>
  </form>
</template>

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

textarea.form-input {
  resize: vertical;
}
</style>
