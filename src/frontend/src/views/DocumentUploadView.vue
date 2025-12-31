<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="text-h5"> Upload Document </v-card-title>

          <v-card-text>
            <error-message v-if="error" type="error" :message="error" closable @close="error = null" />

            <v-file-input
              v-model="selectedFile"
              label="Select PDF document"
              accept=".pdf"
              prepend-icon="mdi-file-pdf-box"
              :disabled="isUploading"
              @change="onFileSelected"
            />

            <v-alert v-if="validationError" type="error" class="mt-4">
              {{ validationError }}
            </v-alert>

            <v-progress-linear
              v-if="isUploading"
              color="primary"
              height="25"
              class="mt-4"
              indeterminate
            >
              <template #default>
                <strong>Uploading...</strong>
              </template>
            </v-progress-linear>
          </v-card-text>

          <v-card-actions>
            <v-btn @click="$router.back()">Cancel</v-btn>
            <v-spacer />
            <v-btn
              color="primary"
              :disabled="!selectedFile || !!validationError || isUploading"
              :loading="isUploading"
              @click="uploadFile"
            >
              Upload
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { validateDocumentFile } from '@/utils/validators'
import ErrorMessage from '@/components/common/ErrorMessage.vue'

const props = defineProps<{
  caseId: string
}>()

const router = useRouter()
const casesStore = useCasesStore()

const selectedFile = ref<File[] | null>(null)
const validationError = ref<string | null>(null)
const error = ref<string | null>(null)

const file = computed(() => (selectedFile.value ? selectedFile.value[0] : null))
const isUploading = computed(() => casesStore.isLoading)

function onFileSelected() {
  validationError.value = null
  if (file.value) {
    validationError.value = validateDocumentFile(file.value)
  }
}

async function uploadFile() {
  if (!file.value || validationError.value) return

  error.value = null

  try {
    // Get the current case details first
    const currentCase = await casesStore.fetchCase(props.caseId)
    
    // Create a new case with the document
    const updatedCase = await casesStore.createCase({
      client_name: currentCase.client_name,
      policy_type: currentCase.policy_type,
      submission_date: currentCase.submission_date,
      assigned_to: currentCase.assigned_to,
      metadata: currentCase.metadata
    }, file.value)
    
    // Navigate back to the case details
    router.push(`/cases/${updatedCase.case_id}`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload failed. Please try again.'
  }
}
</script>
