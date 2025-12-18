// Document types
export enum ProcessingStatusType {
  Pending = 'pending',
  Processing = 'processing',
  Completed = 'completed',
  Failed = 'failed'
}

export enum DocumentType {
  FormA = 'form_a',
  FormB = 'form_b',
  Unknown = 'unknown'
}

export interface Document {
  id: string
  case_id: string
  filename: string
  upload_timestamp: string
  processing_status: ProcessingStatusType
  document_type?: DocumentType
  classification_confidence?: number
  file_size: number
  uploader_id?: string
  blob_url?: string
  classification_result?: any
  extracted_fields?: any[]
  summaries?: any[]
  processing_status_detail?: any
}
