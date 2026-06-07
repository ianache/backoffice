<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TenantPayload } from '../../services/tenants'

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
const languages = ['es', 'en', 'de', 'fr']
const currencies = ['EUR', 'USD', 'GBP']
const units = ['metric', 'imperial']
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
    <div class="form-group">
      <label>Name</label>
      <input v-model="formData.name" type="text" placeholder="Tenant name" required />
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Country</label>
        <select v-model="formData.country">
          <option v-for="c in countries" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>Status</label>
        <select v-model="formData.status">
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Language</label>
        <select v-model="formData.default_language">
          <option v-for="l in languages" :key="l" :value="l">{{ l.toUpperCase() }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>Currency</label>
        <select v-model="formData.default_currency">
          <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <label>Units</label>
      <select v-model="formData.default_units">
        <option v-for="u in units" :key="u" :value="u">{{ u.charAt(0).toUpperCase() + u.slice(1) }}</option>
      </select>
    </div>

    <div class="form-group">
      <label>Products</label>
      <div class="checkbox-group">
        <label v-for="p in availableProducts" :key="p" class="checkbox-label">
          <input 
            type="checkbox" 
            :checked="formData.products.includes(p)" 
            @change="toggleProduct(p)"
          />
          {{ p }}
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

label {
  font-weight: 500;
  font-size: 0.875rem;
  color: #374151;
}

input, select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding-top: 0.25rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 400;
  cursor: pointer;
}
</style>
