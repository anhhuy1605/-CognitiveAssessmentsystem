/**
 * ChatContainer Component - Main chat container with all features
 */

import React, { useState, useCallback } from 'react';
import { ChatMessage } from '../../services/chatService';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import { AlertCircle } from 'lucide-react';
import { chatService } from '../../services/chatService';

interface ChatContainerProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSendMessage: (text: string, audioBlob?: Blob, metadata?: Record<string, any>) => Promise<void>;
  onStartRecording: () => Promise<void>;
  onStopRecording: () => void;
  onFileUpload: (file: File) => void;
  isRecording: boolean;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  currentTranscript?: string;
  elderlyFriendly?: boolean;
}

export default function ChatContainer({
  messages,
  isLoading,
  error,
  onSendMessage,
  onStartRecording,
  onStopRecording,
  onFileUpload,
  isRecording,
  voiceEnabled,
  onToggleVoice,
  currentTranscript,
  elderlyFriendly = true,
}: ChatContainerProps) {
  const [inputText, setInputText] = useState('');

  const handleSend = useCallback(async (text: string) => {
    if (!text.trim()) return;

    // Get current audio blob if recording
    let audioBlob: Blob | undefined;
    if (isRecording) {
      // Stop recording and get blob
      onStopRecording();
      // Note: In real implementation, you'd get the blob from useVoice hook
      // For now, we'll send text only
    }

    await onSendMessage(text, audioBlob);
    setInputText('');
  }, [isRecording, onSendMessage, onStopRecording]);

  const handleFileUpload = useCallback(async (file: File) => {
    try {
      // If audio file, transcribe first
      if (file.type.startsWith('audio/') || file.type.startsWith('video/')) {
        const audioBlob = file;
        const response = await chatService.transcribeAudio(audioBlob);
        
        if (response.success && response.data?.transcript) {
          setInputText(response.data.transcript);
        } else {
          alert('Không thể chuyển đổi audio. Vui lòng thử lại.');
        }
      } else {
        // For other files, just upload
        onFileUpload(file);
      }
    } catch (err: any) {
      console.error('File upload error:', err);
      alert('Lỗi khi upload file: ' + (err.message || 'Unknown error'));
    }
  }, [onFileUpload]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-800 text-sm">{error}</span>
        </div>
      )}

      {/* Messages List */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        currentTranscript={currentTranscript}
        isRecording={isRecording}
        onStopRecording={onStopRecording}
        onSendMessage={handleSend}
        elderlyFriendly={elderlyFriendly}
      />

      {/* Input Area */}
      <ChatInput
        value={inputText}
        onChange={setInputText}
        onSend={handleSend}
        onStartRecording={onStartRecording}
        onStopRecording={onStopRecording}
        onFileUpload={handleFileUpload}
        isRecording={isRecording}
        isProcessing={isLoading}
        voiceEnabled={voiceEnabled}
        onToggleVoice={onToggleVoice}
        elderlyFriendly={elderlyFriendly}
      />
    </div>
  );
}





