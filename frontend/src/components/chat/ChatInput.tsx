/**
 * ChatInput Component - Input area with text, voice, and file upload
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square, Upload, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (text: string) => void;
  onStartRecording: () => Promise<void>;
  onStopRecording: () => void;
  onFileUpload: (file: File) => void;
  isRecording: boolean;
  isProcessing: boolean;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  elderlyFriendly?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  value,
  onChange,
  onSend,
  onStartRecording,
  onStopRecording,
  onFileUpload,
  isRecording,
  isProcessing,
  voiceEnabled,
  onToggleVoice,
  elderlyFriendly = true,
  placeholder = 'Nhập câu trả lời của bạn...',
}: ChatInputProps) {
  const [isComposing, setIsComposing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !isProcessing) {
      onSend(value.trim());
      onChange('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRecordingClick = async () => {
    if (isRecording) {
      onStopRecording();
    } else {
      try {
        await onStartRecording();
      } catch (error: any) {
        console.error('Failed to start recording:', error);
        alert(error.message || 'Không thể bắt đầu ghi âm. Vui lòng kiểm tra quyền microphone.');
      }
    }
  };

  // Auto-focus on mount
  useEffect(() => {
    if (inputRef.current && !isProcessing) {
      inputRef.current.focus();
    }
  }, [isProcessing]);

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-end gap-2 p-4 bg-white border-t border-gray-200">
        {/* File Upload Button */}
        <Button
          type="button"
          variant="secondaryOutline"
          size={elderlyFriendly ? 'lg' : 'default'}
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing || isRecording}
          className="flex-shrink-0"
          aria-label="Upload file"
        >
          <Upload className="h-4 w-4" />
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*,video/*"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="File input"
        />

        {/* Text Input */}
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder={placeholder}
            disabled={isProcessing || isRecording}
            className={`${elderlyFriendly ? 'text-lg py-6' : 'text-base py-3'} pr-24`}
            aria-label="Message input"
          />
        </div>

        {/* Voice Toggle */}
        <Button
          type="button"
          variant="secondaryOutline"
          size={elderlyFriendly ? 'lg' : 'default'}
          onClick={onToggleVoice}
          className="flex-shrink-0"
          aria-label={voiceEnabled ? 'Disable voice' : 'Enable voice'}
        >
          {voiceEnabled ? (
            <Volume2 className="h-4 w-4" />
          ) : (
            <VolumeX className="h-4 w-4" />
          )}
        </Button>

        {/* Record Button */}
        <Button
          type="button"
          variant={isRecording ? 'danger' : 'secondaryOutline'}
          size={elderlyFriendly ? 'lg' : 'default'}
          onClick={handleRecordingClick}
          disabled={isProcessing}
          className="flex-shrink-0"
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          {isRecording ? (
            <Square className="h-4 w-4" />
          ) : (
            <Mic className="h-4 w-4" />
          )}
        </Button>

        {/* Send Button */}
        <Button
          type="submit"
          size={elderlyFriendly ? 'lg' : 'default'}
          disabled={!value.trim() || isProcessing || isRecording}
          className="flex-shrink-0"
          aria-label="Send message"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}





