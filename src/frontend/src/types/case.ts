// Case types matching Azure API
export enum CaseStatus {
  Draft = 'draft',
  InReview = 'in-review',
  PendingDocuments = 'pending-documents',
  Approved = 'approved',
  Rejected = 'rejected',
  Closed = 'closed',
  Deleted = 'deleted'
}

export interface Case {
  case_id: string
  client_name: string
  policy_type: string
  submission_date: string // ISO date format
  status: CaseStatus
  created_at: string
  updated_at: string
  created_by: string
  assigned_to?: string | null
  metadata?: Record<string, any>
  main_document_blob_path?: string | null
  processing_status?: string | null
  total_documents_expected?: number | null
  documents_processed_count?: number
  processing_started_at?: string | null
  processing_completed_at?: string | null
  processing_error?: string | null
  documents?: DocumentSummaryInCase[]
  case_summary?: string | null
  case_summary_updated_at?: string | null
}

export interface DocumentSummaryInCase {
  document_id: string
  filename: string
  content_type: string
  size_bytes: number
  processing_status: string
  classification?: string | null
  source?: string | null
  parent_document_id?: string | null
  page_range?: string | null
  summary?: string | null
  created_at: string
}

export interface CaseCreateRequest {
  client_name: string
  policy_type: string
  submission_date: string
  assigned_to?: string | null
  metadata?: Record<string, any>
}

export interface CaseUpdateRequest {
  client_name?: string | null
  policy_type?: string | null
  submission_date?: string | null
  status?: CaseStatus | null
  assigned_to?: string | null
  metadata?: Record<string, any> | null
}

export interface CaseListResponse {
  items: CaseSummaryResponse[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CaseSummaryResponse {
  case_id: string
  client_name: string
  policy_type: string
  status: CaseStatus
  document_count: number
  documents_processed: number
  created_at: string
  updated_at: string
}
