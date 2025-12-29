<template>
  <div class="d-flex justify-center align-center" :style="{ minHeight: minHeight }">
    <v-progress-circular
      :size="size"
      :width="width"
      color="primary"
      indeterminate
    />
    <span v-if="message" class="ml-4 text-subtitle-1">{{ message }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  size?: number
  width?: number
  message?: string
  minHeight?: string
}>()
</script>
