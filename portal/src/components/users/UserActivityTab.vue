<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as usersService from '../../services/users'
import type { UserEventRecord } from '../../services/users'

const props = defineProps<{
  userId: string
}>()

const events = ref<UserEventRecord[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const ACTION_LABELS: Record<string, string> = {
  'user.created': 'User created',
  'user.updated': 'Profile updated',
  'user.enabled': 'Account enabled',
  'user.disabled': 'Account disabled',
  'user.roles_changed': 'Roles updated',
  'user.mfa_reset': 'MFA reset',
}

const actionLabel = (action: string): string => ACTION_LABELS[action] ?? action

const dotColor = (action: string): string => {
  if (action === 'user.created' || action === 'user.enabled') return 'bg-green-500'
  if (action === 'user.updated' || action === 'user.roles_changed') return 'bg-amber-500'
  if (action === 'user.disabled') return 'bg-red-500'
  if (action === 'user.mfa_reset') return 'bg-blue-500'
  return 'bg-outline-variant'
}

const formatTimestamp = (iso: string): string => {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const contextEntries = (context: Record<string, unknown> | null): [string, string][] => {
  if (!context) return []
  return Object.entries(context).map(([k, v]) => [k, String(v)])
}

onMounted(async () => {
  isLoading.value = true
  error.value = null
  try {
    const data = await usersService.listEvents(props.userId)
    // Newest first
    events.value = [...data].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="isLoading" class="flex flex-col items-center gap-3 py-10">
      <md-linear-progress indeterminate class="w-32"></md-linear-progress>
      <span class="text-sm text-on-surface-variant">Loading activity...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="py-6 text-center text-sm text-error">
      {{ error }}
    </div>

    <!-- Empty state -->
    <div v-else-if="events.length === 0" class="py-10 text-center text-sm text-on-surface-variant">
      No activity recorded yet.
    </div>

    <!-- Timeline -->
    <ol v-else class="relative border-l border-outline-variant ml-3">
      <li
        v-for="event in events"
        :key="event.id"
        class="mb-lg ml-lg"
      >
        <!-- Dot on the timeline -->
        <span
          :class="['timeline-dot', dotColor(event.action)]"
        ></span>

        <p class="font-medium text-sm text-on-surface">{{ actionLabel(event.action) }}</p>
        <p class="text-xs text-on-surface-variant mt-0.5">{{ formatTimestamp(event.created_at) }}</p>

        <!-- Context key-values -->
        <div v-if="contextEntries(event.context).length > 0" class="mt-xs">
          <p
            v-for="([key, val]) in contextEntries(event.context)"
            :key="key"
            class="text-xs text-on-surface-variant"
          >
            <span class="font-medium">{{ key }}:</span> {{ val }}
          </p>
        </div>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.timeline-dot {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 9999px;
  left: -5px;
  margin-top: 3px;
  border: 2px solid var(--surface-container-low);
}
</style>
