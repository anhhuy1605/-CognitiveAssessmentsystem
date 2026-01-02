"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Calculator, Check, X, Minus } from 'lucide-react';
import { parseVietnameseNumber } from './utils';

interface Serial7sInterfaceProps {
  questionId: string;
  onAnswer: (answers: number[]) => void;
  onStop: () => void;
  currentTranscript?: string;
  isRecording?: boolean;
}

const EXPECTED_ANSWERS = [93, 86, 79, 72, 65];
const START_VALUE = 100;
const MAX_STEPS = 5;
const STEP_VALUE = 7;

export default function Serial7sInterface({
  questionId,
  onAnswer,
  onStop,
  currentTranscript = '',
  isRecording = false
}: Serial7sInterfaceProps) {
  const [userAnswers, setUserAnswers] = useState<number[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasStarted, setHasStarted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const lastProcessedRef = useRef<string>('');

  // Extract numbers from transcript
  useEffect(() => {
    if (!currentTranscript || isComplete) return;
    
    // Avoid reprocessing same transcript
    if (currentTranscript === lastProcessedRef.current) return;
    lastProcessedRef.current = currentTranscript;

    if (isRecording) {
      setHasStarted(true);
    }

    // Extract all numbers from transcript
    const numbers = currentTranscript.match(/\d+/g);
    if (numbers && numbers.length > 0) {
      // Process the latest number
      const latestNumber = parseInt(numbers[numbers.length - 1]);
      
      // Only add if it's a new number and not already in answers
      if (latestNumber !== userAnswers[userAnswers.length - 1] && userAnswers.length < MAX_STEPS) {
        const newAnswers = [...userAnswers, latestNumber];
        setUserAnswers(newAnswers);
        setCurrentStep(newAnswers.length);
        
        // Call onAnswer callback
        onAnswer(newAnswers);

        // ✅ AUTO-STOP: Stop after max steps
        if (newAnswers.length >= MAX_STEPS) {
          setIsComplete(true);
          // Call onStop immediately - parent will handle recording stop and submit
          onStop();
        }
      }
    }
  }, [currentTranscript, isRecording, isComplete, userAnswers, onAnswer, onStop]);

  const checkAnswer = (userNum: number, index: number): boolean => {
    return userNum === EXPECTED_ANSWERS[index];
  };

  const getCorrectCount = (): number => {
    return userAnswers.filter((ans, idx) => checkAnswer(ans, idx)).length;
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-6 space-y-6">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-3">
          <Calculator className="w-8 h-8 text-purple-600" />
          <h3 className="text-xl font-bold text-gray-800">Bài tập trừ dần</h3>
        </div>
        <p className="text-gray-700 leading-relaxed">
          Chúng ta sẽ làm bài tập tính toán đơn giản. Bạn hãy tính 100 trừ 7 bằng bao nhiêu? 
          Rồi lấy kết quả vừa tính được trừ tiếp cho 7. Cứ tiếp tục như vậy cho đến khi tôi nói dừng.
        </p>
      </div>

      {/* Visual Tracker */}
      <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
        
        {/* Starting Number */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-3 bg-blue-100 px-6 py-3 rounded-full">
            <span className="text-sm text-gray-600">Bắt đầu từ:</span>
            <span className="text-3xl font-bold text-blue-600">{START_VALUE}</span>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="space-y-3">
          {Array.from({ length: MAX_STEPS }).map((_, index) => {
            const isAnswered = index < userAnswers.length;
            const userAnswer = userAnswers[index];
            const isCorrect = isAnswered && checkAnswer(userAnswer, index);
            const expectedAnswer = EXPECTED_ANSWERS[index];
            const previousValue = index === 0 ? START_VALUE : EXPECTED_ANSWERS[index - 1];

            return (
              <div
                key={index}
                className={`
                  flex items-center gap-4 p-4 rounded-lg border-2 transition-all duration-300
                  ${isAnswered 
                    ? isCorrect 
                      ? 'bg-green-50 border-green-300' 
                      : 'bg-red-50 border-red-300'
                    : index === currentStep && hasStarted
                      ? 'bg-yellow-50 border-yellow-300 ring-2 ring-yellow-400'
                      : 'bg-gray-50 border-gray-200'
                  }
                `}
              >
                {/* Step Number */}
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-bold
                  ${isAnswered 
                    ? isCorrect 
                      ? 'bg-green-500 text-white' 
                      : 'bg-red-500 text-white'
                    : index === currentStep && hasStarted
                      ? 'bg-yellow-500 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }
                `}>
                  {index + 1}
                </div>

                {/* Operation */}
                <div className="flex items-center gap-2">
                  <span className="text-gray-600 font-medium">
                    {previousValue}
                  </span>
                  <Minus className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600 font-medium">{STEP_VALUE}</span>
                  <span className="text-gray-400">=</span>
                </div>

                {/* User Answer */}
                <div className="flex-1 text-center">
                  {isAnswered ? (
                    <div className="flex items-center justify-center gap-2">
                      <span className={`text-2xl font-bold ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
                        {userAnswer}
                      </span>
                      {isCorrect ? (
                        <Check className="w-6 h-6 text-green-600" />
                      ) : (
                        <X className="w-6 h-6 text-red-600" />
                      )}
                    </div>
                  ) : index === currentStep && hasStarted ? (
                    <div className="text-xl text-yellow-600 font-medium animate-pulse">
                      Đang chờ...
                    </div>
                  ) : (
                    <div className="text-xl text-gray-400">?</div>
                  )}
                </div>

                {/* Expected Answer (only show if wrong) */}
                {isAnswered && !isCorrect && (
                  <div className="text-sm text-gray-600">
                    (Đáp án: <span className="font-bold text-green-600">{expectedAnswer}</span>)
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>Tiến độ</span>
            <span className="font-bold">{currentStep}/{MAX_STEPS}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${(currentStep / MAX_STEPS) * 100}%` }}
            />
          </div>
        </div>

        {/* Status Messages */}
        {!hasStarted && (
          <div className="mt-4 text-center text-gray-500 italic">
            🎤 Bấm ghi âm và bắt đầu trả lời...
          </div>
        )}

        {isRecording && !isComplete && (
          <div className="mt-4 text-center">
            <div className="inline-flex items-center gap-2 text-blue-600 font-medium">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              Đang nghe câu trả lời của bạn...
            </div>
          </div>
        )}

        {isComplete && (
          <div className="mt-4 text-center">
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-green-100 text-green-700 rounded-full font-medium">
              <Check className="w-5 h-5" />
              Được rồi, dừng lại ở đây. Bạn làm tốt lắm!
            </div>
            <div className="mt-2 text-sm text-gray-600">
              Bạn đã trả lời đúng: {getCorrectCount()}/{MAX_STEPS}
            </div>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="text-sm text-gray-700 space-y-1">
          <div>• Nói rõ từng số một</div>
          <div>• Hệ thống sẽ tự động dừng sau {MAX_STEPS} bước</div>
          <div>• Bạn không cần nói "dừng"</div>
        </div>
      </div>

    </div>
  );
}
