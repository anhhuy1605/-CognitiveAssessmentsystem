"use client";

/**
 * Question Tracker Provider
 * =========================
 * 
 * Provides question tracking context to child components
 */

import React, { createContext, useContext, useCallback, ReactNode } from 'react';
import { useQuestionTracker, QuestionState, QuestionTracker } from '@/hooks/useQuestionTracker';

interface QuestionTrackerContextType extends QuestionTracker {
  syncWithMessages: (messages: Array<{
    questionId?: string;
    domain?: string;
    questionCategory?: string;
    displayMode?: string;
    hiddenContent?: string[];
  }>) => void;
}

const QuestionTrackerContext = createContext<QuestionTrackerContextType | null>(null);

export function useQuestionTrackerContext() {
  const context = useContext(QuestionTrackerContext);
  if (!context) {
    throw new Error('useQuestionTrackerContext must be used within QuestionTrackerProvider');
  }
  return context;
}

interface QuestionTrackerProviderProps {
  children: ReactNode;
  messages?: Array<{
    questionId?: string;
    domain?: string;
    questionCategory?: string;
    displayMode?: string;
    hiddenContent?: string[];
  }>;
}

export function QuestionTrackerProvider({ children, messages = [] }: QuestionTrackerProviderProps) {
  const tracker = useQuestionTracker();

  // Auto-sync with messages
  React.useEffect(() => {
    if (messages.length > 0) {
      tracker.syncWithMessages(messages);
    }
  }, [messages, tracker]);

  return (
    <QuestionTrackerContext.Provider value={tracker}>
      {children}
    </QuestionTrackerContext.Provider>
  );
}





