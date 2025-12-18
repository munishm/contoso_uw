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
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
