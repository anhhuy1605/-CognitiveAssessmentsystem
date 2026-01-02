/**
 * useVoice Hook - Voice recording and TTS management
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface UseVoiceReturn {
  isRecording: boolean;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  speakText: (text: string) => void;
  voiceEnabled: boolean;
  toggleVoice: () => void;
}

export function useVoice(): UseVoiceReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  /**
   * Start voice recording
   */
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        chunksRef.current = [];
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err: any) {
      console.error('Error starting recording:', err);
      throw new Error('Failed to start recording. Please check microphone permissions.');
    }
  }, []);

  /**
   * Stop voice recording
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  /**
   * Text-to-speech
   */
  const speakText = useCallback((text: string) => {
    if (!voiceEnabled || !('speechSynthesis' in window)) {
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'vi-VN';
    utterance.rate = 0.9; // Slightly slower for elderly users
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    window.speechSynthesis.speak(utterance);
  }, [voiceEnabled]);

  /**
   * Toggle voice/TTS
   */
  const toggleVoice = useCallback(() => {
    setVoiceEnabled(prev => {
      if (!prev) {
        // If disabling, cancel any ongoing speech
        if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel();
        }
      }
      return !prev;
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isRecording]);

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    speakText,
    voiceEnabled,
    toggleVoice,
  };
}

