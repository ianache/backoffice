import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as productsService from '../services/products'
import type { Product, ProductPayload, ProductUpdatePayload } from '../services/products'

export const useProductsStore = defineStore('products', () => {
  const products = ref<Product[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProducts(statusFilter = '') {
    isLoading.value = true
    try {
      products.value = await productsService.listProducts(statusFilter)
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createProduct(payload: ProductPayload) {
    const created = await productsService.createProduct(payload)
    products.value.unshift(created)
    return created
  }

  async function updateProduct(id: string, payload: ProductUpdatePayload) {
    const updated = await productsService.updateProduct(id, payload)
    const index = products.value.findIndex(p => p.id === id)
    if (index !== -1) {
      products.value[index] = updated
    }
    return updated
  }

  return { products, isLoading, error, fetchProducts, createProduct, updateProduct }
})
