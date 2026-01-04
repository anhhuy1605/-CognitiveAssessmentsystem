import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { sessionId } = await params;

    if (!sessionId) {
      return NextResponse.json(
        { success: false, error: 'Session ID is required' },
        { status: 400 }
      );
    }

    // Proxy request to Flask backend
    const response = await fetch(
      `${API_BASE_URL}/api/mmse/chatbot/results/${sessionId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add timeout - increased for comprehensive results generation
        signal: AbortSignal.timeout(60000), // 60 seconds
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
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        message: 'Failed to fetch comprehensive results from backend'
      },
      { status: 500 }
    );
  }
}

