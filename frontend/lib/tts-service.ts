export class TTSService {
  private synth: SpeechSynthesis | null = null
  
  constructor() {
    if (typeof window !== 'undefined') {
      this.synth = window.speechSynthesis
    }
  }
  
  speak(text: string, lang: string = 'vi-VN') {
    if (!this.synth) return
    
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang
    this.synth.speak(utterance)
  }
  
  stop() {
    if (this.synth) {
      this.synth.cancel()
    }
  }
}

export const ttsService = new TTSService()

// lib/tts-service-fixed.ts - Robust TTS Service with proper error handling

import { useState, useCallback, useRef, useEffect } from 'react';

export function useTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<"idle" | "loading" | "playing" | "paused">("idle");
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Bắt đầu đọc
  const speak = (text: string, lang = "vi-VN") => {
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;

      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPlaying(true);
        setStatus("playing");
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPlaying(false);
        setIsPaused(false);
        setStatus("idle");
        setProgress(100);
      };

      utterance.onerror = (e) => {
        setError(e.error);
        setIsSpeaking(false);
        setIsPlaying(false);
        setStatus("idle");
      };

      utterance.onboundary = (event) => {
        // Tiến độ tương đối (không hoàn hảo)
        if (event.charIndex && text.length > 0) {
          setProgress(Math.round((event.charIndex / text.length) * 100));
        }
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  // Dừng đọc
  const stopTTS = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setIsPlaying(false);
    setStatus("idle");
  };

  // Tạm dừng
  const pauseTTS = () => {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
      setStatus("paused");
    }
  };

  // Tiếp tục
  const resumeTTS = () => {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      setStatus("playing");
    }
  };

  // Lấy danh sách giọng tiếng Việt
  const getVietnameseVoices = () => {
    return window.speechSynthesis.getVoices().filter(v => v.lang.startsWith("vi"));
  };

  // Refresh lại trạng thái
  const refreshStatus = () => {
    if (window.speechSynthesis.speaking) {
      setStatus(window.speechSynthesis.paused ? "paused" : "playing");
    } else {
      setStatus("idle");
    }
  };

  return {
    speak,
    stop: stopTTS,
    pause: pauseTTS,
    resume: resumeTTS,
    refreshStatus,
    getVietnameseVoices,
    isSpeaking,
    isPaused,
    error,
    progress,
    status,
    isLoading,
    isPlaying
  };
}


export interface TTSOptions {
  voice?: string;
  preset?: 'natural' | 'slow' | 'fast';
  rate?: number;
  language?: string;
}

export interface TTSStatus {
  apiAvailable: boolean;
  webSpeechAvailable: boolean;
  vietnameseVoicesCount: number;
  currentMethod: 'api' | 'webspeech' | 'none';
  lastError?: string;
}

class RobustTTSService {
  private synth: SpeechSynthesis | null = null;
  private voices: SpeechSynthesisVoice[] = [];
  private currentAudio: HTMLAudioElement | null = null;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private isInitialized = false;
  private speechTimeout: NodeJS.Timeout | null = null;
  private retryCount = 0;
  private maxRetries = 2;

  constructor() {
    this.initializeSpeechSynthesis();
  }

