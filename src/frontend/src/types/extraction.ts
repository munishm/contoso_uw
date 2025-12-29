// Extraction types
export enum ExtractionMethod {
  RuleBased = 'rule_based',
  LLM = 'llm'
}

export enum FieldDataType {
  String = 'string',
  Number = 'number',
  Date = 'date',
  Boolean = 'boolean'
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface SourceLocation {
  page_number: number
  bounding_box?: BoundingBox
}

export interface ExtractedField {
  id: string
  document_id: string
  field_name: string
  field_value: string
  confidence_score: number
  source_location: SourceLocation
  extraction_method: ExtractionMethod
  data_type?: FieldDataType
}
