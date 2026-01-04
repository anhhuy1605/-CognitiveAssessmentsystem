/**
 * MessageList Component - Displays list of chat messages
 */

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage } from '../../services/chatService';
import MessageItem from './MessageItem';
import { Loader2 } from 'lucide-react';
import QuestionTypeRenderer, { requiresSpecialInterface } from '../../components/questions/QuestionTypeRenderer';
import { getCurrentQuestion, isQuestionActive } from '../../utils/questionTracker';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  currentTranscript?: string;
  isRecording?: boolean;
  onStopRecording?: () => void;
  onSendMessage?: (text: string, audioBlob?: Blob, metadata?: Record<string, any>) => void | Promise<void>;
  elderlyFriendly?: boolean;
}

export default function MessageList({
  messages,
  isLoading = false,
  currentTranscript,
  isRecording,
  onStopRecording,
  onSendMessage,
  elderlyFriendly = true,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentQuestion = getCurrentQuestion(messages);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <p className="text-lg">Chưa có tin nhắn nào. Hãy bắt đầu cuộc trò chuyện!</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <AnimatePresence>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <MessageItem message={message} elderlyFriendly={elderlyFriendly} />

            {/* Special Question Interfaces - Only render for active question */}
            {message.type === 'bot' &&
              message.questionId &&
              message.questionCategory &&
              requiresSpecialInterface(message.questionId, message.questionCategory) &&
              isQuestionActive(message.questionId, currentQuestion) && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <QuestionTypeRenderer
                    questionId={message.questionId}
                    questionCategory={message.questionCategory}
                    displayMode={message.displayMode}
                    hiddenContent={message.hiddenContent}
                    currentTranscript={message.questionId === currentQuestion?.questionId ? currentTranscript : undefined}
                    isRecording={isRecording && message.questionId === currentQuestion?.questionId}
                    onStop={() => {
                      if (isRecording && onStopRecording) {
                        onStopRecording();
                      }
                      const finalAnswer = currentTranscript?.trim() || 'Đã hoàn thành';
                      if (finalAnswer && onSendMessage) {
                        onSendMessage(finalAnswer);
                      }
                    }}
                    onTimeUp={() => {
                      if (isRecording && onStopRecording) {
                        onStopRecording();
                      }
                      const finalAnswer = currentTranscript?.trim() || 'Đã kể xong';
                      if (finalAnswer && onSendMessage) {
                        onSendMessage(finalAnswer);
                      }
                    }}
                    onAnswer={(answer) => {
                      console.log('Special interface answer:', answer);
                    }}
                    onComplete={(result) => {
                      console.log('Special interface complete:', result);
                      if (result.imageData && onSendMessage) {
                        onSendMessage('', undefined, { imageData: result.imageData, questionId: message.questionId });
                      }
                    }}
                  />
                </div>
              )}
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Đang xử lý...</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}

