<script setup lang="ts">
import { useAuthStore } from './stores/auth'
import { useUIStore } from './stores/ui'

const authStore = useAuthStore()
const uiStore = useUIStore()
</script>

<template>
  <div id="app">
    <nav v-if="authStore.isAuthenticated" class="main-nav">
      <div class="nav-links">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link v-if="authStore.hasRole('PlatformAdmin')" to="/tenants">Tenants</router-link>
      </div>
      <div class="user-info">
        <button 
          @click="uiStore.toggleTheme()" 
          class="theme-toggle" 
          :title="`Switch to ${uiStore.theme === 'light' ? 'dark' : 'light'} mode`"
        >
          {{ uiStore.theme === 'light' ? '🌙' : '☀️' }}
        </button>
        <span>{{ authStore.user?.name || authStore.user?.email }}</span>
        <button @click="authStore.logout()">Logout</button>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
/* Base styles updated to use tokens from theme.css */
body {
  margin: 0;
  font-family: var(--font-family-sans);
  background-color: var(--background);
  color: var(--on-background);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.main-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: var(--surface-container-lowest);
  border-bottom: 1px solid var(--outline-variant);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  text-decoration: none;
  color: var(--on-surface-variant);
  font-weight: 500;
}

.nav-links a.router-link-active {
  color: var(--primary);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info span {
  font-size: 0.875rem;
  color: var(--on-surface-variant);
}

.theme-toggle {
  background: none;
  border: none;
  font-size: 1.25rem;
  padding: 0.25rem;
  min-width: auto;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

button {
  padding: 0.5rem 1rem;
  border-radius: var(--rounded);
  border: 1px solid var(--outline);
  background: var(--surface-container-low);
  color: var(--on-surface);
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background: var(--surface-container);
}

main {
  min-height: calc(100vh - 64px);
}
</style>
