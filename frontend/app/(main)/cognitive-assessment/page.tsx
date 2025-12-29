"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, Square, Loader2, CheckCircle, Brain,
  Volume2, User, Clock, FileAudio, ArrowRight, ArrowLeft, Play, Home
} from "lucide-react";
import { useLanguage } from '@/contexts/LanguageContext';
import Link from "next/link";
import { useRouter } from 'next/navigation';
import {
  fetchWithFallback,
  getMockQuestions,
  checkBackendHealth,
  API_BASE_URL
} from '@/lib/api-utils';
import UserInfoForm, { UserInfo } from '@/components/UserInfoForm';

// ============================================
// INTERFACES
// ============================================
interface Question {
  id: string;
  category: string;
  domain: string;
  text: string;
  instruction?: string;
}

// UserInfo is now imported from UserInfoForm component

interface AudioFeatures {
  duration: number;
  pitch_mean: number;
  pitch_std: number;
  speech_rate: number;
  tempo: number;
  silence_mean: number;
  number_utterances: number;
}

interface GPTEvaluation {
  vocabulary_score: number | null;
  context_relevance_score: number;
  overall_score: number;
  analysis: string;
  feedback: string;
}

interface TestResult {
  questionId: string;
  question: string;
  transcription?: string;
  timestamp: Date;
  duration: number;
  gpt_evaluation?: GPTEvaluation;
  audio_features?: AudioFeatures;
}

// ============================================
// CONSTANTS
// ============================================
const MAX_RECORDING_DURATION = 180;

