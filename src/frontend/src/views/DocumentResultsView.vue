<template>
  <v-container fluid>
    <loading-spinner v-if="isLoading" message="Loading document..." />

    <error-message v-if="error" type="error" :message="error" />

    <div v-if="!isLoading && document">
      <v-row>
        <v-col cols="12">
          <div class="d-flex align-center mb-4">
            <v-btn icon="mdi-arrow-left" @click="$router.push('/')" />
            <h1 class="text-h5 ml-4">{{ document.filename }}</h1>
            <v-spacer />
            <status-badge :status="document.processing_status" show-icon class="mr-2" />
          </div>
        </v-col>
      </v-row>

      <!-- Processing status -->
      <v-row v-if="document.processing_status === 'processing'">
        <v-col cols="12">
          <v-card>
            <v-card-text>
              <div class="text-center">
                <v-progress-circular indeterminate color="primary" class="mb-4" />
                <p class="text-h6">Processing document...</p>
                <p class="text-body-2 text-grey">
                  This may take a few minutes. The page will automatically update when complete.
                </p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Results -->
      <v-row v-if="document.processing_status === 'completed'">
        <v-col cols="12" md="4">
          <v-card class="mb-4">
            <v-card-title>Classification</v-card-title>
            <v-card-text>
              <p v-if="document.document_type">
                <strong>Type:</strong> {{ formatDocumentType(document.document_type) }}
              </p>
              <p v-if="document.classification_confidence">
                <strong>Confidence:</strong>
                <v-chip :color="getConfidenceColor(document.classification_confidence)" size="small" class="ml-2">
                  {{ formatConfidence(document.classification_confidence) }}
                </v-chip>
              </p>
            </v-card-text>
          </v-card>

          <v-card class="mb-4">
            <v-card-title>Extracted Fields</v-card-title>
            <v-card-text>
              <p class="text-body-2 text-grey">Field extraction results will be displayed here</p>
            </v-card-text>
          </v-card>

          <v-card>
            <v-card-title>Summary</v-card-title>
            <v-card-text>
              <p class="text-body-2 text-grey">Document summary will be displayed here</p>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="8">
          <v-card>
            <v-card-title>Document Viewer</v-card-title>
            <v-card-text>
              <p class="text-body-2 text-grey">PDF viewer will be displayed here</p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Failed status -->
      <v-row v-if="document.processing_status === 'failed'">
        <v-col cols="12">
          <v-alert type="error" title="Processing Failed">
            The document could not be processed. Please try uploading again or contact support if
            the issue persists.
          </v-alert>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatConfidence, getConfidenceColor } from '@/utils/formatters'
import { DOCUMENT_TYPE_LABELS } from '@/utils/constants'

const props = defineProps<{
  documentId: string
}>()

const documentsStore = useDocumentsStore()
const document = computed(() => documentsStore.getDocumentById(props.documentId))
const isLoading = computed(() => documentsStore.isLoading)
const error = computed(() => documentsStore.error)

onMounted(async () => {
  await documentsStore.fetchDocument(props.documentId)
})

// Watch for processing status changes
watch(
  () => document.value?.processing_status,
  status => {
    if (status === 'pending' || status === 'processing') {
      // Polling is already handled by the store
      console.log('Document processing...')
    }
  }
)

function formatDocumentType(type: string): string {
  return DOCUMENT_TYPE_LABELS[type] || type
}
</script>
