/**
 * QuestionTypeRenderer - Routes to appropriate question interface
 * Based on existing implementation with improvements
 */

"use client";

import React from 'react';
import Serial7sInterface from './Serial7sInterface';
import WordRecallInterface from './WordRecallInterface';
import ReverseSpellingInterface from './ReverseSpellingInterface';
import NamingInterface from './NamingInterface';
import AnimalNamingInterface from './AnimalNamingInterface';
import ClockDrawingModal from './ClockDrawingModal';

export interface QuestionTypeRendererProps {
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
}

/**
 * Check if question requires special interface
 */
export function requiresSpecialInterface(questionId: string, questionCategory: string): boolean {
  const normalizedId = questionId.toLowerCase();
  const normalizedCategory = questionCategory.toLowerCase();

  return (
    normalizedId.includes('serial7s') ||
    normalizedId.includes('serial_7s') ||
    normalizedId.includes('attn_serial') ||
    normalizedId.includes('reg_') ||
    normalizedId.includes('rec_') ||
    normalizedId.includes('recall') ||
    normalizedId.includes('spell_backward') ||
    normalizedId.includes('naming') ||
    normalizedId.includes('verbal_fluency') ||
    normalizedId.includes('clock_drawing') ||
    normalizedId.includes('visual_clock') ||
    (normalizedCategory.includes('attention') && normalizedId.includes('calculation')) ||
    normalizedCategory.includes('executive') ||
    normalizedCategory.includes('language')
  );
}

/**
 * Router component to render appropriate question type interface
 */
export default function QuestionTypeRenderer({
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
}: QuestionTypeRendererProps) {
  const normalizedId = questionId.toLowerCase();
  const normalizedCategory = questionCategory.toLowerCase();

  // Serial 7s (Subtraction)
  if (
    normalizedId.includes('serial7s') ||
    normalizedId.includes('serial_7s') ||
    normalizedId.includes('attn_serial') ||
    (normalizedCategory.includes('attention') && normalizedId.includes('calculation'))
  ) {
    return (
      <Serial7sInterface
        questionId={questionId}
        currentTranscript={currentTranscript}
        isRecording={isRecording}
        onAnswer={(answers) => onAnswer?.(answers)}
        onStop={() => onStop?.()}
      />
    );
  }

  // Word Registration
  if (normalizedId.includes('reg_') || normalizedId.includes('registration')) {
    const words = hiddenContent || [];
    return (
      <WordRecallInterface
        questionId={questionId}
        words={words as string[]}
        phase="registration"
        currentTranscript={currentTranscript}
        onComplete={(matched) => onComplete?.({ matchedWords: matched })}
      />
    );
  }

  // Word Recall
  if (normalizedId.includes('rec_') || normalizedId.includes('recall')) {
    const words = hiddenContent || [];
    return (
      <WordRecallInterface
        questionId={questionId}
        words={words as string[]}
        phase="recall"
        currentTranscript={currentTranscript}
        onComplete={(matched) => onComplete?.({ matchedWords: matched })}
        showWords={false}
      />
    );
  }

  // Reverse Spelling
  if (normalizedId.includes('spell_backward') || normalizedId.includes('backward')) {
    const word = normalizedId.includes('world') ? 'WORLD' : 'THỊNH';
    return (
      <ReverseSpellingInterface
        questionId={questionId}
        word={word}
        currentTranscript={currentTranscript}
        onComplete={(spelling) => onComplete?.({ spelling })}
      />
    );
  }

  // Naming Objects
  if (normalizedId.includes('naming') || normalizedCategory.includes('naming')) {
    return (
      <NamingInterface
        questionId={questionId}
        currentTranscript={currentTranscript}
        onComplete={(objects) => onComplete?.({ objects })}
      />
    );
  }

  // Animal Naming (Verbal Fluency)
  if (
    normalizedId.includes('verbal_fluency') ||
    normalizedId.includes('animal') ||
    normalizedCategory.includes('verbal') ||
    normalizedCategory.includes('fluency')
  ) {
    return (
      <AnimalNamingInterface
        questionId={questionId}
        currentTranscript={currentTranscript}
        isRecording={isRecording}
        onTimeUp={() => onTimeUp?.()}
        onComplete={(animals) => onComplete?.({ animals })}
      />
    );
  }

  // Clock Drawing
  if (
    normalizedId.includes('clock_drawing') ||
    normalizedId.includes('visual_clock') ||
    normalizedCategory.includes('visuospatial')
  ) {
    return (
      <ClockDrawingModal
        questionId={questionId}
        targetTime={displayMode}
        onComplete={(result) => onComplete?.(result)}
      />
    );
  }

  // Default: No special interface
  return null;
}
