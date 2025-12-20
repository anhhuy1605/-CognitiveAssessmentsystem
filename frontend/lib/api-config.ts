/**
 * API Configuration utilities for production deployment
 * Handles backend URL configuration based on environment
 */

export const getBackendUrl = (): string => {
  // Check if we're in browser environment
  if (typeof window !== 'undefined') {
    // Client-side: use NEXT_PUBLIC_ environment variable
    return process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || 'http://localhost:5001';
  } else {
    // Server-side: use either public or private environment variable
    return process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || 
           process.env.PYTHON_BACKEND_URL || 
           'http://localhost:5001';
  }
};

export const getFrontendUrl = (): string => {
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_APP_URL || window.location.origin;
  } else {
    return process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  }
};

/**
 * Create API endpoint URL with proper base URL
 */
export const createApiUrl = (endpoint: string): string => {
  const baseUrl = getBackendUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

/**
 * Common API endpoints
 */
export const API_ENDPOINTS = {
  HEALTH: '/api/health',
  MMSE_QUESTIONS: '/api/mmse/questions',
  ASSESS: '/api/assess',
  GENERATE_SUMMARY: '/api/generate-summary',
  AUTO_TRANSCRIBE: '/auto-transcribe',
  RESULTS: '/results',
} as const;

/**
 * Create fetch with timeout and error handling
 */
export const createFetchWithTimeout = (timeoutMs: number = 10000) => {
  return async (url: string, options: RequestInit = {}) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  };
};

/**
 * Check if backend is available
 */
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const fetchWithTimeout = createFetchWithTimeout(5000);
    const response = await fetchWithTimeout(createApiUrl(API_ENDPOINTS.HEALTH));
    return response.ok;
  } catch (error) {
    console.warn('Backend health check failed:', error);
    return false;
  }
};
