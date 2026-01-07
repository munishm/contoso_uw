<template>
  <v-container fluid>
    <loading-spinner v-if="isLoading" message="Loading document..." />

    <error-message v-if="error" type="error" :message="error" />

    <div v-if="!isLoading && document">
      <!-- Header -->
      <v-row>
        <v-col cols="12">
          <div class="d-flex align-center mb-4">
            <v-btn icon="mdi-arrow-left" variant="text" @click="goBack" />
            <div class="ml-3">
              <h1 class="text-h5">{{ document.filename }}</h1>
              <p class="text-body-2 text-grey mb-0">
                {{ document.classification || 'Unclassified' }}
                <span v-if="document.confidence_score">
                  • {{ formatConfidence(document.confidence_score) }} confidence
                </span>
              </p>
            </div>
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
        <!-- Left Column - Extraction Results -->
        <v-col cols="12" md="5" lg="4">
          <!-- Extraction Status Card -->
          <v-card class="mb-4" v-if="document.extraction">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" :color="extractionStatusColor">
                {{ extractionStatusIcon }}
              </v-icon>
              Extraction Results
              <v-spacer />
              <v-chip 
                :color="extractionStatusChipColor" 
                size="small"
                class="mr-2"
              >
                {{ extractionStatusLabel }}
              </v-chip>
              <v-chip 
                v-if="document.extraction.needs_review" 
                color="warning" 
                size="small"
                prepend-icon="mdi-alert"
              >
                Needs Review
              </v-chip>
            </v-card-title>
            <v-card-subtitle v-if="document.extraction.models_used?.length">
              Models: {{ document.extraction.models_used.join(', ') }}
            </v-card-subtitle>
            
            <!-- Extracted Fields -->
            <v-card-text v-if="extractedFields.length > 0">
              <v-list density="compact" class="extraction-list">
                <v-list-item 
                  v-for="(field, index) in extractedFields" 
                  :key="index"
                  class="extraction-field mb-2 pa-3"
                  :class="{ 'needs-review': field.needs_review }"
                  rounded
                >
                  <template v-slot:prepend>
                    <v-icon 
                      v-if="field.needs_review" 
                      color="warning" 
                      size="small"
                      class="mr-2"
                    >
                      mdi-alert-circle
                    </v-icon>
                    <v-icon 
                      v-else 
                      color="success" 
                      size="small"
                      class="mr-2"
                    >
                      mdi-check-circle
                    </v-icon>
                  </template>
                  
                  <v-list-item-title class="field-name text-caption text-grey-darken-1 text-uppercase">
                    {{ formatFieldName(field.field_name) }}
                  </v-list-item-title>
                  
                  <v-list-item-subtitle class="field-value text-body-1 font-weight-medium mt-1">
                    {{ formatFieldValue(field.value) }}
                  </v-list-item-subtitle>
                  
                  <template v-slot:append>
                    <div class="d-flex flex-column align-end">
                      <v-chip 
                        :color="getConfidenceColor(field.confidence)" 
                        size="x-small"
                        class="mb-1"
                      >
                        {{ formatConfidence(field.confidence) }}
                      </v-chip>
                      <v-tooltip v-if="field.citations?.length" location="left">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="x-small" color="grey">
                            mdi-file-document-outline
                          </v-icon>
                        </template>
                        <span>Page {{ field.citations[0]?.page }}</span>
                      </v-tooltip>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
              
              <!-- Review Warning -->
              <v-alert 
                v-if="fieldsNeedingReview.length > 0"
                type="warning" 
                variant="tonal"
                class="mt-4"
                density="compact"
              >
                <strong>{{ fieldsNeedingReview.length }}</strong> field(s) need human review
              </v-alert>
            </v-card-text>
            
            <!-- No Fields Extracted -->
            <v-card-text v-else-if="document.extraction.status === 'completed'">
              <v-alert type="info" variant="tonal" density="compact">
                No fields were extracted from this document
              </v-alert>
            </v-card-text>
            
            <!-- Extraction Error -->
            <v-card-text v-else-if="document.extraction.status === 'error'">
              <v-alert type="error" variant="tonal" density="compact">
                {{ document.extraction.error_message || 'Extraction failed' }}
              </v-alert>
            </v-card-text>
            
            <!-- Extraction Skipped -->
            <v-card-text v-else-if="document.extraction.status === 'skipped'">
              <v-alert type="info" variant="tonal" density="compact">
                Extraction was skipped for this document type
              </v-alert>
            </v-card-text>
          </v-card>
          
          <!-- No Extraction Data -->
          <v-card class="mb-4" v-else>
            <v-card-title>
              <v-icon class="mr-2" color="grey">mdi-text-box-search-outline</v-icon>
              Extraction Results
            </v-card-title>
            <v-card-text>
              <v-alert type="info" variant="tonal" density="compact">
                No extraction data available for this document
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Document Info Card -->
          <v-card class="mb-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-information-outline</v-icon>
              Document Info
            </v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-tag</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-grey">Classification</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2">
                    {{ document.classification || 'Not classified' }}
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="document.source">
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-source-branch</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-grey">Source</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2">
                    {{ document.source }}
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="document.page_range">
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-file-document-multiple</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-grey">Page Range</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2">
                    {{ document.page_range }}
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-clock-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-grey">Processed At</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2">
                    {{ formatDate(document.processing_completed_at) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- Summary Card -->
          <v-card v-if="document.summary" class="mb-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-text-box-outline</v-icon>
              Summary
            </v-card-title>
            <v-card-text>
              <p class="text-body-2">{{ document.summary }}</p>
            </v-card-text>
          </v-card>

          <!-- Download Button -->
          <v-btn 
            variant="tonal" 
            color="primary"
            prepend-icon="mdi-download"
            :loading="isDownloading"
            @click="downloadDocument"
            block
          >
            Download Document
          </v-btn>
        </v-col>

        <!-- Right Column - PDF Viewer -->
        <v-col cols="12" md="7" lg="8">
          <v-card class="pdf-viewer-card">
            <v-card-title class="d-flex align-center py-2">
              <v-icon class="mr-2">mdi-file-pdf-box</v-icon>
              Document Preview
              <v-spacer />
              <v-btn 
                variant="text" 
                size="small"
                icon="mdi-open-in-new"
                @click="openInNewTab"
                title="Open in new tab"
              />
            </v-card-title>
            <v-divider />
            <v-card-text class="pa-0">
              <div v-if="isLoadingPdf" class="pdf-loading d-flex align-center justify-center">
                <v-progress-circular indeterminate color="primary" />
                <span class="ml-3">Loading document...</span>
              </div>
              <div v-else-if="pdfError" class="pdf-error d-flex flex-column align-center justify-center">
                <v-icon size="48" color="grey">mdi-file-alert-outline</v-icon>
                <p class="text-body-2 text-grey mt-2">{{ pdfError }}</p>
                <v-btn 
                  variant="tonal" 
                  color="primary"
                  class="mt-2"
                  prepend-icon="mdi-refresh"
                  @click="loadPdfPreview"
                >
                  Retry
                </v-btn>
              </div>
              <iframe 
                v-else-if="pdfUrl"
                :src="pdfUrl"
                class="pdf-iframe"
                frameborder="0"
              />
              <div v-else class="pdf-placeholder d-flex align-center justify-center">
                <v-btn 
                  variant="tonal" 
                  color="primary"
                  prepend-icon="mdi-eye"
                  @click="loadPdfPreview"
                >
                  Load Preview
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Failed status -->
      <v-row v-if="document.processing_status === 'failed'">
        <v-col cols="12">
          <v-alert type="error" title="Processing Failed">
            {{ document.processing_error || 'The document could not be processed. Please try uploading again or contact support if the issue persists.' }}
          </v-alert>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatConfidence, getConfidenceColor } from '@/utils/formatters'
import { DOCUMENT_TYPE_LABELS } from '@/utils/constants'
import apiClient from '@/services/api'
import type { ExtractedFieldResult } from '@/types/document'

const props = defineProps<{
  caseId: string
  documentId: string
}>()

const router = useRouter()
const documentsStore = useDocumentsStore()
const document = computed(() => documentsStore.getDocumentById(props.documentId))
const isLoading = computed(() => documentsStore.isLoading)
const error = computed(() => documentsStore.error)
const isDownloading = ref(false)

// PDF Viewer state
const pdfUrl = ref<string | null>(null)
const isLoadingPdf = ref(false)
const pdfError = ref<string | null>(null)

// Computed properties for extraction
const extractedFields = computed<ExtractedFieldResult[]>(() => {
  return document.value?.extraction?.fields || []
})

const fieldsNeedingReview = computed(() => {
  return extractedFields.value.filter(f => f.needs_review)
})

const extractionStatusColor = computed(() => {
  const status = document.value?.extraction?.status
  if (status === 'completed') return document.value?.extraction?.needs_review ? 'warning' : 'success'
  if (status === 'error') return 'error'
  if (status === 'skipped') return 'grey'
  return 'info'
})

const extractionStatusIcon = computed(() => {
  const status = document.value?.extraction?.status
  if (status === 'completed') return document.value?.extraction?.needs_review ? 'mdi-alert-circle' : 'mdi-check-circle'
  if (status === 'error') return 'mdi-close-circle'
  if (status === 'skipped') return 'mdi-skip-next-circle'
  return 'mdi-progress-clock'
})

const extractionStatusLabel = computed(() => {
  const status = document.value?.extraction?.status
  if (status === 'completed') return 'Completed'
  if (status === 'error') return 'Error'
  if (status === 'skipped') return 'Skipped'
  return 'Processing'
})

const extractionStatusChipColor = computed(() => {
  const status = document.value?.extraction?.status
  if (status === 'completed') return 'success'
  if (status === 'error') return 'error'
  if (status === 'skipped') return 'grey'
  return 'info'
})

onMounted(async () => {
  await documentsStore.fetchDocument(props.caseId, props.documentId)
  // Auto-load PDF preview when document is ready
  if (document.value?.processing_status === 'completed') {
    loadPdfPreview()
  }
})

// Watch for processing status changes
watch(
  () => document.value?.processing_status,
  (status) => {
    if (status === 'completed' && !pdfUrl.value) {
      loadPdfPreview()
    }
  }
)

function goBack() {
  router.push(`/cases/${props.caseId}`)
}

function formatDocumentType(type: string): string {
  return DOCUMENT_TYPE_LABELS[type] || type
}

function formatFieldName(name: string): string {
  // Convert snake_case or camelCase to Title Case with spaces
  return name
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^\s+/, '')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

function formatFieldValue(value: any): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function formatDate(dateString?: string | null): string {
  if (!dateString) return '—'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

async function downloadDocument() {
  try {
    isDownloading.value = true
    const response = await apiClient.get(`/cases/${props.caseId}/documents/${props.documentId}/download`)
    if (response.data?.download_url) {
      window.open(response.data.download_url, '_blank')
    } else {
      console.error('No download URL in response')
    }
  } catch (err) {
    console.error('Failed to download document:', err)
  } finally {
    isDownloading.value = false
  }
}

async function loadPdfPreview() {
  try {
    isLoadingPdf.value = true
    pdfError.value = null
    const response = await apiClient.get(`/cases/${props.caseId}/documents/${props.documentId}/download`)
    if (response.data?.download_url) {
      // Use Google Docs viewer for better PDF rendering, or direct URL for browsers that support it
      const url = response.data.download_url
      // Direct embed - most modern browsers can render PDFs directly
      pdfUrl.value = url
    } else {
      pdfError.value = 'Unable to load document preview'
    }
  } catch (err) {
    console.error('Failed to load PDF preview:', err)
    pdfError.value = 'Failed to load document. Please try again.'
  } finally {
    isLoadingPdf.value = false
  }
}

function openInNewTab() {
  if (pdfUrl.value) {
    window.open(pdfUrl.value, '_blank')
  } else {
    downloadDocument()
  }
}
</script>

<style scoped>
.extraction-list {
  background: transparent;
}

.extraction-field {
  background: #fafafa;
  border: 1px solid #e0e0e0;
}

.extraction-field.needs-review {
  background: #fff8e1;
  border-color: #ffcc80;
}

.field-name {
  letter-spacing: 0.5px;
}

.field-value {
  color: #1a1a1a;
}

.pdf-viewer-card {
  position: sticky;
  top: 80px;
}

.pdf-iframe {
  width: 100%;
  height: calc(100vh - 200px);
  min-height: 600px;
  border: none;
}

.pdf-loading,
.pdf-error,
.pdf-placeholder {
  height: calc(100vh - 200px);
  min-height: 600px;
  background: #f5f5f5;
}
</style>
