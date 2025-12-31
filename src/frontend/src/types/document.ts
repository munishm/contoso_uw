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

export interface Document {
  document_id: string
  case_id: string
  filename: string
  content_type: string
  size_bytes: number
  blob_path: string
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
  created_by: string
  processing_started_at?: string | null
  processing_completed_at?: string | null
  processing_error?: string | null
}
