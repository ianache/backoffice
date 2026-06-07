<script setup lang="ts">
interface Props {
  variant?: 'filled' | 'outlined' | 'text';
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  icon?: string;
}

withDefaults(defineProps<Props>(), {
  variant: 'filled',
  disabled: false,
  type: 'button',
});
</script>

<template>
  <!-- icon prop renders md-icon directly as a named-slot child of the Web Component.
       This is more reliable than slot forwarding (slot="icon" on a <slot> element
       doesn't consistently propagate the attribute in Vue 3 + custom elements). -->
  <md-filled-button
    v-if="variant === 'filled'"
    :disabled="disabled"
    :type="type"
    class="stitch-button"
  >
    <md-icon v-if="icon" slot="icon">{{ icon }}</md-icon>
    <slot />
  </md-filled-button>

  <md-outlined-button
    v-else-if="variant === 'outlined'"
    :disabled="disabled"
    :type="type"
    class="stitch-button"
  >
    <md-icon v-if="icon" slot="icon">{{ icon }}</md-icon>
    <slot />
  </md-outlined-button>

  <md-text-button
    v-else
    :disabled="disabled"
    :type="type"
    class="stitch-button"
  >
    <md-icon v-if="icon" slot="icon">{{ icon }}</md-icon>
    <slot />
  </md-text-button>
</template>

<style scoped>
.stitch-button {
  --md-filled-button-container-shape: var(--rounded-lg);
  --md-outlined-button-container-shape: var(--rounded-lg);
  --md-text-button-container-shape: var(--rounded-lg);
  font-family: var(--font-family-sans);
}
</style>
