<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Tenant, TenantPayload } from '../../services/tenants'
import TenantForm from './TenantForm.vue'
import WhitelabelForm from './WhitelabelForm.vue'

const props = defineProps<{
  show: boolean
  tenant: Tenant | null
}>()

const emit = defineEmits(['close', 'save'])

const activeTab = ref<'general' | 'whitelabel'>('general')

const defaultPayload: TenantPayload = {
  name: '',
  country: 'Spain',
  status: 'active',
  default_language: 'es',
  default_currency: 'EUR',
  default_units: 'metric',
  products: ['Core'],
  logo_url: '',
  primary_color: '#2563eb',
  secondary_color: '#64748b',
  accent_color: '#10b981',
  font_family: 'Inter',
  font_weight: '400',
  domain: ''
}

const formData = ref<TenantPayload>({ ...defaultPayload })

// Reset form when drawer opens
import { watch } from 'vue'
watch(() => props.show, (isShowing) => {
  if (isShowing) {
    if (props.tenant) {
      const { id, created_at, ...payload } = props.tenant
      formData.value = { ...payload }
    } else {
      formData.value = { ...defaultPayload }
    }
    activeTab.value = 'general'
  }
})

const isEdit = computed(() => !!props.tenant)

const handleSubmit = () => {
  emit('save', formData.value)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slide">
      <div v-if="show" class="drawer-overlay" @click="emit('close')">
        <div class="drawer-content" @click.stop>
          <div class="drawer-header">
            <h2>{{ isEdit ? 'Edit Tenant' : 'Create Tenant' }}</h2>
            <button class="close-btn" @click="emit('close')">&times;</button>
          </div>

          <div class="tabs">
            <button 
              :class="{ active: activeTab === 'general' }" 
              @click="activeTab = 'general'"
            >
              General Info
            </button>
            <button 
              :class="{ active: activeTab === 'whitelabel' }" 
              @click="activeTab = 'whitelabel'"
            >
              Whitelabel
            </button>
          </div>

          <div class="drawer-body">
            <TenantForm v-if="activeTab === 'general'" v-model="formData" />
            <WhitelabelForm v-else v-model="formData" />
          </div>

          <div class="drawer-footer">
            <button class="btn btn-secondary" @click="emit('close')">Cancel</button>
            <button class="btn btn-primary" @click="handleSubmit">
              {{ isEdit ? 'Update Tenant' : 'Create Tenant' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.drawer-content {
  background: white;
  width: 100%;
  max-width: 500px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
}

.drawer-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}

.tabs button {
  flex: 1;
  padding: 1rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-weight: 500;
  color: #6b7280;
}

.tabs button.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.drawer-footer {
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn-primary {
  background: #2563eb;
  border: 1px solid #2563eb;
  color: white;
}

.slide-enter-active, .slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}
</style>
