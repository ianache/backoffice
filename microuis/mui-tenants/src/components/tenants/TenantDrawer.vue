<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Tenant, TenantPayload } from '../../services/tenants'
import TenantForm from './TenantForm.vue'
import WhitelabelForm from './WhitelabelForm.vue'
import StitchButton from 'shell/StitchButton'

const props = defineProps<{
  show: boolean
  tenant: Tenant | null
}>()

const emit = defineEmits(['close', 'save'])

const activeTab = ref(0)

const defaultPayload: TenantPayload = {
  name: '',
  country: 'ES',
  status: 'active',
  owner: '',
  default_language: 'es',
  default_currency: 'EUR',
  default_units: 'metric',
  products: [],
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
      // Copy the products array — sharing the store tenant's reference would let
      // checkbox toggles mutate the store baseline and break the save diff
      formData.value = { ...payload, products: [...(payload.products || [])] }
    } else {
      formData.value = { ...defaultPayload, products: [] }
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
      <div v-if="show" class="drawer-overlay" @click="emit('close')" role="dialog" aria-modal="true" :aria-label="isEdit ? 'Edit Tenant' : 'Create Tenant'">
        <div class="drawer-content" @click.stop>
          <!-- Drawer Header — Stitch side-sheet pattern -->
          <div class="drawer-header">
            <div class="flex flex-col">
              <h2 class="drawer-title">{{ isEdit ? 'Edit Tenant' : 'Create Tenant' }}</h2>
              <p class="drawer-subtitle">{{ isEdit ? `ID: ${tenant?.id}` : 'Fill in the details below' }}</p>
            </div>
            <md-icon-button @click="emit('close')" aria-label="Close drawer">
              <md-icon>close</md-icon>
            </md-icon-button>
          </div>

          <!-- Tabs — uses surface-container-low container color -->
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

          <!-- Scrollable form body -->
          <div class="drawer-body">
            <TenantForm v-if="activeTab === 0" v-model="formData" />
            <WhitelabelForm v-else v-model="formData" />
          </div>

          <md-divider></md-divider>

          <!-- Footer actions — Stitch text + filled button pattern -->
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
/* Drawer overlay — scrim with 40% opacity (M3 standard) */
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

/* Drawer container — M3 tonal elevation level 1 (surface-container-low) */
.drawer-content {
  background: var(--surface-container-low);
  color: var(--on-surface);
  width: 100%;
  max-width: 480px;
  height: 100%;
  display: flex;
  flex-direction: column;
  /* M3 elevation level 3 equivalent: layered shadow for modal drawers */
  box-shadow:
    0 8px 10px -5px rgba(0, 0, 0, 0.16),
    0 16px 24px 2px rgba(0, 0, 0, 0.10),
    0 6px 30px 5px rgba(0, 0, 0, 0.08);
  border-left: 1px solid var(--outline-variant);
}

/* Header region */
.drawer-header {
  padding: var(--spacing-md) var(--spacing-md) var(--spacing-md) var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: var(--surface-container-low);
}

/* Stitch title-large for side drawers */
.drawer-title {
  font-size: 1.25rem;
  font-weight: 500;
  letter-spacing: 0;
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

/* Tabs — inherit surface-container-low background */
md-tabs {
  --md-primary-tab-container-color: var(--surface-container-low);
  --md-tabs-container-color: var(--surface-container-low);
}

/* Scrollable body */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  /* subtle inner scroll track for Stitch */
  scrollbar-width: thin;
  scrollbar-color: var(--outline-variant) transparent;
}

/* Footer — sticky at bottom, same surface as drawer */
.drawer-footer {
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  background: var(--surface-container-low);
  min-height: 52px;
  align-items: center;
}

/* Slide-in animation — M3 standard easing */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
