// Case types
export enum CaseStatus {
  Pending = 'pending',
  InProgress = 'in_progress',
  Completed = 'completed'
}

export interface Case {
  id: string
  case_name: string
  creation_timestamp: string
  status: CaseStatus
  assigned_underwriter_id?: string
  document_ids: string[]
  priority_level?: number
  last_updated_timestamp: string
}
