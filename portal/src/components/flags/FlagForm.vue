<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FeatureFlag, FlagPayload, Segment } from '../../services/flags'
import SegmentPicker from './SegmentPicker.vue'

const props = defineProps<{
  flag?: FeatureFlag | null
  segments?: Segment[]
  linkedSegmentIds?: number[]
}>()

const emit = defineEmits<{
  save: [payload: FlagPayload]
  cancel: []
}>()

// Form state
const name = ref('')
const scope = ref('')
const description = ref('')
const environment = ref('production')
const complex = ref(false)
const ttlDays = ref<number | null>(null)
const tagsRaw = ref('')
const rulesRaw = ref('')
const selectedSegmentIds = ref<number[]>([])

const errors = ref<{ name?: string; scope?: string; rules?: string }>({})

// Reset form when flag changes
watch(
  () => props.flag,
  (flag) => {
    if (flag) {
      name.value = flag.name
      scope.value = flag.scope
      description.value = flag.description ?? ''
      environment.value = flag.environment
      complex.value = flag.complex
      ttlDays.value = flag.ttl
      tagsRaw.value = flag.tags.join(', ')
      rulesRaw.value = flag.rules.length ? JSON.stringify(flag.rules, null, 2) : ''
      selectedSegmentIds.value = props.linkedSegmentIds ?? []
    } else {
      name.value = ''
      scope.value = ''
      description.value = ''
      environment.value = 'production'
      complex.value = false
      ttlDays.value = null
      tagsRaw.value = ''
      rulesRaw.value = ''
      selectedSegmentIds.value = []
    }
    errors.value = {}
  },
  { immediate: true }
)

// Sync pre-selected segments when they arrive asynchronously from the parent
watch(
  () => props.linkedSegmentIds,
  (linkedIds) => { selectedSegmentIds.value = linkedIds ?? [] }
)

function validate(): boolean {
  errors.value = {}
  if (!name.value.trim()) {
    errors.value.name = 'Flag name is required'
  }
  if (!scope.value) {
    errors.value.scope = 'Scope is required'
  }
  if (rulesRaw.value.trim()) {
    try {
      JSON.parse(rulesRaw.value)
    } catch {
      errors.value.rules = 'Rules must be valid JSON array'
    }
  }
  return Object.keys(errors.value).length === 0
}

function handleSave() {
  if (!validate()) return

  const tags = tagsRaw.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t.length > 0)

  let rules = undefined
  if (rulesRaw.value.trim()) {
    try {
      rules = JSON.parse(rulesRaw.value)
    } catch {
      return
    }
  }

  const payload: FlagPayload = {
    name: name.value.trim(),
    scope: scope.value,
    description: description.value.trim() || undefined,
    environment: environment.value,
    complex: complex.value,
    ttl: ttlDays.value ?? undefined,
    tags: tags.length ? tags : undefined,
    rules: rules,
  }

  emit('save', payload)
}

defineExpose({ handleSave, selectedSegmentIds })
</script>

<template>
  <form class="flex flex-col gap-md" @submit.prevent="handleSave">
    <!-- Name -->
    <div class="form-field">
      <label class="form-label">
        Flag Name <span class="text-error">*</span>
      </label>
      <input
        v-model="name"
        type="text"
        class="form-input"
        :class="{ 'form-input--error': errors.name }"
        placeholder="e.g. new_checkout_flow"
      />
      <span v-if="errors.name" class="form-error">{{ errors.name }}</span>
    </div>

    <!-- Scope -->
    <div class="form-field">
      <label class="form-label">
        Scope <span class="text-error">*</span>
      </label>
      <select
        v-model="scope"
        class="form-input"
        :class="{ 'form-input--error': errors.scope }"
      >
        <option value="" disabled>Select scope</option>
        <option value="global">Global</option>
        <option value="tenant">Tenant</option>
        <option value="product">Product</option>
        <option value="company">Company</option>
      </select>
      <span v-if="errors.scope" class="form-error">{{ errors.scope }}</span>
    </div>

    <!-- Description -->
    <div class="form-field">
      <label class="form-label">Description</label>
      <textarea
        v-model="description"
        class="form-input form-textarea"
        placeholder="Brief description of what this flag controls"
        rows="2"
      ></textarea>
    </div>

    <!-- Environment -->
    <div class="form-field">
      <label class="form-label">Environment</label>
      <select v-model="environment" class="form-input">
        <option value="production">Production</option>
        <option value="staging">Staging</option>
        <option value="development">Development</option>
      </select>
    </div>

    <!-- Complex toggle -->
    <div class="form-field">
      <label class="flex items-center gap-sm cursor-pointer">
        <input
          v-model="complex"
          type="checkbox"
          class="form-checkbox"
        />
        <span class="form-label mb-0">Complex flag (multi-rule evaluation)</span>
      </label>
    </div>

    <!-- TTL -->
    <div class="form-field">
      <label class="form-label">TTL (Days)</label>
      <input
        v-model.number="ttlDays"
        type="number"
        class="form-input"
        placeholder="Days until expiry (optional)"
        min="1"
      />
    </div>

    <!-- Tags -->
    <div class="form-field">
      <label class="form-label">Tags</label>
      <input
        v-model="tagsRaw"
        type="text"
        class="form-input"
        placeholder="comma-separated: auth, payments, beta"
      />
      <span class="form-hint">Separate tags with commas</span>
    </div>

    <!-- Segments (FLAG-06) -->
    <div class="form-field">
      <label class="form-label">Segments</label>
      <SegmentPicker
        :segments="props.segments ?? []"
        v-model="selectedSegmentIds"
      />
      <span class="form-hint">Users in selected segments will see this flag as enabled.</span>
    </div>

    <!-- Rules (JSON) -->
    <div class="form-field">
      <label class="form-label">Rules (JSON array)</label>
      <textarea
        v-model="rulesRaw"
        class="form-input form-textarea form-textarea--code"
        :class="{ 'form-input--error': errors.rules }"
        placeholder='[{"attribute":"country","operator":"equals","value":"PE","result":true}]'
        rows="4"
      ></textarea>
      <span v-if="errors.rules" class="form-error">{{ errors.rules }}</span>
      <span v-else class="form-hint">Optional. Phase 5 will add a visual rule builder.</span>
    </div>
  </form>
</template>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--on-surface);
  margin-bottom: 0;
}

.form-input {
  padding: 8px 12px;
  border-radius: var(--rounded);
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

.form-input--error {
  border-color: var(--error);
}

.form-textarea {
  resize: vertical;
  min-height: 56px;
}

.form-textarea--code {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
}

.form-checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}

.form-error {
  font-size: 0.75rem;
  color: var(--error);
}

.form-hint {
  font-size: 0.75rem;
  color: var(--on-surface-variant);
}
</style>
