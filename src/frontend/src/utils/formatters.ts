import { format, formatDistanceToNow } from 'date-fns'

/**
 * Format ISO 8601 date string to readable format
 */
export function formatDate(isoString: string): string {
  return format(new Date(isoString), 'MMM dd, yyyy HH:mm')
}

/**
 * Format date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(isoString: string): string {
  return formatDistanceToNow(new Date(isoString), { addSuffix: true })
}

/**
 * Format confidence score as percentage (0.0-1.0 scale to 0%-100%)
 */
export function formatConfidence(score: number): string {
  // Handle both 0-1 scale and 0-100 scale
  const percentage = score <= 1 ? score * 100 : score
  return `${Math.round(percentage)}%`
}

/**
 * Get confidence level label (works with 0-1 scale)
 */
export function getConfidenceLevel(score: number): 'high' | 'medium' | 'low' {
  const percentage = score <= 1 ? score * 100 : score
  if (percentage >= 90) return 'high'
  if (percentage >= 70) return 'medium'
  return 'low'
}

/**
 * Get confidence color for UI (works with 0-1 scale)
 */
export function getConfidenceColor(score: number): string {
  const percentage = score <= 1 ? score * 100 : score
  if (percentage >= 90) return 'success'
  if (percentage >= 70) return 'warning'
  return 'error'
}

/**
 * Format file size in bytes to human-readable
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Format field name to display label
 */
export function formatFieldName(fieldName: string): string {
  return fieldName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
