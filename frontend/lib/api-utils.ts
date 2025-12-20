export async function fetchWithAuth(url: string, options?: RequestInit) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null
  return fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
      'Authorization': token ? `Bearer ${token}` : '',
    },
  })
}

export async function handleApiError(response: Response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }))
    throw new Error((error as any).message || 'API request failed')
  }
  return response
}

// API Utilities for robust backend communication

// Define Question type locally
interface Question {
  id: string;
  category: string;
  domain: string;
  text: string;
}

// Environment-based API configuration
export const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001')
  : (process.env.NEXT_PUBLIC_API_URL || 'https://your-production-api.com');

// Mock data for development fallbacks
export const getMockQuestions = (): Question[] => [
  {
    id: 'Q1',
    category: 'Định hướng thời gian',
    domain: 'orientation',
    text: 'Hôm nay là ngày bao nhiêu?'
  },
  {
    id: 'Q2',
    category: 'Định hướng thời gian',
    domain: 'orientation',
    text: 'Hôm nay là thứ mấy?'
  },
  {
    id: 'Q3',
    category: 'Định hướng không gian',
    domain: 'orientation',
    text: 'Bạn đang ở đâu?'
  },
  {
    id: 'Q4',
    category: 'Định hướng không gian',
    domain: 'orientation',
    text: 'Đây là tỉnh/thành phố nào?'
  },
  {
    id: 'Q5',
    category: 'Ghi nhận',
    domain: 'registration',
    text: 'Hãy nhắc lại 3 từ sau: Táo, Bàn, Ghế'
  },
  {
    id: 'Q6',
    category: 'Ghi nhận',
    domain: 'registration',
    text: 'Hãy nhắc lại 3 từ: Cây, Sách, Xe'
  },
  {
    id: 'Q7',
    category: 'Chú ý và tính toán',
    domain: 'attention_calculation',
    text: 'Hãy trừ 7 từ 100: 100 - 7 = ?'
  },
  {
    id: 'Q8',
    category: 'Chú ý và tính toán',
    domain: 'attention_calculation',
    text: 'Tiếp tục trừ 7: 93 - 7 = ?'
  },
  {
    id: 'Q9',
    category: 'Hồi tưởng',
    domain: 'recall',
    text: 'Hãy nhắc lại 3 từ đã ghi nhận trước đó'
  },
  {
    id: 'Q10',
    category: 'Ngôn ngữ',
    domain: 'language',
    text: 'Hãy chỉ vào và đọc tên của vật này'
  },
  {
    id: 'Q11',
    category: 'Ngôn ngữ',
    domain: 'language',
    text: 'Hãy lặp lại câu: "Không có nếu, và, hoặc nhưng"'
  },
  {
    id: 'Q12',
    category: 'Xây dựng hình ảnh',
    domain: 'construction',
    text: 'Hãy sao chép hình vẽ này'
  }
];

// Enhanced fetch function with fallback handling
export const fetchWithFallback = async (
  url: string,
  options: RequestInit = {},
  fallbackData?: any
): Promise<Response> => {
  // Create AbortController for timeout - longer for ML operations
  const controller = new AbortController();
  const timeoutMs = url.includes('/assess') ? 60000 : 15000; // 60s for assessments, 15s for others
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    console.log(`🔗 Attempting to fetch: ${url}`, {
      method: options.method || 'GET',
      headers: options.headers,
      hasBody: !!options.body
    });

    const response = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers
      },
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    console.log(`📡 Response from ${url}:`, {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      headers: Object.fromEntries(response.headers.entries())
    });

    if (!response.ok) {
      // Try to get error details from response body
      let errorDetails = response.statusText;
      try {
        const errorBody = await response.clone().json();
        errorDetails = errorBody.error || errorBody.message || errorDetails;
      } catch (e) {
        // Response body is not JSON, use status text
      }
      throw new Error(`HTTP ${response.status}: ${errorDetails}`);
    }

    return response;
  } catch (error: any) {
    console.warn(`⚠️ Backend request failed for ${url}:`, {
      error: error.message,
      type: error.name,
      stack: error.stack?.split('\n')[0]
    });

    // Check if it's a timeout or network error
    if (error.name === 'AbortError') {
      console.warn('⏰ Request timed out after', timeoutMs/1000, 'seconds');
      throw new Error(`Request timed out after ${timeoutMs/1000} seconds`);
    } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
      console.warn('🌐 Network error - backend server may not be running');
      
      // Only use fallback for specific endpoints when backend is down
      if (url.includes('/api/mmse/questions') && fallbackData) {
        console.log('📋 Using mock questions data (backend unavailable)');
        return new Response(JSON.stringify({
          success: true,
          data: {
            questions: getMockQuestions(),
            total_points: 30,
            structure: 'mock_fallback',
            source: 'frontend_fallback'
          }
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (url.includes('/api/user/profile') && fallbackData) {
        console.log('👤 Using mock user data (backend unavailable)');
        return new Response(JSON.stringify({
          success: false,
          message: 'Backend unavailable, using local storage',
          user: fallbackData || getDefaultUserData()
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }

    // For other errors or endpoints, throw to be handled by caller
    throw error;
  }
};

// Backend health check
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000) // 3s timeout
    });
    return response.ok;
  } catch (error) {
    console.warn('🔴 Backend health check failed:', error);
    return false;
  }
};

// Get default user data for fallbacks
export const getDefaultUserData = () => ({
  name: 'Người dùng',
  age: '25',
  gender: 'Nam',
  email: 'user@local.dev',
  phone: '0123456789'
});

// Enhanced error handling wrapper
export const withApiFallback = async <T>(
  apiCall: () => Promise<T>,
  fallback: T,
  errorMessage?: string
): Promise<T> => {
  try {
    return await apiCall();
  } catch (error) {
    console.warn(errorMessage || 'API call failed, using fallback', error);
    return fallback;
  }
};
