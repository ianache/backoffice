<script setup lang="ts">
defineProps<{
  show: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'info'
  action?: any
}>()

const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click="emit('cancel')">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>{{ title }}</h3>
          </div>
          <div class="modal-body">
            <p>{{ message }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="emit('cancel')">
              {{ cancelText || 'Cancel' }}
            </button>
            <button
              :class="['btn', type === 'danger' ? 'btn-danger' : 'btn-primary']"
              @click="emit('confirm')"
            >
              {{ confirmText || 'Confirm' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--scrim);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background: var(--surface-container-lowest);
  color: var(--on-surface);
  padding: 1.5rem;
  border-radius: var(--rounded-lg);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--elevation-dialog);
  border: 1px solid var(--outline-variant);
}

.modal-header h3 {
  margin: 0 0 1rem 0;
}

.modal-footer {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--rounded);
  cursor: pointer;
  border: 1px solid transparent;
  font-weight: 500;
  font-family: var(--font-family-sans);
  font-size: 0.875rem;
  transition: filter 0.15s;
}

.btn-secondary {
  background: var(--surface-container-high);
  border-color: var(--outline-variant);
  color: var(--on-surface);
}

.btn-secondary:hover {
  filter: brightness(0.95);
}

.btn-primary {
  background: var(--primary);
  color: var(--on-primary);
}

.btn-primary:hover {
  filter: brightness(1.08);
}

.btn-danger {
  background: var(--error);
  color: var(--on-error);
}

.btn-danger:hover {
  filter: brightness(1.08);
}
</style>
