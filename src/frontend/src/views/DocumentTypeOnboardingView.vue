<template>
  <v-container fluid class="pa-6">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Document Type Onboarding</h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-6">
          Configure a new document type or update an existing one with extraction models and schemas
        </p>
      </v-col>
    </v-row>

    <v-row>
      <!-- Left Panel: Configuration -->
      <v-col cols="12" md="6">
        <v-card elevation="2">
          <v-card-title class="bg-primary">
            <v-icon start>mdi-cog</v-icon>
            Configuration
          </v-card-title>

          <v-card-text class="pa-6">
            <v-stepper v-model="currentStep" elevation="0">
              <v-stepper-header>
                <v-stepper-item :complete="currentStep > 1" :value="1" title="Upload & Configure" />
                <v-divider />
                <v-stepper-item :complete="currentStep > 2" :value="2" title="Test & Review" />
                <v-divider />
                <v-stepper-item :value="3" title="Finalize" />
              </v-stepper-header>

              <v-stepper-window>
                <!-- Step 1: Upload & Configure -->
                <v-stepper-window-item :value="1">
                  <v-card flat>
                    <v-card-text>
                      <h3 class="text-h6 mb-4">Upload & Configure Document Type</h3>

                      <!-- Mode Selection -->
                      <v-select
                        v-model="editMode"
                        :items="[
                          { title: 'Create New Document Type', value: 'create' },
                          { title: 'Edit Existing Document Type', value: 'edit' }
                        ]"
                        label="Mode"
                        variant="outlined"
                        class="mb-4"
                      />

                      <v-select
                        v-if="editMode === 'edit'"
                        v-model="selectedDocumentTypeId"
                        :items="documentTypes"
                        item-title="name"
                        item-value="id"
                        label="Select Document Type to Edit"
                        variant="outlined"
                        :loading="isLoadingDocumentTypes"
                        @update:model-value="loadDocumentTypeDetails"
                        class="mb-4"
                      />

                      <v-divider class="my-4" />

                      <!-- File Upload Section -->
                      <h4 class="text-subtitle-1 mb-3">Sample Document</h4>
                      <v-file-input
                        v-model="sampleFile"
                        label="Sample Document (PDF)"
                        accept=".pdf"
                        prepend-icon="mdi-file-pdf-box"
                        variant="outlined"
                        :disabled="isClassifying"
                        @update:model-value="onFileSelected"
                        class="mb-3"
                      />

                      <v-btn
                        color="primary"
                        :disabled="!sampleFile || isClassifying"
                        :loading="isClassifying"
                        @click="classifyDocument"
                        size="small"
                        class="mb-4"
                      >
                        <v-icon start>mdi-brain</v-icon>
                        Classify Document
                      </v-btn>

                      <v-alert v-if="classificationResult" type="success" class="mb-4" density="compact">
                        <div class="text-subtitle-2">Document Type: {{ classificationResult.suggested_name }}</div>
                        <div class="text-caption">Confidence: {{ (classificationResult.confidence * 100).toFixed(1) }}%</div>
                      </v-alert>

                      <v-divider class="my-4" />

                      <!-- Document Type Configuration -->
                      <h4 class="text-subtitle-1 mb-3">Document Type Details</h4>

                      <v-text-field
                        v-model="config.document_type_name"
                        label="Document Type Name *"
                        variant="outlined"
                        :rules="[v => !!v || 'Name is required']"
                        density="compact"
                        class="mb-3"
                      />

                      <v-textarea
                        v-model="config.description"
                        label="Description"
                        variant="outlined"
                        rows="2"
                        density="compact"
                        class="mb-3"
                      />

                      <v-text-field
                        v-model="config.version"
                        label="Version *"
                        variant="outlined"
                        placeholder="1.0.0"
                        :rules="[v => !!v || 'Version is required']"
                        density="compact"
                        class="mb-3"
                      />

                      <v-divider class="my-4" />

                      <!-- Extraction Model -->
                      <h4 class="text-subtitle-1 mb-3">Extraction Model</h4>

                      <v-select
                        v-model="selectedModel"
                        :items="extractionModels"
                        :item-title="(item) => `${item.name} (${item.version})`"
                        return-object
                        label="Select Extraction Model *"
                        variant="outlined"
                        :loading="isLoadingModels"
                        density="compact"
                        class="mb-3"
                      />

                      <v-chip
                        v-if="selectedModel"
                        color="primary"
                        class="mb-4"
                        closable
                        size="small"
                        @click:close="selectedModel = null"
                      >
                        {{ selectedModel.name }} - {{ selectedModel.type }}
                      </v-chip>

                      <v-divider class="my-4" />

                      <!-- Custom Prompt -->
                      <h4 class="text-subtitle-1 mb-3">Custom Extraction Prompt (Optional)</h4>
                      <v-textarea
                        v-model="config.custom_prompt"
                        label="Custom Prompt"
                        variant="outlined"
                        rows="3"
                        density="compact"
                        placeholder="Enter custom instructions for extraction..."
                        class="mb-3"
                      />

                      <v-divider class="my-4" />

                      <!-- Schema Definition -->
                      <h4 class="text-subtitle-1 mb-3">Schema Definition</h4>

                      <v-tabs v-model="schemaTab" class="mb-3" density="compact">
                        <v-tab value="input">Input Schema</v-tab>
                        <v-tab value="output">Output Schema</v-tab>
                      </v-tabs>

                      <v-window v-model="schemaTab">
                        <v-window-item value="input">
                          <v-textarea
                            v-model="inputSchemaJson"
                            label="Input Schema (JSON)"
                            variant="outlined"
                            rows="8"
                            density="compact"
                            placeholder='{"field_name": {"type": "string", "description": "..."}}'
                            class="mb-3 code-editor"
                          />
                        </v-window-item>

                        <v-window-item value="output">
                          <v-textarea
                            v-model="outputSchemaJson"
                            label="Output Schema (JSON)"
                            variant="outlined"
                            rows="8"
                            density="compact"
                            placeholder='{"field_name": {"type": "object"}}'
                            class="mb-3 code-editor"
                          />
                        </v-window-item>
                      </v-window>

                      <v-slider
                        v-model="config.confidence_threshold"
                        label="Confidence Threshold"
                        :min="0"
                        :max="1"
                        :step="0.05"
                        thumb-label
                        class="mb-3"
                      >
                        <template #append>
                          <v-text-field
                            v-model.number="config.confidence_threshold"
                            type="number"
                            style="width: 80px"
                            density="compact"
                            variant="outlined"
                            hide-details
                            :min="0"
                            :max="1"
                            :step="0.05"
                          />
                        </template>
                      </v-slider>

                      <v-divider class="my-4" />

                      <!-- Ground Truth -->
                      <h4 class="text-subtitle-1 mb-3">Ground Truth (Optional)</h4>
                      <p class="text-caption mb-3">Upload a JSON file with expected values for evaluation</p>
                      <v-file-input
                        v-model="groundTruthFile"
                        label="Ground Truth JSON (Optional)"
                        accept=".json"
                        prepend-icon="mdi-file-check"
                        variant="outlined"
                        density="compact"
                        clearable
                      />
                    </v-card-text>
                    
                    <!-- Show uploaded file info -->
                    <v-card-text class="text-caption">
                      <v-alert 
                        v-if="uploadedFile" 
                        type="success" 
                        density="compact"
                        class="mb-2"
                      >
                        <v-icon start size="small">mdi-check-circle</v-icon>
                        File ready: {{ uploadedFile.name }} ({{ (uploadedFile.size / 1024).toFixed(2) }} KB)
                      </v-alert>
                      <v-alert 
                        v-else 
                        type="warning" 
                        density="compact"
                        class="mb-2"
                      >
                        <v-icon start size="small">mdi-alert</v-icon>
                        No file uploaded - Please select a PDF file above
                      </v-alert>
                      
                      <!-- Debug button -->
                      <v-btn 
                        size="x-small" 
                        variant="outlined" 
                        @click="debugFileState"
                        class="mt-2"
                      >
                        Debug File State
                      </v-btn>
                    </v-card-text>
                    
                    <v-card-actions>
                      <v-spacer />
                      <v-btn
                        color="primary"
                        :disabled="!isConfigValid"
                        :loading="isTesting"
                        @click="() => { console.log('Button clicked!'); runTestExtraction(); }"
                      >
                        <v-icon start>mdi-test-tube</v-icon>
                        Test Extraction
                      </v-btn>
                    </v-card-actions>

                    <!-- Debug info -->
                    <v-card-text v-if="!isConfigValid" class="text-caption text-error">
                      <div>Validation Status:</div>
                      <div>✓ Document Type Name: {{ config.document_type_name ? 'Valid' : 'Missing' }}</div>
                      <div>✓ Version: {{ config.version ? 'Valid' : 'Missing' }}</div>
                      <div>✓ Model Selected: {{ selectedModel ? 'Valid' : 'Missing' }}</div>
                      <div>✓ Input Schema Fields: {{ Object.keys(parsedInputSchema).length }}</div>
                      <div>✓ Output Schema Fields: {{ Object.keys(parsedOutputSchema).length }}</div>
                      <div>✓ Sample File: {{ uploadedFile ? uploadedFile.name : 'Missing' }}</div>
                    </v-card-text>

                    <!-- Show uploaded file info -->
                    <v-card-text v-if="uploadedFile" class="text-caption">
                      <v-chip color="success" size="small">
                        <v-icon start size="small">mdi-check</v-icon>
                        File ready: {{ uploadedFile.name }}
                      </v-chip>
                    </v-card-text>
                  </v-card>
                </v-stepper-window-item>

                <!-- Step 2: Test & Review -->
                <v-stepper-window-item :value="2">
                  <v-card flat>
                    <v-card-text>
                      <h3 class="text-h6 mb-4">Test Results</h3>

                      <v-progress-linear v-if="isTesting" indeterminate color="primary" class="mb-4" />

                      <v-alert v-if="testError" type="error" class="mb-4">
                        {{ testError }}
                      </v-alert>

                      <div v-if="testResult && !isTesting">
                        <!-- Recommendation Badge -->
                        <v-chip
                          :color="getRecommendationColor(testResult.recommendation)"
                          size="large"
                          class="mb-4"
                        >
                          <v-icon start>{{ getRecommendationIcon(testResult.recommendation) }}</v-icon>
                          {{ testResult.recommendation.toUpperCase() }}
                        </v-chip>

                        <!-- Evaluation Metrics -->
                        <v-row v-if="testResult.evaluation" class="mb-4">
                          <v-col cols="4">
                            <v-card variant="outlined">
                              <v-card-text class="text-center">
                                <div class="text-h4">{{ (testResult.evaluation.average_confidence * 100).toFixed(1) }}%</div>
                                <div class="text-caption">Avg Confidence</div>
                              </v-card-text>
                            </v-card>
                          </v-col>
                          <v-col cols="4">
                            <v-card variant="outlined">
                              <v-card-text class="text-center">
                                <div class="text-h4">{{ (testResult.evaluation.completeness_score * 100).toFixed(1) }}%</div>
                                <div class="text-caption">Completeness</div>
                              </v-card-text>
                            </v-card>
                          </v-col>
                          <v-col cols="4">
                            <v-card variant="outlined">
                              <v-card-text class="text-center">
                                <div class="text-h4">{{ (testResult.evaluation.correctness_score * 100).toFixed(1) }}%</div>
                                <div class="text-caption">Correctness</div>
                              </v-card-text>
                            </v-card>
                          </v-col>
                        </v-row>

                        <v-divider class="my-4" />

                        <v-btn
                          v-if="testResult.recommendation !== 'finalize'"
                          color="primary"
                          variant="outlined"
                          @click="currentStep = 1"
                          class="mb-2"
                          block
                        >
                          <v-icon start>mdi-tune</v-icon>
                          Adjust Configuration
                        </v-btn>

                        <v-btn
                          color="primary"
                          variant="outlined"
                          @click="runTestExtraction"
                          class="mb-2"
                          block
                        >
                          <v-icon start>mdi-refresh</v-icon>
                          Re-run Test
                        </v-btn>

                        <v-btn
                          v-if="extractionModels.length > 1"
                          color="secondary"
                          variant="outlined"
                          @click="showModelComparison = true"
                          class="mb-2"
                          block
                        >
                          <v-icon start>mdi-compare</v-icon>
                          Compare Models (A/B Test)
                        </v-btn>
                      </div>
                    </v-card-text>

                    <v-card-actions>
                      <v-btn @click="currentStep = 1">Back</v-btn>
                      <v-spacer />
                      <v-btn
                        color="success"
                        :disabled="!testResult || isTesting"
                        @click="currentStep = 3"
                      >
                        Finalize
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-stepper-window-item>

                <!-- Step 3: Finalize -->
                <v-stepper-window-item :value="3">
                  <v-card flat>
                    <v-card-text>
                      <h3 class="text-h6 mb-4">Review & Finalize</h3>

                      <v-alert type="info" class="mb-4">
                        Review your configuration before finalizing the onboarding.
                      </v-alert>

                      <v-list>
                        <v-list-item>
                          <v-list-item-title>Document Type</v-list-item-title>
                          <v-list-item-subtitle>{{ config.document_type_name }}</v-list-item-subtitle>
                        </v-list-item>
                        <v-list-item>
                          <v-list-item-title>Version</v-list-item-title>
                          <v-list-item-subtitle>{{ config.version }}</v-list-item-subtitle>
                        </v-list-item>
                        <v-list-item>
                          <v-list-item-title>Extraction Model</v-list-item-title>
                          <v-list-item-subtitle>{{ selectedModel?.name }}</v-list-item-subtitle>
                        </v-list-item>
                        <v-list-item>
                          <v-list-item-title>Fields to Extract</v-list-item-title>
                          <v-list-item-subtitle>{{ Object.keys(parsedInputSchema).length }} fields</v-list-item-subtitle>
                        </v-list-item>
                      </v-list>

                      <v-alert v-if="finalizeError" type="error" class="mt-4">
                        {{ finalizeError }}
                      </v-alert>

                      <v-alert v-if="finalizeSuccess" type="success" class="mt-4">
                        {{ finalizeSuccess }}
                      </v-alert>
                    </v-card-text>

                    <v-card-actions>
                      <v-btn @click="currentStep = 2">Back</v-btn>
                      <v-spacer />
                      <v-btn
                        color="success"
                        :loading="isFinalizing"
                        :disabled="!!finalizeSuccess"
                        @click="finalizeOnboarding"
                      >
                        <v-icon start>mdi-check-circle</v-icon>
                        Complete Onboarding
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-stepper-window-item>
              </v-stepper-window>
            </v-stepper>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Right Panel: Results Preview -->
      <v-col cols="12" md="6">
        <v-card elevation="2" class="sticky-card">
          <v-card-title class="bg-secondary">
            <v-icon start>mdi-eye</v-icon>
            Extraction Results Preview
          </v-card-title>

          <v-card-text class="pa-6">
            <div v-if="!testResult" class="text-center text-medium-emphasis py-10">
              <v-icon size="64" color="grey-lighten-1">mdi-file-search</v-icon>
              <p class="mt-4">Run a test extraction to see results here</p>
            </div>

            <div v-else>
              <v-expansion-panels>
                <v-expansion-panel
                  v-for="field in testResult.extraction_result.fields"
                  :key="field.field_name"
                >
                  <v-expansion-panel-title>
                    <div class="d-flex align-center justify-space-between w-100">
                      <span class="font-weight-medium">{{ formatFieldName(field.field_name) }}</span>
                      <v-chip
                        size="small"
                        :color="getConfidenceColor(field.confidence)"
                        class="mr-2"
                      >
                        {{ (field.confidence * 100).toFixed(0) }}%
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-list density="compact">
                      <v-list-item>
                        <v-list-item-title>Value</v-list-item-title>
                        <v-list-item-subtitle>{{ formatValue(field.value) }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title>Type</v-list-item-title>
                        <v-list-item-subtitle>{{ field.value_type }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title>Model Source</v-list-item-title>
                        <v-list-item-subtitle>{{ field.model_source }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item v-if="field.needs_review">
                        <v-chip color="warning" size="small">
                          <v-icon start size="small">mdi-alert</v-icon>
                          Needs Review: {{ field.review_reason }}
                        </v-chip>
                      </v-list-item>
                    </v-list>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Model Comparison Dialog -->
    <v-dialog v-model="showModelComparison" max-width="1200" scrollable>
      <v-card>
        <v-card-title>
          <v-icon start>mdi-compare</v-icon>
          A/B Model Comparison
        </v-card-title>
        <v-card-text>
          <p class="mb-4">Compare extraction results from different models</p>

          <v-row>
            <v-col
              v-for="(result, index) in comparisonResults"
              :key="index"
              cols="12"
              md="6"
            >
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1">
                  Model {{ index + 1 }}
                  <v-chip
                    size="small"
                    :color="getRecommendationColor(result.recommendation)"
                    class="ml-2"
                  >
                    {{ result.recommendation }}
                  </v-chip>
                </v-card-title>
                <v-card-text>
                  <div v-if="result.evaluation">
                    <div class="mb-2">
                      <strong>Confidence:</strong> {{ (result.evaluation.average_confidence * 100).toFixed(1) }}%
                    </div>
                    <div class="mb-2">
                      <strong>Completeness:</strong> {{ (result.evaluation.completeness_score * 100).toFixed(1) }}%
                    </div>
                    <div>
                      <strong>Correctness:</strong> {{ (result.evaluation.correctness_score * 100).toFixed(1) }}%
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showModelComparison = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  onboardingService,
  type ClassifyDocumentResponse,
  type ExtractionModel,
  type OnboardingTestResponse,
  type OnboardingTestConfig,
  type DocumentType
} from '@/services/onboardingService'

const router = useRouter()

// State
const currentStep = ref(1)
const editMode = ref<'create' | 'edit'>('create')
const selectedDocumentTypeId = ref<string | null>(null)
const documentTypes = ref<DocumentType[]>([])
const isLoadingDocumentTypes = ref(false)

const sampleFile = ref<File | null>(null)
const uploadedFile = ref<File | null>(null)  // Store the actual file
const groundTruthFile = ref<File[] | null>(null)
const isClassifying = ref(false)
const classificationResult = ref<ClassifyDocumentResponse | null>(null)

const extractionModels = ref<ExtractionModel[]>([])
const selectedModel = ref<ExtractionModel | null>(null)
const isLoadingModels = ref(false)

const config = ref<OnboardingTestConfig>({
  document_type_name: '',
  description: '',
  version: '1.0.0',
  input_schema: {},
  output_schema: {},
  extraction_config: { models: [] },
  custom_prompt: '',
  citation_level: 'bounding_box',
  confidence_threshold: 0.7,
  created_by: 'admin@hsbc.com'
})

const inputSchemaJson = ref('{}')
const outputSchemaJson = ref('{}')
const schemaTab = ref('input')

const isTesting = ref(false)
const testResult = ref<OnboardingTestResponse | null>(null)
const testError = ref<string | null>(null)

const isFinalizing = ref(false)
const finalizeSuccess = ref<string | null>(null)
const finalizeError = ref<string | null>(null)

const showModelComparison = ref(false)
const comparisonResults = ref<OnboardingTestResponse[]>([])

// Computed
const file = computed(() => uploadedFile.value)
const groundTruthFileObj = computed(() =>
  groundTruthFile.value ? groundTruthFile.value[0] : null
)

const parsedInputSchema = computed(() => {
  try {
    return JSON.parse(inputSchemaJson.value)
  } catch {
    return {}
  }
})

const parsedOutputSchema = computed(() => {
  try {
    return JSON.parse(outputSchemaJson.value)
  } catch {
    return {}
  }
})

const isConfigValid = computed(() => {
  const valid = (
    config.value.document_type_name.trim() !== '' &&
    config.value.version.trim() !== '' &&
    selectedModel.value !== null &&
    Object.keys(parsedInputSchema.value).length > 0 &&
    Object.keys(parsedOutputSchema.value).length > 0 &&
    uploadedFile.value !== null  // Check if file is uploaded
  )
  console.log('isConfigValid check:', {
    name: config.value.document_type_name.trim() !== '',
    version: config.value.version.trim() !== '',
    model: selectedModel.value !== null,
    inputSchema: Object.keys(parsedInputSchema.value).length > 0,
    outputSchema: Object.keys(parsedOutputSchema.value).length > 0,
    file: uploadedFile.value !== null,
    result: valid
  })
  return valid
})

// Methods
onMounted(async () => {
  await loadExtractionModels()
  await loadDocumentTypes()
})

// Watch sampleFile for changes
watch(sampleFile, (newVal, oldVal) => {
  console.log('🔍 sampleFile watcher triggered')
  console.log('  Old value:', oldVal)
  console.log('  New value:', newVal)
  console.log('  Is File?', newVal instanceof File)
  
  if (newVal instanceof File) {
    uploadedFile.value = newVal
    console.log('✅ File stored from watcher:', {
      name: uploadedFile.value.name,
      size: uploadedFile.value.size,
      type: uploadedFile.value.type
    })
  } else {
    uploadedFile.value = null
    console.log('❌ File cleared from watcher - newVal is:', newVal)
  }
}, { immediate: true })

async function loadDocumentTypes() {
  isLoadingDocumentTypes.value = true
  try {
    documentTypes.value = await onboardingService.getDocumentTypes(true)
  } catch (error) {
    console.error('Failed to load document types:', error)
  } finally {
    isLoadingDocumentTypes.value = false
  }
}

async function loadDocumentTypeDetails() {
  if (!selectedDocumentTypeId.value) return

  try {
    const docType = await onboardingService.getDocumentType(selectedDocumentTypeId.value)
    const versions = await onboardingService.getSchemaVersions(selectedDocumentTypeId.value)

    if (versions.length > 0) {
      const latestVersion = versions[0]
      config.value.document_type_id = selectedDocumentTypeId.value
      config.value.document_type_name = docType.name
      config.value.description = docType.description || ''
      config.value.version = latestVersion.version
      inputSchemaJson.value = JSON.stringify(latestVersion.input_schema, null, 2)
      outputSchemaJson.value = JSON.stringify(latestVersion.output_schema, null, 2)
      config.value.extraction_config = latestVersion.extraction_config
      config.value.citation_level = latestVersion.citation_level
      config.value.confidence_threshold = latestVersion.confidence_threshold
    }
  } catch (error) {
    console.error('Failed to load document type details:', error)
  }
}

async function loadExtractionModels() {
  isLoadingModels.value = true
  try {
    extractionModels.value = await onboardingService.getExtractionModels(true)
  } catch (error) {
    console.error('Failed to load extraction models:', error)
  } finally {
    isLoadingModels.value = false
  }
}

function onFileSelected(file: File | null) {
  console.log('📤 onFileSelected triggered')
  console.log('  file parameter:', file)
  console.log('  sampleFile.value:', sampleFile.value)
  
  // Directly store the file when selected
  if (file instanceof File) {
    uploadedFile.value = file
    console.log('✅ File stored directly from onFileSelected:', {
      name: uploadedFile.value.name,
      size: uploadedFile.value.size,
      type: uploadedFile.value.type
    })
  } else {
    uploadedFile.value = null
    console.log('❌ File cleared from onFileSelected')
  }
  
  classificationResult.value = null
}

function debugFileState() {
  console.log('=== FILE STATE DEBUG ===')
  console.log('sampleFile.value:', sampleFile.value)
  console.log('uploadedFile.value:', uploadedFile.value)
  console.log('file computed:', file.value)
  console.log('isConfigValid:', isConfigValid.value)
  
  alert(`File State:\n\nsampleFile: ${sampleFile.value ? `${sampleFile.value.length} file(s)` : 'null'}\nuploadedFile: ${uploadedFile.value ? uploadedFile.value.name : 'null'}\nfile computed: ${file.value ? file.value.name : 'null'}`)
}

async function classifyDocument() {
  if (!uploadedFile.value) return

  isClassifying.value = true
  try {
    classificationResult.value = await onboardingService.classifyDocument(uploadedFile.value)
    if (editMode.value === 'create' && !config.value.document_type_name) {
      config.value.document_type_name = classificationResult.value.suggested_name
    }
  } catch (error) {
    console.error('Classification failed:', error)
  } finally {
    isClassifying.value = false
  }
}

async function runTestExtraction() {
  alert('runTestExtraction called! Check console for details.')
  console.log('=== TEST EXTRACTION START ===')
  console.log('runTestExtraction called')
  console.log('file.value:', file.value)
  console.log('isConfigValid.value:', isConfigValid.value)
  console.log('config:', config.value)
  console.log('selectedModel:', selectedModel.value)
  console.log('parsedInputSchema:', parsedInputSchema.value)
  console.log('parsedOutputSchema:', parsedOutputSchema.value)
  
  if (!file.value) {
    testError.value = 'Please upload a sample document first'
    console.error('Error: No file')
    return
  }
  
  if (!isConfigValid.value) {
    testError.value = 'Please complete all required configuration fields'
    console.error('Error: Config invalid')
    return
  }

  console.log('Setting isTesting to true')
  isTesting.value = true
  testError.value = null
  currentStep.value = 3
  console.log('Moved to step 3')

  try {
    // Update schemas from JSON
    config.value.input_schema = parsedInputSchema.value
    config.value.output_schema = parsedOutputSchema.value
    console.log('Updated schemas')

    // Update extraction config with selected model
    if (selectedModel.value) {
      config.value.extraction_config = {
        models: [
          {
            model_id: selectedModel.value.id,
            order: 1,
            strategy: 'primary',
            fields: ['*']
          }
        ],
        combination_strategy: 'sequential',
        conflict_resolution: 'flag_for_review'
      }
      console.log('Updated extraction config')
    }

    console.log('About to call testExtraction API...')
    console.log('Final config:', JSON.stringify(config.value, null, 2))

    testResult.value = await onboardingService.testExtraction(
      `test_${Date.now()}`,
      config.value,
      file.value,
      groundTruthFileObj.value || undefined
    )
    
    console.log('Test result received:', testResult.value)
    console.log('=== TEST EXTRACTION SUCCESS ===')
  } catch (error: any) {
    console.error('=== TEST EXTRACTION ERROR ===')
    console.error('Error:', error)
    console.error('Error response:', error.response)
    console.error('Error message:', error.message)
    testError.value = error.response?.data?.detail || error.message || 'Test extraction failed'
    console.error('Test extraction failed:', error)
  } finally {
    console.log('Setting isTesting to false')
    isTesting.value = false
    console.log('=== TEST EXTRACTION END ===')
  }
}

async function finalizeOnboarding() {
  if (!isConfigValid.value) return

  isFinalizing.value = true
  finalizeError.value = null
  finalizeSuccess.value = null

  try {
    const result = await onboardingService.finalizeOnboarding({
      document_type_id: editMode.value === 'edit' ? selectedDocumentTypeId.value || undefined : undefined,
      document_type_name: config.value.document_type_name,
      description: config.value.description,
      version: config.value.version,
      input_schema: parsedInputSchema.value,
      output_schema: parsedOutputSchema.value,
      extraction_config: config.value.extraction_config,
      custom_prompt: config.value.custom_prompt,
      citation_level: config.value.citation_level,
      confidence_threshold: config.value.confidence_threshold,
      created_by: config.value.created_by
    })

    finalizeSuccess.value = result.message

    // Redirect after success
    setTimeout(() => {
      router.push('/')
    }, 2000)
  } catch (error: any) {
    finalizeError.value = error.response?.data?.detail || error.message || 'Finalization failed'
    console.error('Finalization failed:', error)
  } finally {
    isFinalizing.value = false
  }
}

function formatFieldName(name: string): string {
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatValue(value: any): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'error'
}

function getRecommendationColor(recommendation: string): string {
  if (recommendation === 'finalize') return 'success'
  if (recommendation === 'adjust') return 'warning'
  return 'error'
}

function getRecommendationIcon(recommendation: string): string {
  if (recommendation === 'finalize') return 'mdi-check-circle'
  if (recommendation === 'adjust') return 'mdi-tune'
  return 'mdi-refresh'
}
</script>

<style scoped>
.sticky-card {
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 40px);
  overflow-y: auto;
}

.code-editor {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>
