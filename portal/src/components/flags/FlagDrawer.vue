<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FeatureFlag, FlagPayload } from '../../services/flags'
import { getSegmentsByFlag, addSegmentToFlag, removeSegmentFromFlag } from '../../services/flags'
import { useFeatureFlagsStore } from '../../stores/flags'
import FlagForm from './FlagForm.vue'
import StitchButton from '../ui/StitchButton.vue'

const props = defineProps<{
  show: boolean
  flag?: FeatureFlag | null
}>()

const emit = defineEmits<{
  close: []
  saved: [flag: FeatureFlag]
}>()

const flagsStore = useFeatureFlagsStore()

// Key to force FlagForm to remount when drawer opens with a new flag
const formKey = ref(0)
const flagFormRef = ref<InstanceType<typeof FlagForm> | null>(null)
const linkedSegmentIds = ref<number[]>([])

watch(
  () => props.show,
  async (isShowing) => {
    if (isShowing) {
      formKey.value++
      await flagsStore.fetchSegments()
      if (props.flag?.id) {
        const linked = await getSegmentsByFlag(props.flag.id)
        linkedSegmentIds.value = linked.map(s => s.id)
      } else {
        linkedSegmentIds.value = []
      }
    }
  }
)

async function handleSave(payload: FlagPayload) {
  try {
    // Capture both before any await — store update triggers props.flag change which resets selectedSegmentIds
    const selectedIds = [...(flagFormRef.value?.selectedSegmentIds ?? [])]
    const previousIds = [...linkedSegmentIds.value]
    let savedFlag: FeatureFlag
    if (props.flag) {
      savedFlag = await flagsStore.updateFlag(props.flag.id, payload)
    } else {
      savedFlag = await flagsStore.createFlag(payload)
    }
    const toAdd = selectedIds.filter(id => !previousIds.includes(id))
    const toRemove = previousIds.filter(id => !selectedIds.includes(id))
    for (const segmentId of toAdd) {
      await addSegmentToFlag(savedFlag.id, segmentId)
    }
    for (const segmentId of toRemove) {
      await removeSegmentFromFlag(savedFlag.id, segmentId)
    }
    emit('saved', savedFlag)
    emit('close')
  } catch (err: any) {
    console.error('Save flag failed:', err)
  }
}

function triggerSave() {
  flagFormRef.value?.handleSave()
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
        :aria-label="flag ? 'Edit Feature Flag' : 'Create Feature Flag'"
      >
        <div class="drawer-content" @click.stop>
          <!-- Drawer Header -->
          <div class="drawer-header">
            <div class="flex flex-col">
              <h2 class="drawer-title">
                {{ flag ? 'Edit Flag' : 'Create Feature Flag' }}
              </h2>
              <p class="drawer-subtitle">
                {{ flag ? `Editing: ${flag.name}` : 'Define a new feature flag' }}
              </p>
            </div>
            <button
              class="p-2 rounded-full hover:bg-surface-container-high transition-colors"
              @click="emit('close')"
              aria-label="Close drawer"
            >
              <span class="material-symbols-outlined text-[22px] text-on-surface-variant">close</span>
            </button>
          </div>

          <!-- Scrollable form body -->
          <div class="drawer-body">
            <FlagForm
              ref="flagFormRef"
              :key="formKey"
              :flag="flag"
              :segments="flagsStore.segments"
              :linked-segment-ids="linkedSegmentIds"
              @save="handleSave"
              @cancel="emit('close')"
            />
          </div>

          <div class="border-t border-outline-variant"></div>

          <!-- Footer -->
          <div class="drawer-footer">
            <StitchButton variant="text" @click="emit('close')">Cancel</StitchButton>
            <StitchButton variant="filled" @click="triggerSave">
              {{ flag ? 'Save Changes' : 'Create Flag' }}
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
  width: 480px;
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
  flex-shrink: 0;
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
  flex-shrink: 0;
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
