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
    formData.append('case_id', caseId)

    const response = await apiClient.post<Document>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
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
  async getDocument(documentId: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/documents/${documentId}`)
    return response.data
  },

  /**
   * Get processing status for a document
   */
  async getProcessingStatus(documentId: string): Promise<ProcessingStatus> {
    const response = await apiClient.get<ProcessingStatus>(`/documents/${documentId}/status`)
    return response.data
  },

  /**
   * Get documents for a specific case
   */
  async getDocumentsByCase(caseId: string): Promise<Document[]> {
    const response = await apiClient.get<Document[]>(`/cases/${caseId}/documents`)
    return response.data
  }
}