  private initializeSpeechSynthesis() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      this.synth = window.speechSynthesis;
      this.loadVoices();
    }
    this.isInitialized = true;
  }

  private loadVoices() {
    if (!this.synth) return;
    
    const updateVoices = () => {
      this.voices = this.synth!.getVoices();
      console.log('🎤 Loaded voices:', this.voices.length);
    };

    updateVoices();
    
    if (this.voices.length === 0) {
      this.synth.onvoiceschanged = updateVoices;
    }
  }

  getVietnameseVoices(): SpeechSynthesisVoice[] {
    return this.voices.filter(voice => 
      voice.lang.toLowerCase().includes('vi') || 
      voice.name.toLowerCase().includes('vietnam') ||
      voice.lang.toLowerCase().includes('vn')
    );
  }

  async checkStatus(): Promise<TTSStatus> {
    // Always use Web Speech API, no API backend needed
    const webSpeechAvailable = this.synth !== null && this.synth.getVoices().length > 0;
    const vietnameseVoicesCount = this.getVietnameseVoices().length;

    return {
      apiAvailable: false, // Disable API backend
      webSpeechAvailable,
      vietnameseVoicesCount,
      currentMethod: webSpeechAvailable ? 'webspeech' : 'none',
      lastError: webSpeechAvailable ? undefined : 'Web Speech API not available'
    };
  }


  async speakWithWebSpeech(text: string, options: TTSOptions = {}): Promise<boolean> {
    if (!this.synth) {
      throw new Error('Speech synthesis not available');
    }

    // Cancel any ongoing speech first
    this.synth.cancel();
    
    // Wait a bit for cancellation to complete
    await new Promise(resolve => setTimeout(resolve, 100));

    return new Promise((resolve, reject) => {
      try {
        let resolved = false;
        
        this.currentUtterance = new SpeechSynthesisUtterance(text.trim());
        
        // Configure utterance with safe defaults
        this.currentUtterance.rate = Math.max(0.5, Math.min(2.0, options.rate || 0.9));
        this.currentUtterance.pitch = 1;
        this.currentUtterance.volume = 1;
        
        // Try to set language
        const vietnameseVoices = this.getVietnameseVoices();
        if (vietnameseVoices.length > 0) {
          this.currentUtterance.voice = vietnameseVoices[0];
          this.currentUtterance.lang = vietnameseVoices[0].lang;
        } else {
          this.currentUtterance.lang = 'vi-VN';
        }

        const cleanup = () => {
          if (resolved) return;
          resolved = true;
          if (this.speechTimeout) {
            clearTimeout(this.speechTimeout);
            this.speechTimeout = null;
          }
          this.currentUtterance = null;
        };

        this.currentUtterance.onstart = () => {
          console.log('✅ WebSpeech TTS started');
        };

        this.currentUtterance.onend = () => {
          console.log('✅ WebSpeech TTS completed');
          cleanup();
          if (!resolved) resolve(true);
        };

        this.currentUtterance.onerror = (event) => {
          console.warn('⚠️ WebSpeech TTS error (will fallback):', {
            error: (event as any)?.error,
            type: (event as any)?.type,
            elapsedTime: (event as any)?.elapsedTime,
            charIndex: (event as any)?.charIndex
          });
          
          cleanup();
          
          if (!resolved) {
            const errorMessage = (event as any)?.error || 'unknown';
            
            // Handle specific error types
            if (errorMessage === 'interrupted' && this.retryCount < this.maxRetries) {
              this.retryCount++;
              console.log(`🔄 Retrying WebSpeech (attempt ${this.retryCount}/${this.maxRetries})`);
              
              // Retry after a short delay
              setTimeout(() => {
                this.speakWithWebSpeech(text, options)
                  .then(resolve)
                  .catch(reject);
              }, 500);
            } else {
              reject(new Error(`Speech synthesis error: ${errorMessage}`));
            }
          }
        };

        // Set a reasonable timeout
        this.speechTimeout = setTimeout(() => {
          console.warn('⚠️ WebSpeech timeout, cancelling');
          this.synth!.cancel();
          cleanup();
          if (!resolved) {
            reject(new Error('Speech synthesis timeout'));
          }
        }, Math.max(5000, text.length * 100)); // Dynamic timeout based on text length

        // Start speaking
        if (this.synth) {
          this.synth.speak(this.currentUtterance);
        } else {
          reject(new Error('Speech synthesis not available'));
        }
        
      } catch (error) {
        reject(error);
      }
    });
  }

  async speak(text: string, options: TTSOptions = {}): Promise<boolean> {
    if (!text || text.trim().length === 0) {
      console.warn('❌ Empty text provided to TTS');
      return false;
    }

    // Clean and validate text
    const cleanText = text
      .replace(/[{}]/g, '') // Remove template literals
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/[^\w\s.,!?;:àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/gi, '') // Keep only safe characters
      .trim();

    if (cleanText.length === 0) {
      console.warn('❌ Text is empty after cleaning');
      return false;
    }

    if (cleanText.length > 1000) {
      console.warn('⚠️ Text is very long, truncating to 1000 characters');
      cleanText.substring(0, 1000);
    }

    console.log(`🎵 TTS Request: "${cleanText.substring(0, 50)}..."`);
    this.retryCount = 0;

    // Only use WebSpeech API (no API backend)
    try {
      console.log('🎤 Using WebSpeech TTS...');
      const result = await this.speakWithWebSpeech(cleanText, options);
      console.log('✅ WebSpeech successful');
      return result;
    } catch (webSpeechError) {
      console.error('❌ WebSpeech failed:', webSpeechError);

      // Last resort: try simple WebSpeech with English
      try {
        console.log('🔄 Last resort: Simple English WebSpeech...');
        const simpleUtterance = new SpeechSynthesisUtterance(cleanText);
        simpleUtterance.lang = 'en-US';
        simpleUtterance.rate = 0.8;

        if (this.synth) {
          this.synth.cancel();
          this.synth.speak(simpleUtterance);
          return true;
        }
      } catch (lastResortError) {
        console.error('❌ Last resort failed:', lastResortError);
      }

      throw new Error(`WebSpeech TTS failed: ${webSpeechError instanceof Error ? webSpeechError.message : 'Unknown error'}`);
    }
  }

  stop(): void {
    // Stop API audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }

    // Stop WebSpeech
    if (this.synth) {
      this.synth.cancel();
      this.currentUtterance = null;
    }

    // Clear timeouts
    if (this.speechTimeout) {
      clearTimeout(this.speechTimeout);
      this.speechTimeout = null;
    }

    this.retryCount = 0;
  }

  pause(): void {
    if (this.currentAudio && !this.currentAudio.paused) {
      this.currentAudio.pause();
    }
    if (this.synth && this.synth.speaking) {
      this.synth.pause();
    }
  }

  resume(): void {
    if (this.currentAudio && this.currentAudio.paused) {
      this.currentAudio.play().catch(console.error);
    }
    if (this.synth && this.synth.paused) {
      this.synth.resume();
    }
  }

  isSpeaking(): boolean {
    const audioPlaying = this.currentAudio && !this.currentAudio.paused;
    const speechSpeaking = this.synth && this.synth.speaking;
    return !!(audioPlaying || speechSpeaking);
  }

  isPaused(): boolean {
    const audioPaused = this.currentAudio && this.currentAudio.paused;
    const speechPaused = this.synth && this.synth.paused;
    return !!(audioPaused || speechPaused);
  }
}

