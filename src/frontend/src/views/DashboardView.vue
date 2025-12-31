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
      <v-col v-for="caseItem in cases" :key="caseItem.case_id" cols="12" md="6" lg="4">
        <v-card>
          <v-card-title>{{ caseItem.client_name }}</v-card-title>
          <v-card-subtitle>
            {{ caseItem.policy_type }} • Created {{ formatRelativeTime(caseItem.created_at) }}
          </v-card-subtitle>
          <v-card-text>
            <status-badge :status="caseItem.status as any" show-icon />
            <div class="mt-2" v-if="'document_count' in caseItem">
              {{ caseItem.document_count }} document(s)
            </div>
          </v-card-text>
          <v-card-actions>
            <v-btn
              color="primary"
              variant="text"
              @click="$router.push(`/cases/${caseItem.case_id}/upload`)"
            >
              Upload Document
            </v-btn>
            <v-btn variant="text" @click="viewCase(caseItem.case_id)"> View Details </v-btn>
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
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card>
        <v-card-title>Create New Case</v-card-title>
        <v-card-text>
          <v-form ref="caseForm">
            <v-text-field
              v-model="newCase.client_name"
              label="Client Name"
              :rules="[v => !!v || 'Client name is required']"
              required
              class="mb-3"
            />
            
            <v-text-field
              v-model="newCase.policy_type"
              label="Policy Type"
              :rules="[v => !!v || 'Policy type is required']"
              required
              placeholder="e.g., Life Insurance - HNW"
              class="mb-3"
            />
            
            <v-text-field
              v-model="newCase.submission_date"
              label="Submission Date"
              type="date"
              :rules="[v => !!v || 'Submission date is required']"
              required
              class="mb-3"
            />
            
            <v-file-input
              v-model="selectedFile"
              label="Main Document"
              :rules="[v => !!v || 'Document is required']"
              required
              accept=".pdf,.docx,.doc"
              prepend-icon="mdi-file-document"
              show-size
              class="mb-3"
            >
              <template v-slot:selection="{ fileNames }">
                <v-chip
                  v-for="fileName in fileNames"
                  :key="fileName"
                  size="small"
                  label
                  color="primary"
                >
                  {{ fileName }}
                </v-chip>
              </template>
            </v-file-input>
            
            <v-alert
              v-if="createError"
              type="error"
              density="compact"
              closable
              @click:close="createError = null"
            >
              {{ createError }}
            </v-alert>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="closeCreateDialog">Cancel</v-btn>
          <v-btn color="primary" :loading="isCreating" @click="createNewCase">Create Case</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatRelativeTime } from '@/utils/formatters'

const router = useRouter()
const casesStore = useCasesStore()
const showCreateDialog = ref(false)
const caseForm = ref()
const selectedFile = ref<File[]>([])
const isCreating = ref(false)
const createError = ref<string | null>(null)

const newCase = ref({
  client_name: '',
  policy_type: '',
  submission_date: new Date().toISOString().split('T')[0] // Default to today
})

const cases = computed(() => Array.from(casesStore.cases.values()))
const isLoading = computed(() => casesStore.isLoading)
const error = computed(() => casesStore.error)

onMounted(async () => {
  await casesStore.fetchCases()
})

async function createNewCase() {
  createError.value = null
  
  // Validate form
  const { valid } = await caseForm.value.validate()
  if (!valid) return
  
  // Get the file - v-file-input returns array or single file
  const file = Array.isArray(selectedFile.value) ? selectedFile.value[0] : selectedFile.value
  
  // Check if file is selected
  if (!file) {
    createError.value = 'Please select a document to upload'
    return
  }

  isCreating.value = true
  try {
    await casesStore.createCase(
      {
        client_name: newCase.value.client_name,
        policy_type: newCase.value.policy_type,
        submission_date: newCase.value.submission_date
      },
      file
    )
    closeCreateDialog()
  } catch (err) {
    console.error('Failed to create case:', err)
    createError.value = err instanceof Error ? err.message : 'Failed to create case'
  } finally {
    isCreating.value = false
  }
}

function closeCreateDialog() {
  showCreateDialog.value = false
  newCase.value = {
    client_name: '',
    policy_type: '',
    submission_date: new Date().toISOString().split('T')[0]
  }
  selectedFile.value = []
  createError.value = null
  caseForm.value?.reset()
}

function viewCase(caseId: string) {
  router.push(`/cases/${caseId}`)
}
</script>
