import apiClient from './api'
import type { AxiosResponse } from 'axios'

export interface ClassifyDocumentResponse {
  document_type: string
  confidence: number
  suggested_name: string
}

export interface ExtractionModel {
  id: string
  name: string
  type: string
  endpoint?: string
  version: string
  api_version?: string
  capabilities: string[]
  is_active: boolean
}

export interface ExtractedField {
  field_name: string
  value: any
  value_type: string
  confidence: number
  citations: any[]
  needs_review: boolean
  review_reason?: string
  model_source: string
}

export interface ExtractionResult {
  id: string
  document_id: string
  document_type_id: string
  version_id: string
  status: string
  models_used: string[]
  fields: ExtractedField[]
  processing_duration_ms?: number
  evaluation?: Record<string, any>
}

export interface OnboardingTestResponse {
  extraction_result: ExtractionResult
  evaluation?: Record<string, any>
  recommendation: 'finalize' | 'adjust' | 'retry'
}

export interface DocumentType {
  id: string
  name: string
  description?: string
  is_active: boolean
  versions_count: number
}

export interface DocumentTypeVersion {
  id: string
  document_type_id: string
  version: string
  input_schema: Record<string, any>
  output_schema: Record<string, any>
  extraction_config: Record<string, any>
  citation_level: string
  confidence_threshold: number
  created_at: string
  created_by: string
  is_active: boolean
}

export interface OnboardingTestConfig {
  document_type_id?: string
  document_type_name: string
  description?: string
  version: string
  input_schema: Record<string, any>
  output_schema: Record<string, any>
  extraction_config: Record<string, any>
  custom_prompt?: string
  citation_level: string
  confidence_threshold: number
  created_by: string
}

export interface FinalizeOnboardingRequest {
  document_type_id?: string
  document_type_name: string
  description?: string
  version: string
  input_schema: Record<string, any>
  output_schema: Record<string, any>
  extraction_config: Record<string, any>
  custom_prompt?: string
  citation_level: string
  confidence_threshold: number
  created_by: string
}

class OnboardingService {
  /**
   * Classify an uploaded document
   */
  async classifyDocument(file: File): Promise<ClassifyDocumentResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response: AxiosResponse<ClassifyDocumentResponse> = await apiClient.post(
      '/onboarding/classify-document',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    return response.data
  }

  /**
   * Get list of available extraction models
   */
  async getExtractionModels(activeOnly: boolean = true): Promise<ExtractionModel[]> {
    const response: AxiosResponse<ExtractionModel[]> = await apiClient.get(
      '/extraction/models',
      {
        params: { active_only: activeOnly }
      }
    )

    return response.data
  }

  /**
   * Get list of document types
   */
  async getDocumentTypes(activeOnly: boolean = true): Promise<DocumentType[]> {
    const response: AxiosResponse<DocumentType[]> = await apiClient.get(
      '/extraction/document-types',
      {
        params: { active_only: activeOnly }
      }
    )

    return response.data
  }

  /**
   * Get a specific document type with versions
   */
  async getDocumentType(typeId: string): Promise<DocumentType> {
    const response: AxiosResponse<DocumentType> = await apiClient.get(
      `/extraction/document-types/${typeId}`
    )

    return response.data
  }

  /**
   * Get schema versions for a document type
   */
  async getSchemaVersions(typeId: string, activeOnly: boolean = true): Promise<DocumentTypeVersion[]> {
    const response: AxiosResponse<DocumentTypeVersion[]> = await apiClient.get(
      `/extraction/document-types/${typeId}/versions`,
      {
        params: { active_only: activeOnly }
      }
    )

    return response.data
  }

  /**
   * Test extraction with a configuration
   */
  async testExtraction(
    documentId: string,
    config: OnboardingTestConfig,
    file: File,
    groundTruthFile?: File
  ): Promise<OnboardingTestResponse> {
    console.log('testExtraction called with:', { documentId, config, file, groundTruthFile })
    
    const formData = new FormData()
    formData.append('document_id', documentId)
    formData.append('config_json', JSON.stringify(config))
    formData.append('file', file)

    if (groundTruthFile) {
      formData.append('ground_truth_file', groundTruthFile)
    }

    console.log('Sending POST to /onboarding/test-extraction')

    const response: AxiosResponse<OnboardingTestResponse> = await apiClient.post(
      '/onboarding/test-extraction',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    console.log('Received response:', response.data)
    return response.data
  }

  /**
   * Compare multiple model configurations
   */
  async compareModels(
    documentId: string,
    modelConfigs: Record<string, any>[],
    inputSchema: Record<string, any>,
    outputSchema: Record<string, any>,
    file: File
  ): Promise<OnboardingTestResponse[]> {
    const formData = new FormData()
    formData.append('document_id', documentId)
    formData.append(
      'config_json',
      JSON.stringify({
        model_configs: modelConfigs,
        input_schema: inputSchema,
        output_schema: outputSchema
      })
    )
    formData.append('file', file)

    const response: AxiosResponse<OnboardingTestResponse[]> = await apiClient.post(
      '/onboarding/compare-models',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    return response.data
  }

  /**
   * Finalize onboarding
   */
  async finalizeOnboarding(
    request: FinalizeOnboardingRequest
  ): Promise<{ success: boolean; document_type_id: string; version_id: string; message: string }> {
    const response: AxiosResponse<{
      success: boolean
      document_type_id: string
      version_id: string
      message: string
    }> = await apiClient.post('/onboarding/finalize', request)

    return response.data
  }
}

export const onboardingService = new OnboardingService()

