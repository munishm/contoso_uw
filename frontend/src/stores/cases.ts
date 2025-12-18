import { defineStore } from 'pinia'
import { ref } from 'vue'
import { casesService } from '@/services/casesService'
import type { Case, CaseStatus } from '@/types'

export const useCasesStore = defineStore('cases', () => {
  // State
  const cases = ref<Map<string, Case>>(new Map())
  const currentCase = ref<Case | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function createCase(caseName: string, priorityLevel?: number): Promise<Case> {
    isLoading.value = true
    error.value = null

    try {
      const newCase = await casesService.createCase(caseName, priorityLevel)
      cases.value.set(newCase.id, newCase)
      currentCase.value = newCase
      return newCase
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create case'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCases(status?: CaseStatus): Promise<Case[]> {
    isLoading.value = true
    error.value = null

    try {
      const fetchedCases = await casesService.listCases(status)
      fetchedCases.forEach(c => cases.value.set(c.id, c))
      return fetchedCases
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
      cases.value.set(fetchedCase.id, fetchedCase)
      currentCase.value = fetchedCase
      return fetchedCase
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch case'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateStatus(caseId: string, status: CaseStatus): Promise<Case> {
    try {
      const updatedCase = await casesService.updateCaseStatus(caseId, status)
      cases.value.set(updatedCase.id, updatedCase)
      if (currentCase.value?.id === caseId) {
        currentCase.value = updatedCase
      }
      return updatedCase
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update case status'
      throw err
    }
  }

  function getCaseById(id: string): Case | undefined {
    return cases.value.get(id)
  }

  return {
    cases,
    currentCase,
    isLoading,
    error,
    createCase,
    fetchCases,
    fetchCase,
    updateStatus,
    getCaseById
  }
})
