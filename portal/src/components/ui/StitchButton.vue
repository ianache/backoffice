<script setup lang="ts">
interface Props {
  variant?: 'filled' | 'outlined' | 'text';
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

withDefaults(defineProps<Props>(), {
  variant: 'filled',
  disabled: false,
  type: 'button',
});
</script>

<template>
  <md-filled-button
    v-if="variant === 'filled'"
    :disabled="disabled"
    :type="type"
    class="stitch-button"
  >
    <slot />
    <slot name="icon" slot="icon" />
  </md-filled-button>

  <md-outlined-button
    v-else-if="variant === 'outlined'"
    :disabled="disabled"
    :type="type"
    class="stitch-button"
  >
    <slot />
    <slot name="icon" slot="icon" />
  </md-outlined-button>

  <md-text-button
    v-else
    :disabled="disabled"
    :type="type"
    class="stitch-button"
  >
    <slot />
    <slot name="icon" slot="icon" />
  </md-text-button>
</template>

<style scoped>
.stitch-button {
  --md-filled-button-container-shape: var(--rounded-lg);
  --md-outlined-button-container-shape: var(--rounded-lg);
  --md-text-button-container-shape: var(--rounded-lg);
  
  /* Use theme tokens for colors if needed, but md-filled-button already uses --md-sys-color-primary by default */
  /* We map our --primary to --md-sys-color-primary in theme.css or here */
  
  font-family: var(--font-family-sans);
}
</style>
