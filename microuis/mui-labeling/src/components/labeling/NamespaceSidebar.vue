<template>
  <section class="col-span-3 border-r border-outline-variant bg-surface-container-lowest flex flex-col overflow-hidden">
    <div class="p-md border-b border-outline-variant flex items-center justify-between">
      <h3 class="font-title-lg text-on-surface flex items-center gap-xs">
        <span class="material-symbols-outlined text-primary">folder_open</span>
        <span>Namespaces</span>
      </h3>
      <button
        @click="openAddModal"
        class="flex items-center gap-xs px-sm py-1 bg-primary text-on-primary hover:bg-primary-container rounded font-title-md text-xs transition-colors shadow"
      >
        <span class="material-symbols-outlined text-xs">add</span>
        <span>Namespace</span>
      </button>
    </div>

    <!-- Lista de namespaces -->
    <div id="namespacesList" class="flex-1 overflow-y-auto custom-scrollbar p-sm space-y-1">
      <div
        v-for="ns in namespaces"
        :key="ns.id"
        @click="selectNamespace(ns.id)"
        :class="[
          'flex justify-between items-center p-md cursor-pointer transition-all rounded-lg border',
          state.activeNamespace === ns.id
            ? 'bg-primary/10 border-primary/20 text-primary'
            : 'bg-surface-container-lowest border-outline-variant hover:bg-surface-container-low text-on-surface',
        ]"
      >
        <div class="flex flex-col gap-xs overflow-hidden">
          <span class="font-bold text-sm truncate">{{ ns.id }}</span>
          <span class="text-[10px] text-on-surface-variant uppercase tracking-wider">
            {{ ns.strategy === 'eager' ? 'CRITICAL / EAGER' : 'LAZY LOADING' }}
          </span>
        </div>
      </div>
      <div v-if="!loading && namespaces.length === 0" class="p-md text-xs text-on-surface-variant italic text-center">
        No hay namespaces. Crea el primero.
      </div>
    </div>

    <!-- Card Informativo al Pie -->
    <div class="p-md bg-surface-container-low border-t border-outline-variant">
      <div class="flex items-start gap-sm">
        <span class="material-symbols-outlined text-primary mt-0.5">info</span>
        <div>
          <h4 class="text-xs font-bold text-on-surface">Estrategia de Hydration</h4>
          <p class="text-[11px] text-on-surface-variant leading-relaxed mt-1">
            Namespaces <b>Eager</b> se cargan en el bootstrap principal. Los <b>Lazy</b> se descargan bajo demanda (prefetching).
          </p>
        </div>
      </div>
    </div>

    <!-- MODAL: Add Namespace -->
    <div v-if="showAddModal" class="fixed inset-0 z-[60] flex items-center justify-center">
      <div class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="closeAddModal"></div>
      <div class="relative bg-surface w-[480px] rounded-xl shadow-2xl p-lg flex flex-col gap-md border border-outline-variant text-on-surface">
        <div class="flex items-center justify-between border-b border-outline-variant pb-sm">
          <h3 class="font-headline-md">Crear Nuevo Namespace</h3>
          <button @click="closeAddModal" class="p-1 hover:bg-surface-container-high rounded-full">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="space-y-sm">
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant">Identificador (ID)</label>
            <input
              v-model="newNamespace.id"
              type="text"
              class="w-full bg-surface-container border border-outline-variant rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface"
              placeholder="ej: page_dashboard_profile"
            />
            <p v-if="idError" class="text-[11px] text-error mt-1">{{ idError }}</p>
          </div>
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant">Estrategia de Carga</label>
            <select
              v-model="newNamespace.strategy"
              class="w-full bg-surface-container border border-outline-variant rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface"
            >
              <option value="lazy">Lazy Loading (Carga diferida bajo demanda)</option>
              <option value="eager">Eager Loading (Carga crítica al iniciar)</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant">Descripción</label>
            <textarea
              v-model="newNamespace.description"
              rows="2"
              class="w-full bg-surface-container border border-outline-variant rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface"
              placeholder="Describe brevemente el alcance de este namespace..."
            ></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-md pt-sm border-t border-outline-variant">
          <button @click="closeAddModal" class="px-md py-sm border border-outline rounded-lg text-sm hover:bg-surface-container-high transition-colors">
            Cancelar
          </button>
          <button @click="saveNamespace" :disabled="saving" class="px-md py-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg text-sm transition-colors disabled:opacity-50">
            Crear Namespace
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import { listNamespaces, createNamespace, type Namespace, type NamespacePayload } from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const state = useLabelingState()
const toast = useToastStore()

const namespaces = ref<Namespace[]>([])
const loading = ref(false)

const showAddModal = ref(false)
const saving = ref(false)
const idError = ref('')

const newNamespace = reactive<NamespacePayload>({
  id: '',
  strategy: 'lazy',
  description: '',
})

const NAMESPACE_ID_RE = /^[a-z0-9_]{1,100}$/

onMounted(fetchNamespaces)

// Re-fetch whenever the workspace context changes (RF-01 -> RF-02)
watch(() => state.workspaceContext, fetchNamespaces, { deep: true })

async function fetchNamespaces() {
  loading.value = true
  try {
    namespaces.value = await listNamespaces()
    // Seed `common` namespace appears first/highlighted as the default
    // activeNamespace on initial load if no namespace is yet selected.
    if (!state.activeNamespace && namespaces.value.length > 0) {
      const common = namespaces.value.find((ns) => ns.id === 'common')
      state.activeNamespace = (common ?? namespaces.value[0]).id
    }
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  } finally {
    loading.value = false
  }
}

function selectNamespace(id: string) {
  state.activeNamespace = id
  state.selectedKey = null
}

function openAddModal() {
  newNamespace.id = ''
  newNamespace.strategy = 'lazy'
  newNamespace.description = ''
  idError.value = ''
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

async function saveNamespace() {
  idError.value = ''

  if (!newNamespace.id) {
    idError.value = 'El identificador es requerido'
    return
  }
  if (!NAMESPACE_ID_RE.test(newNamespace.id)) {
    idError.value = 'Solo minúsculas, números y guion bajo (máx. 100 caracteres)'
    return
  }

  saving.value = true
  try {
    await createNamespace({
      id: newNamespace.id,
      strategy: newNamespace.strategy,
      description: newNamespace.description,
    })
    toast.success(`Namespace '${newNamespace.id}' creado con éxito.`)
    showAddModal.value = false
    await fetchNamespaces()
  } catch (err: any) {
    if (err?.response?.status === 409) {
      idError.value = 'Namespace ID already exists'
    } else {
      toast.error(extractErrorMessage(err))
    }
  } finally {
    saving.value = false
  }
}
</script>
