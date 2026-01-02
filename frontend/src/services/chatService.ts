/**
 * Chat Service - MMSE Chatbot API interactions
 */

import { apiService, ApiResponse } from './api';

export interface ChatMessage {
  id: string;
  type: 'bot' | 'user' | 'system';
  content: string;
  timestamp: Date;
  hiddenContent?: string[];
  isRevealed?: boolean;
  domain?: string;
  questionId?: string;
  questionCategory?: string;
  displayMode?: string;
  ttsText?: string;
  score?: {
    points_earned: number;
    points_possible: number;
    is_correct: boolean;
    feedback?: string;
  };
}

export interface QuestionMetadata {
  domain: string;
  question_id: string;
  question_category: string;
  display_mode?: string;
  hidden_content?: string[];
  tts_text?: string;
}

export interface SubmitAnswerRequest {
  sessionId: string;
  answer: string;
  audioFile?: File;
  metadata?: Record<string, any>;
}

export interface SubmitAnswerResponse {
  success: boolean;
  message?: string;
  metadata?: QuestionMetadata;
  test_complete?: boolean;
  final_score?: number;
  error?: string;
}

class ChatService {
  /**
   * Get MMSE questions
   */
  async getQuestions(): Promise<ApiResponse<any>> {
    return apiService.get('/mmse/chatbot/questions');
  }

  /**
   * Submit answer to chatbot
   */
  async submitAnswer(
    sessionId: string,
    answer: string,
    audioBlob?: Blob,
    metadata?: Record<string, any>
  ): Promise<ApiResponse<SubmitAnswerResponse>> {
    const formData = new FormData();
    formData.append('sessionId', sessionId);
    formData.append('answer', answer);
    
    if (audioBlob) {
      formData.append('audio', audioBlob, 'audio.webm');
    }
    
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    return apiService.postFormData<SubmitAnswerResponse>(
      '/mmse/chatbot/submit',
      formData
    );
  }

  /**
   * Auto-transcribe audio
   */
  async transcribeAudio(audioBlob: Blob): Promise<ApiResponse<{ transcript: string }>> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.webm');

    return apiService.postFormData<{ transcript: string }>(
      '/mmse/chatbot/auto-transcribe',
      formData
    );
  }

  /**
   * Get session results
   */
  async getResults(sessionId: string): Promise<ApiResponse<any>> {
    return apiService.get(`/mmse/chatbot/results/${sessionId}`);
  }

  /**
   * Save session results
   */
  async saveResults(sessionId: string, data: any): Promise<ApiResponse<any>> {
    return apiService.post('/mmse/chatbot/results', {
      sessionId,
      ...data,
    });
  }

  /**
   * Start new session
   * Note: Session is started automatically when first message is sent
   * This is a placeholder - actual implementation uses submit endpoint
   */
  async startSession(userInfo: {
    name: string;
    age: string;
    gender: string;
    education_years?: string;
  }): Promise<ApiResponse<{ sessionId: string }>> {
    // Generate session ID on client side
    const sessionId = `mmse_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      success: true,
      data: { sessionId },
    };
  }
}

export const chatService = new ChatService();

