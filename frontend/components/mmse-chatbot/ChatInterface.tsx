"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mic, Square, Loader2, User, Brain, Send, Upload, Volume2,
  Eye, EyeOff, Lock, CheckCircle, AlertCircle, Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import HiddenMessage from '@/components/mmse-question-types/HiddenMessage';
import QuestionTypeRenderer, { requiresSpecialInterface } from '@/components/mmse-question-types/QuestionTypeRenderer';
import { getCurrentQuestion, isQuestionActive } from '@/utils/questionTracker';

// ============================================
// TYPES
// ============================================
export interface ChatMessage {
  id: string;
  type: "bot" | "user" | "system";
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
    total_score: number;
    max_score: number;
    percentage: number;
    is_correct: boolean;
    feedback?: string;
  };
  audioUrl?: string;
  actionButtons?: Array<{
    label: string;
    action: string;
    variant?: "primary" | "secondary";
  }>;
}

interface ChatInterfaceProps {
  /**
   * Array of messages to display
   */
  messages: ChatMessage[];
  
  /**
   * Current input text
   */
  inputText: string;
  
  /**
   * Callback when input text changes
   */
  onInputChange: (text: string) => void;
  
  /**
   * Callback when user submits message
   */
  onSendMessage: (text: string, audioBlob?: Blob, metadata?: any) => void;
  
  /**
   * Whether recording is active
   */
  isRecording?: boolean;
  
  /**
   * Callback to start recording
   */
  onStartRecording?: () => void;
  
  /**
   * Callback to stop recording
   */
  onStopRecording?: () => void;
  
  /**
   * Whether processing is in progress
   */
  isProcessing?: boolean;
  
  /**
   * Whether voice/TTS is enabled
   */
  voiceEnabled?: boolean;
  
  /**
   * Callback to toggle voice
   */
  onToggleVoice?: () => void;
  
  /**
   * Current transcript for special interfaces
   */
  currentTranscript?: string;
  
  /**
   * Active question ID for special interfaces
   */
  activeQuestionId?: string;
  
  /**
   * Whether this is for elderly users (larger text, simpler UI)
   */
  elderlyFriendly?: boolean;
  
  /**
   * API base URL
   */
  apiBaseUrl?: string;
}

/**
 * Beautiful, professional chat interface for MMSE chatbot
 * Designed for elderly users with large text and simple controls
 */
