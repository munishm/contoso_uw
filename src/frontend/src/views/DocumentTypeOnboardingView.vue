<template>
  <v-container fluid class="pa-6">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Document Type Onboarding + Evaluation (Admin only)</h1>
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
                        @update:model-value="onFileSelected"
                        class="mb-3"
                      />

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
                        :disabled="editMode === 'edit'"
                        :hint="editMode === 'edit' ? 'Version auto-incremented for edits' : ''"
                        persistent-hint
                        density="compact"
                        class="mb-3"
                      />

                      <v-divider class="my-4" />

                      <!-- Extraction Models (Multi-Model Support) -->
                      <h4 class="text-subtitle-1 mb-3">
                        Extraction Models
                        <v-chip size="x-small" color="info" class="ml-2">Multi-Model</v-chip>
                      </h4>

                      <v-alert type="info" density="compact" class="mb-3">
                        Add one or more models for extraction. Use strategies to define how models work together.
                      </v-alert>

                      <!-- Configured Models List -->
                      <v-card v-if="configuredModels.length > 0" variant="outlined" class="mb-3">
                        <v-list density="compact">
                          <v-list-item
                            v-for="(modelConfig, index) in configuredModels"
                            :key="index"
                          >
                            <template #prepend>
                              <v-avatar :color="getStrategyColor(modelConfig.strategy)" size="32">
                                <span class="text-caption">{{ modelConfig.order }}</span>
                              </v-avatar>
                            </template>
                            <v-list-item-title>
                              {{ getModelName(modelConfig.model_id) }}
                            </v-list-item-title>
                            <v-list-item-subtitle>
                              <v-chip size="x-small" :color="getStrategyColor(modelConfig.strategy)" class="mr-1">
                                {{ modelConfig.strategy }}
                              </v-chip>
                              <span class="text-caption">
                                Fields: {{ modelConfig.fields.join(', ') }}
                              </span>
                            </v-list-item-subtitle>
                            <template #append>
                              <v-btn
                                icon="mdi-pencil"
                                size="x-small"
                                variant="text"
                                @click="editModelConfig(index)"
                              />
                              <v-btn
                                icon="mdi-delete"
                                size="x-small"
                                variant="text"
                                color="error"
                                @click="removeModelConfig(index)"
                              />
                            </template>
                          </v-list-item>
                        </v-list>
                      </v-card>

                      <!-- Add Model Form -->
                      <v-card variant="outlined" class="mb-3 pa-3">
                        <h5 class="text-subtitle-2 mb-2">
                          {{ editingModelIndex !== null ? 'Edit Model' : 'Add Model' }}
                        </h5>
                        <v-row dense>
                          <v-col cols="12">
                            <v-select
                              v-model="newModelConfig.model_id"
                              :items="extractionModels"
                              :item-title="(item) => `${item.name} (${item.version})`"
                              item-value="id"
                              label="Select Model *"
                              variant="outlined"
                              :loading="isLoadingModels"
                              density="compact"
                            />
                          </v-col>
                          <v-col cols="6">
                            <v-select
                              v-model="newModelConfig.strategy"
                              :items="modelStrategies"
                              label="Strategy *"
                              variant="outlined"
                              density="compact"
                            />
                          </v-col>
                          <v-col cols="6">
                            <v-text-field
                              v-model.number="newModelConfig.order"
                              type="number"
                              label="Order"
                              variant="outlined"
                              density="compact"
                              min="1"
                            />
                          </v-col>
                          <v-col cols="12">
                            <v-combobox
                              v-model="newModelConfig.fields"
                              :items="availableFields"
                              label="Fields (use * for all)"
                              variant="outlined"
                              density="compact"
                              multiple
                              chips
                              closable-chips
                              hint="Select fields this model should extract"
                            />
                          </v-col>
                          <v-col cols="12" class="d-flex justify-end">
                            <v-btn
                              v-if="editingModelIndex !== null"
                              variant="text"
                              class="mr-2"
                              @click="cancelEditModelConfig"
                            >
                              Cancel
                            </v-btn>
                            <v-btn
                              color="primary"
                              variant="tonal"
                              :disabled="!newModelConfig.model_id"
                              @click="addOrUpdateModelConfig"
                            >
                              <v-icon start>{{ editingModelIndex !== null ? 'mdi-check' : 'mdi-plus' }}</v-icon>
                              {{ editingModelIndex !== null ? 'Update Model' : 'Add Model' }}
                            </v-btn>
                          </v-col>
                        </v-row>
                      </v-card>

                      <!-- Multi-Model Settings (shown when 2+ models) -->
                      <v-expand-transition>
                        <v-card v-if="configuredModels.length > 1" variant="outlined" class="mb-3 pa-3">
                          <h5 class="text-subtitle-2 mb-2">Multi-Model Settings</h5>
                          <v-row dense>
                            <v-col cols="6">
                              <v-select
                                v-model="multiModelSettings.combination_strategy"
                                :items="combinationStrategies"
                                label="Combination Strategy"
                                variant="outlined"
                                density="compact"
                              />
                            </v-col>
                            <v-col cols="6">
                              <v-select
                                v-model="multiModelSettings.conflict_resolution"
                                :items="conflictResolutions"
                                label="Conflict Resolution"
                                variant="outlined"
                                density="compact"
                              />
                            </v-col>
                          </v-row>
                          <v-alert type="info" density="compact" class="mt-2">
                            <strong>{{ multiModelSettings.combination_strategy }}:</strong>
                            {{ getCombinationDescription(multiModelSettings.combination_strategy) }}
                          </v-alert>
                        </v-card>
                      </v-expand-transition>

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

                      <!-- Schema Definition - Simple Field Editor -->
                      <h4 class="text-subtitle-1 mb-3">
                        Schema Fields
                        <v-chip size="x-small" color="info" class="ml-2">{{ schemaFields.length }} fields</v-chip>
                      </h4>

                      <v-alert type="info" density="compact" class="mb-3">
                        Define the fields to extract. The full JSON schema will be generated automatically.
                      </v-alert>

                      <!-- Existing Fields List -->
                      <v-card v-if="schemaFields.length > 0" variant="outlined" class="mb-3">
                        <v-list density="compact">
                          <v-list-item
                            v-for="(field, index) in schemaFields"
                            :key="index"
                          >
                            <template #prepend>
                              <v-icon :color="getFieldTypeColor(field.type)">{{ getFieldTypeIcon(field.type) }}</v-icon>
                            </template>
                            <v-list-item-title>{{ field.name }}</v-list-item-title>
                            <v-list-item-subtitle>
                              <v-chip size="x-small" :color="getFieldTypeColor(field.type)" class="mr-1">
                                {{ field.type }}
                              </v-chip>
                              <v-chip v-if="field.required" size="x-small" color="error" class="mr-1">required</v-chip>
                              <span v-if="field.description" class="text-caption">{{ field.description }}</span>
                            </v-list-item-subtitle>
                            <template #append>
                              <v-btn
                                icon="mdi-pencil"
                                size="x-small"
                                variant="text"
                                @click="editSchemaField(index)"
                              />
                              <v-btn
                                icon="mdi-delete"
                                size="x-small"
                                variant="text"
                                color="error"
                                @click="removeSchemaField(index)"
                              />
                            </template>
                          </v-list-item>
                        </v-list>
                      </v-card>

                      <!-- Add/Edit Field Form -->
                      <v-card variant="outlined" class="mb-3 pa-3">
                        <h5 class="text-subtitle-2 mb-2">
                          {{ editingFieldIndex !== null ? 'Edit Field' : 'Add Field' }}
                        </h5>
                        <v-row dense>
                          <v-col cols="6">
                            <v-text-field
                              v-model="newField.name"
                              label="Field Name *"
                              variant="outlined"
                              density="compact"
                              placeholder="e.g., customer_name"
                              :rules="[v => !!v || 'Required', v => /^[a-z][a-z0-9_]*$/.test(v) || 'Use snake_case']"
                            />
                          </v-col>
                          <v-col cols="6">
                            <v-select
                              v-model="newField.type"
                              :items="fieldTypes"
                              label="Type *"
                              variant="outlined"
                              density="compact"
                            />
                          </v-col>
                          <v-col cols="12">
                            <v-text-field
                              v-model="newField.description"
                              label="Description (helps AI understand the field)"
                              variant="outlined"
                              density="compact"
                              placeholder="e.g., Full name of the customer"
                            />
                          </v-col>
                          <v-col cols="6">
                            <v-checkbox
                              v-model="newField.required"
                              label="Required field"
                              density="compact"
                              hide-details
                            />
                          </v-col>
                          <v-col cols="6" class="d-flex justify-end align-center">
                            <v-btn
                              v-if="editingFieldIndex !== null"
                              variant="text"
                              size="small"
                              class="mr-2"
                              @click="cancelEditField"
                            >
                              Cancel
                            </v-btn>
                            <v-btn
                              color="primary"
                              variant="tonal"
                              size="small"
                              :disabled="!newField.name || !newField.type"
                              @click="addOrUpdateField"
                            >
                              <v-icon start>{{ editingFieldIndex !== null ? 'mdi-check' : 'mdi-plus' }}</v-icon>
                              {{ editingFieldIndex !== null ? 'Update' : 'Add Field' }}
                            </v-btn>
                          </v-col>
                        </v-row>
                      </v-card>

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
                          <v-col cols="6">
                            <v-card variant="outlined">
                              <v-card-text class="text-center">
                                <div class="text-h4">{{ (testResult.evaluation.completeness_score * 100).toFixed(1) }}%</div>
                                <div class="text-caption">Completeness</div>
                              </v-card-text>
                            </v-card>
                          </v-col>
                          <v-col cols="6">
                            <v-card variant="outlined">
                              <v-card-text class="text-center">
                                <div class="text-h4">{{ (testResult.evaluation.correctness_score * 100).toFixed(1) }}%</div>
                                <div class="text-caption">Correctness</div>
                              </v-card-text>
                            </v-card>
                          </v-col>
                        </v-row>

                        <v-divider class="my-4" />

                        <!-- Action Buttons -->
                        <v-btn
                          color="primary"
                          variant="outlined"
                          @click="runTestExtraction"
                          :loading="isTesting"
                          class="mb-2"
                          block
                        >
                          <v-icon start>mdi-refresh</v-icon>
                          Re-run Test Extraction
                        </v-btn>

                        <v-btn
                          v-if="testResult.recommendation !== 'finalize'"
                          color="warning"
                          variant="outlined"
                          @click="currentStep = 1"
                          class="mb-2"
                          block
                        >
                          <v-icon start>mdi-tune</v-icon>
                          Adjust Configuration
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

