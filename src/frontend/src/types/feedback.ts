// Feedback types
export enum FeedbackType {
  FieldCorrection = 'field_correction',
  SummaryRating = 'summary_rating'
}

export type UserRating = 'correct' | 'incorrect' | 1 | 2 | 3 | 4 | 5

export interface Feedback {
  id: string
  document_id: string
  feedback_type: FeedbackType
  target_entity_id: string
  user_rating: UserRating
  corrected_value?: string
  comments?: string
  user_id?: string
  timestamp: string
}
