/**
 * Validate PDF file type and size
 */
export function validateDocumentFile(file: File): string | null {
  if (file.type !== 'application/pdf') {
    return 'Only PDF files are supported'
  }
  const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB
  if (file.size > MAX_FILE_SIZE) {
    return 'File size must be less than 20MB'
  }
  return null
}

/**
 * Validate case name
 */
export function validateCaseName(name: string): string | null {
  if (name.trim().length === 0) {
    return 'Case name is required'
  }
  if (name.length > 200) {
    return 'Case name must be less than 200 characters'
  }
  return null
}

/**
 * Check if string is a valid UUID
 */
export function isValidUUID(str: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  return uuidRegex.test(str)
}
