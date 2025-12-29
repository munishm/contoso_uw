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
 * Format confidence score as percentage
 */
export function formatConfidence(score: number): string {
  return `${Math.round(score)}%`
}

/**
 * Get confidence level label
 */
export function getConfidenceLevel(score: number): 'high' | 'medium' | 'low' {
  if (score >= 90) return 'high'
  if (score >= 70) return 'medium'
  return 'low'
}

/**
 * Get confidence color for UI
 */
export function getConfidenceColor(score: number): string {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
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
