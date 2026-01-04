/**
 * API Service - Base API configuration and utilities
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

class ApiService {
  private baseURL: string;
  private defaultHeaders: HeadersInit;

  constructor() {
    this.baseURL = API_BASE_URL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Make HTTP request with error handling and retry logic
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = 2
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          error: `HTTP ${response.status}: ${response.statusText}`,
        }));

        // Retry on 5xx errors
        if (response.status >= 500 && retries > 0) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return this.request<T>(endpoint, options, retries - 1);
        }

        return {
          success: false,
          error: errorData.error || errorData.message || `HTTP ${response.status}`,
        };
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error: any) {
      if (error.name === 'AbortError') {
        return {
          success: false,
          error: 'Request timeout',
        };
      }

      // Retry on network errors
      if (retries > 0 && !error.message?.includes('timeout')) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return this.request<T>(endpoint, options, retries - 1);
      }

      return {
        success: false,
        error: error.message || 'Network error',
      };
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : '';
    return this.request<T>(endpoint + queryString, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * POST with FormData (for file uploads)
   */
  async postFormData<T>(
    endpoint: string,
    formData: FormData
  ): Promise<ApiResponse<T>> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        headers: {}, // Let browser set Content-Type with boundary
        body: formData,
      }
    );
  }
}

export const apiService = new ApiService();





