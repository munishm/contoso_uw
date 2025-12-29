import type { DocumentType } from './document'

// Classification types
export interface ClassificationResult {
  id: string
  document_id: string
  predicted_type: DocumentType
  confidence_score: number
  model_version: string
  processing_timestamp: string
  raw_output?: string
}
