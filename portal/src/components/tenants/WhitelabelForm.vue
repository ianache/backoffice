<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TenantPayload } from '../../services/tenants'
// Assuming vue-color-input is used like this, or we can use native color input for simplicity if not.
// For now, I'll use native color inputs with a wrapper class to match the requirement.
import ColorInput from 'vue-color-input'
import { computed } from 'vue'

const props = defineProps<{
  modelValue: TenantPayload
}>()

const emit = defineEmits(['update:modelValue'])

const formData = ref({ ...props.modelValue })

const primaryColor = computed({
  get: () => formData.value.primary_color || '#2563eb',
  set: (val: string) => formData.value.primary_color = val
})

const secondaryColor = computed({
  get: () => formData.value.secondary_color || '#64748b',
  set: (val: string) => formData.value.secondary_color = val
})

const accentColor = computed({
  get: () => formData.value.accent_color || '#10b981',
  set: (val: string) => formData.value.accent_color = val
})

watch(() => props.modelValue, (newVal) => {
  formData.value = { ...newVal }
}, { deep: true })

watch(formData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

const fontFamilies = ['Inter', 'Roboto', 'Open Sans', 'Lato']
const fontWeights = ['300', '400', '500', '600', '700']
</script>

<template>
  <div class="form-container">
    <div class="form-group">
      <label>Custom Domain</label>
      <input v-model="formData.domain" type="text" placeholder="e.g. acme.backoffice.com" />
    </div>

    <div class="form-group">
      <label>Logo URL</label>
      <input v-model="formData.logo_url" type="url" placeholder="https://example.com/logo.png" />
      <div v-if="formData.logo_url" class="logo-preview">
        <img :src="formData.logo_url" alt="Logo Preview" />
      </div>
    </div>

    <div class="color-section">
      <div class="form-group">
        <label>Primary Color</label>
        <ColorInput v-model="primaryColor" format="hex" />
      </div>
      <div class="form-group">
        <label>Secondary Color</label>
        <ColorInput v-model="secondaryColor" format="hex" />
      </div>
      <div class="form-group">
        <label>Accent Color</label>
        <ColorInput v-model="accentColor" format="hex" />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Font Family</label>
        <select v-model="formData.font_family">
          <option v-for="f in fontFamilies" :key="f" :value="f">{{ f }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>Font Weight</label>
        <select v-model="formData.font_weight">
          <option v-for="w in fontWeights" :key="w" :value="w">{{ w }}</option>
        </select>
      </div>
    </div>

    <div class="preview-card" :style="{ 
      borderLeft: `4px solid ${formData.primary_color || '#2563eb'}`,
      fontFamily: formData.font_family || 'sans-serif',
      fontWeight: formData.font_weight || '400'
    }">
      <p :style="{ color: formData.primary_color || '#2563eb' }">Preview Text</p>
      <button :style="{ 
        backgroundColor: formData.accent_color || '#10b981',
        color: 'white',
        border: 'none',
        padding: '0.25rem 0.5rem',
        borderRadius: '4px'
      }">Button</button>
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

.color-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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

.logo-preview {
  margin-top: 0.5rem;
  max-width: 100px;
  max-height: 50px;
  border: 1px solid #eee;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-card {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 4px;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}
</style>
