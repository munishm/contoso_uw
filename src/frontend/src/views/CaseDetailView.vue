<template>
  <v-container fluid>
    <loading-spinner v-if="isLoading" message="Loading case details..." />

    <error-message v-if="error" type="error" :message="error" />

    <div v-if="!isLoading && currentCase">
      <!-- Header -->
      <v-row>
        <v-col cols="12">
          <div class="d-flex align-center mb-4">
            <v-btn icon="mdi-arrow-left" @click="$router.push('/')" />
            <div class="ml-4">
              <h1 class="text-h4">{{ currentCase.client_name }}</h1>
              <p class="text-body-2 text-grey">Case ID: {{ currentCase.case_id }}</p>
            </div>
            <v-spacer />
            <status-badge :status="currentCase.status" show-icon />
          </div>
        </v-col>
      </v-row>

      <!-- Case Information -->
      <v-row>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Case Information</v-card-title>
            <v-card-text>
              <div class="mb-3">
                <p class="text-caption text-grey">Policy Type</p>
                <p class="text-body-1">{{ currentCase.policy_type }}</p>
              </div>
              <div class="mb-3">
                <p class="text-caption text-grey">Submission Date</p>
                <p class="text-body-1">{{ formatDate(currentCase.submission_date) }}</p>
              </div>
              <div class="mb-3">
                <p class="text-caption text-grey">Created By</p>
                <p class="text-body-1">{{ currentCase.created_by }}</p>
              </div>
              <div class="mb-3">
                <p class="text-caption text-grey">Created At</p>
                <p class="text-body-1">{{ formatDateTime(currentCase.created_at) }}</p>
              </div>
              <div class="mb-3">
                <p class="text-caption text-grey">Last Updated</p>
                <p class="text-body-1">{{ formatDateTime(currentCase.updated_at) }}</p>
              </div>
              <div v-if="currentCase.processing_status" class="mb-3">
                <p class="text-caption text-grey">Processing Status</p>
                <p class="text-body-1">{{ formatProcessingStatus(currentCase.processing_status) }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="8">
          <!-- Case Summary -->
          <v-card v-if="currentCase.case_summary" class="mb-4">
            <v-card-title>Case Summary</v-card-title>
            <v-card-text>
              <p class="text-body-1">{{ currentCase.case_summary }}</p>
              <p v-if="currentCase.case_summary_updated_at" class="text-caption text-grey mt-2">
                Last updated: {{ formatDateTime(currentCase.case_summary_updated_at) }}
              </p>
            </v-card-text>
          </v-card>

          <!-- Documents -->
          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Documents</span>
              <v-spacer />
              <v-chip size="small">{{ documents.length }} {{ documents.length === 1 ? 'document' : 'documents' }}</v-chip>
            </v-card-title>
            <v-card-text>
              <loading-spinner v-if="documentsLoading" message="Loading documents..." />
              
              <error-message v-if="documentsError" type="error" :message="documentsError" />

              <div v-if="!documentsLoading && documents.length === 0" class="text-center py-8">
                <v-icon size="48" color="grey">mdi-file-document-outline</v-icon>
                <p class="text-body-1 mt-2">No documents found</p>
              </div>

              <v-list v-if="!documentsLoading && documents.length > 0">
                <v-list-item
                  v-for="doc in documents"
                  :key="doc.document_id"
                  class="mb-2"
                  border
                  rounded
                >
                  <template v-slot:prepend>
                    <v-icon :color="getDocumentIcon(doc.content_type).color">
                      {{ getDocumentIcon(doc.content_type).icon }}
                    </v-icon>
                  </template>

                  <v-list-item-title>{{ doc.filename }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <div class="d-flex align-center gap-2 flex-wrap">
                      <span>{{ formatFileSize(doc.size_bytes) }}</span>
                      <span v-if="doc.classification">• {{ formatDocumentType(doc.classification) }}</span>
                      <span v-if="doc.source">• {{ formatSource(doc.source) }}</span>
                    </div>
                  </v-list-item-subtitle>

                  <template v-slot:append>
                    <div class="d-flex flex-column align-end gap-2">
                      <div class="d-flex align-center gap-1">
                        <status-badge :status="doc.processing_status" size="small" />
                        <v-chip
                          v-if="doc.extraction_status"
                          :color="getExtractionStatusColor(doc.extraction_status)"
                          size="x-small"
                          variant="tonal"
                        >
                          {{ formatExtractionStatus(doc.extraction_status) }}
                        </v-chip>
                      </div>
                      <v-btn
                        size="small"
                        variant="text"
                        color="primary"
                        @click.stop="viewDocument(doc.document_id)"
                      >
                        View
                      </v-btn>
                    </div>
                  </template>

                  <!-- Document Summary -->
                  <div v-if="doc.summary" class="mt-3 pa-3 bg-grey-lighten-5 rounded">
                    <p class="text-caption text-grey mb-1">Summary</p>
                    <p class="text-body-2">{{ doc.summary }}</p>
                  </div>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCasesStore } from '@/stores/cases'
import { documentsService } from '@/services/documentsService'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Document } from '@/types'

