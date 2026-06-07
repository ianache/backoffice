<template>
  <div class="login-container">
    <div class="mb-8 text-center">
      <h2 class="text-2xl font-semibold text-on-surface">Welcome back</h2>
      <p class="text-on-surface-variant">Please enter your credentials to continue</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-6">
      <StitchTextField
        v-model="email"
        label="Email"
        type="email"
        required
        placeholder="admin@backoffice.dev"
        :disabled="isLoading"
      >
        <template #leading-icon>
          <md-icon>mail</md-icon>
        </template>
      </StitchTextField>

      <StitchTextField
        v-model="password"
        label="Password"
        type="password"
        required
        :disabled="isLoading"
      >
        <template #leading-icon>
          <md-icon>lock</md-icon>
        </template>
      </StitchTextField>

      <div class="flex items-center justify-between py-2">
        <label class="flex items-center space-x-3 cursor-pointer group">
          <md-checkbox touch-target="wrapper" :disabled="isLoading"></md-checkbox>
          <span class="text-sm text-on-surface-variant group-hover:text-on-surface transition-colors">Remember me</span>
        </label>
        <a href="#" class="text-sm text-primary font-medium hover:underline">Forgot password?</a>
      </div>

      <div v-if="error" class="p-4 rounded-xl bg-error-container text-on-error-container text-sm flex items-start space-x-3 animate-in fade-in slide-in-from-top-1 duration-200">
        <md-icon class="text-lg mt-0.5">error</md-icon>
        <span class="leading-relaxed">{{ error }}</span>
      </div>

      <div class="pt-2">
        <StitchButton
          type="submit"
          class="w-full h-12"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">Sign In</span>
          <span v-else>Signing in...</span>
          <template #icon v-if="isLoading">
            <md-circular-progress indeterminate style="--md-circular-progress-size: 18px; --md-circular-progress-active-indicator-width: 15;"></md-circular-progress>
          </template>
        </StitchButton>
      </div>
    </form>
    
    <div class="mt-8 pt-6 border-t border-outline-variant text-center">
      <p class="text-sm text-on-surface-variant">
        Don't have an account? 
        <a href="#" class="text-primary font-medium hover:underline">Contact support</a>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import StitchTextField from '../components/ui/StitchTextField.vue'
import StitchButton from '../components/ui/StitchButton.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const error = ref('')

async function handleLogin() {
  if (isLoading.value) return
  isLoading.value = true
  error.value = ''
  try {
    await authStore.loginWithCredentials(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    router.push(redirect)
  } catch (e: any) {
    error.value = e.message || 'Failed to sign in. Please check your credentials.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
}

/* Material symbols use md-icon */
md-icon {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style>
