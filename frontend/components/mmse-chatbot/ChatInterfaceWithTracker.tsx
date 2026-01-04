"use client";

/**
 * Chat Interface with Question Tracker
 * ====================================
 * 
 * Enhanced ChatInterface that uses question tracking
 * to ensure special interfaces render at the right time
 */

import React from 'react';
import { QuestionTrackerProvider, useQuestionTrackerContext } from '@/components/mmse-question-types/QuestionTrackerProvider';
import ChatInterface, { ChatMessage } from './ChatInterface';
import QuestionRenderer from '@/components/mmse-question-types/QuestionRenderer';
import { requiresSpecialInterface } from '@/components/mmse-question-types/QuestionTypeRenderer';

interface ChatInterfaceWithTrackerProps {
  messages: ChatMessage[];
  currentTranscript?: string;
  isRecording: boolean;
  isProcessing: boolean;
  voiceEnabled: boolean;
  onSendMessage: (text: string, audioBlob?: Blob, metadata?: any) => void;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onFileUpload: (file: File) => void;
  onToggleVoice?: () => void;
  elderlyFriendly?: boolean;
}

/**
 * Inner component that uses tracker context
 */
function ChatInterfaceWithTrackerInner(props: ChatInterfaceWithTrackerProps) {
  const { currentQuestion, isQuestionActive } = useQuestionTrackerContext();
  const { messages, currentTranscript, isRecording } = props;

  // Get last bot message with question info
  const lastBotMessage = messages
    .filter(m => m.type === 'bot' && m.questionId)
    .pop();

  // Enhanced message rendering with question tracker
  const enhancedMessages = messages.map((message, index) => {
    if (message.type === 'bot' && message.questionId && message.questionCategory) {
      // Check if this question is currently active
      const isActive = isQuestionActive(message.questionId);
      
      return {
        ...message,
        // Add tracking metadata
        _tracking: {
          isActive,
          isCurrentQuestion: currentQuestion?.questionId === message.questionId,
          index,
        }
      };
    }
    return message;
  });

  return (
    <div className="chat-interface-with-tracker">
      <ChatInterface
        {...props}
        messages={enhancedMessages as ChatMessage[]}
      />
      
      {/* Render special interfaces only for active question */}
      {lastBotMessage && lastBotMessage.questionId && lastBotMessage.questionCategory &&
       requiresSpecialInterface(lastBotMessage.questionId, lastBotMessage.questionCategory) &&
       isQuestionActive(lastBotMessage.questionId) && (
        <div className="special-question-interface">
          <QuestionRenderer
            questionId={lastBotMessage.questionId}
            questionCategory={lastBotMessage.questionCategory}
            displayMode={lastBotMessage.displayMode}
            hiddenContent={lastBotMessage.hiddenContent}
            currentTranscript={currentTranscript}
            isRecording={isRecording}
            onAnswer={(answer) => {
              console.log("QuestionRenderer answer:", answer);
            }}
            onStop={() => {
              if (isRecording && props.onStopRecording) {
                props.onStopRecording();
              }
              const finalAnswer = currentTranscript?.trim() || "Đã hoàn thành";
              if (finalAnswer) {
                props.onSendMessage(finalAnswer);
              }
            }}
            onTimeUp={() => {
              if (isRecording && props.onStopRecording) {
                props.onStopRecording();
              }
              const finalAnswer = currentTranscript?.trim() || "Đã kể xong";
              if (finalAnswer) {
                props.onSendMessage(finalAnswer);
              }
            }}
            onComplete={(result) => {
              console.log("QuestionRenderer complete:", result);
              // Handle clock drawing submission
              if (result.imageData) {
                props.onSendMessage("", undefined, { 
                  imageData: result.imageData, 
                  questionId: lastBotMessage.questionId 
                });
              }
            }}
            targetTime={lastBotMessage.displayMode}
          />
        </div>
      )}
    </div>
  );
}

/**
 * Main component with tracker provider
 */
export default function ChatInterfaceWithTracker(props: ChatInterfaceWithTrackerProps) {
  // Extract messages for sync
  const messagesForSync = props.messages.map(m => ({
    questionId: m.questionId,
    domain: m.domain,
    questionCategory: m.questionCategory,
    displayMode: m.displayMode,
    hiddenContent: m.hiddenContent,
  }));

  return (
    <QuestionTrackerProvider messages={messagesForSync}>
      <ChatInterfaceWithTrackerInner {...props} />
    </QuestionTrackerProvider>
  );
}





