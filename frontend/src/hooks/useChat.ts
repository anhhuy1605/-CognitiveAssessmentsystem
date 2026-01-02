/**
 * useChat Hook - Chat state management and message handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { chatService, ChatMessage, SubmitAnswerResponse } from '../services/chatService';
import { ApiResponse } from '../services/api';

export interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  currentQuestion: { questionId: string; category: string } | null;
  sendMessage: (text: string, audioBlob?: Blob, metadata?: Record<string, any>) => Promise<void>;
  startSession: (userInfo: {
    name: string;
    age: string;
    gender: string;
    education_years?: string;
  }) => Promise<void>;
  clearChat: () => void;
  testComplete: boolean;
  finalScore: number | null;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [testComplete, setTestComplete] = useState(false);
  const [finalScore, setFinalScore] = useState<number | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Get current active question from messages
   */
  const currentQuestion = (() => {
    const lastBotMessage = messages
      .slice()
      .reverse()
      .find(m => m.type === 'bot' && m.questionId && m.questionCategory);
    
    if (!lastBotMessage) return null;
    
    return {
      questionId: lastBotMessage.questionId!,
      category: lastBotMessage.questionCategory!,
    };
  })();

  /**
   * Start new chat session
   * Session is created on first message, so we just generate session ID
   */
  const startSession = useCallback(async (userInfo: {
    name: string;
    age: string;
    gender: string;
    education_years?: string;
  }) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Generate session ID on client side
      // Backend will create session when first message is sent
      const sessionId = `mmse_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(sessionId);
      setMessages([]);
      setTestComplete(false);
      setFinalScore(null);
      
      // Store user info in localStorage for backend to use
      if (typeof window !== 'undefined') {
        localStorage.setItem('mmse_user_info', JSON.stringify(userInfo));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to start session');
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Send message to chatbot
   */
  const sendMessage = useCallback(async (
    text: string,
    audioBlob?: Blob,
    metadata?: Record<string, any>
  ) => {
    if (!sessionId) {
      setError('No active session. Please start a new session first.');
      return;
    }

    if (testComplete) {
      setError('Test is already completed.');
      return;
    }

    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    setError(null);

    // Add user message
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatService.submitAnswer(
        sessionId,
        text,
        audioBlob,
        metadata
      );

      if (!response.success) {
        setError(response.error || 'Failed to send message');
        return;
      }

      const data = response.data as SubmitAnswerResponse;

      // Check if test is complete
      if (data.test_complete) {
        setTestComplete(true);
        setFinalScore(data.final_score || null);
      }

      // Add bot response
      if (data.message) {
        const botMessage: ChatMessage = {
          id: `bot_${Date.now()}`,
          type: 'bot',
          content: data.message,
          timestamp: new Date(),
          hiddenContent: data.metadata?.hidden_content,
          domain: data.metadata?.domain,
          questionId: data.metadata?.question_id,
          questionCategory: data.metadata?.question_category,
          displayMode: data.metadata?.display_mode,
          ttsText: data.metadata?.tts_text || data.message,
        };
        setMessages(prev => [...prev, botMessage]);
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to send message');
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [sessionId, testComplete]);

  /**
   * Clear chat history
   */
  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setTestComplete(false);
    setFinalScore(null);
    setError(null);
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    currentQuestion,
    sendMessage,
    startSession,
    clearChat,
    testComplete,
    finalScore,
  };
}

