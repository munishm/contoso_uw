import type { ProcessingStatusType } from './document'

// Processing status types
export enum ProcessingStepName {
  OCR = 'ocr',
  Classification = 'classification',
  Extraction = 'extraction',
  Summarization = 'summarization'
}

export enum StepStatus {
  Pending = 'pending',
  InProgress = 'in_progress',
  Completed = 'completed',
  Failed = 'failed'
}

export interface ProcessingStep {
  step_name: ProcessingStepName
  status: StepStatus
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface ProcessingStatus {
  id: string
  document_id: string
  status: ProcessingStatusType
  progress_percentage: number
  estimated_completion_time?: string
  error_message?: string
  step_details: ProcessingStep[]
  last_updated: string
}
