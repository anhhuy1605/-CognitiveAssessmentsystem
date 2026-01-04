"use client";

/**
 * Question Renderer with Tracking
 * ================================
 * 
 * Renders special question interfaces only when question is active
 */

import React from 'react';
import { useQuestionTrackerContext } from './QuestionTrackerProvider';
import QuestionTypeRenderer, { requiresSpecialInterface } from './QuestionTypeRenderer';

interface QuestionRendererProps {
  questionId: string;
  questionCategory: string;
  displayMode?: string;
  hiddenContent?: string[];
  currentTranscript?: string;
  isRecording?: boolean;
  onAnswer?: (answer: any) => void;
  onStop?: () => void;
  onTimeUp?: () => void;
  onComplete?: (result: any) => void;
  targetTime?: string;
}

/**
 * Smart question renderer that only renders when question is active
 */
export default function QuestionRenderer({
  questionId,
  questionCategory,
  displayMode,
  hiddenContent,
  currentTranscript,
  isRecording,
  onAnswer,
  onStop,
  onTimeUp,
  onComplete,
  targetTime,
}: QuestionRendererProps) {
  const { isQuestionActive, currentQuestion } = useQuestionTrackerContext();

  // Only render if this question is currently active
  if (!isQuestionActive(questionId)) {
    return null;
  }

  // Double check that this question requires special interface
  if (!requiresSpecialInterface(questionId, questionCategory)) {
    return null;
  }

  // Get metadata from current question
  const metadata = currentQuestion?.metadata || {};

  return (
    <div className="question-renderer-container" data-question-id={questionId}>
      <QuestionTypeRenderer
        questionId={questionId}
        questionCategory={questionCategory}
        displayMode={displayMode || metadata.displayMode}
        hiddenContent={hiddenContent || metadata.hiddenContent}
        currentTranscript={currentTranscript}
        isRecording={isRecording}
        onAnswer={onAnswer}
        onStop={onStop}
        onTimeUp={onTimeUp}
        onComplete={onComplete}
        targetTime={targetTime || metadata.targetTime}
      />
    </div>
  );
}





