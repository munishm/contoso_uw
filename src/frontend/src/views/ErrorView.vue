<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="text-h5"> Error </v-card-title>
          <v-card-text>
            <v-icon size="64" color="error">mdi-alert-circle-outline</v-icon>
            <p class="text-h6 mt-4">Something went wrong</p>
            <p class="text-body-1">The page you're looking for doesn't exist or an error occurred.</p>
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" @click="$router.push('/')"> Go to Dashboard </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// Error view for 404 and general errors
</script>
