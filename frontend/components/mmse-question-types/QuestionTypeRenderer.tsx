"use client";

import React, { useState } from 'react';
import Serial7sInterface from './Serial7sInterface';
import WordRecallInterface from './WordRecallInterface';
import ReverseSpellingInterface from './ReverseSpellingInterface';
import NamingInterface from './NamingInterface';
import AnimalNamingInterface from './AnimalNamingInterface';
import ClockDrawingWhiteboard from './ClockDrawingWhiteboard';
import ClockDrawingModal from './ClockDrawingModal';
import { Button } from '@/components/ui/button';

interface QuestionTypeRendererProps {
  questionId: string;
  questionCategory: string;
  displayMode?: string;
  hiddenContent?: string[];
  currentTranscript?: string;
  isRecording?: boolean;
  onAnswer?: (answer: any) => void;
  onStop?: () => void;
  onTimeUp?: () => void; // ✅ ADD: For Verbal Fluency auto-stop
  onComplete?: (result: any) => void;
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
  onComplete
}: QuestionTypeRendererProps) {
  const normalizedId = questionId.toLowerCase();
  const normalizedCategory = questionCategory.toLowerCase();

  // Serial 7s (Subtraction)
  if (normalizedId.includes('serial7s') || normalizedId.includes('serial_7s') || 
      normalizedId.includes('attn_serial') ||
      (normalizedCategory.includes('attention') && normalizedId.includes('calculation'))) {
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
    // Extract word from question ID or use a default
    // In real implementation, this should come from question data
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

  // Naming objects
  if (normalizedId.includes('naming') || normalizedId.includes('lang_naming')) {
    // In real implementation, imageUrl should come from question data
    return (
      <NamingInterface
        questionId={questionId}
        onAnswer={(answer) => onAnswer?.({ answer })}
      />
    );
  }

  // Animal Naming (Verbal Fluency)
  if (normalizedId.includes('verbal_fluency') || normalizedId.includes('exec_verbal')) {
    return (
      <AnimalNamingInterface
        questionId={questionId}
        currentTranscript={currentTranscript}
        isRecording={isRecording}
        onAnswer={(animals) => {
          onAnswer?.({ animals });
          // Store animals for completion callback
        }}
        onTimeUp={() => {
          onTimeUp?.(); // ✅ Call parent onTimeUp callback (to stop recording)
          onComplete?.({ completed: true });
        }}
      />
    );
  }

  // Clock Drawing (Visual) - Use Modal version
  if (normalizedId.includes('clock') || normalizedId.includes('visual_clock')) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    
    return (
      <>
        <Button
          onClick={() => setIsModalOpen(true)}
          size="lg"
          className="w-full"
        >
          Mở bảng vẽ đồng hồ
        </Button>
        <ClockDrawingModal
          isOpen={isModalOpen}
          targetTime={displayMode || "11:10"}
          onSubmit={(imageData) => {
            // Submit clock drawing image to backend
            onComplete?.({ imageData, questionId });
            setIsModalOpen(false);
          }}
          onClose={() => setIsModalOpen(false)}
          elderlyFriendly={true}
          canvasSize={500}
        />
      </>
    );
  }

  // Default: No special interface
  return null;
}

/**
 * Check if a question ID requires special rendering
 */
export function requiresSpecialInterface(questionId: string, questionCategory: string): boolean {
  const normalizedId = questionId.toLowerCase();
  const normalizedCategory = questionCategory.toLowerCase();
  
  return (
    normalizedId.includes('serial7s') ||
    normalizedId.includes('serial_7s') ||
    normalizedId.includes('reg_') ||
    normalizedId.includes('rec_') ||
    normalizedId.includes('registration') ||
    normalizedId.includes('recall') ||
    normalizedId.includes('spell_backward') ||
    normalizedId.includes('backward') ||
    normalizedId.includes('naming') ||
    normalizedId.includes('lang_naming') ||
    normalizedId.includes('verbal_fluency') ||
    normalizedId.includes('exec_verbal') ||
    normalizedId.includes('clock') ||
    normalizedId.includes('visual_clock') ||
    (normalizedCategory.includes('attention') && normalizedId.includes('calculation'))
  );
}

