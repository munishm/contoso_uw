<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <h1 class="text-h4">Dashboard</h1>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
            New Case
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <loading-spinner v-if="isLoading" message="Loading cases..." />

    <error-message v-if="error" type="error" :message="error" />

    <v-row v-if="!isLoading && cases.length > 0">
      <v-col v-for="caseItem in cases" :key="caseItem.id" cols="12" md="6" lg="4">
        <v-card>
          <v-card-title>{{ caseItem.case_name }}</v-card-title>
          <v-card-subtitle>
            Created {{ formatRelativeTime(caseItem.creation_timestamp) }}
          </v-card-subtitle>
          <v-card-text>
            <status-badge :status="caseItem.status as any" show-icon />
            <div class="mt-2">{{ caseItem.document_ids.length }} document(s)</div>
          </v-card-text>
          <v-card-actions>
            <v-btn
              color="primary"
              variant="text"
              @click="$router.push(`/cases/${caseItem.id}/upload`)"
            >
              Upload Document
            </v-btn>
            <v-btn variant="text" @click="viewCase(caseItem.id)"> View Details </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-if="!isLoading && cases.length === 0">
      <v-col cols="12" class="text-center">
        <v-icon size="64" color="grey">mdi-folder-open-outline</v-icon>
        <p class="text-h6 mt-4">No cases found</p>
        <p class="text-body-2 text-grey">Create your first case to get started</p>
      </v-col>
    </v-row>

    <!-- Create Case Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card>
        <v-card-title>Create New Case</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newCaseName"
            label="Case Name"
            :rules="[v => !!v || 'Case name is required']"
            required
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="isCreating" @click="createNewCase">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCasesStore } from '@/stores/cases'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatRelativeTime } from '@/utils/formatters'

const casesStore = useCasesStore()
const showCreateDialog = ref(false)
const newCaseName = ref('')
const isCreating = ref(false)

const cases = computed(() => Array.from(casesStore.cases.values()))
const isLoading = computed(() => casesStore.isLoading)
const error = computed(() => casesStore.error)

onMounted(async () => {
  await casesStore.fetchCases()
})

async function createNewCase() {
  if (!newCaseName.value.trim()) return

  isCreating.value = true
  try {
    await casesStore.createCase(newCaseName.value)
    showCreateDialog.value = false
    newCaseName.value = ''
  } catch (err) {
    console.error('Failed to create case:', err)
  } finally {
    isCreating.value = false
  }
}

function viewCase(caseId: string) {
  // Navigate to case details (to be implemented)
  console.log('View case:', caseId)
}
</script>
