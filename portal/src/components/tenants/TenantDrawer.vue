<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Tenant, TenantPayload } from '../../services/tenants'
import TenantForm from './TenantForm.vue'
import WhitelabelForm from './WhitelabelForm.vue'
import StitchButton from '../ui/StitchButton.vue'

const props = defineProps<{
  show: boolean
  tenant: Tenant | null
}>()

const emit = defineEmits(['close', 'save'])

const activeTab = ref(0)

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

watch(() => props.show, (isShowing) => {
  if (isShowing) {
    if (props.tenant) {
      const { id, created_at, ...payload } = props.tenant
      formData.value = { ...payload }
    } else {
      formData.value = { ...defaultPayload }
    }
    activeTab.value = 0
  }
})

const isEdit = computed(() => !!props.tenant)

const handleSubmit = () => {
  emit('save', formData.value)
}

const handleTabChange = (e: any) => {
  activeTab.value = e.target.activeTabIndex
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slide">
      <div v-if="show" class="drawer-overlay" @click="emit('close')">
        <div class="drawer-content" @click.stop>
          <div class="drawer-header">
            <h2 class="text-title-large">{{ isEdit ? 'Edit Tenant' : 'Create Tenant' }}</h2>
            <md-icon-button @click="emit('close')">
              <md-icon>close</md-icon>
            </md-icon-button>
          </div>

          <md-tabs :active-tab-index="activeTab" @change="handleTabChange">
            <md-primary-tab>
              <md-icon slot="icon">info</md-icon>
              General Info
            </md-primary-tab>
            <md-primary-tab>
              <md-icon slot="icon">palette</md-icon>
              Whitelabel
            </md-primary-tab>
          </md-tabs>

          <div class="drawer-body">
            <TenantForm v-if="activeTab === 0" v-model="formData" />
            <WhitelabelForm v-else v-model="formData" />
          </div>

          <md-divider></md-divider>

          <div class="drawer-footer">
            <StitchButton variant="text" @click="emit('close')">Cancel</StitchButton>
            <StitchButton variant="filled" @click="handleSubmit">
              {{ isEdit ? 'Update Tenant' : 'Create Tenant' }}
            </StitchButton>
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
  box-shadow: var(--md-sys-elevation-level3);
}

.drawer-header {
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-title-large {
  font-size: 1.375rem;
  font-weight: 400;
  margin: 0;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.drawer-footer {
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  background: var(--surface-container-low);
}

md-tabs {
  --md-primary-tab-container-color: var(--surface-container-low);
  --md-tabs-container-color: var(--surface-container-low);
}

.slide-enter-active, .slide-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}
</style>
