<template>
  <v-alert
    :type="type"
    :title="title"
    :text="message"
    :closable="closable"
    class="mb-4"
    @click:close="$emit('close')"
  />
</template>

<script setup lang="ts">
defineProps<{
  type?: 'error' | 'warning' | 'info' | 'success'
  title?: string
  message: string
  closable?: boolean
}>()

defineEmits<{
  close: []
}>()
</script>
