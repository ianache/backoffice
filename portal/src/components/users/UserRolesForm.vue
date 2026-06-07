<script setup lang="ts">
import { computed } from 'vue'

interface RolesModel {
  tenantRole: string
  productRoles: Record<string, string>
}

const props = defineProps<{
  modelValue: RolesModel
}>()

const emit = defineEmits<{
  'update:modelValue': [value: RolesModel]
}>()

const tenantRoles = [
  {
    id: 'TenantOwner',
    label: 'TenantOwner',
    description: 'Full administrative control over the tenant',
  },
  {
    id: 'TenantAdmin',
    label: 'TenantAdmin',
    description: 'Can manage users and settings',
  },
  {
    id: 'TenantViewer',
    label: 'TenantViewer',
    description: 'Read-only access to tenant data',
  },
]

const productOptions = ['', 'ProductManager', 'ProductDeveloper', 'ProductQA']

// Default product slots when productRoles is empty
const DEFAULT_PRODUCTS = ['analytics', 'platform']

const productSlots = computed<string[]>(() => {
  const keys = Object.keys(props.modelValue.productRoles ?? {})
  return keys.length > 0 ? keys : DEFAULT_PRODUCTS
})

const selectTenantRole = (roleId: string) => {
  emit('update:modelValue', { ...props.modelValue, tenantRole: roleId })
}

const updateProductRole = (productId: string, role: string) => {
  const updated = { ...props.modelValue.productRoles, [productId]: role }
  emit('update:modelValue', { ...props.modelValue, productRoles: updated })
}
</script>

<template>
  <div class="flex flex-col gap-xl">
    <!-- Section 1: Tenant Role -->
    <div>
      <h3 class="section-heading">Tenant Role</h3>
      <div class="flex flex-col gap-sm mt-sm">
        <label
          v-for="role in tenantRoles"
          :key="role.id"
          :class="[
            'role-card cursor-pointer',
            modelValue.tenantRole === role.id
              ? 'border-2 border-primary bg-primary/5'
              : 'border border-outline-variant hover:border-outline'
          ]"
          @click="selectTenantRole(role.id)"
        >
          <input
            type="radio"
            :name="'tenant-role'"
            :value="role.id"
            :checked="modelValue.tenantRole === role.id"
            class="sr-only"
            @change="selectTenantRole(role.id)"
          />
          <div class="flex items-start gap-md">
            <div
              class="w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5"
              :class="modelValue.tenantRole === role.id ? 'border-primary' : 'border-outline-variant'"
            >
              <div
                v-if="modelValue.tenantRole === role.id"
                class="w-2 h-2 rounded-full bg-primary"
              ></div>
            </div>
            <div>
              <p class="font-semibold text-sm text-on-surface">{{ role.label }}</p>
              <p class="text-sm text-on-surface-variant mt-0.5">{{ role.description }}</p>
            </div>
          </div>
        </label>
      </div>
    </div>

    <!-- Section 2: Product Roles -->
    <div>
      <h3 class="section-heading">Product Roles</h3>
      <div class="flex flex-col gap-sm mt-sm">
        <div
          v-for="productId in productSlots"
          :key="productId"
          class="flex items-center justify-between gap-md py-sm px-md border border-outline-variant rounded-xl"
        >
          <span class="text-sm font-medium text-on-surface capitalize">{{ productId }}</span>
          <select
            :value="modelValue.productRoles?.[productId] ?? ''"
            @change="updateProductRole(productId, ($event.target as HTMLSelectElement).value)"
            class="product-role-select"
          >
            <option v-for="opt in productOptions" :key="opt" :value="opt">
              {{ opt === '' ? 'No role' : opt }}
            </option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-heading {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  margin: 0;
}

.role-card {
  display: block;
  border-radius: 0.75rem;
  padding: 1rem;
  transition: border-color 0.15s, background-color 0.15s;
}

.product-role-select {
  font-size: 0.875rem;
  color: var(--on-surface);
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  border-radius: 0.5rem;
  padding: 4px 8px;
  outline: none;
  cursor: pointer;
  transition: border-color 0.15s;
}

.product-role-select:focus {
  border-color: var(--primary);
}
</style>
