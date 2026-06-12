<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FeatureFlag, FlagPayload, Segment } from '../../services/flags'
import { listProductsLookup, listCompaniesLookup, listTenantsLookup, type LookupOption } from '../../services/lookups'
import { validateFlagTarget, buildTargetFields } from './flagFormModel'
import { useUserContext } from 'shell/useUserContext'
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
const selectedSegmentIds = ref<number[]>([])

// Scope-target state (TGT-01/TGT-02)
const tenantId = ref('')
const productId = ref('')
const companyId = ref('')
const tenantOptions = ref<LookupOption[]>([])
const productOptions = ref<LookupOption[]>([])
const companyOptions = ref<LookupOption[]>([])
const tenantsLoading = ref(false)
const productsLoading = ref(false)
const companiesLoading = ref(false)
const tenantsLoaded = ref(false)
const productsLoaded = ref(false)
const companiesLoaded = ref(false)

const errors = ref<{ name?: string; scope?: string; target?: string }>({})

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
      selectedSegmentIds.value = props.linkedSegmentIds ?? []
      tenantId.value = flag.tenant_id ?? ''
      productId.value = flag.product_id ?? ''
      companyId.value = flag.company_id ?? ''
      // Pre-fetch the catalog for the flag's current scope so the combobox
      // shows the pre-selected value as soon as it renders.
      ensureCatalogLoaded(flag.scope)
    } else {
      name.value = ''
      scope.value = ''
      description.value = ''
      environment.value = 'production'
      complex.value = false
      ttlDays.value = null
      tagsRaw.value = ''
      selectedSegmentIds.value = []
      tenantId.value = ''
      productId.value = ''
      companyId.value = ''
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

// Clear the previously selected target when the scope changes, and lazily
// fetch the catalog for the new scope.
watch(scope, (newScope, oldScope) => {
  if (oldScope && newScope !== oldScope) {
    tenantId.value = ''
    productId.value = ''
    companyId.value = ''
  }
  ensureCatalogLoaded(newScope)
})

async function ensureCatalogLoaded(targetScope: string) {
  if (targetScope === 'product' && !productsLoaded.value) {
    productsLoading.value = true
    try {
      productOptions.value = await listProductsLookup()
    } finally {
      productsLoaded.value = true
      productsLoading.value = false
    }
  } else if (targetScope === 'company' && !companiesLoaded.value) {
    companiesLoading.value = true
    try {
      companyOptions.value = await listCompaniesLookup()
    } finally {
      companiesLoaded.value = true
      companiesLoading.value = false
    }
  } else if (targetScope === 'tenant' && !tenantsLoaded.value) {
    tenantsLoading.value = true
    try {
      tenantOptions.value = await listTenantsLookup()
    } catch {
      // BFF /tenants is PlatformAdmin-only — fall back to the logged-in
      // user's own tenant for TenantAdmin/TenantOwner.
      const ctx = useUserContext()
      tenantOptions.value = ctx.tenant_id ? [{ id: ctx.tenant_id, name: 'My tenant' }] : []
    } finally {
      tenantsLoaded.value = true
      tenantsLoading.value = false
    }
  }
}

function validate(): boolean {
  errors.value = {}
  if (!name.value.trim()) {
    errors.value.name = 'Flag name is required'
  }
  if (!scope.value) {
    errors.value.scope = 'Scope is required'
  }
  errors.value.target = validateFlagTarget(scope.value, {
    tenantId: tenantId.value,
    productId: productId.value,
    companyId: companyId.value,
  }) ?? undefined
  if (errors.value.target === undefined) {
    delete errors.value.target
  }
  return Object.keys(errors.value).length === 0
}

function handleSave() {
  if (!validate()) return

  const tags = tagsRaw.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t.length > 0)

  const payload: FlagPayload = {
    name: name.value.trim(),
    scope: scope.value,
    ...buildTargetFields(scope.value, {
      tenantId: tenantId.value,
      productId: productId.value,
      companyId: companyId.value,
    }),
    description: description.value.trim() || undefined,
    environment: environment.value,
    complex: complex.value,
    ttl: ttlDays.value ?? undefined,
    tags: tags.length ? tags : undefined,
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

    <!-- Product target (scope=product) -->
    <div v-if="scope === 'product'" class="form-field">
      <label class="form-label">Product <span class="text-error">*</span></label>
      <select v-model="productId" class="form-input" :class="{ 'form-input--error': errors.target }">
        <option value="" disabled>Select product</option>
        <option v-for="o in productOptions" :key="o.id" :value="o.id">{{ o.name }} ({{ o.id }})</option>
      </select>
      <span v-if="!productsLoading && productOptions.length === 0" class="form-hint">No active products — create one in the Products catalog.</span>
      <span v-if="errors.target" class="form-error">{{ errors.target }}</span>
    </div>

    <!-- Tenant target (scope=tenant) -->
    <div v-if="scope === 'tenant'" class="form-field">
      <label class="form-label">Tenant <span class="text-error">*</span></label>
      <select v-model="tenantId" class="form-input" :class="{ 'form-input--error': errors.target }">
        <option value="" disabled>Select tenant</option>
        <option v-for="o in tenantOptions" :key="o.id" :value="o.id">{{ o.name }} (#{{ o.id }})</option>
      </select>
      <span v-if="!tenantsLoading && tenantOptions.length === 0" class="form-hint">No tenants available.</span>
      <span v-if="errors.target" class="form-error">{{ errors.target }}</span>
    </div>

    <!-- Company target (scope=company) -->
    <div v-if="scope === 'company'" class="form-field">
      <label class="form-label">Company <span class="text-error">*</span></label>
      <select v-model="companyId" class="form-input" :class="{ 'form-input--error': errors.target }">
        <option value="" disabled>Select company</option>
        <option v-for="o in companyOptions" :key="o.id" :value="o.id">{{ o.name }} ({{ o.id }})</option>
      </select>
      <span v-if="!companiesLoading && companyOptions.length === 0" class="form-hint">No active companies — create one in /companies.</span>
      <span v-if="errors.target" class="form-error">{{ errors.target }}</span>
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

    <!-- Rules (read-only notice) -->
    <div class="form-field">
      <label class="form-label">Rules</label>
      <p class="text-sm text-on-surface-variant bg-surface-container rounded-lg px-3 py-2 border border-outline-variant">
        Rules are managed in the
        <span class="text-primary font-medium">Rule Builder</span>
        — open it from the drawer header when editing a flag.
      </p>
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
