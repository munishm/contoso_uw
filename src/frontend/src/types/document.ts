// Document types
export enum ProcessingStatusType {
  Pending = 'pending',
  Classifying = 'classifying',
  ExtractingEntities = 'extracting-entities',
  Summarizing = 'summarizing',
  Completed = 'completed',
  Failed = 'failed'
}

export enum DocumentType {
  ApplicationForm = 'application_form',
  FinancialStatement = 'financial_statement',
  MedicalReport = 'medical_report',
  IdentityDocument = 'identity_document',
  PropertyAssessment = 'property_assessment',
  BankStatement = 'bank_statement',
  TaxReturn = 'tax_return',
  InsurancePolicy = 'insurance_policy',
  LegalDocument = 'legal_document',
  Other = 'other'
}

// Extraction result types (embedded in document)
export interface ExtractionCitation {
  type: string
  page: number
  bbox?: {
    x: number
    y: number
    width: number
    height: number
  }
  text_snippet?: string
}

export interface ExtractedFieldResult {
  field_name: string
  value: any
  value_type?: string
  confidence: number
  citations: ExtractionCitation[]
  needs_review: boolean
  review_reason?: string
  alternatives?: Array<{
    value: any
    confidence: number
    model_source: string
  }>
  model_source?: string
}

// Evaluation types
export interface CorrectnessEvaluation {
  score: number
  fuzzy_score?: number
  extraction_correct: boolean
  normalized_entity?: string
  cleaned_source_length?: number
}

export interface CompletenessEvaluation {
  score: number
  is_complete: boolean
  missing_info?: string[]
  reasoning?: string
}

export interface FieldEvaluationResult {
  field_name: string
  extracted_value: any
  evaluations: {
    correctness: CorrectnessEvaluation | null
    completeness: CompletenessEvaluation | null
  }
  summary: {
    overall_score: number
    evaluators_run: string[]
    warnings: string[]
    errors: string[]
  }
}

export interface EvaluationAggregateSummary {
  average_overall_score: number
  average_correctness_score: number
  average_completeness_score: number | null
  fields_correct: number
  fields_complete: number
  evaluators_run: string[]
  failed_evaluations: number
}

export interface EvaluationResults {
  total_fields: number
  results: FieldEvaluationResult[]
  aggregate_summary: EvaluationAggregateSummary
}

export interface DocumentExtractionResult {
  extraction_id?: string
  document_type_id?: string
  version_id?: string
  status: string
  models_used: string[]
  fields: ExtractedFieldResult[]
  processing_duration_ms?: number
  error_message?: string
  needs_review: boolean
  extraction_started_at?: string
  extraction_completed_at?: string
  evaluation?: EvaluationResults | null
}

// Field color info for annotated PDF legend
export interface FieldColorInfo {
  color: string
  hex: string
  needs_review: boolean
}

export interface FieldColorsResponse {
  document_id: string
  fields: Record<string, FieldColorInfo>
}

// Summarization evaluation result
export interface SummarizationEvaluationResult {
  overall_score?: number
  final_composite_score: number
  weights?: Record<string, number>
  evaluations?: {
    entity_coverage?: { score: number; feedback?: string }
    groundedness?: { score: number; feedback?: string }
    semantic_fidelity?: { score: number; feedback?: string }
  }
  evaluated_at?: string
}

export interface Document {
  document_id: string
  case_id: string
  filename: string
  content_type: string
  size_bytes: number
  blob_path?: string
  processing_status: ProcessingStatusType | string
  classification?: DocumentType | string | null
  confidence_score?: number | null
  extracted_text?: string | null
  summary?: string | null
  summarization_evaluation?: SummarizationEvaluationResult | null
  source?: string | null
  parent_document_id?: string | null
  page_range?: string | null
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
  created_by?: string
  processing_started_at?: string | null
  processing_completed_at?: string | null
  processing_error?: string | null
  // Extraction fields for list view
  has_extraction?: boolean
  extraction_status?: string | null
  extraction_needs_review?: boolean
  // Extraction results embedded in document (detail view)
  extraction?: DocumentExtractionResult | null
}
