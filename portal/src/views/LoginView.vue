<template>
  <div class="login-view">
    <p>Redirecting to login...</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  if (!authStore.isAuthenticated) {
    authStore.login()
  }
})
</script>
