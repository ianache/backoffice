<script setup lang="ts">
import { useToastStore } from '../../stores/toast'

const toastStore = useToastStore()
</script>

<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toastStore.toasts"
          :key="toast.id"
          :class="['toast', `toast--${toast.type}`]"
          role="alert"
        >
          <span class="material-symbols-outlined toast-icon">
            {{ toast.type === 'success' ? 'check_circle' : 'error' }}
          </span>
          <span class="toast-message">{{ toast.message }}</span>
          <button class="toast-close" @click="toastStore.remove(toast.id)" aria-label="Dismiss">
            <span class="material-symbols-outlined" style="font-size:18px">close</span>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 280px;
  max-width: 420px;
  padding: 12px 14px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  font-size: 0.875rem;
  font-weight: 500;
  pointer-events: all;
}

.toast--success {
  background: #166534;
  color: #f0fdf4;
}

.toast--error {
  background: var(--error-container);
  color: var(--on-error-container);
  border: 1px solid var(--error);
}

[data-theme='dark'] .toast--success {
  background: rgba(52, 168, 83, 0.2);
  color: #86efac;
  border: 1px solid rgba(52, 168, 83, 0.4);
}

.toast-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
  line-height: 1.4;
}

.toast-close {
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  padding: 2px;
  display: flex;
  align-items: center;
  border-radius: 4px;
  flex-shrink: 0;
}

.toast-close:hover {
  opacity: 1;
}

/* TransitionGroup animations */
.toast-enter-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
