<script setup lang="ts">
import type { AuditLogDiff, AuditLogEntry } from '../../services/audit'

defineProps<{
  show: boolean
  diff: AuditLogDiff | null
  entry: AuditLogEntry | null
  isLoading?: boolean
  error?: string | null
}>()

defineEmits(['close'])

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click="$emit('close')">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Change Details</h3>
            <button class="close-btn" @click="$emit('close')" aria-label="Close">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="isLoading" class="diff-loading">Loading diff…</div>
            <div v-else-if="error" class="diff-error">{{ error }}</div>
            <div v-else-if="diff">
              <div v-if="entry" class="diff-meta">
                <span class="diff-meta-item"><strong>Action:</strong> {{ entry.action_type }}</span>
                <span class="diff-meta-item"><strong>Target:</strong> {{ entry.target_type }} #{{ entry.target_id }}</span>
              </div>

              <div v-if="Object.keys(diff.added ?? {}).length" class="diff-section diff-added">
                <h4>Added</h4>
                <ul>
                  <li v-for="(value, key) in diff.added" :key="`added-${key}`">
                    <span class="diff-key">{{ key }}</span>: <span class="diff-value">{{ formatValue(value) }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="Object.keys(diff.removed ?? {}).length" class="diff-section diff-removed">
                <h4>Removed</h4>
                <ul>
                  <li v-for="(value, key) in diff.removed" :key="`removed-${key}`">
                    <span class="diff-key">{{ key }}</span>: <span class="diff-value">{{ formatValue(value) }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="Object.keys(diff.modified ?? {}).length" class="diff-section diff-modified">
                <h4>Modified</h4>
                <ul>
                  <li v-for="(change, key) in diff.modified" :key="`modified-${key}`">
                    <span class="diff-key">{{ key }}</span>:
                    <span class="diff-value-before">{{ formatValue(change.before) }}</span>
                    →
                    <span class="diff-value-after">{{ formatValue(change.after) }}</span>
                  </li>
                </ul>
              </div>

              <p v-if="!Object.keys(diff.added ?? {}).length && !Object.keys(diff.removed ?? {}).length && !Object.keys(diff.modified ?? {}).length" class="diff-empty">
                No field-level changes recorded for this entry.
              </p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="$emit('close')">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: var(--scrim); display: flex; align-items: center; justify-content: center; z-index: 2000;
}
.modal-content {
  background: var(--surface-container-lowest); color: var(--on-surface);
  padding: 1.5rem; border-radius: var(--rounded-lg); width: 100%; max-width: 700px;
  max-height: 80vh; overflow-y: auto; box-shadow: var(--elevation-dialog); border: 1px solid var(--outline-variant);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.modal-header h3 { margin: 0; }
.close-btn { background: none; border: none; cursor: pointer; color: var(--on-surface-variant); display: flex; }
.diff-meta { display: flex; gap: 1.5rem; margin-bottom: 1rem; font-size: 0.875rem; color: var(--on-surface-variant); }
.diff-section { margin-bottom: 1rem; border-radius: var(--rounded); padding: 0.75rem 1rem; }
.diff-section h4 { margin: 0 0 0.5rem 0; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }
.diff-section ul { margin: 0; padding-left: 1.25rem; font-family: var(--font-mono, monospace); font-size: 0.8125rem; }
.diff-added { background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.3); }
.diff-added h4 { color: #16a34a; }
.diff-removed { background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.3); }
.diff-removed h4 { color: #dc2626; }
.diff-modified { background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(234, 179, 8, 0.3); }
.diff-modified h4 { color: #ca8a04; }
.diff-value-before { color: #dc2626; text-decoration: line-through; }
.diff-value-after { color: #16a34a; }
.diff-empty { color: var(--on-surface-variant); font-size: 0.875rem; }
.diff-loading, .diff-error { padding: 2rem; text-align: center; color: var(--on-surface-variant); }
.modal-footer { margin-top: 1rem; display: flex; justify-content: flex-end; }
.btn { padding: 0.5rem 1rem; border-radius: var(--rounded); cursor: pointer; border: 1px solid transparent; font-weight: 500; font-family: var(--font-family-sans); font-size: 0.875rem; transition: filter 0.15s; }
.btn-secondary { background: var(--surface-container-high); border-color: var(--outline-variant); color: var(--on-surface); }
.btn-secondary:hover { filter: brightness(0.95); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
