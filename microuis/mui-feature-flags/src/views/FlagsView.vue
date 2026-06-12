<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useFeatureFlagsStore } from '../stores/flags'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import type { FeatureFlag } from '../services/flags'
import FlagTable from '../components/flags/FlagTable.vue'
import FlagDrawer from '../components/flags/FlagDrawer.vue'
import ConfirmDialog from '../components/flags/ConfirmDialog.vue'
import StitchButton from 'shell/StitchButton'
import { useBoFlags } from 'shell/boFlags'
import { useFlagFilters } from '../composables/useFlagFilters'

const flagsStore = useFeatureFlagsStore()
const toast = useToastStore()
const { boFeatureCreate } = useBoFlags()

const { flags } = storeToRefs(flagsStore)
const { filters, filteredFlags, availableTags, hasActiveFilters, clearFilters } = useFlagFilters(flags)

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
      <StitchButton v-if="boFeatureCreate" icon="toggle_on" @click="openCreateDrawer">
        Create Flag
      </StitchButton>
    </div>

    <!-- Filter bar (FLT-01..05, client-side) -->
    <div class="flex flex-wrap items-center gap-sm">
      <select class="filter-select" v-model="filters.status">
        <option value="all">All Statuses</option>
        <option value="enabled">Enabled</option>
        <option value="disabled">Disabled</option>
      </select>
      <select class="filter-select" v-model="filters.tag">
        <option value="">Any Tags</option>
        <option v-for="t in availableTags" :key="t" :value="t">{{ t }}</option>
      </select>
      <select class="filter-select" v-model="filters.complexity">
        <option value="all">Complexity</option>
        <option value="complex">Complex</option>
        <option value="simple">Simple</option>
      </select>
      <select class="filter-select" v-model="filters.environment">
        <option value="">All Environments</option>
        <option value="production">production</option>
        <option value="staging">staging</option>
        <option value="development">development</option>
      </select>
      <select class="filter-select" v-model="filters.scopeTarget">
        <option value="">All Scopes</option>
        <option value="global">Global</option>
        <option value="tenant">Tenants</option>
        <option value="product">Products</option>
        <option value="company">Companies</option>
      </select>
      <button v-if="hasActiveFilters" class="clear-filters-btn" @click="clearFilters">
        <span class="material-symbols-outlined text-[16px]">close</span>
        Clear filters
      </button>
    </div>

    <!-- Data table card -->
    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden">
      <FlagTable
        :flags="filteredFlags"
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
  color: var(--on-surface);
  font-size: 0.875rem;
  font-family: var(--font-family-sans);
  cursor: pointer;
}

.clear-filters-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  color: var(--on-surface-variant);
  font-size: 0.875rem;
  font-family: var(--font-family-sans);
  cursor: pointer;
  border-radius: var(--rounded);
}

.clear-filters-btn:hover {
  color: var(--on-surface);
  background: var(--surface-container-low);
}
</style>
