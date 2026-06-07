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

const countries = ['Spain', 'USA', 'Germany', 'France', 'UK']
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
        <md-select-option v-for="c in countries" :key="c" :value="c">
          <div slot="headline">{{ c }}</div>
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

    <div class="form-group">
      <label class="section-label">Available Products</label>
      <div class="checkbox-group">
        <label v-for="p in availableProducts" :key="p" class="checkbox-item">
          <md-checkbox 
            :checked="formData.products.includes(p)" 
            @change="toggleProduct(p)"
          />
          <span class="text-body-medium">{{ p }}</span>
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.section-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--on-surface-variant);
  margin-bottom: var(--spacing-sm);
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
}

.text-body-medium {
  font-size: 0.875rem;
  color: var(--on-surface);
}

md-outlined-select {
  width: 100%;
}
</style>
