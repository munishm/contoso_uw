<template>
  <v-chip
    :color="color"
    :size="size"
    :variant="variant"
    label
  >
    <v-icon v-if="showIcon" :icon="icon" start />
    {{ label }}
  </v-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatusType } from '@/types'

const props = defineProps<{
  status: ProcessingStatusType
  size?: 'small' | 'default' | 'large'
  variant?: 'flat' | 'elevated' | 'outlined'
  showIcon?: boolean
}>()

const color = computed(() => {
  switch (props.status) {
    case 'completed':
      return 'success'
    case 'processing':
      return 'info'
    case 'failed':
      return 'error'
    default:
      return 'default'
  }
})

const icon = computed(() => {
  switch (props.status) {
    case 'completed':
      return 'mdi-check-circle'
    case 'processing':
      return 'mdi-loading'
    case 'failed':
      return 'mdi-alert-circle'
    default:
      return 'mdi-clock-outline'
  }
})

const label = computed(() => {
  return props.status.charAt(0).toUpperCase() + props.status.slice(1)
})
</script>
