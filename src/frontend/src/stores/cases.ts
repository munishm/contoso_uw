import { defineStore } from 'pinia'
import { ref } from 'vue'
import { casesService } from '@/services/casesService'
import type {
  Case,
  CaseStatus,
  CaseCreateRequest,
  CaseUpdateRequest,
  CaseSummaryResponse
} from '@/types'

export const useCasesStore = defineStore('cases', () => {
  // State
  const cases = ref<Map<string, Case | CaseSummaryResponse>>(new Map())
  const currentCase = ref<Case | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const totalCases = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Actions
  async function createCase(request: CaseCreateRequest, file: File): Promise<Case> {
    isLoading.value = true
    error.value = null

    try {
      const newCase = await casesService.createCase(request, file)
      cases.value.set(newCase.case_id, newCase)
      currentCase.value = newCase
      return newCase
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create case'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCases(params?: {
    page?: number
    page_size?: number
    status?: CaseStatus
    client_name?: string
    assigned_to?: string
  }): Promise<CaseSummaryResponse[]> {
    isLoading.value = true
    error.value = null

    try {
      const response = await casesService.listCases(params)
      response.items.forEach(c => cases.value.set(c.case_id, c))
      totalCases.value = response.total
      currentPage.value = response.page
      pageSize.value = response.page_size
      return response.items
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch cases'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCase(caseId: string): Promise<Case> {
    isLoading.value = true
    error.value = null

    try {
      const fetchedCase = await casesService.getCase(caseId)
      cases.value.set(fetchedCase.case_id, fetchedCase)
      currentCase.value = fetchedCase
      return fetchedCase
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch case'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateCase(
    caseId: string,
    request: CaseUpdateRequest
  ): Promise<Case> {
    isLoading.value = true
    error.value = null

    try {
      const updatedCase = await casesService.updateCase(caseId, request)
      cases.value.set(updatedCase.case_id, updatedCase)
      if (currentCase.value?.case_id === caseId) {
        currentCase.value = updatedCase
      }
      return updatedCase
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update case'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCase(caseId: string): Promise<void> {
    try {
      await casesService.deleteCase(caseId)
      cases.value.delete(caseId)
      if (currentCase.value?.case_id === caseId) {
        currentCase.value = null
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete case'
      throw err
    }
  }

  function getCaseById(id: string): Case | CaseSummaryResponse | undefined {
    return cases.value.get(id)
  }

  return {
    cases,
    currentCase,
    isLoading,
    error,
    totalCases,
    currentPage,
    pageSize,
    createCase,
    fetchCases,
    fetchCase,
    updateCase,
    deleteCase,
    getCaseById
  }
})
