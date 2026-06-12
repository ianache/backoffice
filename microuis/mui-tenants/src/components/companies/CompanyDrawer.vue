<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { Company, CompanyPayload } from '../../services/companies'
import { list as listTenants } from '../../services/tenants'
import { useUserContext } from 'shell/useUserContext'
import StitchButton from 'shell/StitchButton'
import StitchTextField from 'shell/StitchTextField'

const props = defineProps<{
  show: boolean
  company: Company | null
  error?: string | null
}>()

const emit = defineEmits(['close', 'save'])

const defaultPayload: CompanyPayload = {
  id: '',
  name: '',
  status: 'active',
  tenant_id: ''
}

interface TenantOption {
  value: string
  label: string
}

const formData = ref<CompanyPayload>({ ...defaultPayload })
const slugError = ref('')
const nameError = ref('')
const tenantError = ref('')

const tenantOptions = ref<TenantOption[]>([])
const tenantSelectDisabled = ref(false)

const isEdit = computed(() => !!props.company)

const SLUG_RE = /^[a-z0-9_]{1,50}$/

const loadTenantOptions = async () => {
  try {
    const tenants = await listTenants()
    tenantOptions.value = tenants.map(t => ({ value: String(t.id), label: `${t.name} (#${t.id})` }))
    tenantSelectDisabled.value = false
  } catch {
    // 403 for TenantAdmin/TenantOwner — fall back to the logged-in user's own tenant
    const ctx = useUserContext()
    tenantOptions.value = [{ value: ctx.tenant_id, label: `My tenant (#${ctx.tenant_id})` }]
    if (!isEdit.value) {
      formData.value.tenant_id = ctx.tenant_id
    }
    tenantSelectDisabled.value = true
  }
}

onMounted(() => {
  loadTenantOptions()
})

watch(() => props.show, (isShowing) => {
  if (isShowing) {
    if (props.company) {
      const { created_at, updated_at, ...payload } = props.company
      formData.value = { ...payload }
    } else {
      formData.value = { ...defaultPayload }
      // Pre-select fallback tenant (if applicable) for create mode
      if (tenantSelectDisabled.value && tenantOptions.value.length) {
        formData.value.tenant_id = tenantOptions.value[0].value
      }
    }
    slugError.value = ''
    nameError.value = ''
    tenantError.value = ''
  }
})

const validateSlug = () => {
  if (isEdit.value) { slugError.value = ''; return true }
  if (!SLUG_RE.test(formData.value.id)) {
    slugError.value = 'Lowercase letters, digits and _ only (max 50)'
    return false
  }
  slugError.value = ''
  return true
}

const validateName = () => {
  if (!formData.value.name.trim()) {
    nameError.value = 'Name is required'
    return false
  }
  nameError.value = ''
  return true
}

const validateTenant = () => {
  if (!formData.value.tenant_id) {
    tenantError.value = 'Tenant is required'
    return false
  }
  tenantError.value = ''
  return true
}

const handleSubmit = () => {
  const slugOk = validateSlug()
  const nameOk = validateName()
  const tenantOk = validateTenant()
  if (!slugOk || !nameOk || !tenantOk) return
  emit('save', { ...formData.value })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slide">
      <div v-if="show" class="drawer-overlay" @click="emit('close')" role="dialog" aria-modal="true" :aria-label="isEdit ? 'Edit Company' : 'New Company'">
        <div class="drawer-content" @click.stop>
          <!-- Header -->
          <div class="drawer-header">
            <div class="flex flex-col">
              <h2 class="drawer-title">{{ isEdit ? 'Edit Company' : 'New Company' }}</h2>
              <p class="drawer-subtitle">{{ isEdit ? `ID: ${company?.id}` : 'Define a new company' }}</p>
            </div>
            <md-icon-button @click="emit('close')" aria-label="Close drawer">
              <md-icon>close</md-icon>
            </md-icon-button>
          </div>

          <!-- Body -->
          <div class="drawer-body">
            <div class="form-container">
              <div class="form-section">
                <p class="form-section-label">Identity</p>

                <StitchTextField
                  v-model="formData.id"
                  label="Company ID (slug)"
                  placeholder="e.g. acme"
                  :disabled="isEdit"
                  :error="!!slugError"
                  :error-text="slugError"
                  supporting-text="Lowercase letters, numbers, underscores — immutable after creation."
                  required
                  @change="validateSlug"
                />

                <StitchTextField
                  v-model="formData.name"
                  label="Company Name"
                  placeholder="e.g. Acme Corp"
                  :error="!!nameError"
                  :error-text="nameError"
                  required
                  @change="validateName"
                />

                <md-outlined-select
                  label="Status"
                  :value="formData.status"
                  @change="(e: any) => formData.status = e.target.value"
                >
                  <md-select-option value="active">
                    <div slot="headline">Active</div>
                  </md-select-option>
                  <md-select-option value="inactive">
                    <div slot="headline">Inactive</div>
                  </md-select-option>
                </md-outlined-select>

                <md-outlined-select
                  label="Tenant"
                  :value="formData.tenant_id"
                  :disabled="isEdit || tenantSelectDisabled"
                  @change="(e: any) => { formData.tenant_id = e.target.value; validateTenant() }"
                >
                  <md-select-option v-for="opt in tenantOptions" :key="opt.value" :value="opt.value">
                    <div slot="headline">{{ opt.label }}</div>
                  </md-select-option>
                </md-outlined-select>
                <p v-if="tenantError" class="field-error">{{ tenantError }}</p>
                <p v-if="isEdit" class="field-hint">Tenant is immutable after creation.</p>
              </div>

              <!-- Backend error (e.g. 409 duplicate slug) -->
              <p v-if="error" class="form-error">{{ error }}</p>
            </div>
          </div>

          <md-divider></md-divider>

          <!-- Footer -->
          <div class="drawer-footer">
            <StitchButton variant="text" @click="emit('close')">Cancel</StitchButton>
            <StitchButton variant="filled" @click="handleSubmit">
              {{ isEdit ? 'Update Company' : 'Create Company' }}
            </StitchButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Drawer chrome — mirrors ProductDrawer (Stitch side-sheet pattern) */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.drawer-content {
  background: var(--surface-container-low);
  color: var(--on-surface);
  width: 100%;
  max-width: 480px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 8px 10px -5px rgba(0, 0, 0, 0.16),
    0 16px 24px 2px rgba(0, 0, 0, 0.10),
    0 6px 30px 5px rgba(0, 0, 0, 0.08);
  border-left: 1px solid var(--outline-variant);
}

.drawer-header {
  padding: var(--spacing-md) var(--spacing-md) var(--spacing-md) var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: var(--surface-container-low);
}

.drawer-title {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--on-surface);
  margin: 0;
  font-family: var(--font-family-sans);
  line-height: 1.4;
}

.drawer-subtitle {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--on-surface-variant);
  margin: 2px 0 0;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  scrollbar-width: thin;
  scrollbar-color: var(--outline-variant) transparent;
}

.drawer-footer {
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  background: var(--surface-container-low);
  min-height: 52px;
  align-items: center;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  margin: 0 0 2px;
  font-family: var(--font-family-sans);
}

.field-error {
  font-size: 0.6875rem;
  color: var(--error);
  margin: -8px 0 0;
}

.field-hint {
  font-size: 0.6875rem;
  color: var(--on-surface-variant);
  margin: -8px 0 0;
}

.form-error {
  font-size: 0.75rem;
  color: var(--error);
  background: var(--error-container);
  border-radius: 8px;
  padding: var(--spacing-sm) var(--spacing-md);
}

md-outlined-select {
  width: 100%;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
