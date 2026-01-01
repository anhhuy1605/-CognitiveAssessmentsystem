"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, Square, Loader2, CheckCircle, Brain, Volume2, User, Clock,
  ArrowRight, Home, Send, MessageCircle, Activity, FileText,
  Shield, Eye, EyeOff, AlertCircle, Sparkles, HelpCircle, FileAudio, Upload
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { useRouter } from "next/navigation";

// ============================================
// TYPES
// ============================================
interface UserInfo {
  name: string;
  age: string;
  gender: "male" | "female" | "other" | "";
  education_years: string;
  city: string;
  district: string;
}

interface ActionButton {
  label: string;
  action: string;
  variant?: "primary" | "secondary";
}

interface Message {
  id: string;
  type: "bot" | "user" | "system";
  content: string;
  timestamp: Date;
  hiddenContent?: string[];
  isRevealed?: boolean;
  domain?: string;
  questionId?: string;
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
  actionButtons?: ActionButton[];
}

interface DomainScore {
  name: string;
  code: string;
  score: number;
  maxScore: number;
  status: "pending" | "active" | "completed";
}

interface MMSEQuestion {
  question_id: string;
  question_category: string;
  display_mode: string;
  chatbot_message: string;
  points: number;
  expected_answer_format?: string;
  acceptable_answers?: string[];
  hidden_content?: string[];
  feedback_templates?: {
    correct: string;
    incorrect: string;
    partial?: string;
  };
}

interface MMSEDomain {
  domain_code: string;
  domain_name: string;
  max_points: number;
  questions: MMSEQuestion[];
}

interface SessionState {
  sessionId: string;
  userInfo: UserInfo;
  greeting: string;
  currentDomain: number;
  currentQuestion: number;
  messages: Message[];
  domainScores: DomainScore[];
  totalScore: number;
  hiddenContent: {
    registration: string[];
    recall: string[];
    isRevealed: boolean;
  };
  linguisticData: {
    totalWords: number;
    uniqueWords: Set<string>;
    responses: string[];
  };
  startTime: Date;
  registrationTime?: Date;
  isComplete: boolean;
}

// ============================================
// CONSTANTS
// ============================================
// Get API URL from environment, with better fallback handling
const getApiBaseUrl = () => {
  // Try multiple environment variable names
  const apiUrl = 
    process.env.NEXT_PUBLIC_API_URL || 
    process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL ||
    (typeof window !== 'undefined' ? window.location.origin.replace(/:\d+$/, ':5001') : 'http://localhost:5001');
  
  // In production (Vercel), should never use localhost
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && apiUrl.includes('localhost')) {
    console.error('⚠️ API_BASE_URL is using localhost in production! Set NEXT_PUBLIC_API_URL environment variable on Vercel.');
  }
  
  return apiUrl;
};

const API_BASE_URL = getApiBaseUrl();

const DOMAIN_ICONS: Record<string, string> = {
  ORIENTATION: "🧭",
  REGISTRATION: "📝",
  ATTENTION: "🎯",
  RECALL: "🔄",
  LANGUAGE: "💬",
  VISUOSPATIAL: "🎨",
};