export default function ChatInterface({
  messages,
  inputText,
  onInputChange,
  onSendMessage,
  isRecording = false,
  onStartRecording,
  onStopRecording,
  isProcessing = false,
  voiceEnabled = false,
  onToggleVoice,
  currentTranscript,
  activeQuestionId,
  elderlyFriendly = true,
  apiBaseUrl = '/api'
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);
  
  // Get current active question
  const currentQuestion = getCurrentQuestion(messages);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle file upload
  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    console.log("📁 ChatInterface: handleFileUpload called", e.target.files);
    
    const file = e.target.files?.[0];
    if (!file) {
      console.warn("⚠️ ChatInterface: No file selected");
      return;
    }

    console.log(`📄 ChatInterface: File selected: ${file.name}, size: ${(file.size / 1024).toFixed(1)} KB, type: ${file.type || 'unknown'}`);

    // Validate file type
    const validTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm', 'audio/ogg', 'audio/m4a', 'audio/x-m4a'];
    const isValidType = validTypes.includes(file.type) || file.type.startsWith('audio/') || file.name.match(/\.(wav|mp3|webm|ogg|m4a)$/i);
    
    if (!isValidType) {
      console.error("❌ ChatInterface: Invalid file type:", file.type);
      alert('Vui lòng chọn file audio hợp lệ (WAV, MP3, WebM, OGG, M4A)');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      console.error("❌ ChatInterface: File too large:", file.size);
      alert('File quá lớn. Vui lòng chọn file nhỏ hơn 10MB');
      return;
    }

    console.log("✅ ChatInterface: File validation passed, starting FileReader...");

    // Read file as blob and submit
    const reader = new FileReader();
    
    reader.onloadstart = () => {
      console.log("📖 ChatInterface: FileReader onloadstart");
    };
    
    reader.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentLoaded = Math.round((event.loaded / event.total) * 100);
        console.log(`📖 ChatInterface: FileReader progress ${percentLoaded}%`);
      }
    };
    
    reader.onload = async () => {
      console.log("📖 ChatInterface: FileReader onload - File read complete");
      try {
        const blob = new Blob([reader.result as ArrayBuffer], { type: file.type || 'audio/webm' });
        console.log(`✅ ChatInterface: Blob created: size=${blob.size} bytes, type=${blob.type}`);
        console.log("📤 ChatInterface: Calling onSendMessage with blob...");
        onSendMessage('', blob);
      } catch (error: any) {
        console.error("❌ ChatInterface: Error creating blob or sending:", error);
        alert(`Lỗi khi xử lý file: ${error.message || 'Unknown error'}`);
      }
    };
    
    reader.onerror = (error) => {
      console.error("❌ ChatInterface: FileReader error:", error);
      alert('Lỗi khi đọc file. Vui lòng thử lại.');
    };
    
    reader.onabort = () => {
      console.warn("⚠️ ChatInterface: FileReader aborted");
      alert('Đọc file bị hủy. Vui lòng thử lại.');
    };
    
    reader.onloadend = () => {
      console.log("📖 ChatInterface: FileReader onloadend");
    };
    
    console.log("📖 ChatInterface: Starting FileReader.readAsArrayBuffer...");
    reader.readAsArrayBuffer(file);
  }, [onSendMessage]);

  // Handle send button
  const handleSend = useCallback(() => {
    if (inputText.trim() && !isProcessing) {
      onSendMessage(inputText.trim());
    }
  }, [inputText, isProcessing, onSendMessage]);

  // Handle keyboard shortcuts
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  // Text size classes for elderly-friendly design
  const textSize = elderlyFriendly ? 'text-lg' : 'text-base';
  const buttonSize = elderlyFriendly ? 'lg' : 'default';

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className={`flex items-start gap-3 max-w-[85%] sm:max-w-[70%] ${
                message.type === "user" ? "flex-row-reverse" : ""
              }`}>
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md ${
                  message.type === "user"
                    ? "bg-gradient-to-br from-green-500 to-teal-600"
                    : message.type === "system"
                    ? "bg-gradient-to-br from-yellow-400 to-orange-500"
                    : "bg-gradient-to-br from-blue-500 to-indigo-600"
                }`}>
                  {message.type === "user" ? (
                    <User className="w-5 h-5 text-white" />
                  ) : message.type === "system" ? (
                    <CheckCircle className="w-5 h-5 text-white" />
                  ) : (
                    <Brain className="w-5 h-5 text-white" />
                  )}
                </div>

                {/* Message Bubble */}
                <div className={`flex flex-col gap-2 ${
                  message.type === "user" ? "items-end" : "items-start"
                }`}>
                  <div className={`px-4 py-3 rounded-2xl shadow-sm ${
                    message.type === "user"
                      ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-tr-sm"
                      : message.type === "system"
                      ? "bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 text-gray-800 rounded-tl-sm"
                      : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
                  }`}>
                    {/* Message Content with Hidden Support */}
                    <HiddenMessage
                      visibleText={message.content}
                      hiddenContent={message.hiddenContent}
                      isRevealed={message.isRevealed}
                      textSize={elderlyFriendly ? "lg" : "md"}
                      elderlyFriendly={elderlyFriendly}
                    />

                    {/* Special Question Interfaces */}
                    {message.type === "bot" && message.questionId && message.questionCategory && 
                     requiresSpecialInterface(message.questionId, message.questionCategory) &&
                     isQuestionActive(message.questionId, currentQuestion) && (
                      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <QuestionTypeRenderer
                          questionId={message.questionId}
                          questionCategory={message.questionCategory}
                          displayMode={message.displayMode}
                          hiddenContent={message.hiddenContent}
                          currentTranscript={message.questionId === activeQuestionId ? currentTranscript : undefined}
                          isRecording={isRecording && message.questionId === activeQuestionId}
                          onStop={() => {
                            if (isRecording && onStopRecording) {
                              onStopRecording();
                            }
                            const finalAnswer = currentTranscript?.trim() || "Đã hoàn thành";
                            if (finalAnswer) {
                              onSendMessage(finalAnswer);
                            }
                          }}
                          onTimeUp={() => {
                            if (isRecording && onStopRecording) {
                              onStopRecording();
                            }
                            const finalAnswer = currentTranscript?.trim() || "Đã kể xong";
                            if (finalAnswer) {
                              onSendMessage(finalAnswer);
                            }
                          }}
                          onAnswer={(answer) => {
                            console.log("Special interface answer:", answer);
                          }}
                          onComplete={(result) => {
                            console.log("Special interface complete:", result);
                          }}
                        />
                      </div>
                    )}

                    {/* Score Badge */}
                    {message.score && (
                      <div className={`mt-3 px-3 py-2 rounded-lg ${
                        message.score.is_correct
                          ? "bg-green-100 text-green-800 border border-green-300"
                          : "bg-red-100 text-red-800 border border-red-300"
                      }`}>
                        <div className="flex items-center gap-2">
                          {message.score.is_correct ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : (
                            <AlertCircle className="w-4 h-4" />
                          )}
                          <span className="text-sm font-medium">
                            {message.score.points_earned}/{message.score.points_possible} điểm
                          </span>
                        </div>
                        {message.score.feedback && (
                          <p className="text-xs mt-1">{message.score.feedback}</p>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    {message.actionButtons && message.actionButtons.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {message.actionButtons.map((button, idx) => (
                          <Button
                            key={idx}
                            variant={button.variant === "primary" ? "default" : button.variant === "secondary" ? "secondaryOutline" : "default"}
                            size={buttonSize}
                            onClick={() => {
                              // Handle action button click
                              console.log("Action button clicked:", button.action);
                            }}
                            className="text-sm"
                          >
                            {button.label}
                          </Button>
                        ))}
                      </div>
                    )}

                    {/* Audio Playback */}
                    {message.audioUrl && (
                      <div className="mt-3">
                        <audio 
                          controls 
                          src={message.audioUrl} 
                          className="w-full h-10"
                        />
                      </div>
                    )}

                    {/* Timestamp */}
                    <div className="mt-2 text-xs opacity-60">
                      {message.timestamp.toLocaleTimeString('vi-VN', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Processing Indicator */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div className="px-4 py-3 bg-white border border-gray-200 rounded-2xl rounded-tl-sm shadow-sm">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  <span className={`text-gray-600 ${textSize}`}>Đang xử lý...</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-200 shadow-lg">
        <div className="flex items-end gap-2">
          {/* Voice Recording Button */}
          <motion.button
            onClick={isRecording ? onStopRecording : onStartRecording}
            disabled={isProcessing}
            className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all flex-shrink-0 ${
              isRecording
                ? "bg-red-500 hover:bg-red-600 animate-pulse"
                : "bg-blue-500 hover:bg-blue-600"
            } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
            whileTap={{ scale: 0.95 }}
            title={isRecording ? "Dừng ghi âm" : "Bắt đầu ghi âm"}
          >
            {isRecording ? (
              <Square className="w-6 h-6" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </motion.button>

          {/* File Upload Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="audio/*,.wav,.mp3,.webm,.ogg,.m4a"
            className="hidden"
          />
          <motion.button
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing || isRecording}
            className="w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all bg-purple-500 hover:bg-purple-600 text-white flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
            whileTap={{ scale: 0.95 }}
            title="Upload file audio"
          >
            <Upload className="w-6 h-6" />
          </motion.button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <Input
              value={inputText}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isRecording ? "Đang ghi âm..." : "Nhập câu trả lời hoặc ghi âm..."}
              disabled={isProcessing}
              className={`${textSize} h-14 pr-12 border-2 rounded-xl ${
                elderlyFriendly ? 'text-lg' : 'text-base'
              }`}
            />
            {inputText.trim() && (
              <Button
                onClick={handleSend}
                disabled={isProcessing}
                size="sm"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-10"
              >
                <Send className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Voice TTS Toggle */}
          {onToggleVoice && (
            <motion.button
              onClick={onToggleVoice}
              className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all flex-shrink-0 ${
                voiceEnabled
                  ? "bg-green-500 hover:bg-green-600"
                  : "bg-gray-400 hover:bg-gray-500"
              } text-white`}
              whileTap={{ scale: 0.95 }}
              title={voiceEnabled ? "Tắt giọng nói" : "Bật giọng nói"}
            >
              <Volume2 className="w-6 h-6" />
            </motion.button>
          )}
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 flex items-center gap-2 text-red-600"
          >
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className={`${textSize} font-medium`}>Đang ghi âm...</span>
          </motion.div>
        )}
      </div>
    </div>
  );
}

