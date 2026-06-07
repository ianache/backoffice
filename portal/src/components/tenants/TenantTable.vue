<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Tenant } from '../../services/tenants'

const props = defineProps<{
  tenants: Tenant[]
  isLoading: boolean
}>()

const emit = defineEmits(['edit', 'delete', 'suspend', 'search'])

const searchQuery = ref('')

const handleSearch = () => {
  emit('search', searchQuery.value)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}
</script>

<template>
  <div class="table-container">
    <div class="table-header">
      <div class="search-bar">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search tenants..." 
          @input="handleSearch"
        />
      </div>
    </div>

    <div v-if="isLoading" class="loading">Loading tenants...</div>
    
    <table v-else class="tenant-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Status</th>
          <th>Country</th>
          <th>Products</th>
          <th>Created At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tenant in tenants" :key="tenant.id">
          <td>
            <div class="tenant-name">
              <img v-if="tenant.logo_url" :src="tenant.logo_url" class="mini-logo" />
              <span>{{ tenant.name }}</span>
            </div>
          </td>
          <td>
            <span :class="['status-badge', tenant.status]">
              {{ tenant.status }}
            </span>
          </td>
          <td>{{ tenant.country }}</td>
          <td>
            <div class="product-tags">
              <span v-for="p in tenant.products" :key="p" class="product-tag">
                {{ p }}
              </span>
            </div>
          </td>
          <td>{{ formatDate(tenant.created_at) }}</td>
          <td class="actions">
            <button class="action-btn" @click="emit('edit', tenant)">Edit</button>
            <button 
              v-if="tenant.status === 'active'" 
              class="action-btn suspend" 
              @click="emit('suspend', tenant)"
            >
              Suspend
            </button>
            <button class="action-btn delete" @click="emit('delete', tenant)">Delete</button>
          </td>
        </tr>
        <tr v-if="tenants.length === 0">
          <td colspan="6" class="no-data">No tenants found</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.table-header {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.search-bar input {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  width: 100%;
  max-width: 300px;
}

.tenant-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.tenant-table th {
  padding: 0.75rem 1rem;
  background: #f9fafb;
  font-weight: 600;
  color: #4b5563;
  font-size: 0.875rem;
  border-bottom: 1px solid #f3f4f6;
}

.tenant-table td {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

.tenant-name {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.mini-logo {
  width: 24px;
  height: 24px;
  object-fit: contain;
  border-radius: 4px;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.suspended {
  background: #fee2e2;
  color: #991b1b;
}

.product-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.product-tag {
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-weight: 500;
  padding: 0.25rem;
}

.action-btn:hover {
  text-decoration: underline;
}

.action-btn.suspend {
  color: #d97706;
}

.action-btn.delete {
  color: #dc2626;
}

.loading, .no-data {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}
</style>
