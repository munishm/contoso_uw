import apiClient from '@/services/api'

/**
 * Test API connectivity and authentication
 */
export async function testApiConnection() {
  try {
    console.log('Testing API connection...')
    console.log('Base URL:', import.meta.env.VITE_API_BASE_URL)
    
    // Test health endpoint (no auth required)
    try {
      const healthResponse = await apiClient.get('/health', {
        baseURL: '/api'
      })
      console.log('✅ Health check passed:', healthResponse.data)
    } catch (healthError: any) {
      console.log('⚠️ Health check failed:', healthError.message)
    }

    // Test cases endpoint
    try {
      const casesResponse = await apiClient.get('/cases', {
        params: { page: 1, page_size: 1 }
      })
      console.log('✅ Cases API accessible:', {
        total: casesResponse.data.total,
        status: casesResponse.status
      })
      return { success: true, message: 'API connection successful' }
    } catch (error: any) {
      console.error('❌ API connection failed:', error.message)
      return {
        success: false,
        message: error.message,
        details: error.response?.data
      }
    }
  } catch (error: any) {
    console.error('❌ Unexpected error:', error)
    return {
      success: false,
      message: 'Unexpected error',
      details: error.message
    }
  }
}
