<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>{{ appTitle }}</v-app-bar-title>
      <v-spacer />
      <v-btn icon="mdi-home" @click="$router.push('/')" />
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { testApiConnection } from '@/utils/apiTest'

const appTitle = computed(() => import.meta.env.VITE_APP_TITLE || 'Underwriter UI')

// Test API connection on app load (for debugging)
onMounted(async () => {
  if (import.meta.env.DEV) {
    await testApiConnection()
  }
})
</script>
