import apiClient from './api'
import type { Document, ProcessingStatus } from '@/types'

export const documentsService = {
  /**
   * Upload a document to a case
   */
  async uploadDocument(
    caseId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<Document>(`/cases/${caseId}/documents`, formData, {
      headers: { 'Content-Type': undefined }, // Let browser set Content-Type with boundary
      onUploadProgress: progressEvent => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress?.(progress)
        }
      }
    })

    return response.data
  },

  /**
   * Get a document by ID with full details
   */
  async getDocument(caseId: string, documentId: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/cases/${caseId}/documents/${documentId}`)
    return response.data
  },

  /**
   * Get processing status for a document
   */
  async getProcessingStatus(caseId: string, documentId: string): Promise<ProcessingStatus> {
    const response = await apiClient.get<ProcessingStatus>(`/cases/${caseId}/documents/${documentId}`)
    return response.data
  },

  /**
   * Get documents for a specific case
   */
  async getDocumentsByCase(caseId: string): Promise<Document[]> {
    const response = await apiClient.get<{ items: Document[] }>(`/cases/${caseId}/documents`)
    return response.data.items
  },

  /**
   * Get document summary from the summaries collection
   */
  async getDocumentSummary(caseId: string, documentId: string): Promise<{ summary: string | null; document_type: string | null }> {
    try {
      const response = await apiClient.get<{ summary: string | null; document_type: string | null }>(`/cases/${caseId}/documents/${documentId}/summary`)
      return response.data
    } catch {
      // Return null if summary not found
      return { summary: null, document_type: null }
    }
  }
}
