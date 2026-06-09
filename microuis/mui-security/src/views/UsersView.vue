<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUsersStore } from '../stores/users'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import type { KcUser, UserPayload } from '../services/users'
import UserTable from '../components/users/UserTable.vue'
import UserDrawer from '../components/users/UserDrawer.vue'
import ConfirmDialog from '../components/users/ConfirmDialog.vue'
import StitchButton from 'shell/StitchButton'

const usersStore = useUsersStore()
const toast = useToastStore()

const showDrawer = ref(false)
const selectedUser = ref<KcUser | null>(null)

const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  confirmText: '',
  type: 'info' as 'info' | 'danger',
  action: null as (() => Promise<void>) | null,
})

onMounted(() => {
  usersStore.fetchUsers()
})

const openCreateDrawer = () => {
  selectedUser.value = null
  showDrawer.value = true
}

const openEditDrawer = (user: KcUser) => {
  selectedUser.value = user
  showDrawer.value = true
}

const handleSave = async (payload: UserPayload) => {
  try {
    if (selectedUser.value) {
      await usersStore.updateUser(selectedUser.value.id, payload)
      toast.success('Member updated successfully')
    } else {
      await usersStore.createUser(payload)
      toast.success('Member invited successfully')
    }
    showDrawer.value = false
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  }
}

const handleDisable = (user: KcUser) => {
  confirmDialog.value = {
    show: true,
    title: 'Disable Member',
    message: `Are you sure you want to disable ${user.first_name} ${user.last_name}? They will lose access to all products.`,
    confirmText: 'Disable',
    type: 'danger',
    action: async () => {
      await usersStore.toggleUserStatus(user.id, false)
    },
  }
}

const handleEnable = async (user: KcUser) => {
  try {
    await usersStore.toggleUserStatus(user.id, true)
    toast.success(`${user.first_name} ${user.last_name} enabled`)
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  }
}

const handleResetMfa = (user: KcUser) => {
  confirmDialog.value = {
    show: true,
    title: 'Reset MFA',
    message: `Reset MFA for ${user.first_name} ${user.last_name}? They will need to re-enroll on next login.`,
    confirmText: 'Reset MFA',
    type: 'danger',
    action: async () => {
      await usersStore.resetMfa(user.id)
    },
  }
}

const handleConfirm = async () => {
  if (confirmDialog.value.action) {
    try {
      await confirmDialog.value.action()
      confirmDialog.value.show = false
      toast.success(`${confirmDialog.value.title} completed`)
    } catch (err: any) {
      confirmDialog.value.show = false
      toast.error(extractErrorMessage(err))
    }
  }
}
</script>

<template>
  <div class="flex flex-col gap-xl">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-md">
      <div>
        <h1 class="page-title">Access Management</h1>
        <p class="page-subtitle">Control user access and granular permissions across your tenant environment</p>
      </div>
      <div class="flex items-center gap-md">
        <!-- Stats badges -->
        <span class="stats-badge stats-badge--active">
          {{ usersStore.activeCount() }} Active
        </span>
        <span class="stats-badge stats-badge--pending">
          {{ usersStore.pendingCount() }} Pending
        </span>
        <StitchButton icon="person_add" @click="openCreateDrawer">
          Invite Member
        </StitchButton>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="flex border-b border-outline-variant gap-0 -mt-sm">
      <button class="tab-item tab-item--active">Members</button>
      <button class="tab-item tab-item--disabled" disabled>Roles</button>
      <button class="tab-item tab-item--disabled" disabled>API Keys</button>
    </div>

    <!-- 12-column grid: table (8 cols) + Role Insights sidebar (4 cols) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-lg">
      <!-- Table column -->
      <div class="lg:col-span-8 bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden shadow-sm">
        <UserTable
          :users="usersStore.users"
          :is-loading="usersStore.isLoading"
          @edit="openEditDrawer"
          @disable="handleDisable"
          @enable="handleEnable"
          @reset-mfa="handleResetMfa"
        />
      </div>

      <!-- Role Insights sidebar -->
      <div class="lg:col-span-4">
        <div class="bg-surface-container-lowest rounded-xl border border-outline-variant p-lg">
          <h3 class="sidebar-title">Role Insights</h3>
          <p class="sidebar-subtitle mb-lg">Role definitions for this tenant</p>

          <div class="flex flex-col gap-sm">
            <!-- TenantOwner -->
            <div class="role-insight-card">
              <div class="flex items-center gap-sm mb-xs">
                <span class="role-dot bg-primary/70"></span>
                <span class="text-sm font-semibold text-on-surface">TenantOwner</span>
              </div>
              <p class="text-xs text-on-surface-variant">Full administrative control over the tenant and all its members.</p>
            </div>

            <!-- TenantAdmin -->
            <div class="role-insight-card">
              <div class="flex items-center gap-sm mb-xs">
                <span class="role-dot bg-primary/50"></span>
                <span class="text-sm font-semibold text-on-surface">TenantAdmin</span>
              </div>
              <p class="text-xs text-on-surface-variant">Can manage users, settings, and product access assignments.</p>
            </div>

            <!-- TenantViewer -->
            <div class="role-insight-card">
              <div class="flex items-center gap-sm mb-xs">
                <span class="role-dot bg-outline-variant"></span>
                <span class="text-sm font-semibold text-on-surface">TenantViewer</span>
              </div>
              <p class="text-xs text-on-surface-variant">Read-only access to tenant data and member listing.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Drawer -->
    <UserDrawer
      :show="showDrawer"
      :user="selectedUser"
      @close="showDrawer = false"
      @save="handleSave"
    />

    <!-- Confirm Dialog -->
    <ConfirmDialog
      v-bind="confirmDialog"
      @confirm="handleConfirm"
      @cancel="confirmDialog.show = false"
    />
  </div>
</template>

<style scoped>
.page-title {
  font-size: 2rem;
  font-weight: 600;
  line-height: 2.5rem;
  letter-spacing: -0.01em;
  color: var(--on-surface);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 1rem;
  font-weight: 400;
  color: var(--on-surface-variant);
  margin: 0;
}

.stats-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.stats-badge--active {
  background-color: #dcfce7;
  color: #166534;
}

.stats-badge--pending {
  background-color: var(--surface-container-high);
  color: var(--on-surface-variant);
}

[data-theme='dark'] .stats-badge--active {
  background-color: rgba(52, 168, 83, 0.15);
  color: #86efac;
}

.tab-item {
  padding: 10px 16px;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  background: transparent;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s;
}

.tab-item--active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  font-weight: 600;
}

.tab-item--disabled {
  color: var(--on-surface-variant);
  opacity: 0.5;
  cursor: not-allowed;
}

.sidebar-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--on-surface);
  margin: 0 0 2px 0;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  color: var(--on-surface-variant);
  margin: 0;
}

.role-insight-card {
  padding: 12px;
  border: 1px solid var(--outline-variant);
  border-radius: 0.75rem;
  background: var(--surface-container-low);
}

.role-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 9999px;
  flex-shrink: 0;
}
</style>
>