// ============================================
// MAIN COMPONENT
// ============================================
export default function MMSEChatbotPage() {
  const router = useRouter();
  
  // ============================================
  // STATE
  // ============================================
  const [currentStep, setCurrentStep] = useState<"userInfo" | "chat" | "results">("userInfo");
  const [userInfo, setUserInfo] = useState<UserInfo>({
    name: "",
    age: "",
    gender: "",
    education_years: "",
    city: "",
    district: "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof UserInfo, string>>>({});
  
  // Session state
  const [session, setSession] = useState<SessionState | null>(null);
  const [mmseData, setMmseData] = useState<{ domains: MMSEDomain[] } | null>(null);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  
  // Chat state
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isInitializingMic, setIsInitializingMic] = useState(false); // ✅ FIX: Track mic initialization
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [currentAudioBlob, setCurrentAudioBlob] = useState<Blob | null>(null);
  
  // ✅ REAL-TIME: Score notification state
  const [scoreNotification, setScoreNotification] = useState<{
    points_earned: number;
    points_possible: number;
    total_score: number;
    max_score: number;
    percentage: number;
    is_correct: boolean;
    feedback?: string;
  } | null>(null);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ============================================
  // EFFECTS
  // ============================================
  useEffect(() => {
    loadMMSEQuestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [session?.messages]);

  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, []);

  // ============================================
  // FUNCTIONS
  // ============================================
  const loadMMSEQuestions = async () => {
    setIsLoadingQuestions(true);
    
    // Strategy: Try JSON first (faster, more reliable), then backend
    // JSON fallback should work on Vercel since it's in public folder
    try {
      console.log("📄 Loading MMSE questions from local JSON...");
      const localData = await fetch("/mmse_audio_questions_standardized.json", {
        signal: AbortSignal.timeout(3000), // 3 second timeout
      });
      
      if (localData.ok) {
        const json = await localData.json();
        console.log("✅ MMSE questions loaded from local JSON");
        setMmseData({ 
          domains: json.mmse_vietnamese_chatbot?.domains || [],
          metadata: json.mmse_vietnamese_chatbot?.metadata || {},
        });
        setIsLoadingQuestions(false);
        return;
      } else {
        console.warn(`⚠️ Local JSON returned ${localData.status}, trying backend...`);
      }
    } catch (fallbackError: any) {
      if (fallbackError.name !== 'AbortError') {
        console.warn("⚠️ Could not load local JSON, trying backend:", fallbackError.message);
      }
    }
    
    // Fallback: Try backend
    try {
      console.log(`📡 Loading MMSE questions from: ${API_BASE_URL}/api/mmse/chatbot/questions`);
      const response = await fetch(`${API_BASE_URL}/api/mmse/chatbot/questions`, {
        method: "GET",
        headers: {
          "Accept": "application/json",
        },
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ MMSE questions loaded from backend:", data);
        setMmseData(data);
        setIsLoadingQuestions(false);
        return;
      } else {
        console.warn(`⚠️ Backend returned ${response.status}`);
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.warn("⏰ Backend request timeout");
      } else {
        console.warn("⚠️ Could not load MMSE questions from backend:", error.message);
      }
    }
    
    // If both failed, try to load JSON with absolute path
    try {
      console.log("📄 Retrying JSON with absolute path...");
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
      const localData = await fetch(`${baseUrl}/mmse_audio_questions_standardized.json`, {
        signal: AbortSignal.timeout(3000),
      });
      
      if (localData.ok) {
        const json = await localData.json();
        console.log("✅ MMSE questions loaded from JSON (retry)");
        setMmseData({ 
          domains: json.mmse_vietnamese_chatbot?.domains || [],
          metadata: json.mmse_vietnamese_chatbot?.metadata || {},
        });
        setIsLoadingQuestions(false);
        return;
      }
    } catch (retryError) {
      console.error("❌ All attempts to load MMSE questions failed");
    }
    
    setIsLoadingQuestions(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const generateGreeting = (info: UserInfo): string => {
    const age = parseInt(info.age);
    if (isNaN(age)) return "bạn";
    
    if (age >= 60) {
      return info.gender === "male" ? "ông" : "bà";
    } else if (age >= 30) {
      return info.gender === "male" ? "anh" : "chị";
    } else {
      return info.gender === "male" ? "anh" : "em";
    }
  };

  const validateUserInfo = (): boolean => {
    const newErrors: Partial<Record<keyof UserInfo, string>> = {};
    
    if (!userInfo.name.trim()) newErrors.name = "Vui lòng nhập họ tên";
    
    // Age validation: 40-100 (v2.1 requirement)
    if (!userInfo.age.trim()) {
      newErrors.age = "Vui lòng nhập tuổi";
    } else {
      const age = parseInt(userInfo.age);
      if (isNaN(age) || age < 40 || age > 100) {
        newErrors.age = "Vui lòng nhập tuổi từ 40-100";
      }
    }
    
    // Gender validation: required, only male/female
    if (!userInfo.gender || (userInfo.gender !== "male" && userInfo.gender !== "female")) {
      newErrors.gender = "Vui lòng chọn giới tính";
    }
    
    // Education validation: 0-25 years (v2.1 requirement)
    if (!userInfo.education_years.trim()) {
      newErrors.education_years = "Vui lòng nhập số năm học";
    } else {
      const eduYears = parseInt(userInfo.education_years);
      if (isNaN(eduYears) || eduYears < 0 || eduYears > 25) {
        newErrors.education_years = "Vui lòng nhập số năm học từ 0-25";
      }
    }
    
    // Location validation: required for orientation questions (v2.1 requirement)
    if (!userInfo.city.trim()) {
      newErrors.city = "Vui lòng nhập Tỉnh/Thành phố";
    }
    if (!userInfo.district.trim()) {
      newErrors.district = "Vui lòng nhập Quận/Huyện";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const startChat = async () => {
    if (!validateUserInfo() || !mmseData) return;

    const greeting = generateGreeting(userInfo);
    const sessionId = `mmse_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Create session in backend first
    try {
      const sessionResponse = await fetch(`${API_BASE_URL}/api/mmse/chatbot/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          user_info: {
            name: userInfo.name,
            age: userInfo.age,
            gender: userInfo.gender,
            education_years: userInfo.education_years,
            city: userInfo.city,
            district: userInfo.district
          }
        })
      });

      if (!sessionResponse.ok) {
        console.warn("Failed to create session in backend, continuing with frontend-only session");
      } else {
        const sessionData = await sessionResponse.json();
        console.log("✅ Session created in backend:", sessionData);
      }
    } catch (error) {
      console.error("Error creating session in backend:", error);
      // Continue anyway, backend will create session on first submit
    }
    
    // Initialize domain scores
    const domainScores: DomainScore[] = mmseData.domains.map((d, idx) => ({
      name: d.domain_name,
      code: d.domain_code,
      score: 0,
      maxScore: d.max_points,
      status: idx === 0 ? "active" : "pending"
    }));

    // Create initial session state
    const newSession: SessionState = {
      sessionId,
      userInfo,
      greeting,
      currentDomain: 0,
      currentQuestion: 0,
      messages: [],
      domainScores,
      totalScore: 0,
      hiddenContent: {
        registration: ["Con mèo", "Chiếc xe", "Cây lúa"],
        recall: [],
        isRevealed: false
      },
      linguisticData: {
        totalWords: 0,
        uniqueWords: new Set(),
        responses: []
      },
      startTime: new Date(),
      isComplete: false
    };

    setSession(newSession);
    setCurrentStep("chat");

    // Add welcome messages
    setTimeout(() => {
      addBotMessage(newSession, `Xin chào ${greeting} ${userInfo.name}! 👋`);
      
      setTimeout(() => {
        addBotMessage(newSession, 
          `Tôi là trợ lý đánh giá sức khỏe nhận thức. Hôm nay chúng ta sẽ cùng trò chuyện và làm một số câu hỏi đơn giản để kiểm tra trí nhớ và khả năng tư duy của ${greeting} nhé.`
        );
        
        setTimeout(() => {
          addBotMessage(newSession, 
            `Bài đánh giá gồm 6 phần: Định hướng, Ghi nhận, Chú ý, Nhớ lại, Ngôn ngữ và Hình vẽ. ${greeting} sẵn sàng bắt đầu chưa?`,
            {
              actionButtons: [
                {
                  label: "✅ Có, tôi sẵn sàng",
                  action: "ready",
                  variant: "primary"
                },
                {
                  label: "⏸️ Chờ một chút",
                  action: "wait",
                  variant: "secondary"
                }
              ]
            }
          );
        }, 1500);
      }, 1000);
    }, 500);
  };

  const addBotMessage = (currentSession: SessionState, content: string, options?: Partial<Message>) => {
    const processedContent = content.replace(/{greeting}/g, currentSession.greeting);
    
    const newMessage: Message = {
      id: `bot_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      type: "bot",
      content: processedContent,
      timestamp: new Date(),
      ...options
    };

    setSession(prev => {
      if (!prev) return prev;
      return { ...prev, messages: [...prev.messages, newMessage] };
    });

    // Speak message if voice enabled
    if (voiceEnabled) {
      speakText(processedContent);
    }
  };

  const speakText = (text: string) => {
    if (!("speechSynthesis" in window)) return;
    
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "vi-VN";
    utterance.rate = 0.85;
    utterance.pitch = 1.0;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
  };

  const handleActionButton = async (action: string, messageId: string) => {
    if (!session) return;

    // Remove action buttons from the message after clicking
    setSession(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        messages: prev.messages.map(msg => 
          msg.id === messageId 
            ? { ...msg, actionButtons: undefined }
            : msg
        )
      };
    });

    if (action === "ready") {
      // User is ready, start the test
      const responseText = "Có, tôi sẵn sàng";
      await handleUserInput(responseText);
    } else if (action === "wait") {
      // User wants to wait
      const greeting = session.greeting || "bạn";
      addBotMessage(session, `Không sao cả, ${greeting} cứ từ từ. Khi nào ${greeting} sẵn sàng, hãy cho tôi biết nhé!`);
    }
  };

  // Helper function to render content with hidden words blurred
  const renderContentWithHiddenWords = (content: string, hiddenContent?: string[], isRevealed?: boolean) => {
    if (!hiddenContent || hiddenContent.length === 0 || isRevealed) {
      return content;
    }

    // Create a simple replacement approach: find and blur each hidden word
    let processedContent = content;
    const parts: JSX.Element[] = [];
    let keyCounter = 0;
    
    // For each hidden word, find all occurrences and mark them
    const markers: Array<{ index: number; length: number; word: string; original: string }> = [];
    
    hiddenContent.forEach(hiddenWord => {
      const normalizedHidden = hiddenWord.toLowerCase().trim();
      const regex = new RegExp(`\\b${normalizedHidden.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      let match;
      
      while ((match = regex.exec(content)) !== null) {
        markers.push({
          index: match.index,
          length: match[0].length,
          word: hiddenWord,
          original: match[0] // Preserve original case
        });
      }
    });
    
    // Sort markers by index
    markers.sort((a, b) => a.index - b.index);
    
    // Remove overlapping markers (keep first occurrence)
    const filteredMarkers: typeof markers = [];
    let lastEnd = 0;
    markers.forEach(marker => {
      if (marker.index >= lastEnd) {
        filteredMarkers.push(marker);
        lastEnd = marker.index + marker.length;
      }
    });
    
    // Build parts array
    let lastIndex = 0;
    filteredMarkers.forEach(marker => {
      // Add text before marker
      if (marker.index > lastIndex) {
        parts.push(
          <span key={`text-${keyCounter++}`}>
            {content.substring(lastIndex, marker.index)}
          </span>
        );
      }
      
      // Add blurred hidden word
      parts.push(
        <span 
          key={`hidden-${keyCounter++}`}
          className="blur-sm opacity-40 select-none inline-block"
          style={{ filter: 'blur(5px)', userSelect: 'none' }}
          title="Nội dung ẩn"
        >
          {content.substring(marker.index, marker.index + marker.length)}
        </span>
      );
      
      lastIndex = marker.index + marker.length;
    });
    
    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(
        <span key={`text-${keyCounter++}`}>
          {content.substring(lastIndex)}
        </span>
      );
    }
    
    return parts.length > 0 ? <>{parts}</> : content;
  };

  const handleUserInput = async (text: string, audioBlob?: Blob) => {
    if (!session || !text.trim()) return;
    
    // Add user message and reveal hidden content in one update
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      type: "user",
      content: text,
      timestamp: new Date(),
      audioUrl: audioBlob ? URL.createObjectURL(audioBlob) : undefined
    };

    setSession(prev => {
      if (!prev) return prev;
      const messages = [...prev.messages];
      
      // ✅ REVEAL: Find the last bot message with hiddenContent and reveal it
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].type === 'bot' && messages[i].hiddenContent && !messages[i].isRevealed) {
          messages[i] = { ...messages[i], isRevealed: true };
          break;
        }
      }
      
      // Add user message
      return { ...prev, messages: [...messages, userMessage] };
    });

    setInputText("");
    setCurrentAudioBlob(null);
    setIsProcessing(true);

    try {
      // Submit answer to backend
      const formData = new FormData();
      formData.append("session_id", session.sessionId);
      formData.append("answer", text);
      if (audioBlob) {
        formData.append("audio", audioBlob, "recording.webm");
      }

      const response = await fetch(`${API_BASE_URL}/api/mmse/chatbot/submit`, {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        
        // ✅ FIX: Backend returns the next question directly in data.message
        // We should use that instead of calling askNextQuestion() to avoid duplication
        if (data.message) {
          const messageText = data.message.trim();
          
          // Check if this is a question (backend always returns next question)
          // Add it as bot message
          addBotMessage(session, messageText, {
            domain: data.metadata?.domain,
            questionId: data.metadata?.question_id
          });
          
          // ✅ FIX: Update session state to match backend
          if (data.metadata) {
            setSession(prev => {
              if (!prev) return prev;
              // Update current question index based on backend state
              // Backend has already advanced, so we sync frontend state
              return {
                ...prev,
                // Note: We don't have direct access to backend's question index,
                // but backend will return the correct question in next submission
              };
            });
          }
          
          // ✅ FIX: Don't call askNextQuestion() - backend already provided the question
          // This prevents duplication
        } else {
          // Fallback: if no message, get next question from frontend
          setTimeout(() => {
            askNextQuestion();
          }, 1000);
        }
        
        // ✅ REAL-TIME: Update scores immediately
        if (data.score) {
          const scoreData = data.score;
          
          // Update total score
          setSession(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              totalScore: scoreData.total_score || 0
            };
          });
          
          // ✅ Show score notification (iPhone-style push notification)
          setScoreNotification(scoreData);
          
          // Auto-hide notification after 2.5 seconds
          setTimeout(() => {
            setScoreNotification(null);
          }, 2500);
        }
        
        // Update domain scores if available
        if (data.score_update) {
          updateScore(data.score_update.domain, data.score_update.points);
        }
        
        // Check if test complete
        if (data.test_complete) {
          if (data.final_score) {
            const finalMessage = `🎉 Hoàn thành! Điểm tổng: ${data.final_score.total}/${data.final_score.max} (${data.final_score.percentage}%)`;
            addBotMessage(session, finalMessage);
          }
          completeTest(data);
        }
      } else {
        // Fallback: process locally
        processAnswerLocally(text);
      }
    } catch (error) {
      console.error("Error submitting answer:", error);
      // Fallback to local processing
      processAnswerLocally(text);
    } finally {
      setIsProcessing(false);
    }
  };

  const processAnswerLocally = (answer: string) => {
    if (!session || !mmseData) return;

    const currentDomain = mmseData.domains[session.currentDomain];
    const currentQ = currentDomain?.questions[session.currentQuestion];
    
    if (!currentQ) {
      askNextQuestion();
      return;
    }

    // Simple scoring
    let score = 0;
    const lowerAnswer = answer.toLowerCase().trim();
    
    // Check acceptable answers
    if (currentQ.acceptable_answers) {
      const isCorrect = currentQ.acceptable_answers.some(
        acc => lowerAnswer.includes(acc.toLowerCase())
      );
      score = isCorrect ? currentQ.points : 0;
    } else {
      // For open questions, give partial credit
      score = answer.trim().length > 2 ? currentQ.points : 0;
    }

    // Generate feedback
    const feedback = score > 0 
      ? currentQ.feedback_templates?.correct || "Tốt lắm!"
      : currentQ.feedback_templates?.incorrect || "Cảm ơn câu trả lời của bạn.";

    addBotMessage(session, feedback.replace(/{user_answer}/g, answer));
    updateScore(currentDomain.domain_code, score);

    // Update linguistic data
    const words = answer.split(/\s+/);
    setSession(prev => {
      if (!prev) return prev;
      const newUniqueWords = new Set(prev.linguisticData.uniqueWords);
      words.forEach(w => newUniqueWords.add(w.toLowerCase()));
      return {
        ...prev,
        linguisticData: {
          ...prev.linguisticData,
          totalWords: prev.linguisticData.totalWords + words.length,
          uniqueWords: newUniqueWords,
          responses: [...prev.linguisticData.responses, answer]
        }
      };
    });

    // Move to next question
    setTimeout(() => {
      moveToNextQuestion();
    }, 1500);
  };

  const updateScore = (domainCode: string, points: number) => {
    setSession(prev => {
      if (!prev) return prev;
      const updatedScores = prev.domainScores.map(d => {
        if (d.code === domainCode) {
          return { ...d, score: d.score + points };
        }
        return d;
      });
      const newTotal = updatedScores.reduce((sum, d) => sum + d.score, 0);
      return { ...prev, domainScores: updatedScores, totalScore: newTotal };
    });
  };

  const moveToNextQuestion = () => {
    if (!session || !mmseData) return;

    const currentDomain = mmseData.domains[session.currentDomain];
    
    if (session.currentQuestion < currentDomain.questions.length - 1) {
      // Next question in same domain
      setSession(prev => {
        if (!prev) return prev;
        return { ...prev, currentQuestion: prev.currentQuestion + 1 };
      });
      setTimeout(() => askNextQuestion(), 500);
    } else if (session.currentDomain < mmseData.domains.length - 1) {
      // Move to next domain
      setSession(prev => {
        if (!prev) return prev;
        const updatedScores = prev.domainScores.map((d, idx) => ({
          ...d,
          status: idx === prev.currentDomain ? "completed" : 
                  idx === prev.currentDomain + 1 ? "active" : d.status
        })) as DomainScore[];
        
        return {
          ...prev,
          currentDomain: prev.currentDomain + 1,
          currentQuestion: 0,
          domainScores: updatedScores
        };
      });
      
      // Announce new domain
      setTimeout(() => {
        const nextDomain = mmseData.domains[session.currentDomain + 1];
        addBotMessage(session, 
          `Tuyệt vời! Bây giờ chúng ta chuyển sang phần **${nextDomain.domain_name}** ${DOMAIN_ICONS[nextDomain.domain_code] || "📋"}`
        );
        setTimeout(() => askNextQuestion(), 1000);
      }, 500);
    } else {
      // Test complete
      completeTest({});
    }
  };

  const askNextQuestion = () => {
    if (!session || !mmseData) return;

    const currentDomain = mmseData.domains[session.currentDomain];
    const currentQ = currentDomain?.questions[session.currentQuestion];
    
    if (!currentQ) {
      completeTest({});
      return;
    }

    // Handle hidden content for Registration
    if (currentDomain.domain_code === "REGISTRATION" && currentQ.hidden_content) {
      setSession(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          hiddenContent: {
            ...prev.hiddenContent,
            registration: currentQ.hidden_content || prev.hiddenContent.registration
          }
        };
      });
    }

    // Add question message
    addBotMessage(session, currentQ.chatbot_message, {
      domain: currentDomain.domain_code,
      questionId: currentQ.question_id,
      hiddenContent: currentQ.display_mode === "hidden_until_response" ? currentQ.hidden_content : undefined,
      isRevealed: false
    });
  };

  const completeTest = async (data: any) => {
    if (!session) return;

    // Mark all domains as complete
    setSession(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        isComplete: true,
        domainScores: prev.domainScores.map(d => ({ ...d, status: "completed" as const }))
      };
    });

    // Calculate linguistic metrics
    const ttr = session.linguisticData.uniqueWords.size / 
                Math.max(session.linguisticData.totalWords, 1);
    const mlu = session.linguisticData.totalWords / 
                Math.max(session.linguisticData.responses.length, 1);

    // Add completion message
    addBotMessage(session, 
      `🎉 Chúc mừng ${session.greeting}! Chúng ta đã hoàn thành bài đánh giá rồi!`
    );

    setTimeout(() => {
      addBotMessage(session, 
        `📊 **Tổng điểm MMSE của ${session.greeting}: ${session.totalScore}/30**\n\n` +
        getScoreInterpretation(session.totalScore)
      );
    }, 1500);

    // Save to database with full features
    try {
      // First, get full results from backend (includes mci_result and acoustic_features)
      let fullResults = null;
      try {
        const backendResponse = await fetch(`${API_BASE_URL}/api/mmse/chatbot/results`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sessionId: session.sessionId,
            userId: "mmse_chatbot_user",
            userInfo: session.userInfo,
            startedAt: session.startTime.toISOString(),
            completedAt: new Date().toISOString(),
            totalScore: session.totalScore,
            domainScores: session.domainScores.map(d => ({
              domain: d.code,
              name: d.name,
              score: d.score,
              maxScore: d.maxScore
            })),
            linguisticData: {
              totalWords: session.linguisticData.totalWords,
              uniqueWords: session.linguisticData.uniqueWords.size,
              ttr,
              mlu,
              responses: session.linguisticData.responses
            },
            messages: session.messages.map(m => ({
              type: m.type,
              content: m.content,
              timestamp: m.timestamp.toISOString()
            })),
            interpretation: getScoreInterpretation(session.totalScore)
          })
        });
        
        if (backendResponse.ok) {
          const backendData = await backendResponse.json();
          if (backendData.success && backendData.data) {
            fullResults = backendData.data;
            console.log("✅ Got full results from backend with features");
          }
        }
      } catch (err) {
        console.warn("Flask save warning:", err);
      }

      // Prepare payload with full features
      const payload = fullResults || {
        sessionId: session.sessionId,
        userId: "mmse_chatbot_user",
        userInfo: session.userInfo, // Includes: name, age, gender, education_years, city, district
        startedAt: session.startTime.toISOString(),
        completedAt: new Date().toISOString(),
        totalScore: session.totalScore,
        domainScores: session.domainScores.map(d => ({
          domain: d.code,
          name: d.name,
          score: d.score,
          maxScore: d.maxScore
        })),
        linguisticData: {
          totalWords: session.linguisticData.totalWords,
          uniqueWords: session.linguisticData.uniqueWords.size,
          ttr,
          mlu,
          responses: session.linguisticData.responses
        },
        messages: session.messages.map(m => ({
          type: m.type,
          content: m.content,
          timestamp: m.timestamp.toISOString()
        })),
        interpretation: getScoreInterpretation(session.totalScore),
        // These will be added by backend if available:
        mciResult: null,
        acousticFeatures: null,
        linguisticFeatures: null
      };

      // Save to Next.js database with full features
      await fetch("/api/save-cognitive-assessment-results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...payload,
          assessmentType: "mmse_chatbot",
          finalMmseScore: session.totalScore,
          // Map features to database fields
          cognitiveAnalysis: payload.mciResult || null,
          audioFeatures: payload.acousticFeatures || null,
          questionResults: {
            domainScores: payload.domainScores,
            linguisticData: payload.linguisticData,
            linguisticFeatures: payload.linguisticFeatures,
            mciResult: payload.mciResult
          }
        })
      });

      console.log("✅ Saved MMSE chatbot results to database with full features");

    } catch (error) {
      console.error("Error saving results:", error);
    }

    // Show results after delay
    setTimeout(() => {
      setCurrentStep("results");
    }, 4000);
  };

  const getScoreInterpretation = (score: number): string => {
    if (score >= 24) {
      return "✅ **Chức năng nhận thức bình thường**\n\nKết quả cho thấy chức năng nhận thức trong giới hạn bình thường. Hãy tiếp tục duy trì các hoạt động rèn luyện trí não!";
    } else if (score >= 18) {
      return "⚠️ **Suy giảm nhận thức nhẹ (MCI)**\n\nKết quả cho thấy có dấu hiệu suy giảm nhận thức nhẹ. Khuyến nghị theo dõi định kỳ và tham khảo ý kiến bác sĩ chuyên khoa.";
    } else if (score >= 10) {
      return "🔶 **Suy giảm nhận thức trung bình**\n\nKết quả cho thấy có suy giảm nhận thức đáng kể. Nên đến khám chuyên khoa thần kinh hoặc tâm thần để được đánh giá chi tiết.";
    } else {
      return "🔴 **Suy giảm nhận thức nặng**\n\nKết quả cho thấy suy giảm nhận thức nghiêm trọng. Cần được khám và điều trị bởi bác sĩ chuyên khoa ngay.";
    }
  };

  // Recording functions
  const startRecording = async () => {
    try {
      // ✅ FIX: Show initialization state
      setIsInitializingMic(true);
      
      // ✅ FIX: Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      // ✅ FIX: Wait for stream to be active
      if (!stream.active) {
        await new Promise((resolve) => {
          const checkActive = () => {
            if (stream.active) {
              resolve(true);
            } else {
              setTimeout(checkActive, 100);
            }
          };
          checkActive();
        });
      }

      // ✅ FIX: Wait additional time for mic to fully initialize (500ms)
      await new Promise(resolve => setTimeout(resolve, 500));

      // ✅ FIX: Verify audio track is ready
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0 || audioTracks[0].readyState !== 'live') {
        throw new Error("Microphone chưa sẵn sàng");
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4"
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        setCurrentAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
        
        // Auto-transcribe
        transcribeAudio(blob);
      };

      // ✅ FIX: Start recording with smaller chunks for better quality
      mediaRecorder.start(500); // 500ms chunks instead of 1000ms
      
      // ✅ FIX: Only set isRecording = true AFTER mic is ready and recording started
      // This ensures the red button only appears when mic is actually recording
      setIsInitializingMic(false); // Hide initialization indicator
      setIsRecording(true);
      setRecordingDuration(0);

      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);

      console.log("✅ Recording started - mic is ready");

    } catch (error) {
      console.error("Error starting recording:", error);
      setIsInitializingMic(false);
      alert("Không thể truy cập microphone. Vui lòng kiểm tra quyền truy cập.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    setIsRecording(false);
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm', 'audio/ogg', 'audio/m4a', 'audio/x-m4a'];
    const isValidType = validTypes.includes(file.type) || file.name.match(/\.(wav|mp3|webm|ogg|m4a)$/i);
    
    if (!isValidType) {
      alert('Vui lòng chọn file audio hợp lệ (WAV, MP3, WebM, OGG, M4A)');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      alert('File quá lớn. Vui lòng chọn file nhỏ hơn 10MB');
      return;
    }

    // Convert File to Blob
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        const blob = new Blob([event.target.result], { type: file.type });
        setCurrentAudioBlob(blob);
        
        // Auto-transcribe the uploaded file
        transcribeAudio(blob);
        
        // Show success message
        console.log(`✅ File uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
      }
    };
    reader.onerror = () => {
      alert('Lỗi khi đọc file. Vui lòng thử lại.');
    };
    reader.readAsArrayBuffer(file);

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const transcribeAudio = async (blob: Blob) => {
    setIsProcessing(true);
    try {
      // First, check if backend is reachable
      try {
        const healthCheck = await fetch(`${API_BASE_URL}/api/health`, {
          method: "GET",
          signal: AbortSignal.timeout(3000) // 3 second timeout
        });
        if (!healthCheck.ok) {
          console.warn("Backend health check failed:", healthCheck.status);
        }
      } catch (healthError) {
        console.error("Backend not reachable:", healthError);
        throw new Error(`Không thể kết nối đến backend tại ${API_BASE_URL}. Vui lòng kiểm tra xem backend đã chạy chưa.`);
      }

      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");
      formData.append("language", "vi");
      formData.append("use_vietnamese_asr", "true");

      console.log(`Attempting transcription to ${API_BASE_URL}/auto-transcribe`);

      // Try auto-transcribe endpoint first
      let response: Response | null = null;
      try {
        response = await fetch(`${API_BASE_URL}/auto-transcribe`, {
          method: "POST",
          body: formData,
          signal: AbortSignal.timeout(30000) // 30 second timeout for transcription
        });
      } catch (fetchError: any) {
        console.warn("Auto-transcribe endpoint failed, trying /api/transcribe:", fetchError);
        // Fallback to /api/transcribe
        try {
          response = await fetch(`${API_BASE_URL}/api/transcribe`, {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(30000)
          });
        } catch (fallbackError: any) {
          console.error("Both transcription endpoints failed:", fallbackError);
          if (fallbackError.name === 'AbortError') {
            throw new Error("Request timeout. Backend có thể đang quá tải hoặc không phản hồi.");
          }
          throw new Error(`Không thể kết nối đến server tại ${API_BASE_URL}. Vui lòng kiểm tra xem backend đã chạy chưa.`);
        }
      }

      if (response && response.ok) {
        const data = await response.json();
        const transcript = data.transcription?.transcript || data.transcript || "";
        if (transcript) {
          setInputText(transcript);
        } else {
          console.warn("No transcript in response:", data);
          // Show user-friendly message if session exists
          if (session) {
            addBotMessage(session, "Xin lỗi, tôi không nghe rõ. Bạn có thể gõ câu trả lời được không?");
          }
        }
      } else {
        const errorText = response ? await response.text() : "Unknown error";
        console.error("Transcription failed:", response?.status, errorText);
        if (session) {
          addBotMessage(session, "Xin lỗi, có lỗi xảy ra khi xử lý giọng nói. Bạn có thể gõ câu trả lời được không?");
        }
      }
    } catch (error: any) {
      console.error("Transcription error:", error);
      const errorMessage = error.message || "Không thể kết nối đến server";
      if (session) {
        addBotMessage(session, `⚠️ ${errorMessage}. Bạn có thể gõ câu trả lời thay vì nói.`);
      } else {
        // If no session, just show alert
        alert(`⚠️ ${errorMessage}. Vui lòng kiểm tra xem backend đã chạy chưa (${API_BASE_URL})`);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <AnimatePresence mode="wait">
        {/* ============================================ */}
        {/* STEP 1: USER INFO FORM */}
        {/* ============================================ */}
        {currentStep === "userInfo" && (
          <motion.div
            key="userInfo"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="min-h-screen flex items-center justify-center p-4"
          >
            <div className="w-full max-w-2xl">
              {/* Header */}
              <motion.div 
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="text-center mb-8"
              >
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg mb-4">
                  <Brain className="w-10 h-10 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                  Đánh Giá Nhận Thức MMSE
                </h1>
                <p className="text-gray-600 text-lg">
                  Bài kiểm tra trò chuyện thân thiện với trợ lý AI
                </p>
              </motion.div>

              {/* Form Card */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100"
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-800">Thông tin cá nhân</h2>
                    <p className="text-sm text-gray-500">Giúp chúng tôi cá nhân hóa bài đánh giá</p>
                  </div>
                </div>

                <div className="space-y-5">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Họ và tên *
                    </label>
                    <Input
                      value={userInfo.name}
                      onChange={(e) => setUserInfo({ ...userInfo, name: e.target.value })}
                      placeholder="Ví dụ: Nguyễn Văn An"
                      className={`h-12 text-lg border-2 rounded-xl ${errors.name ? "border-red-400" : "border-gray-200"}`}
                    />
                    {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
                  </div>

                  {/* Age & Gender */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Tuổi *
                      </label>
                      <Input
                        type="number"
                        min="40"
                        max="100"
                        value={userInfo.age}
                        onChange={(e) => setUserInfo({ ...userInfo, age: e.target.value })}
                        placeholder="65"
                        className={`h-12 text-lg border-2 rounded-xl ${errors.age ? "border-red-400" : "border-gray-200"}`}
                      />
                      {errors.age && <p className="text-red-500 text-sm mt-1">{errors.age}</p>}
                      <p className="text-xs text-gray-500 mt-1">
                        Hệ thống được thiết kế cho người từ 40-100 tuổi
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Giới tính *
                      </label>
                      <select
                        value={userInfo.gender}
                        onChange={(e) => setUserInfo({ ...userInfo, gender: e.target.value as any })}
                        className={`w-full h-12 text-lg border-2 rounded-xl px-4 ${errors.gender ? "border-red-400" : "border-gray-200"}`}
                      >
                        <option value="">Chọn giới tính</option>
                        <option value="male">Nam</option>
                        <option value="female">Nữ</option>
                      </select>
                      {errors.gender && <p className="text-red-500 text-sm mt-1">{errors.gender}</p>}
                      <p className="text-xs text-gray-500 mt-1">
                        Để hệ thống xưng hô đúng văn hóa (Ông/Bà)
                      </p>
                    </div>
                  </div>

                  {/* Education */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Số năm đi học *
                    </label>
                    <Input
                      type="number"
                      min="0"
                      max="25"
                      value={userInfo.education_years}
                      onChange={(e) => setUserInfo({ ...userInfo, education_years: e.target.value })}
                      placeholder="12"
                      className={`h-12 text-lg border-2 rounded-xl ${errors.education_years ? "border-red-400" : "border-gray-200"}`}
                    />
                    {errors.education_years && <p className="text-red-500 text-sm mt-1">{errors.education_years}</p>}
                    <p className="text-xs text-gray-600 mt-1 mb-2">
                      Ví dụ: Tiểu học 5 năm = 5, Trung học phổ thông = 12, Đại học 4 năm = 16
                    </p>
                    <div className="text-xs text-gray-500 space-y-1 bg-gray-50 p-3 rounded-lg">
                      <div><strong>Ví dụ:</strong></div>
                      <div>• Chưa đi học: 0 năm</div>
                      <div>• Tiểu học (lớp 1-5): 5 năm</div>
                      <div>• THCS (lớp 6-9): 9 năm</div>
                      <div>• THPT (lớp 10-12): 12 năm</div>
                      <div>• Đại học: 16 năm</div>
                      <div>• Thạc sĩ: 18 năm</div>
                      <div>• Tiến sĩ: 21 năm</div>
                    </div>
                  </div>

                  {/* Location */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Tỉnh/Thành phố *
                      </label>
                      <Input
                        value={userInfo.city}
                        onChange={(e) => setUserInfo({ ...userInfo, city: e.target.value })}
                        placeholder="Ví dụ: Hà Nội, Đà Nẵng, TP.HCM"
                        className={`h-12 text-lg border-2 rounded-xl ${errors.city ? "border-red-400" : "border-gray-200"}`}
                      />
                      {errors.city && <p className="text-red-500 text-sm mt-1">{errors.city}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Quận/Huyện *
                      </label>
                      <Input
                        value={userInfo.district}
                        onChange={(e) => setUserInfo({ ...userInfo, district: e.target.value })}
                        placeholder="Ví dụ: Quận Hoàn Kiếm, Huyện Hóc Môn"
                        className={`h-12 text-lg border-2 rounded-xl ${errors.district ? "border-red-400" : "border-gray-200"}`}
                      />
                      {errors.district && <p className="text-red-500 text-sm mt-1">{errors.district}</p>}
                    </div>
                  </div>

                  {/* Greeting Preview */}
                  {userInfo.name && userInfo.age && userInfo.gender && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-4 border-2 border-green-200"
                    >
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-6 h-6 text-green-600" />
                        <div>
                          <p className="font-semibold text-gray-800">
                            Xin chào {generateGreeting(userInfo)} {userInfo.name.split(" ").pop()}!
                          </p>
                          <p className="text-sm text-gray-600">
                            Chúng tôi sẽ xưng hô với {generateGreeting(userInfo)} trong suốt bài đánh giá
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* Start Button */}
                <Button
                  onClick={startChat}
                  disabled={!mmseData || isLoadingQuestions}
                  className="w-full h-14 mt-8 text-lg font-bold rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoadingQuestions || !mmseData ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      {isLoadingQuestions ? "Đang tải..." : "Đang khởi tạo..."}
                    </>
                  ) : (
                    <>
                      <MessageCircle className="w-5 h-5 mr-2" />
                      Bắt đầu trò chuyện
                    </>
                  )}
                </Button>
                {!isLoadingQuestions && !mmseData && (
                  <p className="text-sm text-red-500 mt-2 text-center">
                    ⚠️ Không thể tải dữ liệu. Vui lòng tải lại trang.
                  </p>
                )}
              </motion.div>

              {/* Tips */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="mt-6 bg-white/80 backdrop-blur rounded-2xl p-6 border border-gray-100"
              >
                <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" />
                  Hướng dẫn sử dụng
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <Volume2 className="w-4 h-4 text-blue-500" />
                    <span>Câu hỏi được đọc to tự động</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mic className="w-4 h-4 text-green-500" />
                    <span>Trả lời bằng giọng nói hoặc gõ</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-purple-500" />
                    <span>Khoảng 15-20 phút</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-teal-500" />
                    <span>Bảo mật thông tin</span>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}

        {/* ============================================ */}
        {/* STEP 2: CHAT INTERFACE */}
        {/* ============================================ */}
        {currentStep === "chat" && session && (
          <motion.div
            key="chat"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex h-screen"
          >
            {/* Sidebar */}
            <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
              {/* User Info */}
              <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                    {session.userInfo.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-800">{session.userInfo.name}</h3>
                    <p className="text-sm text-gray-500">{session.userInfo.age} tuổi</p>
                  </div>
                </div>
              </div>

              

              {/* ✅ REMOVED: Progress List - now using horizontal progress bar */}

              {/* Controls */}
              <div className="p-4 border-t border-gray-100 space-y-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                >
                  <Volume2 className={`w-4 h-4 mr-2 ${voiceEnabled ? "text-blue-500" : "text-gray-400"}`} />
                  Giọng nói: {voiceEnabled ? "Bật" : "Tắt"}
                </Button>
                <Link href="/">
                  <Button variant="ghost" className="w-full justify-start text-gray-600">
                    <Home className="w-4 h-4 mr-2" />
                    Về trang chủ
                  </Button>
                </Link>
              </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col bg-gray-50">
              {/* Chat Header with Progress and Score */}
              <div className="p-4 bg-white border-b border-gray-200 relative">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <h2 className="font-bold text-gray-800">MMSE Chatbot</h2>
                    <p className="text-sm text-gray-500">
                      {isSpeaking ? "🔊 Đang nói..." : "Sẵn sàng trò chuyện"}
                    </p>
                  </div>
                  {/* ✅ Score Display (separate from progress) */}
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {session.totalScore}/30
                    </div>
                    <div className="text-xs text-gray-500">điểm</div>
                  </div>
                </div>
                {/* ✅ Progress Bar - Shows question progress, not score */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm text-gray-600 font-medium">Tiến độ:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2.5">
                    <motion.div
                      className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2.5 rounded-full transition-all duration-500"
                      initial={{ width: 0 }}
                      animate={{ 
                        width: `${session.messages.filter(m => m.type === "user").length > 0 
                          ? (session.messages.filter(m => m.type === "user").length / 30) * 100 
                          : 0}%` 
                      }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                    />
                  </div>
                  <span className="text-sm text-gray-600 font-medium min-w-[60px] text-right">
                    {session.messages.filter(m => m.type === "user").length}/30 câu
                  </span>
                </div>
                
                {/* ✅ Score Notification (iPhone-style push notification) */}
                <AnimatePresence>
                  {scoreNotification && (
                    <motion.div
                      key="score-notification"
                      initial={{ y: -100, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      exit={{ y: -100, opacity: 0 }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                      className="absolute top-full left-0 right-0 mt-2 mx-4 z-50"
                    >
                    <div className="bg-white rounded-xl shadow-2xl border-2 border-gray-200 p-4">
                      <div className="flex items-center gap-3">
                        {scoreNotification.is_correct ? (
                          <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                            <span className="text-2xl">✓</span>
                          </div>
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                            <span className="text-xl">○</span>
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className={`text-lg font-bold ${
                              scoreNotification.points_earned > 0 ? "text-green-600" : "text-gray-500"
                            }`}>
                              +{scoreNotification.points_earned} điểm
                            </span>
                            {scoreNotification.is_correct && (
                              <span className="text-green-600">✓</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500 mt-0.5">
                            ({scoreNotification.points_earned}/{scoreNotification.points_possible} câu này)
                          </div>
                          <div className="text-sm font-semibold text-blue-600 mt-1">
                            Tổng: {scoreNotification.total_score}/{scoreNotification.max_score} điểm ({scoreNotification.percentage}%)
                          </div>
                          {scoreNotification.feedback && (
                            <div className="text-xs text-gray-600 mt-1 italic">
                              💡 {scoreNotification.feedback}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {session.messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div className={`flex items-start gap-3 max-w-2xl ${
                      message.type === "user" ? "flex-row-reverse" : ""
                    }`}>
                      {/* Avatar */}
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.type === "user"
                          ? "bg-gradient-to-br from-green-500 to-teal-600"
                          : "bg-gradient-to-br from-blue-500 to-indigo-600"
                      }`}>
                        {message.type === "user" ? (
                          <User className="w-4 h-4 text-white" />
                        ) : (
                          <Brain className="w-4 h-4 text-white" />
                        )}
                      </div>

                      {/* Bubble */}
                      <div className={`px-4 py-3 rounded-2xl shadow-sm ${
                        message.type === "user"
                          ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-tr-sm"
                          : message.type === "system"
                          ? "bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 text-gray-800 rounded-tl-sm"
                          : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
                      }`}>
                        <p className="whitespace-pre-wrap">
                          {renderContentWithHiddenWords(
                            message.content, 
                            message.hiddenContent, 
                            message.isRevealed
                          )}
                        </p>
                        
                        {/* Action Buttons */}
                        {message.actionButtons && message.actionButtons.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {message.actionButtons.map((button, idx) => (
                              <motion.button
                                key={idx}
                                onClick={() => handleActionButton(button.action, message.id)}
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 ${
                                  button.variant === "primary"
                                    ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 shadow-md hover:shadow-lg"
                                    : "bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300"
                                }`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                              >
                                {button.label}
                              </motion.button>
                            ))}
                          </div>
                        )}
                        
                        {/* Revealed Hidden Content Indicator */}
                        {message.hiddenContent && message.isRevealed && (
                          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <p className="text-xs text-yellow-700 font-medium">
                              ✨ Đã hiển thị: {message.hiddenContent.join(", ")}
                            </p>
                          </div>
                        )}

                        {/* Audio Playback */}
                        {message.audioUrl && (
                          <audio controls src={message.audioUrl} className="mt-2 w-full" />
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Processing Indicator */}
                {isProcessing && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                        <Brain className="w-4 h-4 text-white" />
                      </div>
                      <div className="px-4 py-3 bg-white border border-gray-200 rounded-2xl rounded-tl-sm">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                          <span className="text-gray-500">Đang xử lý...</span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-4 bg-white border-t border-gray-200">
                <div className="flex items-center gap-3">
                  {/* Voice Button */}
                  <motion.button
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isProcessing || isInitializingMic}
                    className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all ${
                      isRecording
                        ? "bg-red-500 hover:bg-red-600 animate-pulse"
                        : isInitializingMic
                        ? "bg-yellow-500 hover:bg-yellow-600"
                        : "bg-blue-500 hover:bg-blue-600"
                    } text-white`}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isRecording ? (
                      <Square className="w-6 h-6" />
                    ) : isInitializingMic ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
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
                    className="w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all bg-purple-500 hover:bg-purple-600 text-white"
                    whileTap={{ scale: 0.95 }}
                    title="Upload file audio từ máy tính"
                  >
                    <Upload className="w-6 h-6" />
                  </motion.button>

                  {/* Mic Initialization Indicator */}
                  {isInitializingMic && (
                    <div className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
                      🎤 Đang khởi tạo mic...
                    </div>
                  )}

                  {/* Recording Timer */}
                  {isRecording && (
                    <div className="px-3 py-1 bg-red-100 text-red-700 rounded-full font-mono text-sm">
                      🔴 {formatTime(recordingDuration)}
                    </div>
                  )}

                  {/* Text Input */}
                  <div className="flex-1 relative">
                    <Input
                      ref={inputRef}
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey && inputText.trim()) {
                          e.preventDefault();
                          handleUserInput(inputText, currentAudioBlob || undefined);
                        }
                      }}
                      placeholder="Gõ hoặc nói câu trả lời..."
                      disabled={isRecording || isProcessing}
                      className="h-14 text-lg pr-14 border-2 border-gray-200 rounded-xl focus:border-blue-400"
                    />
                    <Button
                      onClick={() => handleUserInput(inputText, currentAudioBlob || undefined)}
                      disabled={!inputText.trim() || isProcessing}
                      className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-blue-500 hover:bg-blue-600 p-0"
                    >
                      <Send className="w-4 h-4 text-white" />
                    </Button>
                  </div>
                </div>

                {/* Help Text */}
                <p className="mt-2 text-sm text-gray-500 text-center">
                  {isRecording 
                    ? "Đang ghi âm... Nhấn nút đỏ để dừng"
                    : "Nhấn nút micro để ghi âm, nút upload để chọn file audio, hoặc gõ câu trả lời"
                  }
                </p>
                
                {/* Selected File Info */}
                {currentAudioBlob && (
                  <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                    <FileAudio className="w-4 h-4 text-green-600" />
                    <span className="text-sm text-green-700">
                      ✅ File audio đã sẵn sàng ({((currentAudioBlob.size || 0) / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* ============================================ */}
        {/* STEP 3: RESULTS */}
        {/* ============================================ */}
        {currentStep === "results" && session && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="min-h-screen p-4 md:p-8"
          >
            <div className="max-w-4xl mx-auto">
              {/* Header */}
              <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="text-center mb-8"
              >
                <div className="text-6xl mb-4">🎉</div>
                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                  Kết quả đánh giá MMSE
                </h1>
                <p className="text-gray-600">
                  {session.greeting.charAt(0).toUpperCase() + session.greeting.slice(1)} {session.userInfo.name}
                </p>
              </motion.div>

              {/* Score Card */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-3xl shadow-xl p-8 mb-6 border border-gray-100"
              >
                <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 mb-4">
                    <span className="text-5xl font-bold text-white">{session.totalScore}</span>
                  </div>
                  <p className="text-2xl text-gray-600">/30 điểm</p>
                  
                  <div className={`inline-block mt-4 px-6 py-2 rounded-full text-lg font-semibold ${
                    session.totalScore >= 24
                      ? "bg-green-100 text-green-800"
                      : session.totalScore >= 18
                      ? "bg-yellow-100 text-yellow-800"
                      : session.totalScore >= 10
                      ? "bg-orange-100 text-orange-800"
                      : "bg-red-100 text-red-800"
                  }`}>
                    {session.totalScore >= 24
                      ? "Bình thường"
                      : session.totalScore >= 18
                      ? "Suy giảm nhẹ"
                      : session.totalScore >= 10
                      ? "Suy giảm trung bình"
                      : "Suy giảm nặng"
                    }
                  </div>
                </div>

                {/* Domain Scores */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {session.domainScores.map((domain) => (
                    <div
                      key={domain.code}
                      className="bg-gray-50 rounded-xl p-4 text-center"
                    >
                      <span className="text-2xl">{DOMAIN_ICONS[domain.code] || "📋"}</span>
                      <h4 className="font-semibold text-gray-800 mt-2">{domain.name}</h4>
                      <p className="text-2xl font-bold text-blue-600">
                        {domain.score}/{domain.maxScore}
                      </p>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Linguistic Analysis */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-3xl shadow-xl p-8 mb-6 border border-gray-100"
              >
                <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Activity className="w-6 h-6 text-purple-500" />
                  Phân tích ngôn ngữ
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-purple-50 rounded-xl">
                    <p className="text-3xl font-bold text-purple-600">
                      {session.linguisticData.totalWords}
                    </p>
                    <p className="text-sm text-gray-600">Tổng số từ</p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-xl">
                    <p className="text-3xl font-bold text-blue-600">
                      {(session.linguisticData.uniqueWords.size / Math.max(session.linguisticData.totalWords, 1)).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-600">TTR</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-xl">
                    <p className="text-3xl font-bold text-green-600">
                      {(session.linguisticData.totalWords / Math.max(session.linguisticData.responses.length, 1)).toFixed(1)}
                    </p>
                    <p className="text-sm text-gray-600">MLU</p>
                  </div>
                </div>
              </motion.div>

              {/* Actions */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="flex flex-col gap-4"
              >
                <Button
                  onClick={() => router.push(`/results?sessionId=${session.sessionId}`)}
                  className="w-full h-14 text-lg font-bold rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white"
                >
                  <FileText className="w-5 h-5 mr-2" />
                  Xem báo cáo chi tiết
                </Button>
                
                <Button
                  onClick={() => window.location.reload()}
                  variant="secondaryOutline"
                  className="w-full h-12 text-lg rounded-xl border-2"
                >
                  🔄 Làm bài đánh giá mới
                </Button>
                
                <Link href="/" className="w-full">
                  <Button variant="ghost" className="w-full h-12 text-lg rounded-xl">
                    <Home className="w-5 h-5 mr-2" />
                    Về trang chủ
                  </Button>
                </Link>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


