import axios, { type AxiosInstance, type AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for document processing
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor for error handling (FAIL IMMEDIATELY - no retries per spec)
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    const errorData = error.response?.data as any
    console.error('API Error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: errorData?.message || error.message,
      details: errorData?.details
    })
    return Promise.reject(error)
  }
)

export default apiClient
