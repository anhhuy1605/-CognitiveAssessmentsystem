/**
 * Question Tracker Hook
 * =====================
 * 
 * Tracks current active question and manages question state
 * to ensure special interfaces render at the right time
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface QuestionState {
  questionId: string;
  questionCategory: string;
  domain: string;
  index: number;
  isActive: boolean;
  metadata?: {
    displayMode?: string;
    hiddenContent?: string[];
    targetTime?: string;
    [key: string]: any;
  };
}

export interface QuestionTracker {
  currentQuestion: QuestionState | null;
  previousQuestion: QuestionState | null;
  questionHistory: QuestionState[];
  isQuestionActive: (questionId: string) => boolean;
  setCurrentQuestion: (question: QuestionState) => void;
  clearCurrentQuestion: () => void;
  getQuestionByIndex: (index: number) => QuestionState | null;
  getQuestionsByDomain: (domain: string) => QuestionState[];
}

/**
 * Hook to track current question state
 */
export function useQuestionTracker() {
  const [currentQuestion, setCurrentQuestionState] = useState<QuestionState | null>(null);
  const [previousQuestion, setPreviousQuestion] = useState<QuestionState | null>(null);
  const [questionHistory, setQuestionHistory] = useState<QuestionState[]>([]);
  const questionRef = useRef<QuestionState | null>(null);

  // Update current question
  const setCurrentQuestion = useCallback((question: QuestionState) => {
    // Mark previous as inactive
    if (questionRef.current) {
      questionRef.current.isActive = false;
      setPreviousQuestion(questionRef.current);
      
      // Add to history
      setQuestionHistory(prev => {
        const exists = prev.find(q => q.questionId === question.questionId);
        if (!exists) {
          return [...prev, { ...questionRef.current!, isActive: false }];
        }
        return prev;
      });
    }

    // Set new question as active
    const newQuestion = { ...question, isActive: true };
    questionRef.current = newQuestion;
    setCurrentQuestionState(newQuestion);
  }, []);

  // Clear current question
  const clearCurrentQuestion = useCallback(() => {
    if (questionRef.current) {
      questionRef.current.isActive = false;
      setPreviousQuestion(questionRef.current);
      setQuestionHistory(prev => [...prev, { ...questionRef.current!, isActive: false }]);
    }
    questionRef.current = null;
    setCurrentQuestionState(null);
  }, []);

  // Check if question is active
  const isQuestionActive = useCallback((questionId: string): boolean => {
    return currentQuestion?.questionId === questionId && currentQuestion?.isActive === true;
  }, [currentQuestion]);

  // Get question by index
  const getQuestionByIndex = useCallback((index: number): QuestionState | null => {
    return questionHistory.find(q => q.index === index) || null;
  }, [questionHistory]);

  // Get questions by domain
  const getQuestionsByDomain = useCallback((domain: string): QuestionState[] => {
    return questionHistory.filter(q => q.domain === domain);
  }, [questionHistory]);

  // Sync with messages (auto-detect current question from last bot message)
  const syncWithMessages = useCallback((messages: Array<{ questionId?: string; domain?: string; questionCategory?: string; displayMode?: string; hiddenContent?: string[] }>) => {
    const lastBotMessage = messages
      .filter(m => m.questionId)
      .pop();

    if (lastBotMessage?.questionId) {
      setCurrentQuestion({
        questionId: lastBotMessage.questionId,
        questionCategory: lastBotMessage.questionCategory || '',
        domain: lastBotMessage.domain || '',
        index: questionHistory.length,
        isActive: true,
        metadata: {
          displayMode: lastBotMessage.displayMode,
          hiddenContent: lastBotMessage.hiddenContent,
        }
      });
    }
  }, [questionHistory.length, setCurrentQuestion]);

  return {
    currentQuestion,
    previousQuestion,
    questionHistory,
    isQuestionActive,
    setCurrentQuestion,
    clearCurrentQuestion,
    getQuestionByIndex,
    getQuestionsByDomain,
    syncWithMessages,
  } as QuestionTracker & { syncWithMessages: (messages: any[]) => void };
}