// Multi-Model Configuration
interface ModelConfig {
  model_id: string
  order: number
  strategy: 'primary' | 'fallback' | 'parallel'
  fields: string[]
}

const configuredModels = ref<ModelConfig[]>([])
const editingModelIndex = ref<number | null>(null)
const newModelConfig = ref<ModelConfig>({
  model_id: '',
  order: 1,
  strategy: 'primary',
  fields: ['*']
})

const modelStrategies = [
  { title: 'Primary', value: 'primary' },
  { title: 'Fallback', value: 'fallback' },
  { title: 'Parallel', value: 'parallel' }
]

const combinationStrategies = [
  { title: 'Sequential', value: 'sequential' },
  { title: 'Parallel', value: 'parallel' },
  { title: 'Ensemble', value: 'ensemble' },
  { title: 'Hybrid', value: 'hybrid' }
]

const conflictResolutions = [
  { title: 'Highest Confidence', value: 'highest_confidence' },
  { title: 'Flag for Review', value: 'flag_for_review' },
  { title: 'Average', value: 'average' },
  { title: 'Vote', value: 'vote' }
]

const multiModelSettings = ref({
  combination_strategy: 'sequential',
  conflict_resolution: 'flag_for_review'
})

// Schema Field Editor
interface SchemaField {
  name: string
  type: string
  description: string
  required: boolean
}