// Singleton instance
let robustTTSService: RobustTTSService | null = null;

function getRobustTTSService(): RobustTTSService {
  if (!robustTTSService) {
    robustTTSService = new RobustTTSService();
  }
  return robustTTSService;
}

// Enhanced React Hook
export function useRobustTTS() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<TTSStatus | null>(null);
  const [progress, setProgress] = useState(0);
  
  const ttsServiceRef = useRef<RobustTTSService>(getRobustTTSService());

  // Status polling
  useEffect(() => {
    const updateStatus = () => {
      const service = ttsServiceRef.current;
      setIsSpeaking(service.isSpeaking());
      setIsPaused(service.isPaused());
      setIsPlaying(service.isSpeaking() && !service.isPaused());
    };

    const interval = setInterval(updateStatus, 300);
    return () => clearInterval(interval);
  }, []);

  const speak = useCallback(async (text: string, options: TTSOptions = {}): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    setProgress(0);

    try {
      const result = await ttsServiceRef.current.speak(text, options);
      setProgress(100);
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown TTS error';
      setError(errorMessage);
      console.error('❌ TTS Error:', errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const stop = useCallback(() => {
    ttsServiceRef.current.stop();
    setError(null);
    setProgress(0);
  }, []);

  const pause = useCallback(() => {
    ttsServiceRef.current.pause();
  }, []);

  const resume = useCallback(() => {
    ttsServiceRef.current.resume();
  }, []);

  const refreshStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const newStatus = await ttsServiceRef.current.checkStatus();
      setStatus(newStatus);
      if (newStatus.lastError) {
        setError(newStatus.lastError);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to refresh status';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getVietnameseVoices = useCallback(() => {
    return ttsServiceRef.current.getVietnameseVoices();
  }, []);

  // Initialize status
  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  return {
    speak,
    stop,
    pause,
    resume,
    refreshStatus,
    getVietnameseVoices,
    isSpeaking,
    isPaused,
    error,
    progress,
    status,
    isLoading,
    isPlaying
  };
}