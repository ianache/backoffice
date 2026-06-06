<template>
  <div class="dashboard-view">
    <h1>BackOffice Dashboard</h1>
    <div v-if="authStore.user">
      <p><strong>User:</strong> {{ authStore.user.email }}</p>
      <p><strong>Name:</strong> {{ authStore.user.name }}</p>
      <p><strong>Roles:</strong> {{ authStore.roles.join(', ') }}</p>
    </div>
    <button @click="authStore.logout()">Log Out</button>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
const authStore = useAuthStore()
</script>