const schemaFields = ref<SchemaField[]>([])
const editingFieldIndex = ref<number | null>(null)
const newField = ref<SchemaField>({
  name: '',
  type: 'string',
  description: '',
  required: false
})

const fieldTypes = [
  { title: 'String', value: 'string' },
  { title: 'Number', value: 'number' },
  { title: 'Integer', value: 'integer' },
  { title: 'Boolean', value: 'boolean' },
  { title: 'Date', value: 'date' },
  { title: 'Currency', value: 'currency' },
  { title: 'Array', value: 'array' },
  { title: 'Object', value: 'object' }
]

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
  created_by: 'admin@contoso.com'
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

// Map field types to valid JSON Schema types
const getJsonSchemaType = (fieldType: string): any => {
  switch (fieldType) {
    case 'date':
      return { type: 'string', format: 'date' }
    case 'currency':
      return { type: 'number' }
    case 'string':
    case 'number':
    case 'integer':
    case 'boolean':
    case 'array':
    case 'object':
      return { type: fieldType }
    default:
      return { type: 'string' }
  }
}

// Build input schema from schema fields
const parsedInputSchema = computed(() => {
  if (schemaFields.value.length === 0) return {}
  
  const properties: Record<string, any> = {}
  const required: string[] = []
  
  for (const field of schemaFields.value) {
    const typeInfo = getJsonSchemaType(field.type)
    properties[field.name] = {
      ...typeInfo,
      description: field.description || `The ${field.name.replace(/_/g, ' ')} field`
    }
    if (field.required) {
      required.push(field.name)
    }
  }
  
  return {
    type: 'object',
    properties,
    required
  }
})

