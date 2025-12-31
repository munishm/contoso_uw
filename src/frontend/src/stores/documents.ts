import { defineStore } from 'pinia'
import { ref } from 'vue'
import { documentsService } from '@/services/documentsService'
import type { Document } from '@/types'
import { POLL_INTERVAL_MS, MAX_POLL_ATTEMPTS } from '@/utils/constants'

export const useDocumentsStore = defineStore('documents', () => {
  // State
  const documents = ref<Map<string, Document>>(new Map())
  const currentDocument = ref<Document | null>(null)
  const uploadProgress = ref(0)
  const isUploading = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function uploadDocument(caseId: string, file: File): Promise<Document> {
    isUploading.value = true
    error.value = null
    uploadProgress.value = 0

    try {
      const document = await documentsService.uploadDocument(caseId, file, progress => {
        uploadProgress.value = progress
      })

      documents.value.set(document.document_id, document)
      currentDocument.value = document

      // Start polling for processing status
      pollProcessingStatus(caseId, document.document_id)

      return document
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Upload failed'
      throw err
    } finally {
      isUploading.value = false
    }
  }

  async function fetchDocument(caseId: string, documentId: string): Promise<Document> {
    isLoading.value = true
    error.value = null

    try {
      const document = await documentsService.getDocument(caseId, documentId)
      documents.value.set(document.document_id, document)
      if (currentDocument.value?.document_id === documentId) {
        currentDocument.value = document
      }
      return document
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Fetch failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function pollProcessingStatus(caseId: string, documentId: string): Promise<void> {
    let attempts = 0

    const poll = async () => {
      if (attempts >= MAX_POLL_ATTEMPTS) {
        error.value = 'Processing timeout - please refresh'
        return
      }

      try {
        const document = await documentsService.getProcessingStatus(caseId, documentId)
        documents.value.set(documentId, document)

        // Stop polling if completed or failed
        if (document.processing_status === 'completed' || document.processing_status === 'failed') {
          await fetchDocument(caseId, documentId)
          return
        }

        // Continue polling
        attempts++
        setTimeout(poll, POLL_INTERVAL_MS)
      } catch (err) {
        error.value = 'Failed to fetch processing status'
        console.error('Polling error:', err)
      }
    }

    poll()
  }

  function getDocumentById(id: string): Document | undefined {
    return documents.value.get(id)
  }

  return {
    documents,
    currentDocument,
    uploadProgress,
    isUploading,
    isLoading,
    error,
    uploadDocument,
    fetchDocument,
    pollProcessingStatus,
    getDocumentById
  }
})