// ============================================
// MAIN COMPONENT
// ============================================
export default function CognitiveAssessmentPage() {
  const { t, language } = useLanguage();
  const router = useRouter();

  // ============================================
  // STATE
  // ============================================

  // Step management: 'userInfo' -> 'assessment' -> 'completed'
  const [currentStep, setCurrentStep] = useState<'userInfo' | 'assessment' | 'completed'>('userInfo');
  
  // User info (MANDATORY)
  const [userInfo, setUserInfo] = useState<UserInfo>({
    name: '',
    age: '',
    gender: '',
    education_years: '',
    notes: ''
  });
  const [userInfoErrors, setUserInfoErrors] = useState<Partial<UserInfo>>({});
  
  // Questions
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionsLoaded, setQuestionsLoaded] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  
  // Recording
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [hasRecording, setHasRecording] = useState(false);
  const [currentAudioBlob, setCurrentAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  
  // Processing
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTTSSpeaking, setIsTTSSpeaking] = useState(false);
  
  // Results
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [sessionId, setSessionId] = useState('session_placeholder');

  // Generate unique session ID on client side only
  useEffect(() => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  }, []);
  
  // Backend
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  
  // Timer refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Current question
  const currentQuestion = questions[currentQuestionIndex];

  // ============================================
  // EFFECTS
  // ============================================
  
  // Load questions on mount
  useEffect(() => {
    loadQuestions();
    checkBackend();
  }, []);
  
  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, []);

  // ============================================
  // FUNCTIONS
  // ============================================
  
  const checkBackend = async () => {
    setBackendStatus('checking');
    try {
      const isHealthy = await checkBackendHealth();
      setBackendStatus(isHealthy ? 'connected' : 'disconnected');
    } catch {
      setBackendStatus('disconnected');
    }
  };
  
  const loadQuestions = async () => {
    try {
      // Try backend first
      const response = await fetchWithFallback(`${API_BASE_URL}/api/mmse/questions`);
      if (response.ok) {
        const data = await response.json();
        if (data.questions && Array.isArray(data.questions)) {
          setQuestions(data.questions);
          setQuestionsLoaded(true);
          return;
        }
      }
    } catch (error) {
      console.warn('Backend unavailable, using mock questions');
    }
    
    // Fallback to mock
    const mockQuestions = getMockQuestions();
    setQuestions(mockQuestions);
    setQuestionsLoaded(true);
  };
  
  // Validate user info
  const validateUserInfo = (): boolean => {
    const errors: Partial<UserInfo> = {};
    
    if (!userInfo.name.trim()) {
      errors.name = 'Vui lòng nhập họ tên';
    }
    
    if (!userInfo.age.trim()) {
      errors.age = 'Vui lòng nhập tuổi';
    } else {
      const age = parseInt(userInfo.age);
      if (isNaN(age) || age < 1 || age > 120) {
        errors.age = 'Tuổi không hợp lệ';
      }
    }
    
    if (!userInfo.gender) {
      errors.gender = 'Vui lòng chọn giới tính';
    }
    
    setUserInfoErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // Start assessment
  const startAssessment = () => {
    // User info is already validated in UserInfoForm component
    setCurrentStep('assessment');
    // Speak first question with personalized greeting
    setTimeout(() => {
      speakQuestion(0);
    }, 500);
  };
  
  // Text-to-speech for question
  const speakQuestion = (index: number) => {
    if (!questions[index]) return;
    
    const question = questions[index];
    const text = question.text.replace('{greeting}', getGreeting());
    
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === 'vi' ? 'vi-VN' : 'en-US';
      utterance.rate = 0.85; // Slower for elderly
      utterance.pitch = 1.0;
      
      utterance.onstart = () => setIsTTSSpeaking(true);
      utterance.onend = () => setIsTTSSpeaking(false);
      utterance.onerror = () => setIsTTSSpeaking(false);
      
      window.speechSynthesis.speak(utterance);
    }
  };
  
  const getGreeting = (): string => {
    const addressTerm = userInfo.address_term || 'Bạn';
    const hour = new Date().getHours();
    let timeGreeting = '';
    if (hour < 12) timeGreeting = 'Chào buổi sáng';
    else if (hour < 18) timeGreeting = 'Chào buổi chiều';
    else timeGreeting = 'Chào buổi tối';

    return `${timeGreeting} ${addressTerm.toLowerCase()}`;
  };
  
  // Recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        setCurrentAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        setHasRecording(true);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(1000);
      setIsRecording(true);
      setRecordingDuration(0);
      recordingStartTimeRef.current = Date.now();
      
      // Start timer
      recordingTimerRef.current = setInterval(() => {
        if (recordingStartTimeRef.current) {
          const elapsed = Math.floor((Date.now() - recordingStartTimeRef.current) / 1000);
          setRecordingDuration(elapsed);
          
          if (elapsed >= MAX_RECORDING_DURATION) {
            stopRecording();
          }
        }
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Không thể khởi động micro. Vui lòng kiểm tra quyền truy cập.');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    
    setIsRecording(false);
  };
  
  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCurrentAudioBlob(file);
      setAudioUrl(URL.createObjectURL(file));
      setHasRecording(true);
    }
  };
  
  // Submit current answer and move to next question
  const submitAnswer = async () => {
    if (!currentQuestion || !currentAudioBlob) return;
    
    setIsProcessing(true);
    
    try {
      // Prepare form data with user info
      const formData = new FormData();
      formData.append('audio', currentAudioBlob, 'recording.webm');
      formData.append('language', language);
      formData.append('question', currentQuestion.text.replace('{greeting}', getGreeting()));
      formData.append('questionId', currentQuestion.id);
      
      // Include user info for evaluation
      formData.append('user_name', userInfo.name);
      formData.append('user_age', userInfo.age);
      formData.append('user_gender', userInfo.gender);
      formData.append('user_education', userInfo.education_years);
      
      if (language === 'vi') {
        formData.append('use_vietnamese_asr', 'true');
      }
      
      const response = await fetch(`${API_BASE_URL}/auto-transcribe`, {
        method: 'POST',
        body: formData
      });
      
      let transcription = '';
      let gptEval: GPTEvaluation | undefined;
      let audioFeatures: AudioFeatures | undefined;
      
      if (response.ok) {
        const data = await response.json();
        transcription = data.transcription?.transcript || data.transcript || '';
        gptEval = data.gpt_evaluation;
        audioFeatures = data.audio_features;
      }
      
      // Save result
      const result: TestResult = {
        questionId: currentQuestion.id,
        question: currentQuestion.text,
        transcription,
        timestamp: new Date(),
        duration: recordingDuration,
        gpt_evaluation: gptEval,
        audio_features: audioFeatures
      };
      
      setTestResults(prev => [...prev, result]);
      
      // Move to next question or complete
      if (currentQuestionIndex < questions.length - 1) {
        const nextIndex = currentQuestionIndex + 1;
        setCurrentQuestionIndex(nextIndex);
        resetRecording();
        
        // Speak next question
        setTimeout(() => {
          speakQuestion(nextIndex);
        }, 300);
      } else {
        // Assessment completed
        setCurrentStep('completed');
        saveResults([...testResults, result]);
      }
      
    } catch (error) {
      console.error('Error processing answer:', error);
      alert('Có lỗi xảy ra. Vui lòng thử lại.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  const resetRecording = () => {
    setHasRecording(false);
    setCurrentAudioBlob(null);
    setAudioUrl(null);
    setRecordingDuration(0);
  };
  
  // Go to previous question
  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      const prevIndex = currentQuestionIndex - 1;
      setCurrentQuestionIndex(prevIndex);
      resetRecording();
      speakQuestion(prevIndex);
    }
  };
  
  // Save results to both Flask backend AND Next.js database
  const saveResults = async (results: TestResult[]) => {
    try {
      // Calculate MMSE score based on results
      const totalQuestions = results.length;
      const answeredQuestions = results.filter(r => r.transcription).length;
      const completionRate = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
      
      // Calculate average GPT score if available
      const gptScores = results
        .filter(r => r.gpt_evaluation?.overall_score)
        .map(r => r.gpt_evaluation!.overall_score);
      const averageGptScore = gptScores.length > 0 
        ? gptScores.reduce((a, b) => a + b, 0) / gptScores.length 
        : 0;
      
      // Estimate MMSE score (scale GPT score 0-10 to MMSE 0-30)
      const estimatedMmseScore = Math.round((averageGptScore / 10) * 30);
      
      // Prepare question results for database
      const questionResults = results.map(r => ({
        questionId: r.questionId,
        questionText: r.question,
        transcript: r.transcription || '',
        duration: r.duration,
        gptEvaluation: r.gpt_evaluation,
        audioFeatures: r.audio_features,
        status: r.transcription ? 'completed' : 'skipped',
        processedAt: r.timestamp.toISOString()
      }));

      // 1. Save to Flask backend (for acoustic/linguistic analysis)
      const flaskPayload = {
        session_id: sessionId,
        user_info: userInfo,
        results: results.map(r => ({
          question_id: r.questionId,
          question: r.question,
          transcription: r.transcription,
          duration: r.duration,
          gpt_evaluation: r.gpt_evaluation,
          audio_features: r.audio_features,
          timestamp: r.timestamp.toISOString()
        })),
        completed_at: new Date().toISOString()
      };
      
      // Save to Flask backend (don't await to not block)
      fetchWithFallback(`${API_BASE_URL}/api/mmse/results/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(flaskPayload)
      }).catch(err => console.warn('Flask backend save warning:', err));

      // 2. Save to Next.js database (PRIMARY - for results page)
      const nextjsPayload = {
        sessionId: sessionId,
        userId: 'assessment_user',
        userInfo: {
          name: userInfo.name,
          age: userInfo.age,
          gender: userInfo.gender,
          education_years: userInfo.education_years,
          notes: userInfo.notes
        },
        startedAt: new Date(results[0]?.timestamp || Date.now()).toISOString(),
        totalQuestions,
        answeredQuestions,
        completionRate,
        memoryScore: 0,
        cognitiveScore: 0,
        finalMmseScore: estimatedMmseScore,
        overallGptScore: averageGptScore,
        questionResults: questionResults,
        cognitiveAnalysis: {
          overallAssessment: estimatedMmseScore >= 24 
            ? 'Chức năng nhận thức bình thường' 
            : estimatedMmseScore >= 18 
            ? 'Suy giảm nhận thức nhẹ - cần theo dõi' 
            : 'Suy giảm nhận thức đáng kể - khuyên nghị kiểm tra chuyên sâu',
          riskLevel: estimatedMmseScore >= 24 ? 'low' : estimatedMmseScore >= 18 ? 'medium' : 'high'
        },
        usageMode: 'personal',
        assessmentType: 'cognitive'
      };

      // Save to Next.js database (this is the primary storage for results page)
      const response = await fetch('/api/save-cognitive-assessment-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nextjsPayload)
      });
      
      const result = await response.json();
      if (result.success) {
        console.log('✅ Results saved to Next.js database:', result.id);
      } else {
        console.error('❌ Failed to save to Next.js database:', result.error);
      }
      
    } catch (error) {
      console.error('Error saving results:', error);
    }
  };
  
  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // ============================================
  // RENDER
  // ============================================
  
  return (
    <div className="min-h-screen" style={{
      background: 'linear-gradient(135deg, #FEF7ED 0%, #FDECD4 50%, #FCE0C3 100%)'
    }}>
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-white/80 border-b-2 border-amber-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition">
            <div className="w-12 h-12 rounded-full flex items-center justify-center text-2xl" style={{
              background: 'linear-gradient(135deg, #F4A261 0%, #E88D4D 100%)'
            }}>
              🧠
            </div>
            <div>
              <h1 className="text-xl font-bold text-amber-900">Đánh Giá Nhận Thức</h1>
              <p className="text-sm text-amber-700">Bài kiểm tra trí nhớ</p>
            </div>
          </Link>
          
          <div className="flex items-center gap-3">
            {/* Backend status */}
            <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${
              backendStatus === 'connected' 
                ? 'bg-green-100 text-green-800' 
                : backendStatus === 'checking'
                ? 'bg-amber-100 text-amber-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {backendStatus === 'connected' ? '✓ Đã kết nối' : 
               backendStatus === 'checking' ? '⏳ Đang kết nối...' : '✗ Mất kết nối'}
            </div>
            
            <Link href="/">
              <Button variant="ghost" className="text-amber-700 hover:bg-amber-100">
                <Home className="w-5 h-5 mr-2" />
                Trang chủ
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {/* STEP 1: User Info Form */}
          {currentStep === 'userInfo' && (
            <motion.div
              key="userInfo"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="py-8"
            >
              {/* Welcome message */}
              <div className="text-center mb-8">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                  className="text-6xl mb-4"
                >
                  🧠
                </motion.div>
                <motion.h2
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="text-3xl font-bold text-gray-800 mb-3"
                >
                  Chào mừng đến với bài kiểm tra nhận thức
                </motion.h2>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed"
                >
                  Trước khi bắt đầu, vui lòng cung cấp một số thông tin cá nhân.
                  Điều này giúp chúng tôi cá nhân hóa bài kiểm tra và đưa ra đánh giá chính xác hơn.
                </motion.p>
              </div>

              {/* User Info Form Component */}
              <UserInfoForm
                userInfo={userInfo}
                onUserInfoChange={setUserInfo}
                onNext={startAssessment}
                errors={userInfoErrors}
                isSubmitting={isProcessing}
                title="Thông tin cá nhân"
                description="Vui lòng điền đầy đủ thông tin để chúng tôi có thể đánh giá chính xác nhất."
              />

              {/* Enhanced Tips for elderly */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 }}
                className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200"
              >
                <h4 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  💡 Hướng dẫn sử dụng
                </h4>
                <div className="grid md:grid-cols-2 gap-4">
                  <ul className="space-y-3 text-gray-700">
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">🔊</span>
                      <span>Mỗi câu hỏi sẽ được <strong>đọc to</strong> bằng giọng nói tự nhiên</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">🎤</span>
                      <span>Nhấn nút <strong>ghi âm</strong> và trả lời bằng giọng nói của bạn</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">⏱️</span>
                      <span>Không cần vội, hãy <strong>trả lời thoải mái</strong></span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">🔄</span>
                      <span>Có thể <strong>ghi âm lại</strong> nếu chưa hài lòng</span>
                    </li>
                  </ul>
                  <ul className="space-y-3 text-gray-700">
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">📝</span>
                      <span>Bài kiểm tra gồm <strong>{questions.length || '...'}</strong> câu hỏi</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">⏰</span>
                      <span>Thời gian khoảng <strong>15-20 phút</strong></span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">🔒</span>
                      <span><strong>An toàn và bảo mật</strong> thông tin cá nhân</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-2xl">📊</span>
                      <span>Nhận kết quả và <strong>lời khuyên</strong> chi tiết</span>
                    </li>
                  </ul>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* STEP 2: Assessment */}
          {currentStep === 'assessment' && (
            <motion.div
              key="assessment"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Progress bar */}
              <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-amber-200">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xl font-bold text-amber-900">
                    Câu hỏi {currentQuestionIndex + 1} / {questions.length}
                  </span>
                  <span className="text-xl font-bold text-amber-700">
                    {Math.round(((currentQuestionIndex + 1) / questions.length) * 100)}%
                  </span>
                </div>
                <div className="w-full h-4 bg-amber-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: 'linear-gradient(135deg, #F4A261 0%, #E88D4D 100%)' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                
                {/* Question dots */}
                <div className="flex flex-wrap gap-2 mt-4 justify-center">
                  {questions.map((_, idx) => (
                    <div
                      key={idx}
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                        idx < currentQuestionIndex
                          ? 'bg-green-500 text-white'
                          : idx === currentQuestionIndex
                          ? 'bg-amber-500 text-white ring-4 ring-amber-200 scale-110'
                          : 'bg-amber-100 text-amber-600'
                      }`}
                    >
                      {idx < currentQuestionIndex ? '✓' : idx + 1}
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Current Question */}
              <div className="bg-white rounded-3xl shadow-xl p-8 border-2 border-amber-200">
                {/* Question category */}
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-4 py-2 rounded-full text-lg font-semibold" style={{
                    background: 'linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)',
                    color: '#92400E'
                  }}>
                    {currentQuestion?.category || 'Đang tải...'}
                  </span>
                  <span className="text-amber-600">
                    {currentQuestion?.domain || ''}
                  </span>
                </div>
                
                {/* Question text */}
                <div className="bg-amber-50 rounded-2xl p-6 mb-6 border-2 border-amber-200">
                  <p className="text-2xl leading-relaxed text-amber-900 font-medium">
                    {currentQuestion?.text.replace('{greeting}', getGreeting()) || 'Đang tải câu hỏi...'}
                  </p>
                </div>
                
                {/* Read question button */}
                <Button
                  onClick={() => speakQuestion(currentQuestionIndex)}
                  disabled={isTTSSpeaking}
                  className="mb-6 px-6 py-4 text-xl rounded-2xl border-2 border-amber-400 hover:bg-amber-100"
                  variant="ghost"
                >
                  <Volume2 className={`w-6 h-6 mr-3 ${isTTSSpeaking ? 'text-amber-600 animate-pulse' : 'text-amber-500'}`} />
                  {isTTSSpeaking ? 'Đang đọc...' : '🔊 Nghe câu hỏi'}
                </Button>
                
                {/* Recording section */}
                <div className="space-y-6">
                  {/* Recording button */}
                  <div className="flex flex-col items-center">
                    <motion.button
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={isProcessing}
                      className={`w-40 h-40 rounded-full flex flex-col items-center justify-center text-white shadow-xl transition-all ${
                        isRecording 
                          ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                          : 'hover:scale-105'
                      }`}
                      style={{
                        background: isRecording 
                          ? undefined 
                          : 'linear-gradient(135deg, #F4A261 0%, #E88D4D 100%)'
                      }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {isRecording ? (
                        <>
                          <Square className="w-12 h-12 mb-2" />
                          <span className="text-xl font-bold">DỪNG</span>
                        </>
                      ) : (
                        <>
                          <Mic className="w-12 h-12 mb-2" />
                          <span className="text-xl font-bold">GHI ÂM</span>
                        </>
                      )}
                    </motion.button>
                    
                    {/* Timer display */}
                    <div className={`mt-4 px-6 py-3 rounded-full text-2xl font-mono font-bold ${
                      isRecording ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      <Clock className="w-6 h-6 inline mr-2" />
                      {formatTime(recordingDuration)}
                    </div>
                    
                    <p className="mt-3 text-lg text-amber-600">
                      {isRecording 
                        ? '🔴 Đang ghi âm... Nhấn DỪNG khi trả lời xong'
                        : hasRecording
                        ? '✅ Đã ghi âm xong! Nhấn "Tiếp tục" hoặc ghi âm lại'
                        : '👆 Nhấn nút để bắt đầu ghi âm câu trả lời'}
                    </p>
                  </div>
                  
                  {/* File upload alternative */}
                  <div className="text-center">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      accept="audio/*"
                      className="hidden"
                    />
                    <Button
                      variant="ghost"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-amber-600 hover:bg-amber-100 text-lg"
                    >
                      <FileAudio className="w-5 h-5 mr-2" />
                      Hoặc chọn file âm thanh có sẵn
                    </Button>
                  </div>
                  
                  {/* Audio playback */}
                  {audioUrl && (
                    <div className="bg-amber-50 rounded-2xl p-4 border-2 border-amber-200">
                      <p className="text-lg text-amber-800 mb-3 font-medium">🎧 Nghe lại câu trả lời:</p>
                      <audio controls src={audioUrl} className="w-full rounded-xl" />
                    </div>
                  )}
                </div>
                
                {/* Navigation buttons */}
                <div className="flex gap-4 mt-8">
                  {/* Previous button */}
                  <Button
                    onClick={goToPreviousQuestion}
                    disabled={currentQuestionIndex === 0 || isProcessing}
                    className="flex-1 py-5 text-xl rounded-2xl border-2 border-amber-400 text-amber-700 hover:bg-amber-50"
                    variant="ghost"
                  >
                    <ArrowLeft className="w-6 h-6 mr-2" />
                    Quay lại
                  </Button>
                  
                  {/* Next/Submit button */}
                  <Button
                    onClick={submitAnswer}
                    disabled={!hasRecording || isProcessing}
                    className="flex-[2] py-5 text-xl rounded-2xl text-white shadow-lg hover:shadow-xl transition-all"
                    style={{
                      background: hasRecording && !isProcessing
                        ? 'linear-gradient(135deg, #F4A261 0%, #E88D4D 100%)'
                        : '#ccc'
                    }}
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-6 h-6 mr-2 animate-spin" />
                        Đang xử lý...
                      </>
                    ) : currentQuestionIndex === questions.length - 1 ? (
                      <>
                        <CheckCircle className="w-6 h-6 mr-2" />
                        Hoàn thành
                      </>
                    ) : (
                      <>
                        Tiếp tục
                        <ArrowRight className="w-6 h-6 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </div>
              
              {/* User info reminder */}
              <div className="bg-white rounded-2xl p-4 shadow border-2 border-amber-200">
                <div className="flex items-center gap-3 text-amber-800">
                  <User className="w-6 h-6 text-amber-600" />
                  <span className="font-medium">{userInfo.name}</span>
                  <span>•</span>
                  <span>{userInfo.age} tuổi</span>
                  <span>•</span>
                  <span>{userInfo.gender === 'male' ? 'Nam' : userInfo.gender === 'female' ? 'Nữ' : 'Khác'}</span>
                </div>
              </div>
            </motion.div>
          )}

          {/* STEP 3: Completed */}
          {currentStep === 'completed' && (
            <motion.div
              key="completed"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-8"
            >
              {/* Celebration */}
              <div className="text-center py-10">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                  className="text-8xl mb-6"
                >
                  🎉
                </motion.div>
                <h2 className="text-4xl font-bold text-amber-900 mb-4">
                  Chúc mừng bạn!
                </h2>
                <p className="text-2xl text-amber-700">
                  Bạn đã hoàn thành bài kiểm tra
                </p>
              </div>
              
              {/* Summary */}
              <div className="bg-white rounded-3xl shadow-xl p-8 border-2 border-amber-200">
                <h3 className="text-2xl font-bold text-amber-900 mb-6 flex items-center gap-3">
                  <Brain className="w-8 h-8 text-amber-600" />
                  Tóm tắt kết quả
                </h3>
                
                <div className="grid grid-cols-2 gap-6 mb-8">
                  <div className="bg-green-50 rounded-2xl p-6 text-center border-2 border-green-200">
                    <div className="text-5xl font-bold text-green-600 mb-2">
                      {testResults.length}
                    </div>
                    <div className="text-lg text-green-700">Câu hỏi đã trả lời</div>
                  </div>
                  
                  <div className="bg-amber-50 rounded-2xl p-6 text-center border-2 border-amber-200">
                    <div className="text-5xl font-bold text-amber-600 mb-2">
                      {Math.round(
                        testResults.reduce((sum, r) => sum + (r.gpt_evaluation?.overall_score || 0), 0) / 
                        Math.max(testResults.filter(r => r.gpt_evaluation).length, 1)
                      )}/10
                    </div>
                    <div className="text-lg text-amber-700">Điểm đánh giá AI</div>
                  </div>
                </div>
                
                {/* User info used */}
                <div className="bg-amber-50 rounded-2xl p-6 border-2 border-amber-200 mb-6">
                  <h4 className="font-bold text-amber-900 mb-3">Thông tin người kiểm tra:</h4>
                  <div className="grid grid-cols-2 gap-4 text-lg text-amber-800">
                    <div><strong>Họ tên:</strong> {userInfo.name}</div>
                    <div><strong>Tuổi:</strong> {userInfo.age}</div>
                    <div><strong>Giới tính:</strong> {userInfo.gender === 'male' ? 'Nam' : userInfo.gender === 'female' ? 'Nữ' : 'Khác'}</div>
                    <div><strong>Số năm học:</strong> {userInfo.education_years || 'Không cung cấp'}</div>
                  </div>
                </div>
                
                {/* Encouraging message */}
                <div className="bg-green-50 rounded-2xl p-6 border-2 border-green-200">
                  <div className="flex items-start gap-4">
                    <span className="text-4xl">💪</span>
                    <div>
                      <h4 className="text-xl font-bold text-green-800 mb-2">Thật tuyệt vời!</h4>
                      <p className="text-lg text-green-700 leading-relaxed">
                        Cảm ơn bạn đã hoàn thành bài kiểm tra. 
                        Kết quả sẽ được chuyên gia phân tích và gửi đến bạn.
                        Hãy tiếp tục duy trì các hoạt động rèn luyện trí não nhé!
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Action buttons */}
              <div className="flex flex-col gap-4">
                <Button
                  onClick={() => router.push(`/results?sessionId=${sessionId}`)}
                  className="w-full py-6 text-2xl font-bold rounded-2xl text-white shadow-lg"
                  style={{ background: 'linear-gradient(135deg, #F4A261 0%, #E88D4D 100%)' }}
                >
                  📊 Xem kết quả chi tiết
                </Button>
                
                <Button
                  onClick={() => window.location.reload()}
                  variant="ghost"
                  className="w-full py-5 text-xl rounded-2xl border-2 border-amber-400 text-amber-700"
                >
                  🔄 Làm bài kiểm tra mới
                </Button>
                
                <Link href="/" className="w-full">
                  <Button
                    variant="ghost"
                    className="w-full py-5 text-xl rounded-2xl text-amber-600"
                  >
                    🏠 Về trang chủ
                  </Button>
                </Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      
      {/* Footer */}
      <footer className="text-center py-6 text-amber-600">
        <p>© 2024 Hệ thống Đánh giá Nhận thức • Phiên: {sessionId.slice(0, 20)}...</p>
      </footer>
    </div>
  );
}
