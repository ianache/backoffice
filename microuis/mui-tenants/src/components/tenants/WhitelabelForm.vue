<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { TenantPayload } from '../../services/tenants'
import ColorInput from 'vue-color-input'
import StitchTextField from 'shell/StitchTextField'

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
    <!-- Section: Domain & Logo -->
    <div class="form-section">
      <p class="form-section-label">Domain & Branding</p>

      <StitchTextField
        v-model="formData.domain"
        label="Custom Domain"
        placeholder="e.g. acme.backoffice.com"
      />

      <StitchTextField
        v-model="formData.logo_url"
        label="Logo URL"
        placeholder="https://example.com/logo.png"
        type="url"
      />

      <div v-if="formData.logo_url" class="logo-preview">
        <img :src="formData.logo_url" alt="Logo Preview" />
      </div>
    </div>

    <!-- Section: Colors -->
    <div class="form-section">
      <p class="form-section-label">Color Palette</p>
      <div class="color-section">
        <div class="color-item">
          <label class="color-label">Primary</label>
          <ColorInput v-model="primaryColor" format="hex" />
        </div>
        <div class="color-item">
          <label class="color-label">Secondary</label>
          <ColorInput v-model="secondaryColor" format="hex" />
        </div>
        <div class="color-item">
          <label class="color-label">Accent</label>
          <ColorInput v-model="accentColor" format="hex" />
        </div>
      </div>
    </div>

    <!-- Section: Typography -->
    <div class="form-section">
      <p class="form-section-label">Typography</p>
      <div class="form-row">
        <md-outlined-select
          label="Font Family"
          :value="formData.font_family"
          @change="(e: any) => formData.font_family = e.target.value"
        >
          <md-select-option v-for="f in fontFamilies" :key="f" :value="f">
            <div slot="headline">{{ f }}</div>
          </md-select-option>
        </md-outlined-select>

        <md-outlined-select
          label="Font Weight"
          :value="formData.font_weight"
          @change="(e: any) => formData.font_weight = e.target.value"
        >
          <md-select-option v-for="w in fontWeights" :key="w" :value="w">
            <div slot="headline">{{ w }}</div>
          </md-select-option>
        </md-outlined-select>
      </div>
    </div>

    <!-- Live Preview card — tonal elevation level 0 -->
    <div
      class="preview-card"
      :style="{
        borderLeft: `4px solid ${formData.primary_color || '#2563eb'}`,
        fontFamily: formData.font_family || 'sans-serif',
        fontWeight: formData.font_weight || '400'
      }"
    >
      <p class="preview-title" :style="{ color: formData.primary_color || '#2563eb' }">
        Design System Preview
      </p>
      <p class="preview-body">
        This is how your tenant's text will appear in the platform.
      </p>
      <!-- Preview action button using StitchButton overridden with tenant colors -->
      <div class="preview-actions">
        <button
          class="preview-action-btn"
          :style="{
            backgroundColor: formData.primary_color || '#2563eb',
            fontFamily: formData.font_family || 'sans-serif'
          }"
        >
          Action Button
        </button>
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

/* Stitch form section grouping */
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

/* Color palette section */
.color-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.color-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.color-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--on-surface-variant);
}

/* Logo preview container */
.logo-preview {
  height: 64px;
  background: var(--surface-container);
  border-radius: var(--rounded);
  border: 1px solid var(--outline-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-sm);
}

.logo-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* Live preview card — surface-container-lowest, tonal level 0 */
.preview-card {
  padding: var(--spacing-md);
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  border-radius: var(--rounded-md);
}

.preview-title {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-xs);
}

.preview-body {
  font-size: 0.8125rem;
  color: var(--on-surface-variant);
  margin: 0 0 var(--spacing-sm);
}

.preview-actions {
  margin-top: var(--spacing-sm);
}

/* Preview button — shows tenant primary color; not a real UI button */
.preview-action-btn {
  color: #ffffff;
  border: none;
  padding: 6px 16px;
  border-radius: var(--rounded);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: default;
  letter-spacing: 0.01em;
}

md-outlined-select {
  width: 100%;
}
</style>
