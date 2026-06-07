<script setup lang="ts">
import { ref, computed } from 'vue'
import type { KcUser } from '../../services/users'

const props = defineProps<{
  users: KcUser[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  edit: [user: KcUser]
  disable: [user: KcUser]
  enable: [user: KcUser]
  'reset-mfa': [user: KcUser]
}>()

type StatusFilter = 'all' | 'active' | 'inactive'
const activeFilter = ref<StatusFilter>('all')
const isCompact = ref(false)
const activeMenu = ref<string | null>(null)

const filteredUsers = computed(() => {
  if (activeFilter.value === 'all') return props.users
  if (activeFilter.value === 'active') return props.users.filter(u => u.enabled)
  return props.users.filter(u => !u.enabled)
})

const initials = (user: KcUser): string => {
  const first = user.first_name?.charAt(0) ?? ''
  const last = user.last_name?.charAt(0) ?? ''
  return (first + last).toUpperCase() || user.email.charAt(0).toUpperCase()
}

const roleBadgeClass = (role: string | null): string => {
  switch (role) {
    case 'TenantOwner':
    case 'TenantAdmin':
      return 'bg-primary/10 text-primary'
    case 'TenantViewer':
      return 'bg-outline-variant/40 text-on-surface-variant'
    case 'ProductManager':
    case 'ProductDeveloper':
    case 'ProductQA':
      return 'bg-secondary/10 text-secondary'
    default:
      return 'bg-outline-variant/40 text-on-surface-variant'
  }
}

const roleLabel = (role: string | null): string => role ?? 'No role'

const toggleMenu = (userId: string) => {
  activeMenu.value = activeMenu.value === userId ? null : userId
}
</script>

<template>
  <div class="flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="px-md py-sm flex flex-wrap items-center justify-between gap-md border-b border-outline-variant bg-surface-container-low/50 min-h-[52px]">
      <div class="flex items-center gap-lg">
        <h2 class="text-sm font-medium text-on-surface whitespace-nowrap">All Members</h2>
        <div class="flex items-center gap-xs bg-surface-container-lowest border border-outline-variant rounded-lg p-1">
          <button
            v-for="tab in (['all', 'active', 'inactive'] as StatusFilter[])"
            :key="tab"
            @click="activeFilter = tab"
            :class="[
              'px-md py-xs rounded-md text-xs transition-colors capitalize whitespace-nowrap',
              activeFilter === tab
                ? 'bg-surface-container-high text-primary font-bold'
                : 'text-secondary hover:text-on-surface font-medium'
            ]"
          >
            {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
          </button>
        </div>
      </div>
      <div class="flex items-center gap-xs shrink-0">
        <button
          @click="isCompact = !isCompact"
          class="p-sm hover:bg-surface-variant rounded-lg transition-colors"
          title="Toggle density"
        >
          <span class="material-symbols-outlined text-on-surface-variant icon-action">
            {{ isCompact ? 'density_small' : 'density_medium' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Data Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <colgroup>
          <col style="min-width: 240px" />
          <col style="width: 160px" />
          <col style="width: 120px" />
          <col style="width: 100px" />
        </colgroup>
        <thead>
          <tr class="bg-surface-container-low/30 border-b border-outline-variant">
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">User</th>
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Role</th>
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Status</th>
            <th :class="['px-lg table-col-header text-right', isCompact ? 'py-sm' : 'py-md']">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant">
          <!-- Loading state -->
          <tr v-if="isLoading">
            <td colspan="4" class="px-lg py-10 text-center text-on-surface-variant">
              <div class="flex flex-col items-center gap-3">
                <md-linear-progress indeterminate class="w-32"></md-linear-progress>
                <span class="text-sm">Loading members...</span>
              </div>
            </td>
          </tr>
          <!-- Empty state -->
          <tr v-else-if="filteredUsers.length === 0">
            <td colspan="4" class="px-lg py-10 text-center text-on-surface-variant text-sm">
              No members yet.
            </td>
          </tr>
          <!-- Data rows -->
          <tr
            v-for="user in filteredUsers"
            :key="user.id"
            class="hover:bg-surface-container-low transition-colors group"
          >
            <!-- User: avatar + name + email -->
            <td :class="['px-lg', isCompact ? 'py-sm' : 'py-md']">
              <div class="flex items-center gap-md">
                <div class="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-bold text-sm shrink-0">
                  {{ initials(user) }}
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-on-surface truncate">
                    {{ user.first_name }} {{ user.last_name }}
                  </p>
                  <p class="text-xs text-on-surface-variant truncate">{{ user.email }}</p>
                </div>
              </div>
            </td>
            <!-- Role badge -->
            <td :class="['px-lg', isCompact ? 'py-sm' : 'py-md']">
              <span :class="['role-badge', roleBadgeClass(user.tenant_role)]">
                {{ roleLabel(user.tenant_role) }}
              </span>
            </td>
            <!-- Status dot + label -->
            <td :class="['px-lg', isCompact ? 'py-sm' : 'py-md']">
              <div class="flex items-center gap-xs">
                <span
                  class="w-2 h-2 rounded-full shrink-0"
                  :class="user.enabled ? 'bg-green-500' : 'bg-neutral-400'"
                ></span>
                <span class="text-sm" :class="user.enabled ? 'text-green-700' : 'text-on-surface-variant'">
                  {{ user.enabled ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </td>
            <!-- Actions -->
            <td :class="['px-lg text-right', isCompact ? 'py-sm' : 'py-md']">
              <div class="flex items-center justify-end gap-xs">
                <button
                  @click="emit('edit', user)"
                  class="action-btn"
                  title="Manage access"
                >
                  <span class="material-symbols-outlined icon-action">edit</span>
                </button>
                <div class="relative">
                  <button
                    :id="`user-menu-anchor-${user.id}`"
                    @click="toggleMenu(user.id)"
                    class="action-btn-muted"
                    title="More actions"
                  >
                    <span class="material-symbols-outlined icon-action">more_vert</span>
                  </button>
                  <md-menu
                    :anchor="`user-menu-anchor-${user.id}`"
                    :open="activeMenu === user.id"
                    @closed="activeMenu = null"
                    quick
                    positioning="popover"
                  >
                    <md-menu-item v-if="user.enabled" @click="emit('disable', user); activeMenu = null">
                      <div slot="headline">Disable</div>
                      <md-icon slot="start">block</md-icon>
                    </md-menu-item>
                    <md-menu-item v-else @click="emit('enable', user); activeMenu = null">
                      <div slot="headline">Enable</div>
                      <md-icon slot="start">check_circle</md-icon>
                    </md-menu-item>
                    <md-divider></md-divider>
                    <md-menu-item @click="emit('reset-mfa', user); activeMenu = null">
                      <div slot="headline">Reset MFA</div>
                      <md-icon slot="start">security</md-icon>
                    </md-menu-item>
                  </md-menu>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer count -->
    <div class="px-md py-sm border-t border-outline-variant flex items-center justify-between bg-surface-container-low/50 min-h-[48px]">
      <p class="text-xs text-on-surface-variant">
        Showing {{ filteredUsers.length }} of {{ users.length }} members
      </p>
    </div>
  </div>
</template>

<style scoped>
.table-col-header {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  white-space: nowrap;
}

.icon-action {
  font-size: 20px;
  display: block;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.action-btn {
  padding: 6px;
  color: var(--secondary);
  border-radius: 8px;
  transition: color 0.15s, background-color 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
}

.action-btn:hover {
  color: var(--primary);
  background-color: color-mix(in srgb, var(--primary) 10%, transparent);
}

.action-btn:active {
  transform: scale(0.95);
}

.action-btn-muted {
  padding: 6px;
  color: var(--secondary);
  border-radius: 8px;
  transition: color 0.15s, background-color 0.15s;
  display: flex;
  align-items: center;
}

.action-btn-muted:hover {
  color: var(--on-surface);
  background-color: var(--surface-variant);
}
</style>
