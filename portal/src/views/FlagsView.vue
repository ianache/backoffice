<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFeatureFlagsStore } from '../stores/flags'
import { useToastStore, extractErrorMessage } from '../stores/toast'
import type { FeatureFlag } from '../services/flags'
import FlagTable from '../components/flags/FlagTable.vue'
import FlagDrawer from '../components/flags/FlagDrawer.vue'
import ConfirmDialog from '../components/tenants/ConfirmDialog.vue'
import StitchButton from '../components/ui/StitchButton.vue'

const flagsStore = useFeatureFlagsStore()
const toast = useToastStore()

const showDrawer = ref(false)
const selectedFlag = ref<FeatureFlag | null>(null)

const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  confirmText: '',
  type: 'info' as 'info' | 'danger',
  action: null as (() => Promise<void>) | null,
})

onMounted(() => {
  flagsStore.fetchFlags()
})

const openCreateDrawer = () => {
  selectedFlag.value = null
  showDrawer.value = true
}

const openEditDrawer = (flag: FeatureFlag) => {
  selectedFlag.value = flag
  showDrawer.value = true
}

const handleSaved = (flag: FeatureFlag) => {
  const isEdit = !!selectedFlag.value
  toast.success(isEdit ? 'Feature flag updated successfully' : 'Feature flag created successfully')
  showDrawer.value = false
}

const handleDisable = (flag: FeatureFlag) => {
  confirmDialog.value = {
    show: true,
    title: 'Disable Feature Flag',
    message: `Are you sure you want to disable "${flag.name}"? This may impact live users relying on this flag.`,
    confirmText: 'Disable',
    type: 'danger',
    action: async () => {
      await flagsStore.toggleFlag(flag.id, false)
    },
  }
}

const handleEnable = async (flag: FeatureFlag) => {
  try {
    await flagsStore.toggleFlag(flag.id, true)
    toast.success(`"${flag.name}" enabled`)
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
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

const handleClone = (flag: FeatureFlag) => {
  toast.success(`Clone / Promote coming in Phase 5 (flag: ${flag.name})`)
}

const handlePromote = (flag: FeatureFlag) => {
  toast.success(`Promote coming in Phase 5 (flag: ${flag.name})`)
}
</script>

<template>
  <div class="flex flex-col gap-xl">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-md">
      <div>
        <h1 class="page-title">Feature Flags</h1>
        <p class="page-subtitle">Configure and manage feature flags across all hierarchy levels</p>
      </div>
      <StitchButton icon="toggle_on" @click="openCreateDrawer">
        Create Flag
      </StitchButton>
    </div>

    <!-- Filter bar (visual only, Phase 4) -->
    <div class="flex flex-wrap items-center gap-sm">
      <select class="filter-select" disabled>
        <option>All Statuses</option>
      </select>
      <select class="filter-select" disabled>
        <option>Any Tags</option>
      </select>
      <select class="filter-select" disabled>
        <option>Complexity</option>
      </select>
      <select class="filter-select" disabled>
        <option>Environment</option>
      </select>
    </div>

    <!-- Data table card -->
    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden">
      <FlagTable
        :flags="flagsStore.flags"
        :is-loading="flagsStore.isLoading"
        @edit="openEditDrawer"
        @clone="handleClone"
        @promote="handlePromote"
        @disable="handleDisable"
        @enable="handleEnable"
      />
    </div>

    <!-- Drawer -->
    <FlagDrawer
      :show="showDrawer"
      :flag="selectedFlag"
      @close="showDrawer = false"
      @saved="handleSaved"
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

.filter-select {
  padding: 6px 12px;
  border-radius: var(--rounded);
  border: 1px solid var(--outline-variant);
  background: var(--surface-container-low);
  color: var(--on-surface-variant);
  font-size: 0.875rem;
  font-family: var(--font-family-sans);
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
