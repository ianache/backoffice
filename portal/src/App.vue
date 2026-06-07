<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from './components/layout/MainLayout.vue'
import AuthLayout from './components/layout/AuthLayout.vue'

const route = useRoute()

/**
 * Dynamically switch layouts based on route meta.
 * Defaults to MainLayout if no layout is specified.
 */
const layout = computed(() => {
  if (route.meta.layout === 'auth') {
    return AuthLayout
  }
  return MainLayout
})
</script>

<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<style>
/* 
  Global styles are now primarily in theme.css and tailwind.css.
  We keep #app as a full-height container.
*/
#app {
  height: 100vh;
  width: 100%;
}
</style>
