import type { BoundingBox } from './extraction'

// Summary types
export enum SummaryType {
  Extractive = 'extractive',
  Abstractive = 'abstractive'
}

export interface Citation {
  id: string
  summary_id: string
  cited_text: string
  source_page_number: number
  source_bounding_box?: BoundingBox
  citation_number?: number
}

export interface Summary {
  id: string
  document_id: string
  summary_type: SummaryType
  summary_text: string
  citations: Citation[]
  generation_timestamp: string
  model_version: string
  word_count?: number
}
