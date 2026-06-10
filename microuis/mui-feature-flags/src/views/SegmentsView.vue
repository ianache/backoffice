<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import type { Segment, SegmentPayload } from '../services/flags'
import { listSegments, createSegment, updateSegment, deleteSegment } from '../services/flags'
import SegmentTable from '../components/flags/SegmentTable.vue'
import SegmentForm from '../components/flags/SegmentForm.vue'
import StitchButton from 'shell/StitchButton'

const toast = useToastStore()

const segments = ref<Segment[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingSegment = ref<Segment | null>(null)
const formRef = ref<InstanceType<typeof SegmentForm> | null>(null)

// Filters (SEG-04 / SEG-05)
const showOrphansOnly = ref(false)
const typeFilter = ref<'all' | 'manual' | 'rule_based'>('all')

const filteredSegments = computed(() => {
  let result = segments.value
  if (showOrphansOnly.value) result = result.filter(s => s.flag_count === 0)
  if (typeFilter.value !== 'all') result = result.filter(s => (s.type ?? 'manual') === typeFilter.value)
  return result
})

const orphanCount = computed(() => segments.value.filter(s => s.flag_count === 0).length)

function reviewOrphans(): void {
  showOrphansOnly.value = true
  typeFilter.value = 'all'
}

async function loadSegments(): Promise<void> {
  loading.value = true
  try {
    segments.value = await listSegments()
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    loading.value = false
  }
}

onMounted(loadSegments)

function handleEdit(segment: Segment): void {
  editingSegment.value = segment
  showForm.value = true
}

async function handleDelete(segment: Segment): Promise<void> {
  try {
    await deleteSegment(segment.id)
    await loadSegments()
    toast.success(`Segment "${segment.name}" deleted`)
  } catch (err) {
    toast.error(extractErrorMessage(err))
  }
}

async function handleSave(payload: SegmentPayload): Promise<void> {
  try {
    if (editingSegment.value) {
      await updateSegment(editingSegment.value.id, payload)
      toast.success('Segment updated successfully')
    } else {
      await createSegment(payload)
      toast.success('Segment created successfully')
    }
    showForm.value = false
    editingSegment.value = null
    formRef.value?.reset()
    await loadSegments()
  } catch (err) {
    toast.error(extractErrorMessage(err))
  }
}

function handleCancel(): void {
  showForm.value = false
  editingSegment.value = null
}

function openCreateForm(): void {
  editingSegment.value = null
  showForm.value = true
}
</script>

<template>
  <div class="flex flex-col gap-xl">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-md">
      <div>
        <h1 class="page-title">Segments</h1>
        <p class="page-subtitle">Target specific user groups by defining reusable logical blocks</p>
      </div>
      <StitchButton icon="group_add" @click="openCreateForm">
        Create Segment
      </StitchButton>
    </div>

    <!-- Filters Bar -->
    <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex flex-wrap items-center gap-md shadow-sm">
      <label class="form-label mb-0">Type:</label>
      <select
        v-model="typeFilter"
        class="bg-surface-container-low border border-outline-variant rounded-lg py-2 px-md text-body-md text-on-surface-variant outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="all">All Types</option>
        <option value="manual">Manual</option>
        <option value="rule_based">Rule-based</option>
      </select>

      <label v-if="showOrphansOnly" class="flex items-center gap-xs text-label-md text-on-surface-variant">
        <span class="rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 px-2 py-0.5 text-xs font-medium">
          Showing orphans only
        </span>
        <button type="button" class="text-primary hover:underline" @click="showOrphansOnly = false">
          Clear
        </button>
      </label>
    </div>

    <!-- Inline form panel -->
    <SegmentForm
      v-if="showForm"
      ref="formRef"
      :segment="editingSegment ?? undefined"
      @save="handleSave"
      @cancel="handleCancel"
    />

    <!-- Data table card -->
    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden">
      <SegmentTable
        :segments="filteredSegments"
        :is-loading="loading"
        @edit="handleEdit"
        @delete="handleDelete"
      />
    </div>

    <!-- Bento Info Section -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-lg">
      <div class="md:col-span-2 bg-primary-container rounded-2xl p-xl text-on-primary shadow-lg relative overflow-hidden">
        <div class="relative z-10">
          <h2 class="font-headline-md text-headline-md mb-md">Segment Insights</h2>
          <p class="font-body-lg text-body-lg opacity-90 max-w-lg">
            {{ segments.length }} segment{{ segments.length !== 1 ? 's' : '' }} defined,
            referenced by {{ segments.reduce((sum, s) => sum + s.flag_count, 0) }} flag association{{ segments.reduce((sum, s) => sum + s.flag_count, 0) !== 1 ? 's' : '' }} in total.
          </p>
        </div>
      </div>
      <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-xl shadow-sm flex flex-col justify-center">
        <div class="flex items-center gap-md mb-md">
          <div class="w-12 h-12 rounded-full bg-error-container flex items-center justify-center text-error">
            <span class="material-symbols-outlined text-[28px]">warning</span>
          </div>
          <h3 class="font-title-lg text-title-lg text-on-surface">Orphan Segments</h3>
        </div>
        <p class="font-body-md text-body-md text-on-surface-variant mb-md">
          {{ orphanCount }} segment{{ orphanCount !== 1 ? 's' : '' }} {{ orphanCount !== 1 ? 'are' : 'is' }} currently not used by any feature flags and could be deleted to clean up.
        </p>
        <a
          class="text-primary font-bold text-label-md hover:underline flex items-center gap-1 cursor-pointer"
          @click="reviewOrphans"
        >
          Review segments <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
        </a>
      </div>
    </div>
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

.form-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--on-surface-variant);
}
</style>
