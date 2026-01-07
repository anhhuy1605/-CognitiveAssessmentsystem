import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001';

export async function GET(request: NextRequest) {
  try {
    // Proxy request to Flask backend
    const response = await fetch(
      `${API_BASE_URL}/api/mmse/chatbot/sessions`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(30000), // 30 seconds
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Flask API error (${response.status}):`, errorText);
      return NextResponse.json(
        { 
          success: false, 
          error: `Backend API error: ${response.status}`,
          details: errorText 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying request to Flask backend:', error);
    
    // Return empty list instead of error for better UX
    return NextResponse.json({
      success: true,
      sessions: [],
      count: 0,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

