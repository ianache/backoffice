<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProductsStore } from '../stores/products'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import type { Product, ProductPayload } from '../services/products'
import ProductTable from '../components/products/ProductTable.vue'
import ProductDrawer from '../components/products/ProductDrawer.vue'
import StitchButton from 'shell/StitchButton'

const productsStore = useProductsStore()
const toast = useToastStore()

const showDrawer = ref(false)
const selectedProduct = ref<Product | null>(null)

const recentChanges = computed(() =>
  [...productsStore.products]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 3)
)

const formatRelative = (iso: string) => {
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 60) return `${Math.max(mins, 1)} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

onMounted(() => {
  productsStore.fetchProducts()
})

const openCreateDrawer = () => {
  selectedProduct.value = null
  showDrawer.value = true
}

const openEditDrawer = (product: Product) => {
  selectedProduct.value = product
  showDrawer.value = true
}

const handleSave = async (payload: ProductPayload) => {
  try {
    if (selectedProduct.value) {
      const { id, ...updatePayload } = payload
      await productsStore.updateProduct(selectedProduct.value.id, updatePayload)
      toast.success('Product updated successfully')
    } else {
      await productsStore.createProduct(payload)
      toast.success('Product created successfully')
    }
    showDrawer.value = false
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  }
}
</script>

<template>
  <div class="flex flex-col gap-lg">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-md">
      <div class="max-w-3xl">
        <h1 class="text-headline-lg font-semibold text-on-surface leading-tight tracking-tight">Product Management</h1>
        <p class="text-body-md text-on-surface-variant mt-1">Manage the catalog of products, their lifecycle, and cross-platform associations.</p>
      </div>
      <div class="flex items-center gap-md">
        <StitchButton icon="add" @click="openCreateDrawer">
          New Product
        </StitchButton>
      </div>
    </div>

    <!-- Main Grid: table (9) + insights sidebar (3) per Stitch design -->
    <div class="grid grid-cols-12 gap-lg">
      <!-- Table Area -->
      <div class="col-span-12 lg:col-span-9">
        <div class="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden shadow-sm">
          <ProductTable
            :products="productsStore.products"
            :loading="productsStore.isLoading"
            @edit="openEditDrawer"
          />
        </div>
      </div>

      <!-- Insights Sidebar -->
      <aside class="col-span-12 lg:col-span-3 flex flex-col gap-lg">
        <!-- Recent Changes (derived from real updated_at) -->
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg shadow-sm">
          <h3 class="text-label-md font-bold text-on-surface mb-lg">Recent Changes</h3>
          <div v-if="recentChanges.length" class="flex flex-col gap-md">
            <div v-for="(product, i) in recentChanges" :key="product.id" class="flex gap-md">
              <div class="relative">
                <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined text-sm">edit</span>
                </div>
                <div v-if="i < recentChanges.length - 1" class="absolute top-8 left-1/2 -translate-x-1/2 w-0.5 h-full bg-outline-variant/30"></div>
              </div>
              <div class="flex flex-col pb-4">
                <p class="text-xs text-on-surface font-bold">{{ product.name }} updated</p>
                <p class="text-[10px] text-secondary">{{ formatRelative(product.updated_at) }}</p>
              </div>
            </div>
          </div>
          <p v-else class="text-xs text-on-surface-variant">No catalog activity yet.</p>
        </div>

        <!-- Promo Card (Stitch decorative) -->
        <div class="bg-primary-container rounded-xl p-lg text-on-primary-container shadow-lg relative overflow-hidden group">
          <div class="absolute -right-4 -bottom-4 opacity-10 rotate-12 transition-transform group-hover:scale-110 duration-500">
            <span class="material-symbols-outlined text-[120px]" style="font-variation-settings: 'FILL' 1">inventory_2</span>
          </div>
          <h4 class="text-label-md font-bold mb-2">Automate Lifecycle</h4>
          <p class="text-xs opacity-80 mb-lg leading-relaxed">Connect your CI/CD pipelines to automatically sync product versions with deployment states.</p>
        </div>
      </aside>
    </div>

    <!-- Create/Edit Drawer -->
    <ProductDrawer
      :show="showDrawer"
      :product="selectedProduct"
      @close="showDrawer = false"
      @save="handleSave"
    />
  </div>
</template>
