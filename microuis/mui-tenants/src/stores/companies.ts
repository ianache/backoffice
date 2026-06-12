import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as companiesService from '../services/companies'
import type { Company, CompanyPayload, CompanyUpdatePayload } from '../services/companies'

export const useCompaniesStore = defineStore('companies', () => {
  const companies = ref<Company[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCompanies(statusFilter = '') {
    isLoading.value = true
    try {
      companies.value = await companiesService.listCompanies(statusFilter)
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createCompany(payload: CompanyPayload) {
    try {
      const created = await companiesService.createCompany(payload)
      companies.value.unshift(created)
      error.value = null
      return created
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  async function updateCompany(id: string, payload: CompanyUpdatePayload) {
    try {
      const updated = await companiesService.updateCompany(id, payload)
      const index = companies.value.findIndex(c => c.id === id)
      if (index !== -1) {
        companies.value[index] = updated
      }
      error.value = null
      return updated
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  return { companies, isLoading, error, fetchCompanies, createCompany, updateCompany }
})
