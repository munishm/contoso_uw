import apiClient from './api'
import type { Case, CaseStatus } from '@/types'

export const casesService = {
  /**
   * Create a new case
   */
  async createCase(caseName: string, priorityLevel?: number): Promise<Case> {
    const response = await apiClient.post<Case>('/cases', {
      case_name: caseName,
      priority_level: priorityLevel
    })
    return response.data
  },

  /**
   * Get all cases
   */
  async listCases(status?: CaseStatus): Promise<Case[]> {
    const params = status ? { status } : {}
    const response = await apiClient.get<Case[]>('/cases', { params })
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
   * Update case status
   */
  async updateCaseStatus(caseId: string, status: CaseStatus): Promise<Case> {
    const response = await apiClient.patch<Case>(`/cases/${caseId}`, { status })
    return response.data
  }
}
