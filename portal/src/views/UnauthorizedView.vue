<template>
  <div class="unauthorized-view">
    <h1>Access Denied</h1>
    <p>You do not have the required permissions to access this page.</p>
    <p v-if="authStore.user">
      Logged in as: {{ authStore.user.email }}<br />
      Your roles: {{ authStore.roles.join(', ') || 'none' }}
    </p>
    <button @click="authStore.logout()">Log Out</button>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
const authStore = useAuthStore()
</script>
