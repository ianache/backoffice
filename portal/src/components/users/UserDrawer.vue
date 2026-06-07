<script setup lang="ts">
import { ref, watch } from 'vue'
import type { KcUser, UserPayload } from '../../services/users'
import UserForm from './UserForm.vue'
import UserRolesForm from './UserRolesForm.vue'
import UserActivityTab from './UserActivityTab.vue'
import StitchButton from '../ui/StitchButton.vue'

const props = defineProps<{
  show: boolean
  user: KcUser | null
}>()

const emit = defineEmits<{
  close: []
  save: [payload: UserPayload]
}>()

type TabId = 'general' | 'roles' | 'activity'
const activeTab = ref<TabId>('general')

const defaultFormData: Partial<UserPayload> = {
  email: '',
  firstName: '',
  lastName: '',
}

const defaultRolesData = {
  tenantRole: '',
  productRoles: {} as Record<string, string>,
}

const formData = ref<Partial<UserPayload>>({ ...defaultFormData })
const rolesData = ref({ ...defaultRolesData, productRoles: {} as Record<string, string> })

const resetFromUser = (user: KcUser | null) => {
  if (user) {
    formData.value = {
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
    }
    rolesData.value = {
      tenantRole: user.tenantRole ?? '',
      productRoles: { ...user.productRoles },
    }
  } else {
    formData.value = { ...defaultFormData }
    rolesData.value = { tenantRole: '', productRoles: {} }
  }
  activeTab.value = 'general'
}

watch(
  () => props.show,
  (isShowing) => {
    if (isShowing) {
      resetFromUser(props.user)
    }
  }
)

watch(
  () => props.user,
  (newUser) => {
    if (props.show) {
      resetFromUser(newUser)
    }
  }
)

const handleSave = () => {
  const payload: UserPayload = {
    email: formData.value.email ?? '',
    firstName: formData.value.firstName ?? '',
    lastName: formData.value.lastName ?? '',
    tenantRole: rolesData.value.tenantRole,
    productRoles: rolesData.value.productRoles,
  }
  emit('save', payload)
}

const setTab = (tab: TabId) => {
  activeTab.value = tab
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slide">
      <div
        v-if="show"
        class="drawer-overlay"
        @click="emit('close')"
        role="dialog"
        aria-modal="true"
        aria-label="Manage Access"
      >
        <div class="drawer-content" @click.stop>
          <!-- Drawer Header -->
          <div class="drawer-header">
            <div class="flex flex-col">
              <h2 class="drawer-title">Manage Access</h2>
              <p class="drawer-subtitle">
                {{ user ? `${user.firstName} ${user.lastName}` : 'Invite a new member' }}
              </p>
            </div>
            <md-icon-button @click="emit('close')" aria-label="Close drawer">
              <md-icon>close</md-icon>
            </md-icon-button>
          </div>

          <!-- Tabs -->
          <div class="drawer-tabs">
            <button
              v-for="tab in ['general', 'roles', 'activity'] as TabId[]"
              :key="tab"
              @click="setTab(tab)"
              :class="[
                'tab-btn capitalize',
                activeTab === tab ? 'tab-btn--active' : 'tab-btn--inactive'
              ]"
              :disabled="tab === 'activity' && !user"
            >
              {{ tab }}
            </button>
          </div>

          <!-- Scrollable form body -->
          <div class="drawer-body">
            <UserForm
              v-if="activeTab === 'general'"
              v-model="formData"
            />
            <UserRolesForm
              v-else-if="activeTab === 'roles'"
              v-model="rolesData"
            />
            <UserActivityTab
              v-else-if="activeTab === 'activity' && show && user"
              :user-id="user.id"
            />
          </div>

          <md-divider></md-divider>

          <!-- Footer -->
          <div class="drawer-footer">
            <StitchButton variant="text" @click="emit('close')">Cancel</StitchButton>
            <StitchButton variant="filled" @click="handleSave">
              {{ user ? 'Save Changes' : 'Invite Member' }}
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
  width: 440px;
  max-width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 8px 10px -5px rgba(0, 0, 0, 0.16),
    0 16px 24px 2px rgba(0, 0, 0, 0.1),
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

.drawer-tabs {
  display: flex;
  border-bottom: 1px solid var(--outline-variant);
  background: var(--surface-container-low);
  padding: 0 var(--spacing-md);
  gap: 0;
}

.tab-btn {
  padding: 10px 16px;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: color 0.15s;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.tab-btn--active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  font-weight: 600;
}

.tab-btn--inactive {
  color: var(--on-surface-variant);
}

.tab-btn--inactive:hover:not(:disabled) {
  color: var(--on-surface);
}

.tab-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
