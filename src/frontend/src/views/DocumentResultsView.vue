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
          <!-- Summary Card - at top -->
          <v-card v-if="effectiveSummary" class="mb-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-text-box-outline</v-icon>
              Summary
              <v-spacer />
              <!-- Summary Evaluation Score Badge -->
              <v-chip 
                v-if="summaryEvaluation?.final_composite_score != null" 
                :color="getSummaryEvaluationColor(summaryEvaluation.final_composite_score)"
                size="small"
              >
                {{ formatPercentage(summaryEvaluation.final_composite_score) }}
              </v-chip>
            </v-card-title>
            <v-card-text>
              <p class="text-body-2">{{ effectiveSummary }}</p>
              
              <!-- Summary Evaluation Details -->
              <v-expand-transition>
                <div v-if="summaryEvaluation && showSummaryEvaluation" class="mt-4">
                  <v-divider class="mb-3" />
                  <p class="text-caption text-grey mb-2">Evaluation Scores</p>
                  <v-row dense>
                    <v-col cols="4" v-if="summaryEvaluation.evaluations?.entity_coverage">
                      <div class="text-center">
                        <v-chip 
                          :color="getSummaryEvaluationColor(summaryEvaluation.evaluations.entity_coverage.score)"
                          size="x-small"
                          class="mb-1"
                        >
                          {{ formatPercentage(summaryEvaluation.evaluations.entity_coverage.score) }}
                        </v-chip>
                        <p class="text-caption text-grey">Coverage</p>
                      </div>
                    </v-col>
                    <v-col cols="4" v-if="summaryEvaluation.evaluations?.groundedness">
                      <div class="text-center">
                        <v-chip 
                          :color="getSummaryEvaluationColor(summaryEvaluation.evaluations.groundedness.score)"
                          size="x-small"
                          class="mb-1"
                        >
                          {{ formatPercentage(summaryEvaluation.evaluations.groundedness.score) }}
                        </v-chip>
                        <p class="text-caption text-grey">Grounded</p>
                      </div>
                    </v-col>
                    <v-col cols="4" v-if="summaryEvaluation.evaluations?.semantic_fidelity">
                      <div class="text-center">
                        <v-chip 
                          :color="getSummaryEvaluationColor(summaryEvaluation.evaluations.semantic_fidelity.score)"
                          size="x-small"
                          class="mb-1"
                        >
                          {{ formatPercentage(summaryEvaluation.evaluations.semantic_fidelity.score) }}
                        </v-chip>
                        <p class="text-caption text-grey">Fidelity</p>
                      </div>
                    </v-col>
                  </v-row>
                  
                  <!-- Feedback Section -->
                  <div class="mt-3">
                    <p class="text-caption text-grey mb-2">Feedback</p>
                    <div v-if="summaryEvaluation.evaluations?.entity_coverage?.feedback" class="mb-1">
                      <v-icon size="x-small" color="primary" class="mr-1">mdi-check-circle-outline</v-icon>
                      <span class="text-caption">{{ summaryEvaluation.evaluations.entity_coverage.feedback }}</span>
                    </div>
                    <div v-if="summaryEvaluation.evaluations?.groundedness?.feedback" class="mb-1">
                      <v-icon size="x-small" color="primary" class="mr-1">mdi-file-document-check-outline</v-icon>
                      <span class="text-caption">{{ summaryEvaluation.evaluations.groundedness.feedback }}</span>
                    </div>
                    <div v-if="summaryEvaluation.evaluations?.semantic_fidelity?.feedback" class="mb-1">
                      <v-icon size="x-small" color="primary" class="mr-1">mdi-text-box-check-outline</v-icon>
                      <span class="text-caption">{{ summaryEvaluation.evaluations.semantic_fidelity.feedback }}</span>
                    </div>
                  </div>
                </div>
              </v-expand-transition>
              
              <!-- Toggle evaluation details -->
              <v-btn 
                v-if="summaryEvaluation"
                variant="text" 
                size="x-small" 
                class="mt-2"
                @click="showSummaryEvaluation = !showSummaryEvaluation"
              >
                {{ showSummaryEvaluation ? 'Hide' : 'Show' }} evaluation details
                <v-icon end size="x-small">{{ showSummaryEvaluation ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </v-btn>
            </v-card-text>
          </v-card>

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
            
            <!-- PDF View Toggle -->
            <v-card-text class="py-2" v-if="hasExtractedFields">
              <v-btn-toggle 
                v-model="pdfViewMode" 
                mandatory 
                density="compact"
                color="primary"
                class="w-100"
              >
                <v-btn value="interactive" class="flex-grow-1" size="small">
                  <v-icon start size="small">mdi-cursor-default-click</v-icon>
                  Interactive
                </v-btn>
                <v-btn value="annotated" class="flex-grow-1" size="small">
                  <v-icon start size="small">mdi-pencil-box-outline</v-icon>
                  Annotated
                </v-btn>
                <v-btn value="original" class="flex-grow-1" size="small">
                  <v-icon start size="small">mdi-file-pdf-box</v-icon>
                  Original
                </v-btn>
              </v-btn-toggle>
              <p class="text-caption text-grey mt-2 mb-0" v-if="pdfViewMode === 'annotated' || pdfViewMode === 'interactive'">
                Hover to highlight, click to scroll to location in the PDF
              </p>
            </v-card-text>
            
            <!-- Extracted Fields -->
            <v-card-text v-if="extractedFields.length > 0">
              <v-list density="compact" class="extraction-list">
                <v-list-item 
                  v-for="(field, index) in extractedFields" 
                  :key="index"
                  class="extraction-field mb-2 pa-3"
                  :class="{ 
                    'needs-review': field.needs_review,
                    'selected': selectedField === field.field_name,
                    'clickable': field.citations?.length > 0
                  }"
                  :style="getFieldStyle(field)"
                  rounded
                  @click="toggleFieldHighlight(field)"
                >
                  <v-list-item-title class="field-name text-caption text-grey-darken-1 text-uppercase">
                    {{ formatFieldName(field.field_name) }}
                  </v-list-item-title>
                  
                  <v-list-item-subtitle class="field-value text-body-1 font-weight-medium mt-1">
                    {{ formatFieldValue(field.value) }}
                  </v-list-item-subtitle>
                  
                  <template v-slot:append>
                    <div class="d-flex flex-column align-end">
                      <!-- Evaluation Indicators -->
                      <div class="d-flex gap-1 mb-1" v-if="getFieldEvaluation(field.field_name)">
                        <v-tooltip location="left">
                          <template v-slot:activator="{ props }">
                            <v-chip 
                              v-bind="props"
                              :color="getEvaluationColor(getFieldEvaluation(field.field_name)?.evaluations.correctness?.score)"
                              size="small"
                              density="compact"
                              label
                            >
                              <v-icon start size="x-small">mdi-check-circle</v-icon>
                              {{ formatPercentage(getFieldEvaluation(field.field_name)?.evaluations.correctness?.score) }}
                            </v-chip>
                          </template>
                          <span>Correctness Score</span>
                        </v-tooltip>
                        <v-tooltip location="left" v-if="getFieldEvaluation(field.field_name)?.evaluations.completeness">
                          <template v-slot:activator="{ props }">
                            <v-chip 
                              v-bind="props"
                              :color="getEvaluationColor(getFieldEvaluation(field.field_name)?.evaluations.completeness?.score)"
                              size="small"
                              density="compact"
                              label
                            >
                              <v-icon start size="x-small">mdi-format-list-checks</v-icon>
                              {{ formatPercentage(getFieldEvaluation(field.field_name)?.evaluations.completeness?.score) }}
                            </v-chip>
                          </template>
                          <span>Completeness Score</span>
                        </v-tooltip>
                      </div>
                      <div class="d-flex align-center">
                        <v-tooltip v-if="field.citations?.length" location="left">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="x-small" color="grey" class="mr-1">
                              mdi-file-document-outline
                            </v-icon>
                          </template>
                          <span>Page {{ field.citations[0]?.page }}</span>
                        </v-tooltip>
                        <v-icon 
                          v-if="highlightedField === field.field_name"
                          size="x-small" 
                          color="primary"
                        >
                          mdi-eye
                        </v-icon>
                      </div>
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

          <!-- Evaluation Metrics Card -->
          <v-card class="mb-4" v-if="document.extraction?.evaluation">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-clipboard-check-outline</v-icon>
              Evaluation Metrics
              <v-spacer />
              <v-btn 
                icon 
                size="x-small" 
                variant="text"
                @click="evaluationExpanded = !evaluationExpanded"
              >
                <v-icon>{{ evaluationExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </v-btn>
            </v-card-title>
            
            <v-expand-transition>
              <div v-show="evaluationExpanded">
                <v-card-text>
                  <!-- Aggregate Summary -->
                  <div class="mb-4">
                    <v-row dense>
                      <!-- Overall Score -->
                      <v-col cols="12">
                        <div class="d-flex align-center mb-2">
                          <span class="text-caption text-grey mr-2">Overall Quality</span>
                          <v-spacer />
                          <v-chip 
                            :color="getEvaluationColor(document.extraction.evaluation.aggregate_summary.average_overall_score)"
                            size="small"
                          >
                            {{ formatPercentage(document.extraction.evaluation.aggregate_summary.average_overall_score) }}
                          </v-chip>
                        </div>
                        <v-progress-linear
                          :model-value="document.extraction.evaluation.aggregate_summary.average_overall_score * 100"
                          :color="getEvaluationColor(document.extraction.evaluation.aggregate_summary.average_overall_score)"
                          height="8"
                          rounded
                        />
                      </v-col>
                      
                      <!-- Correctness Score -->
                      <v-col cols="12">
                        <div class="d-flex align-center mb-2">
                          <v-icon size="small" class="mr-1">mdi-check-circle</v-icon>
                          <span class="text-caption text-grey mr-2">Correctness</span>
                          <v-spacer />
                          <v-chip 
                            :color="getEvaluationColor(document.extraction.evaluation.aggregate_summary.average_correctness_score)"
                            size="small"
                          >
                            {{ formatPercentage(document.extraction.evaluation.aggregate_summary.average_correctness_score) }}
                          </v-chip>
                        </div>
                        <v-progress-linear
                          :model-value="document.extraction.evaluation.aggregate_summary.average_correctness_score * 100"
                          :color="getEvaluationColor(document.extraction.evaluation.aggregate_summary.average_correctness_score)"
                          height="8"
                          rounded
                        />
                      </v-col>
                      
                      <!-- Completeness Score -->
                      <v-col cols="12" v-if="document.extraction.evaluation.aggregate_summary.average_completeness_score !== null">
                        <div class="d-flex align-center mb-2">
                          <v-icon size="small" class="mr-1">mdi-format-list-checks</v-icon>
                          <span class="text-caption text-grey mr-2">Completeness</span>
                          <v-spacer />
                          <v-chip 
                            :color="getEvaluationColor(document.extraction.evaluation.aggregate_summary.average_completeness_score)"
                            size="small"
                          >
                            {{ formatPercentage(document.extraction.evaluation.aggregate_summary.average_completeness_score) }}
                          </v-chip>
                        </div>
                        <v-progress-linear
                          :model-value="document.extraction.evaluation.aggregate_summary.average_completeness_score * 100"
                          :color="getEvaluationColor(document.extraction.evaluation.aggregate_summary.average_completeness_score)"
                          height="8"
                          rounded
                        />
                      </v-col>
                    </v-row>
                  </div>
                  
                  <!-- Statistics -->
                  <v-divider class="mb-3" />
                  <v-row dense class="text-center">
                    <v-col cols="4">
                      <div class="text-h6 font-weight-bold">{{ document.extraction.evaluation.total_fields }}</div>
                      <div class="text-caption text-grey">Fields Evaluated</div>
                    </v-col>
                    <v-col cols="4">
                      <div class="text-h6 font-weight-bold text-success">
                        {{ document.extraction.evaluation.aggregate_summary.fields_correct }}
                      </div>
                      <div class="text-caption text-grey">Correct</div>
                    </v-col>
                    <v-col cols="4" v-if="document.extraction.evaluation.aggregate_summary.average_completeness_score !== null">
                      <div class="text-h6 font-weight-bold text-info">
                        {{ document.extraction.evaluation.aggregate_summary.fields_complete }}
                      </div>
                      <div class="text-caption text-grey">Complete</div>
                    </v-col>
                  </v-row>
                  
                  <!-- Warnings -->
                  <v-alert 
                    v-if="document.extraction.evaluation.aggregate_summary.failed_evaluations > 0"
                    type="warning" 
                    variant="tonal"
                    density="compact"
                    class="mt-3"
                  >
                    {{ document.extraction.evaluation.aggregate_summary.failed_evaluations }} evaluation(s) failed
                  </v-alert>
                </v-card-text>
              </div>
            </v-expand-transition>
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
              {{ pdfViewModeTitle }}
              <v-chip 
                v-if="(pdfViewMode === 'annotated' || pdfViewMode === 'interactive') && selectedField" 
                size="small" 
                color="primary"
                class="ml-2"
                closable
                @click:close="clearHighlight"
              >
                <v-icon start size="x-small">mdi-target</v-icon>
                {{ formatFieldName(selectedField) }}
              </v-chip>
              <v-spacer />
              <v-btn 
                variant="text" 
                size="small"
                icon="mdi-refresh"
                @click="refreshPdf"
                title="Refresh PDF"
                :loading="isLoadingPdf"
              />
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
              <!-- Interactive PDF Viewer with click-based selection -->
              <template v-if="pdfViewMode === 'interactive'">
                <pdf-viewer-with-highlights
                  ref="interactivePdfViewerRef"
                  :case-id="caseId"
                  :document-id="documentId"
                  :fields="extractedFields"
                  :field-colors="fieldColors"
                  :selected-field="selectedField"
                  :num-pages="documentNumPages"
                  @select-field="handleFieldSelect"
                  @loaded="onInteractivePdfLoaded"
                  @error="onInteractivePdfError"
                />
              </template>
              
              <!-- Annotated/Original PDF iframe view -->
              <template v-if="pdfViewMode !== 'interactive'">
                <div v-if="isLoadingPdf" class="pdf-loading d-flex align-center justify-center">
                  <v-progress-circular indeterminate color="primary" />
                  <span class="ml-3">{{ pdfViewMode === 'annotated' ? 'Generating annotated PDF...' : 'Loading document...' }}</span>
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
                  v-else-if="currentPdfUrl"
                  :key="pdfKey"
                  :src="currentPdfUrl"
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
              </template>
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
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import { documentsService } from '@/services/documentsService'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import PdfViewerWithHighlights from '@/components/pdf/PdfViewerWithHighlights.vue'
import { formatConfidence, getConfidenceColor } from '@/utils/formatters'
import { DOCUMENT_TYPE_LABELS } from '@/utils/constants'
import apiClient from '@/services/api'
import type { ExtractedFieldResult, FieldColorInfo, FieldEvaluationResult } from '@/types/document'

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

// Document summary from summaries collection
const documentSummary = ref<string | null>(null)

// Summarization evaluation state
const showSummaryEvaluation = ref(false)

// PDF Viewer state
const pdfViewMode = ref<'interactive' | 'annotated' | 'original'>('interactive')
const originalPdfUrl = ref<string | null>(null)  // Direct Azure Blob URL (for iframe)
const originalPdfBlobUrl = ref<string | null>(null)  // Blob URL for PDF.js (no CORS issues)
const annotatedPdfUrl = ref<string | null>(null)
const isLoadingPdf = ref(false)
const pdfError = ref<string | null>(null)
const pdfKey = ref(0) // Force iframe refresh
const interactivePdfViewerRef = ref<InstanceType<typeof PdfViewerWithHighlights> | null>(null)

// Field selection (click-based)
const selectedField = ref<string | null>(null)
const highlightedField = ref<string | null>(null)  // For annotated PDF mode
const hoveredField = ref<string | null>(null)
const fieldColors = ref<Record<string, FieldColorInfo>>({})

// Evaluation state
const evaluationExpanded = ref(true)

// Computed properties
const currentPdfUrl = computed(() => {
  if (pdfViewMode.value === 'annotated' && annotatedPdfUrl.value) {
    return annotatedPdfUrl.value
  }
  return originalPdfUrl.value
})

const pdfViewModeTitle = computed(() => {
  switch (pdfViewMode.value) {
    case 'interactive': return 'Interactive View'
    case 'annotated': return 'Annotated Document'
    default: return 'Document Preview'
  }
})

const hasExtractedFields = computed(() => {
  return extractedFields.value.length > 0
})

// Compute the number of pages from citation data
const documentNumPages = computed(() => {
  let maxPage = 0
  for (const field of extractedFields.value) {
    if (field.citations?.length) {
      for (const citation of field.citations) {
        if (citation.page > maxPage) {
          maxPage = citation.page
        }
      }
    }
  }
  return maxPage || 3 // Default to 3 if no citations
})

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

// Effective summary - prefer fetched summary from summaries collection, fallback to document.summary
const effectiveSummary = computed(() => {
  return documentSummary.value || document.value?.summary || null
})

// Summarization evaluation from document
const summaryEvaluation = computed(() => {
  return document.value?.summarization_evaluation || null
})

// Get color for summary evaluation score
function getSummaryEvaluationColor(score: number): string {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'error'
}

// Format percentage
function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${Math.round(value * 100)}%`
}

onMounted(async () => {
  await documentsStore.fetchDocument(props.caseId, props.documentId)
  // Auto-load PDF preview when document is ready
  if (document.value?.processing_status === 'completed') {
    loadPdfPreview()
    loadFieldColors()
    loadDocumentSummary()
  }
})

// Load document summary from summaries collection
async function loadDocumentSummary() {
  try {
    const summaryData = await documentsService.getDocumentSummary(props.caseId, props.documentId)
    documentSummary.value = summaryData.summary
  } catch (err) {
    console.error('Failed to load document summary:', err)
  }
}

// Watch for processing status changes
watch(
  () => document.value?.processing_status,
  (status) => {
    if (status === 'completed' && !originalPdfUrl.value) {
      loadPdfPreview()
      loadFieldColors()
      loadDocumentSummary()
    }
  }
)

// Watch for PDF view mode changes
watch(pdfViewMode, async () => {
  // Force iframe refresh when switching modes
  pdfKey.value++
  
  if (pdfViewMode.value === 'annotated') {
    if (!annotatedPdfUrl.value) {
      await loadAnnotatedPdf()
    }
  } else if (pdfViewMode.value === 'original') {
    // Clear highlight when switching to original
    highlightedField.value = null
    hoveredField.value = null
  }
  // Interactive mode uses originalPdfUrl with client-side overlays
})

// Watch for highlighted field changes
watch(highlightedField, async () => {
  if (pdfViewMode.value === 'annotated') {
    await loadAnnotatedPdf()
  }
})

function goBack() {
  router.push(`/cases/${props.caseId}`)
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

// Evaluation helper functions
function getFieldEvaluation(fieldName: string) {
  if (!document.value?.extraction?.evaluation?.results) return null
  return document.value.extraction.evaluation.results.find(r => r.field_name === fieldName)
}

function getEvaluationColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'grey'
  if (score >= 0.8) return 'success'
  if (score >= 0.5) return 'warning'
  return 'error'
}

function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return '—'
  return score.toFixed(2)
}

function getFieldStyle(field: ExtractedFieldResult) {
  const isSelected = selectedField.value === field.field_name
  
  if (isSelected) {
    const color = fieldColors.value[field.field_name]
    if (color) {
      return {
        borderLeft: `4px solid ${color.hex}`,
        backgroundColor: `${color.hex}25`,
        boxShadow: `0 0 8px ${color.hex}50`,
      }
    }
    return {
      borderLeft: '4px solid #1976d2',
      backgroundColor: '#1976d225',
      boxShadow: '0 0 8px #1976d250',
    }
  }
  return {}
}

// Interactive PDF viewer events
function onInteractivePdfLoaded() {
  console.log('Interactive PDF viewer loaded')
}

function onInteractivePdfError(errorMsg: string) {
  console.error('Interactive PDF viewer error:', errorMsg)
  // Don't auto-switch, let user see the error and decide
  pdfError.value = errorMsg
}

// Handle field selection from PDF viewer or extraction list
function handleFieldSelect(fieldName: string | null) {
  selectedField.value = fieldName
  highlightedField.value = fieldName  // Also set for annotated PDF
}

function toggleFieldHighlight(field: ExtractedFieldResult) {
  if (!field.citations?.length) return
  
  if (selectedField.value === field.field_name) {
    // Deselect
    selectedField.value = null
    highlightedField.value = null
  } else {
    // Select
    selectedField.value = field.field_name
    highlightedField.value = field.field_name
    // Switch to interactive view if in original
    if (pdfViewMode.value === 'original') {
      pdfViewMode.value = 'interactive'
    }
  }
}

function clearHighlight() {
  selectedField.value = null
  highlightedField.value = null
}

async function loadFieldColors() {
  try {
    const response = await apiClient.get(
      `/cases/${props.caseId}/documents/${props.documentId}/field-colors`
    )
    if (response.data?.fields) {
      fieldColors.value = response.data.fields
    }
  } catch (err) {
    console.warn('Failed to load field colors:', err)
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
    
    // Load original PDF URL (for iframe views)
    const response = await apiClient.get(`/cases/${props.caseId}/documents/${props.documentId}/download`)
    if (response.data?.download_url) {
      originalPdfUrl.value = response.data.download_url
    }
    
    // Also load PDF as blob for interactive view (avoids CORS issues)
    await loadPdfAsBlob()
    
    // Also load annotated PDF if we have extraction results
    if (hasExtractedFields.value && pdfViewMode.value === 'annotated') {
      await loadAnnotatedPdf()
    }
  } catch (err) {
    console.error('Failed to load PDF preview:', err)
    pdfError.value = 'Failed to load document. Please try again.'
  } finally {
    isLoadingPdf.value = false
  }
}

async function loadPdfAsBlob() {
  try {
    // Fetch PDF through backend API as blob (bypasses CORS)
    const response = await apiClient.get(
      `/cases/${props.caseId}/documents/${props.documentId}/content`,
      { responseType: 'blob' }
    )
    
    // Create blob URL
    const blob = new Blob([response.data], { type: 'application/pdf' })
    
    // Revoke previous blob URL if exists
    if (originalPdfBlobUrl.value) {
      URL.revokeObjectURL(originalPdfBlobUrl.value)
    }
    
    originalPdfBlobUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    console.warn('Failed to load PDF as blob:', err)
    // Not critical - interactive view will show error and user can use annotated view
  }
}

async function loadAnnotatedPdf() {
  try {
    isLoadingPdf.value = true
    pdfError.value = null
    
    // Build URL with query params
    let url = `/cases/${props.caseId}/documents/${props.documentId}/annotated-pdf?show_labels=true`
    if (highlightedField.value) {
      url += `&highlight_field=${encodeURIComponent(highlightedField.value)}`
    }
    
    // Get annotated PDF as blob
    const response = await apiClient.get(url, {
      responseType: 'blob'
    })
    
    // Create blob URL for the annotated PDF
    const blob = new Blob([response.data], { type: 'application/pdf' })
    
    // Revoke previous URL if exists
    if (annotatedPdfUrl.value) {
      URL.revokeObjectURL(annotatedPdfUrl.value)
    }
    
    annotatedPdfUrl.value = URL.createObjectURL(blob)
    pdfKey.value++ // Force iframe refresh
  } catch (err: any) {
    console.error('Failed to load annotated PDF:', err)
    // Fall back to original PDF
    if (err.response?.status === 400) {
      // Document doesn't support annotation, use original
      pdfViewMode.value = 'original'
    } else {
      pdfError.value = 'Failed to generate annotated PDF. Showing original.'
      pdfViewMode.value = 'original'
    }
  } finally {
    isLoadingPdf.value = false
  }
}

async function refreshPdf() {
  if (pdfViewMode.value === 'annotated') {
    await loadAnnotatedPdf()
  } else {
    await loadPdfPreview()
  }
}

function openInNewTab() {
  if (currentPdfUrl.value) {
    window.open(currentPdfUrl.value, '_blank')
  } else {
    downloadDocument()
  }
}

// Cleanup blob URLs on unmount
onUnmounted(() => {
  if (annotatedPdfUrl.value) {
    URL.revokeObjectURL(annotatedPdfUrl.value)
  }
  if (originalPdfBlobUrl.value) {
    URL.revokeObjectURL(originalPdfBlobUrl.value)
  }
})
</script>

<style scoped>
.extraction-list {
  background: transparent;
}

.extraction-field {
  background: #fafafa;
  border: 1px solid #e0e0e0;
  transition: all 0.2s ease;
}

.extraction-field.clickable {
  cursor: pointer;
}

.extraction-field.clickable:hover {
  background: #f0f0f0;
  transform: translateX(2px);
}

.extraction-field.needs-review {
  background: #fff8e1;
  border-color: #ffcc80;
}

.extraction-field.selected {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  transform: scale(1.01);
  transition: all 0.2s ease;
}

.field-name {
  letter-spacing: 0.5px;
}

.field-value {
  color: #1a1a1a;
}

/* Evaluation chip spacing */
.gap-1 {
  gap: 4px;
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
