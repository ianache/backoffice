<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from '../stores/toast'
import type { Segment, SegmentPayload } from '../services/flags'
import { listSegments, createSegment, updateSegment, deleteSegment } from '../services/flags'
import SegmentTable from '../components/flags/SegmentTable.vue'
import SegmentForm from '../components/flags/SegmentForm.vue'
import StitchButton from '../components/ui/StitchButton.vue'

const toast = useToastStore()

const segments = ref<Segment[]>([])
const loading = ref(false)
const showForm = ref(false)
const editingSegment = ref<Segment | null>(null)
const formRef = ref<InstanceType<typeof SegmentForm> | null>(null)

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
        <p class="page-subtitle">Define user segments for targeted feature flag evaluation</p>
      </div>
      <StitchButton icon="group_add" @click="openCreateForm">
        Create Segment
      </StitchButton>
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
        :segments="segments"
        :is-loading="loading"
        @edit="handleEdit"
        @delete="handleDelete"
      />
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
</style>
