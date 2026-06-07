<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TenantPayload } from '../../services/tenants'
import StitchTextField from '../ui/StitchTextField.vue'

const props = defineProps<{
  modelValue: TenantPayload
}>()

const emit = defineEmits(['update:modelValue'])

const formData = ref({ ...props.modelValue })

watch(() => props.modelValue, (newVal) => {
  formData.value = { ...newVal }
}, { deep: true })

watch(formData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

const countries = [
  { value: 'ES', label: 'Spain' },
  { value: 'US', label: 'USA' },
  { value: 'DE', label: 'Germany' },
  { value: 'FR', label: 'France' },
  { value: 'GB', label: 'UK' },
  { value: 'PE', label: 'Peru' }
]
const languages = [
  { value: 'es', label: 'Spanish' },
  { value: 'en', label: 'English' },
  { value: 'de', label: 'German' },
  { value: 'fr', label: 'French' }
]
const currencies = ['EUR', 'USD', 'GBP']
const units = [
  { value: 'metric', label: 'Metric' },
  { value: 'imperial', label: 'Imperial' }
]
const availableProducts = ['Core', 'Analytics', 'Support', 'API']

const toggleProduct = (product: string) => {
  const index = formData.value.products.indexOf(product)
  if (index === -1) {
    formData.value.products.push(product)
  } else {
    formData.value.products.splice(index, 1)
  }
}
</script>

<template>
  <div class="form-container">
    <!-- Section: Identity -->
    <div class="form-section">
      <p class="form-section-label">Identity</p>
      <StitchTextField
        v-model="formData.name"
        label="Tenant Name"
        placeholder="e.g. Acme Corp"
        required
      />

      <div class="form-row">
        <md-outlined-select
          label="Country"
          :value="formData.country"
          @change="(e: any) => formData.country = e.target.value"
        >
          <md-select-option v-for="c in countries" :key="c.value" :value="c.value">
            <div slot="headline">{{ c.label }}</div>
          </md-select-option>
        </md-outlined-select>

        <md-outlined-select
          label="Status"
          :value="formData.status"
          @change="(e: any) => formData.status = e.target.value"
        >
          <md-select-option value="active">
            <div slot="headline">Active</div>
          </md-select-option>
          <md-select-option value="suspended">
            <div slot="headline">Suspended</div>
          </md-select-option>
        </md-outlined-select>
      </div>
    </div>

    <!-- Section: Localization -->
    <div class="form-section">
      <p class="form-section-label">Localization</p>
      <div class="form-row">
        <md-outlined-select
          label="Default Language"
          :value="formData.default_language"
          @change="(e: any) => formData.default_language = e.target.value"
        >
          <md-select-option v-for="l in languages" :key="l.value" :value="l.value">
            <div slot="headline">{{ l.label }}</div>
          </md-select-option>
        </md-outlined-select>

        <md-outlined-select
          label="Default Currency"
          :value="formData.default_currency"
          @change="(e: any) => formData.default_currency = e.target.value"
        >
          <md-select-option v-for="c in currencies" :key="c" :value="c">
            <div slot="headline">{{ c }}</div>
          </md-select-option>
        </md-outlined-select>
      </div>

      <md-outlined-select
        label="Measurement Units"
        :value="formData.default_units"
        @change="(e: any) => formData.default_units = e.target.value"
      >
        <md-select-option v-for="u in units" :key="u.value" :value="u.value">
          <div slot="headline">{{ u.label }}</div>
        </md-select-option>
      </md-outlined-select>
    </div>

    <!-- Section: Products — md-checkbox for each product -->
    <div class="form-section">
      <p class="form-section-label">Product Access</p>
      <div class="checkbox-group">
        <label v-for="p in availableProducts" :key="p" class="checkbox-item">
          <md-checkbox
            :checked="formData.products.includes(p)"
            @change="toggleProduct(p)"
          />
          <span class="checkbox-label">{{ p }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Stitch form section — groups related fields with a label */
.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* Section label — body-small with on-surface-variant */
.form-section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  margin: 0 0 2px;
  font-family: var(--font-family-sans);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

/* Product checkboxes */
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm) var(--spacing-lg);
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
}

.checkbox-label {
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--on-surface);
}

md-outlined-select {
  width: 100%;
}
</style>
