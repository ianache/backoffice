import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark'

export const useUIStore = defineStore('ui', () => {
  const theme = ref<Theme>('light')

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  function setTheme(newTheme: Theme) {
    theme.value = newTheme
  }

  // Apply theme to document element
  watch(theme, (newTheme) => {
    document.documentElement.setAttribute('data-theme', newTheme)
    // Also update class for tailwind-like compatibility if needed
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, { immediate: true })

  return { theme, toggleTheme, setTheme }
}, {
  persist: true
})
