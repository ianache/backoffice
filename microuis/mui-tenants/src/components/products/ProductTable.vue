<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Product } from '../../services/products'

type StatusFilter = 'all' | 'active' | 'inactive'

const props = defineProps<{
  products: Product[]
  loading?: boolean
}>()

const emit = defineEmits(['edit'])

const statusFilter = ref<StatusFilter>('all')

const filteredProducts = computed(() => {
  if (statusFilter.value === 'all') return props.products
  return props.products.filter(p => p.status === statusFilter.value)
})

const formatDate = (iso: string) => {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="px-md py-sm flex flex-wrap items-center justify-between gap-md border-b border-outline-variant bg-surface-container-low/50 min-h-[52px]">
      <div class="flex items-center gap-lg">
        <h2 class="text-title-md font-medium text-on-surface whitespace-nowrap">Product Catalog</h2>
        <div class="flex items-center gap-xs bg-surface-container-lowest border border-outline-variant rounded-lg p-1">
          <button
            v-for="tab in (['all', 'active', 'inactive'] as StatusFilter[])"
            :key="tab"
            @click="statusFilter = tab"
            :class="[
              'px-md py-1.5 rounded-md text-label-md transition-colors capitalize',
              statusFilter === tab
                ? 'bg-surface-container-high font-bold text-primary'
                : 'text-secondary hover:text-on-surface font-medium'
            ]"
          >
            {{ tab }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-surface-container-low border-b border-outline-variant">
            <th class="px-lg py-md table-col-header">Product Info</th>
            <th class="px-lg py-md table-col-header">Status &amp; Labels</th>
            <th class="px-lg py-md table-col-header">Created</th>
            <th class="px-lg py-md table-col-header">Last Updated</th>
            <th class="px-lg py-md table-col-header text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant">
          <tr
            v-for="product in filteredProducts"
            :key="product.id"
            class="hover:bg-surface-container-lowest transition-colors group cursor-pointer"
            @click="emit('edit', product)"
          >
            <!-- Product Info: slug + name + description (Stitch pattern) -->
            <td class="px-lg py-lg">
              <div class="flex flex-col">
                <span class="text-[10px] font-bold text-primary tracking-widest mb-1 uppercase">{{ product.id }}</span>
                <span class="text-label-md font-bold text-on-background group-hover:text-primary transition-colors">{{ product.name }}</span>
                <span v-if="product.description" class="text-xs text-secondary mt-1 max-w-[280px] truncate">{{ product.description }}</span>
              </div>
            </td>
            <!-- Status & Labels -->
            <td class="px-lg py-lg">
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-2">
                  <span :class="['flex h-2 w-2 rounded-full', product.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400']"></span>
                  <span :class="['text-label-sm capitalize', product.status === 'active' ? 'text-emerald-700 font-bold' : 'text-secondary']">{{ product.status }}</span>
                </div>
                <div v-if="product.labels.length" class="flex flex-wrap gap-xs">
                  <span
                    v-for="label in product.labels"
                    :key="label"
                    class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-tertiary-fixed-variant text-[10px] font-bold uppercase"
                  >
                    {{ label }}
                  </span>
                </div>
              </div>
            </td>
            <!-- Created -->
            <td class="px-lg py-lg text-body-md text-on-surface-variant font-mono tabular-nums">
              {{ formatDate(product.created_at) }}
            </td>
            <!-- Last Updated -->
            <td class="px-lg py-lg text-body-md text-on-surface-variant font-mono tabular-nums">
              {{ formatDate(product.updated_at) }}
            </td>
            <!-- Actions -->
            <td class="px-lg py-lg text-right">
              <button
                @click.stop="emit('edit', product)"
                class="p-sm text-secondary hover:text-primary hover:bg-primary-fixed rounded-lg transition-all active:scale-95"
                title="Edit Product"
              >
                <span class="material-symbols-outlined icon-action">edit</span>
              </button>
            </td>
          </tr>
          <tr v-if="!loading && filteredProducts.length === 0">
            <td colspan="5" class="px-lg py-xl text-center text-on-surface-variant text-body-md">
              No products found. Create your first product.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer -->
    <div class="p-md bg-surface flex items-center justify-between border-t border-outline-variant">
      <span class="text-label-sm text-secondary">Showing {{ filteredProducts.length }} of {{ products.length }} products</span>
    </div>
  </div>
</template>

<style scoped>
.table-col-header {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  white-space: nowrap;
}

.icon-action {
  font-size: 20px;
}
</style>
