const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
const FREQTRADE_URL = process.env.NEXT_PUBLIC_FREQTRADE_URL || 'http://localhost:8080'

export interface ApiResponse<T> {
  status: 'success' | 'error'
  data?: T
  message?: string
  timestamp?: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      if (!response.ok) {
        return {
          status: 'error',
          message: `HTTP error! status: ${response.status}`,
        }
      }

      const data = await response.json()
      return {
        status: 'success',
        data,
        timestamp: new Date().toISOString(),
      }
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }
}

// Freqtrade API Client
export const freqtradeApi = new ApiClient(FREQTRADE_URL)

// Custom Backend API Client
export const backendApi = new ApiClient(API_URL)

// Freqtrade API endpoints
export const freqtradeEndpoints = {
  status: () => freqtradeApi.get('/api/v1/status'),
  balance: () => freqtradeApi.get('/api/v1/balance'),
  trades: () => freqtradeApi.get('/api/v1/trades'),
  profit: () => freqtradeApi.get('/api/v1/profit'),
  daily: () => freqtradeApi.get('/api/v1/daily'),
  stats: () => freqtradeApi.get('/api/v1/stats'),
}

// Backend API endpoints (proxying to Freqtrade)
export const backendEndpoints = {
  health: () => backendApi.get('/api/health'),
  status: () => backendApi.get('/api/status'),
  balance: () => backendApi.get('/api/balance'),
  trades: () => backendApi.get('/api/trades'),
  profit: () => backendApi.get('/api/profit'),
  performance: () => backendApi.get('/api/performance'),
  daily: () => backendApi.get('/api/daily'),
  strategies: () => backendApi.get('/api/strategies'),
}