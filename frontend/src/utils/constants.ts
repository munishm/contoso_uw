// File upload constraints
export const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB in bytes
export const ALLOWED_FILE_TYPES = ['application/pdf']
export const ALLOWED_FILE_EXTENSIONS = ['.pdf']

// Processing status polling
export const POLL_INTERVAL_MS = 5000 // 5 seconds
export const MAX_POLL_ATTEMPTS = 60 // 5 minutes total (60 * 5s)

// Confidence thresholds
export const CONFIDENCE_HIGH = 90
export const CONFIDENCE_MEDIUM = 70

// Pagination
export const DEFAULT_PAGE_SIZE = 50

// Document types
export const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  form_a: 'Form A',
  form_b: 'Form B',
  unknown: 'Unknown'
}

// Processing steps
export const PROCESSING_STEP_LABELS: Record<string, string> = {
  ocr: 'OCR Processing',
  classification: 'Classification',
  extraction: 'Field Extraction',
  summarization: 'Summarization'
}

// Step weights for progress calculation
export const STEP_WEIGHTS: Record<string, number> = {
  ocr: 25,
  classification: 15,
  extraction: 30,
  summarization: 30
}
