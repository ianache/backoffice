<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import { useFeatureFlagsStore } from '../stores/flags'
import type { RuleSchema } from '../services/flags'
import RuleCard from '../components/flags/RuleCard.vue'
import RuleSimulator from '../components/flags/RuleSimulator.vue'

interface RuleLocal extends RuleSchema {
  _id: string
}

const route = useRoute()
const router = useRouter()
const store = useFeatureFlagsStore()

const flagId = computed(() => Number(route.params.id))
const flag = computed(() => store.flags.find(f => f.id === flagId.value) ?? null)

const localRules = ref<RuleLocal[]>([])
const localRollout = ref(0)
const isSaving = ref(false)

onMounted(async () => {
  if (store.flags.length === 0) await store.fetchFlags()
  if (flag.value) {
    localRules.value = flag.value.rules.map(r => ({ ...r, _id: crypto.randomUUID() }))
    localRollout.value = flag.value.rollout ?? 0
  } else {
    // Flag not found — redirect back
    router.push({ name: 'flags' })
  }
})

function addRule(): void {
  localRules.value.push({
    _id: crypto.randomUUID(),
    attribute: '',
    operator: 'equals',
    value: '',
    result: true,
  })
}

function updateRule(index: number, updated: RuleLocal): void {
  // Use splice to mutate in place (not full replacement) — avoids vuedraggable reactivity pitfall
  localRules.value.splice(index, 1, updated)
}

function deleteRule(index: number): void {
  localRules.value.splice(index, 1)
}

async function saveChanges(): Promise<void> {
  isSaving.value = true
  try {
    const rules = localRules.value.map(({ _id, ...r }) => r)  // strip _id before PATCH
    await store.updateFlag(flagId.value, {
      rules,
      rollout: localRollout.value,
      complex: rules.length > 0,  // auto-set complex=true when rules exist
    })
    router.push({ name: 'flags' })
  } finally {
    isSaving.value = false
  }
}

function cancel(): void {
  router.push({ name: 'flags' })
}
</script>

<template>
  <div class="rule-builder-page flex flex-col h-full">
    <!-- Page header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-outline-variant bg-surface flex-shrink-0">
      <div class="flex items-center gap-3">
        <button type="button" @click="cancel" class="flex items-center gap-1 text-sm text-on-surface-variant hover:text-on-surface transition-colors">
          <span class="material-symbols-outlined text-base">arrow_back</span>
          Back
        </button>
        <span class="text-on-surface-variant">/</span>
        <h1 class="text-base font-semibold text-on-surface">Rule Builder</h1>
        <span v-if="flag" class="text-sm text-on-surface-variant">— {{ flag.name }}</span>
      </div>
      <!-- Environment tabs: decorative only -->
      <div class="flex items-center gap-1 bg-surface-container rounded-lg p-1">
        <button v-for="env in ['Production', 'Staging', 'Development']" :key="env"
          :class="['px-3 py-1 rounded text-xs font-medium transition-colors', env === 'Production' ? 'bg-surface text-on-surface shadow-sm' : 'text-on-surface-variant hover:text-on-surface']"
          type="button">
          {{ env }}
        </button>
      </div>
      <!-- Save / Cancel -->
      <div class="flex items-center gap-2">
        <button type="button" @click="cancel" class="px-4 py-2 text-sm text-on-surface-variant hover:text-on-surface transition-colors">
          Cancel
        </button>
        <button type="button" @click="saveChanges" :disabled="isSaving"
          class="px-4 py-2 bg-primary text-on-primary text-sm font-medium rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center gap-2">
          <span v-if="isSaving" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
          Save Changes
        </button>
      </div>
    </div>

    <!-- Main content: 12-col grid -->
    <div class="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
      <!-- Left: Rule canvas (8 cols) -->
      <div class="col-span-8 flex flex-col overflow-auto border-r border-outline-variant relative">
        <!-- Dotted grid background (decorative) -->
        <div class="absolute inset-0 pointer-events-none opacity-[0.03]"
          style="background-image: radial-gradient(var(--primary) 0.5px, transparent 0.5px); background-size: 20px 20px;">
        </div>
        <!-- Canvas content -->
        <div class="relative z-10 px-8 py-6 flex flex-col gap-0">
          <!-- Rollout slider -->
          <div class="mb-6 flex items-center gap-4 bg-surface-container-lowest rounded-xl border border-outline-variant px-5 py-4">
            <span class="text-sm font-medium text-on-surface whitespace-nowrap">Rollout</span>
            <input type="range" min="0" max="100" v-model.number="localRollout"
              class="flex-1 accent-primary h-2 cursor-pointer" />
            <span class="text-sm font-semibold text-primary w-10 text-right">{{ localRollout }}%</span>
          </div>

          <!-- Draggable rule cards list -->
          <draggable
            v-model="localRules"
            item-key="_id"
            handle=".drag-handle"
            :animation="200"
            ghost-class="rule-card--ghost"
          >
            <template #item="{ element, index }">
              <div>
                <!-- AND connector between cards (not before first) -->
                <div v-if="index > 0" class="flex justify-center items-center relative my-1 pointer-events-none">
                  <div class="w-px h-6 bg-outline-variant"></div>
                  <div class="absolute bg-surface-container-lowest px-3 py-0.5 rounded-full border border-outline-variant text-xs font-bold text-primary select-none">
                    AND
                  </div>
                </div>
                <RuleCard
                  :rule="element"
                  :index="index"
                  @update="updateRule(index, $event)"
                  @delete="deleteRule(index)"
                />
              </div>
            </template>
          </draggable>

          <!-- Add New Logic Block button -->
          <button type="button" @click="addRule"
            class="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 border-dashed border-outline-variant text-sm text-on-surface-variant hover:border-primary hover:text-primary transition-colors group">
            <span class="material-symbols-outlined text-base group-hover:text-primary">add_circle</span>
            Add New Logic Block
          </button>

          <!-- Empty state when no rules -->
          <div v-if="localRules.length === 0" class="mt-6 text-center text-sm text-on-surface-variant italic py-8 opacity-50">
            No rules yet. Add a logic block to define evaluation conditions.
          </div>
        </div>
      </div>

      <!-- Right: Simulator sidebar (4 cols) -->
      <div class="col-span-4 p-4 overflow-auto bg-surface-container-low">
        <RuleSimulator :rules="localRules" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.rule-card--ghost {
  opacity: 0.4;
  background-color: var(--primary-container);
}
</style>