const route = useRoute()
const router = useRouter()
const casesStore = useCasesStore()

const caseId = computed(() => route.params.caseId as string)
const currentCase = computed(() => casesStore.currentCase)
const isLoading = computed(() => casesStore.isLoading)
const error = computed(() => casesStore.error)

const documents = ref<Document[]>([])
const documentsLoading = ref(false)
const documentsError = ref<string | null>(null)

onMounted(async () => {
  await loadCaseDetails()
  await loadDocuments()
})

async function loadCaseDetails() {
  try {
    await casesStore.fetchCase(caseId.value)
  } catch (err) {
    console.error('Failed to load case:', err)
  }
}

async function loadDocuments() {
  documentsLoading.value = true
  documentsError.value = null
  
  try {
    documents.value = await documentsService.getDocumentsByCase(caseId.value)
  } catch (err) {
    documentsError.value = err instanceof Error ? err.message : 'Failed to load documents'
    console.error('Failed to load documents:', err)
  } finally {
    documentsLoading.value = false
  }
}

function viewDocument(documentId: string) {
  console.log('viewDocument called with:', documentId, 'caseId:', caseId.value)
  const path = `/cases/${caseId.value}/documents/${documentId}`
  console.log('Navigating to:', path)
  router.push(path)
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDocumentType(type: string): string {
  const labels: Record<string, string> = {
    application_form: 'Application Form',
    financial_statement: 'Financial Statement',
    medical_report: 'Medical Report',
    identity_document: 'Identity Document',
    property_assessment: 'Property Assessment',
    bank_statement: 'Bank Statement',
    tax_return: 'Tax Return',
    insurance_policy: 'Insurance Policy',
    legal_document: 'Legal Document',
    other: 'Other'
  }
  return labels[type] || type
}

function formatSource(source: string): string {
  const labels: Record<string, string> = {
    main_upload: 'Main Upload',
    extracted: 'Extracted',
    manual_upload: 'Manual Upload'
  }
  return labels[source] || source
}

function formatProcessingStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function getDocumentIcon(contentType: string): { icon: string; color: string } {
  if (contentType.includes('pdf')) return { icon: 'mdi-file-pdf-box', color: 'red' }
  if (contentType.includes('word') || contentType.includes('document')) return { icon: 'mdi-file-word', color: 'blue' }
  if (contentType.includes('image')) return { icon: 'mdi-file-image', color: 'green' }
  return { icon: 'mdi-file-document', color: 'grey' }
}

function getExtractionStatusColor(status: string): string {
  switch (status) {
    case 'completed': return 'success'
    case 'skipped': return 'grey'
    case 'error': return 'error'
    case 'review_required': return 'warning'
    default: return 'info'
  }
}

function formatExtractionStatus(status: string): string {
  switch (status) {
    case 'completed': return 'Extracted'
    case 'skipped': return 'Skipped'
    case 'error': return 'Error'
    case 'review_required': return 'Review'
    default: return status
  }
}
</script>
