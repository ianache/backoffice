<script setup lang="ts">
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div id="app">
    <nav v-if="authStore.isAuthenticated" class="main-nav">
      <div class="nav-links">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link v-if="authStore.hasRole('PlatformAdmin')" to="/tenants">Tenants</router-link>
      </div>
      <div class="user-info">
        <span>{{ authStore.username }}</span>
        <button @click="authStore.logout()">Logout</button>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  background-color: #f3f4f6;
}

.main-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  text-decoration: none;
  color: #4b5563;
  font-weight: 500;
}

.nav-links a.router-link-active {
  color: #2563eb;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info span {
  font-size: 0.875rem;
  color: #6b7280;
}

button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
}

main {
  min-height: calc(100vh - 64px);
}
</style>
