<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import { useFeatureFlagsStore } from '../stores/flags'
import type { RuleSchema } from '../services/flags'
import RuleCard from '../components/flags/RuleCard.vue'
import RuleSimulator from '../components/flags/RuleSimulator.vue'
import StitchButton from 'shell/StitchButton'

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
    <div class="flex flex-col gap-sm md:flex-row md:items-center md:justify-between px-xl py-lg border-b border-outline-variant bg-surface flex-shrink-0">
      <div>
        <h2 class="font-headline-lg text-headline-lg text-on-surface flex items-center gap-md">
          <button type="button" @click="cancel" class="flex items-center gap-1 text-sm text-on-surface-variant hover:text-on-surface transition-colors">
            <span class="material-symbols-outlined text-base">arrow_back</span>
            Back
          </button>
          <span class="text-on-surface-variant">/</span>
          Rule Builder<span v-if="flag">: <span class="text-primary">{{ flag.name }}</span></span>
        </h2>
      </div>
      <!-- Save / Cancel -->
      <div class="flex items-center gap-md">
        <button type="button" @click="cancel"
          class="px-lg py-sm border border-outline-variant text-on-surface font-label-lg text-label-lg rounded-lg hover:bg-surface-container-low transition-all">
          Cancel
        </button>
        <StitchButton icon="save" :disabled="isSaving" @click="saveChanges">
          {{ isSaving ? 'Saving…' : 'Save Changes' }}
        </StitchButton>
      </div>
    </div>

    <!-- Main content: 12-col grid -->
    <div class="flex-grow px-xl py-lg grid grid-cols-12 gap-xl overflow-auto">
      <!-- Left Column: Rule Editor (8 cols) -->
      <div class="col-span-12 lg:col-span-8 space-y-lg">
        <!-- Environment Selector (decorative) -->
        <div class="flex items-center gap-md border-b border-outline-variant pb-xs">
          <button type="button"
            class="px-md py-sm font-label-lg text-label-lg flex items-center gap-sm border-b-2 border-primary text-primary">
            <span class="w-2 h-2 rounded-full bg-red-500"></span> Production
          </button>
          <button type="button"
            class="px-md py-sm font-label-lg text-label-lg flex items-center gap-sm text-on-surface-variant hover:bg-surface-container-low rounded-t-lg transition-colors">
            <span class="w-2 h-2 rounded-full bg-amber-500"></span> Staging
          </button>
          <button type="button"
            class="px-md py-sm font-label-lg text-label-lg flex items-center gap-sm text-on-surface-variant hover:bg-surface-container-low rounded-t-lg transition-colors">
            <span class="w-2 h-2 rounded-full bg-gray-400"></span> Development
          </button>
        </div>

        <!-- Rule Blocks Canvas -->
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg space-y-gutter relative overflow-hidden">
          <!-- Dotted grid background (decorative) -->
          <div class="absolute inset-0 opacity-[0.03] pointer-events-none"
            style="background-image: radial-gradient(#005bbf 0.5px, transparent 0.5px); background-size: 20px 20px;">
          </div>

          <!-- Rollout slider -->
          <div class="relative z-10 flex items-center gap-md bg-white rounded-lg border border-outline-variant px-md py-md">
            <span class="font-label-lg text-label-lg text-on-surface whitespace-nowrap">Rollout</span>
            <input type="range" min="0" max="100" v-model.number="localRollout"
              class="flex-1 accent-primary h-2 cursor-pointer" />
            <span class="font-label-lg text-label-lg font-bold text-primary w-10 text-right">{{ localRollout }}%</span>
          </div>

          <!-- Draggable rule cards list -->
          <draggable
            v-model="localRules"
            item-key="_id"
            handle=".drag-handle"
            :animation="200"
            ghost-class="rule-card--ghost"
            class="relative z-10 space-y-gutter"
          >
            <template #item="{ element, index }">
              <div>
                <!-- AND connector between cards (not before first) -->
                <div v-if="index > 0" class="flex justify-center relative -my-2 z-20 pointer-events-none">
                  <div class="w-px h-12 bg-outline-variant"></div>
                  <div class="absolute top-1/2 -translate-y-1/2 bg-white px-md py-xs rounded-full border border-outline-variant shadow-sm font-label-lg text-label-lg text-primary font-bold select-none">
                    AND
                  </div>
                </div>
                <RuleCard
                  :rule="element"
                  :index="index"
                  mode="flag"
                  @update="updateRule(index, $event)"
                  @delete="deleteRule(index)"
                />
              </div>
            </template>
          </draggable>

          <!-- Add New Logic Block button -->
          <button type="button" @click="addRule"
            class="relative z-10 w-full border-2 border-dashed border-outline-variant rounded-lg p-md flex items-center justify-center gap-md text-on-surface-variant font-label-lg text-label-lg hover:bg-surface-container-low hover:border-primary transition-all group">
            <span class="material-symbols-outlined group-hover:text-primary" data-icon="add_circle">add_circle</span>
            Add New Logic Block
          </button>

          <!-- Empty state when no rules -->
          <div v-if="localRules.length === 0" class="relative z-10 text-center text-sm text-on-surface-variant italic py-8 opacity-50">
            No rules yet. Add a logic block to define evaluation conditions.
          </div>
        </div>
      </div>

      <!-- Right Column: Simulator sidebar (4 cols) -->
      <div class="col-span-12 lg:col-span-4 space-y-lg">
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
