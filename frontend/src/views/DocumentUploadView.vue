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
              :rules="fileRules"
              :disabled="isUploading"
              @change="onFileSelected"
            />

            <v-alert v-if="validationError" type="error" class="mt-4">
              {{ validationError }}
            </v-alert>

            <v-progress-linear
              v-if="isUploading"
              :model-value="uploadProgress"
              color="primary"
              height="25"
              class="mt-4"
            >
              <template #default="{ value }">
                <strong>{{ Math.ceil(value) }}%</strong>
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
import { useDocumentsStore } from '@/stores/documents'
import { validateDocumentFile } from '@/utils/validators'
import ErrorMessage from '@/components/common/ErrorMessage.vue'

const props = defineProps<{
  caseId: string
}>()

const router = useRouter()
const documentsStore = useDocumentsStore()

const selectedFile = ref<File[] | null>(null)
const validationError = ref<string | null>(null)
const error = ref<string | null>(null)

const file = computed(() => (selectedFile.value ? selectedFile.value[0] : null))
const isUploading = computed(() => documentsStore.isUploading)
const uploadProgress = computed(() => documentsStore.uploadProgress)

const fileRules = [
  (v: File[]) => !!v && v.length > 0 || 'Document is required',
  (v: File[]) => !v || !v[0] || v[0].type === 'application/pdf' || 'Only PDF files are allowed',
  (v: File[]) => !v || !v[0] || v[0].size <= 20 * 1024 * 1024 || 'File size must be less than 20MB'
]

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
    const document = await documentsStore.uploadDocument(props.caseId, file.value)
    // Navigate to results page
    router.push(`/documents/${document.id}`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload failed. Please try again.'
  }
}
</script>
