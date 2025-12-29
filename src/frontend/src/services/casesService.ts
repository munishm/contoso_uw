import apiClient from './api'
import type {
  Case,
  CaseStatus,
  CaseCreateRequest,
  CaseUpdateRequest,
  CaseListResponse
} from '@/types'

export const casesService = {
  /**
   * Create a new case with required document upload
   * According to the API spec, main_document is required
   */
  async createCase(request: CaseCreateRequest, file: File): Promise<Case> {
    // Create case with document using multipart/form-data
    const formData = new FormData()
    formData.append('client_name', request.client_name)
    formData.append('policy_type', request.policy_type)
    formData.append('submission_date', request.submission_date)
    if (request.assigned_to) {
      formData.append('assigned_to', request.assigned_to)
    }
    if (request.metadata) {
      formData.append('metadata', JSON.stringify(request.metadata))
    }
    // API expects 'main_document' as the field name
    formData.append('main_document', file)

    const response = await apiClient.post<Case>('/cases', formData, {
      headers: { 'Content-Type': undefined } // Let browser set Content-Type with boundary
    })
    return response.data
  },

  /**
   * List cases with pagination and filters
   */
  async listCases(params?: {
    page?: number
    page_size?: number
    status?: CaseStatus
    client_name?: string
    assigned_to?: string
    include_deleted?: boolean
  }): Promise<CaseListResponse> {
    const response = await apiClient.get<CaseListResponse>('/cases', { params })
    return response.data
  },

  /**
   * Get a single case by ID
   */
  async getCase(caseId: string): Promise<Case> {
    const response = await apiClient.get<Case>(`/cases/${caseId}`)
    return response.data
  },

  /**
   * Update an existing case
   */
  async updateCase(caseId: string, request: CaseUpdateRequest): Promise<Case> {
    const response = await apiClient.put<Case>(`/cases/${caseId}`, request)
    return response.data
  },

  /**
   * Delete a case (soft delete)
   */
  async deleteCase(caseId: string): Promise<void> {
    await apiClient.delete(`/cases/${caseId}`)
  },

  /**
   * Restore a deleted case
   */
  async restoreCase(caseId: string): Promise<Case> {
    const response = await apiClient.post<Case>(`/cases/${caseId}/restore`)
    return response.data
  },

  /**
   * Get case status history
   */
  async getStatusHistory(caseId: string): Promise<any> {
    const response = await apiClient.get(`/cases/${caseId}/status-history`)
    return response.data
  }
}
