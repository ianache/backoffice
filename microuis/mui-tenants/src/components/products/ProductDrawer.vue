<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Product, ProductPayload } from '../../services/products'
import StitchButton from 'shell/StitchButton'
import StitchTextField from 'shell/StitchTextField'

const props = defineProps<{
  show: boolean
  product: Product | null
}>()

const emit = defineEmits(['close', 'save'])

const defaultPayload: ProductPayload = {
  id: '',
  name: '',
  description: '',
  status: 'active',
  labels: []
}

const formData = ref<ProductPayload>({ ...defaultPayload })
const labelInput = ref('')
const slugError = ref('')

watch(() => props.show, (isShowing) => {
  if (isShowing) {
    if (props.product) {
      const { created_at, updated_at, ...payload } = props.product
      formData.value = { ...payload, labels: [...(payload.labels || [])] }
    } else {
      formData.value = { ...defaultPayload, labels: [] }
    }
    labelInput.value = ''
    slugError.value = ''
  }
})

const isEdit = computed(() => !!props.product)

const SLUG_RE = /^[a-z0-9_]{1,50}$/

const validateSlug = () => {
  if (isEdit.value) { slugError.value = ''; return true }
  if (!SLUG_RE.test(formData.value.id)) {
    slugError.value = 'Lowercase letters, digits and _ only (max 50)'
    return false
  }
  slugError.value = ''
  return true
}

const addLabel = () => {
  const label = labelInput.value.trim().toUpperCase()
  if (label && !formData.value.labels.includes(label)) {
    formData.value.labels.push(label)
  }
  labelInput.value = ''
}

const removeLabel = (label: string) => {
  formData.value.labels = formData.value.labels.filter(l => l !== label)
}

const handleSubmit = () => {
  if (!validateSlug()) return
  emit('save', { ...formData.value })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slide">
      <div v-if="show" class="drawer-overlay" @click="emit('close')" role="dialog" aria-modal="true" :aria-label="isEdit ? 'Edit Product' : 'New Product'">
        <div class="drawer-content" @click.stop>
          <!-- Header -->
          <div class="drawer-header">
            <div class="flex flex-col">
              <h2 class="drawer-title">{{ isEdit ? 'Edit Product' : 'New Product' }}</h2>
              <p class="drawer-subtitle">{{ isEdit ? `ID: ${product?.id}` : 'Define a new catalog product' }}</p>
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
                  v-if="!isEdit"
                  v-model="formData.id"
                  label="Product ID (slug)"
                  placeholder="e.g. core_banking"
                  :error="!!slugError"
                  :error-text="slugError"
                  supporting-text="Immutable after creation. Lowercase, digits, underscores."
                  required
                  @change="validateSlug"
                />

                <StitchTextField
                  v-model="formData.name"
                  label="Product Name"
                  placeholder="e.g. Core Banking Suite"
                  required
                />

                <StitchTextField
                  v-model="formData.description"
                  label="Description"
                  placeholder="Short description of the product"
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
              </div>

              <div class="form-section">
                <p class="form-section-label">Labels</p>
                <div class="flex items-center gap-sm">
                  <StitchTextField
                    v-model="labelInput"
                    label="Add label"
                    placeholder="e.g. ENTERPRISE"
                    class="flex-1"
                    @keydown.enter.prevent="addLabel"
                  />
                  <StitchButton variant="text" @click="addLabel">Add</StitchButton>
                </div>
                <div v-if="formData.labels.length" class="flex flex-wrap gap-xs">
                  <span
                    v-for="label in formData.labels"
                    :key="label"
                    class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-surface-container-high text-on-tertiary-fixed-variant text-[11px] font-bold uppercase"
                  >
                    {{ label }}
                    <button @click="removeLabel(label)" class="material-symbols-outlined text-[14px] hover:text-error leading-none" :aria-label="`Remove ${label}`">close</button>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <md-divider></md-divider>

          <!-- Footer -->
          <div class="drawer-footer">
            <StitchButton variant="text" @click="emit('close')">Cancel</StitchButton>
            <StitchButton variant="filled" @click="handleSubmit">
              {{ isEdit ? 'Update Product' : 'Create Product' }}
            </StitchButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Drawer chrome — mirrors TenantDrawer (Stitch side-sheet pattern) */
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
