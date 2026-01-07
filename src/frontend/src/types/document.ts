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