// Build output schema from schema fields
const parsedOutputSchema = computed(() => {
  if (schemaFields.value.length === 0) return {}
  
  const properties: Record<string, any> = {}
  
  for (const field of schemaFields.value) {
    const valueTypeInfo = getJsonSchemaType(field.type)
    properties[field.name] = {
      type: 'object',
      properties: {
        value: valueTypeInfo,
        confidence: { type: 'number' },
        citations: { type: 'array' },
        needs_review: { type: 'boolean' }
      }
    }
  }
  
  return {
    type: 'object',
    properties
  }
})

const isConfigValid = computed(() => {
  const valid = (
    config.value.document_type_name.trim() !== '' &&
    config.value.version.trim() !== '' &&
    configuredModels.value.length > 0 &&
    schemaFields.value.length > 0 &&  // Changed: at least one field defined
    uploadedFile.value !== null
  )
  console.log('isConfigValid check:', {
    name: config.value.document_type_name.trim() !== '',
    version: config.value.version.trim() !== '',
    models: configuredModels.value.length > 0,
    fields: schemaFields.value.length > 0,
    file: uploadedFile.value !== null,
    result: valid
  })
  return valid
})

// Available fields from schema fields for model assignment
const availableFields = computed(() => {
  return ['*', ...schemaFields.value.map(f => f.name)]
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
      
      // Auto-increment version for edit mode
      const currentVersion = latestVersion.version
      const versionParts = currentVersion.split('.')
      if (versionParts.length === 3) {
        // Increment patch version
        versionParts[2] = String(parseInt(versionParts[2]) + 1)
        config.value.version = versionParts.join('.')
      } else {
        config.value.version = currentVersion
      }
      
      // Load schema fields from existing input schema
      schemaFields.value = parseSchemaToFields(latestVersion.input_schema)
      
      config.value.extraction_config = latestVersion.extraction_config
      config.value.citation_level = latestVersion.citation_level
      config.value.confidence_threshold = latestVersion.confidence_threshold

      // Load configured models from existing extraction config
      if (latestVersion.extraction_config?.models) {
        configuredModels.value = latestVersion.extraction_config.models.map((m: any) => ({
          model_id: m.model_id,
          order: m.order || 1,
          strategy: m.strategy || 'primary',
          fields: m.fields || ['*']
        }))
        // Load multi-model settings
        if (latestVersion.extraction_config.combination_strategy) {
          multiModelSettings.value.combination_strategy = latestVersion.extraction_config.combination_strategy
        }
        if (latestVersion.extraction_config.conflict_resolution) {
          multiModelSettings.value.conflict_resolution = latestVersion.extraction_config.conflict_resolution
        }
      }
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

// Multi-Model Management Functions
function getModelName(modelId: string): string {
  const model = extractionModels.value.find(m => m.id === modelId)
  return model ? `${model.name} (${model.version})` : modelId
}

function getStrategyColor(strategy: string): string {
  switch (strategy) {
    case 'primary': return 'success'
    case 'fallback': return 'warning'
    case 'parallel': return 'info'
    default: return 'grey'
  }
}

function getCombinationDescription(strategy: string): string {
  switch (strategy) {
    case 'sequential': return 'Model B processes Model A output in order'
    case 'parallel': return 'Models run concurrently, results merged'
    case 'ensemble': return 'Voting/averaging across all model results'
    case 'hybrid': return 'Custom combination logic based on field types'
    default: return ''
  }
}

// Schema Field Management
function getFieldTypeIcon(type: string): string {
  switch (type) {
    case 'string': return 'mdi-format-text'
    case 'number': return 'mdi-numeric'
    case 'integer': return 'mdi-numeric'
    case 'boolean': return 'mdi-toggle-switch'
    case 'date': return 'mdi-calendar'
    case 'currency': return 'mdi-currency-usd'
    case 'array': return 'mdi-code-brackets'
    case 'object': return 'mdi-code-braces'
    default: return 'mdi-help-circle'
  }
}

function getFieldTypeColor(type: string): string {
  switch (type) {
    case 'string': return 'blue'
    case 'number': return 'green'
    case 'integer': return 'green'
    case 'boolean': return 'purple'
    case 'date': return 'orange'
    case 'currency': return 'teal'
    case 'array': return 'indigo'
    case 'object': return 'brown'
    default: return 'grey'
  }
}

function addOrUpdateField() {
  if (!newField.value.name || !newField.value.type) return

  const field: SchemaField = {
    name: newField.value.name.toLowerCase().replace(/\s+/g, '_'),
    type: newField.value.type,
    description: newField.value.description,
    required: newField.value.required
  }

  if (editingFieldIndex.value !== null) {
    schemaFields.value[editingFieldIndex.value] = field
    editingFieldIndex.value = null
  } else {
    schemaFields.value.push(field)
  }

  // Reset form
  newField.value = {
    name: '',
    type: 'string',
    description: '',
    required: false
  }
}

function editSchemaField(index: number) {
  const field = schemaFields.value[index]
  newField.value = { ...field }
  editingFieldIndex.value = index
}

function removeSchemaField(index: number) {
  schemaFields.value.splice(index, 1)
}

function cancelEditField() {
  editingFieldIndex.value = null
  newField.value = {
    name: '',
    type: 'string',
    description: '',
    required: false
  }
}

// Parse existing schema to fields (for edit mode)
function parseSchemaToFields(schema: any): SchemaField[] {
  const fields: SchemaField[] = []
  const properties = schema?.properties || schema || {}
  const required = schema?.required || []
  
  for (const [name, def] of Object.entries(properties)) {
    const fieldDef = def as any
    fields.push({
      name,
      type: fieldDef.type || 'string',
      description: fieldDef.description || '',
      required: required.includes(name)
    })
  }
  
  return fields
}

function addOrUpdateModelConfig() {
  if (!newModelConfig.value.model_id) return

  const modelConfig: ModelConfig = {
    model_id: newModelConfig.value.model_id,
    order: newModelConfig.value.order || configuredModels.value.length + 1,
    strategy: newModelConfig.value.strategy,
    fields: newModelConfig.value.fields.length > 0 ? newModelConfig.value.fields : ['*']
  }

  if (editingModelIndex.value !== null) {
    // Update existing
    configuredModels.value[editingModelIndex.value] = modelConfig
    editingModelIndex.value = null
  } else {
    // Add new
    configuredModels.value.push(modelConfig)
  }

  // Reset form
  newModelConfig.value = {
    model_id: '',
    order: configuredModels.value.length + 1,
    strategy: 'primary',
    fields: ['*']
  }
}

function editModelConfig(index: number) {
  const modelConfig = configuredModels.value[index]
  newModelConfig.value = { ...modelConfig }
  editingModelIndex.value = index
}

function removeModelConfig(index: number) {
  configuredModels.value.splice(index, 1)
  // Re-order remaining models
  configuredModels.value.forEach((m, i) => {
    m.order = i + 1
  })
}

function cancelEditModelConfig() {
  editingModelIndex.value = null
  newModelConfig.value = {
    model_id: '',
    order: configuredModels.value.length + 1,
    strategy: 'primary',
    fields: ['*']
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
  console.log('=== TEST EXTRACTION START ===')
  console.log('runTestExtraction called')
  console.log('file.value:', file.value)
  console.log('isConfigValid.value:', isConfigValid.value)
  console.log('config:', config.value)
  console.log('configuredModels:', configuredModels.value)
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
  currentStep.value = 2
  console.log('Moved to step 2 (Test & Review)')

  try {
    // Update schemas from JSON
    config.value.input_schema = parsedInputSchema.value
    config.value.output_schema = parsedOutputSchema.value
    console.log('Updated schemas')

    // Update extraction config with configured models (multi-model support)
    config.value.extraction_config = {
      models: configuredModels.value.map(m => ({
        model_id: m.model_id,
        order: m.order,
        strategy: m.strategy,
        fields: m.fields
      })),
      combination_strategy: multiModelSettings.value.combination_strategy,
      conflict_resolution: multiModelSettings.value.conflict_resolution
    }
    console.log('Updated extraction config with multi-model:', config.value.extraction_config)

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
