"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Timer, PawPrint, Check } from 'lucide-react';

interface AnimalNamingInterfaceProps {
  questionId: string;
  onAnswer: (animals: string[]) => void;
  onTimeUp: () => void;
  currentTranscript?: string;
  isRecording?: boolean;
}

const TIME_LIMIT_SECONDS = 60;

// Vietnamese animal keywords for extraction
const ANIMAL_KEYWORDS = [
  'chó', 'mèo', 'gà', 'vịt', 'lợn', 'bò', 'trâu', 'ngựa', 'dê', 'cừu',
  'hổ', 'sư tử', 'voi', 'khỉ', 'gấu', 'cáo', 'sói', 'hươu', 'nai',
  'cá', 'cá mập', 'cá heo', 'cá voi', 'bạch tuộc', 'mực',
  'chim', 'đại bàng', 'diều hâu', 'phượng hoàng', 'công', 'két', 'vẹt',
  'rắn', 'rùa', 'cá sấu', 'thằn lằn', 'tắc kè',
  'kiến', 'ong', 'bướm', 'gián', 'ruồi', 'muỗi', 'châu chấu',
  'chuột', 'thỏ', 'sóc', 'nhím', 'gà mái', 'gà trống', 'chó con', 'mèo con',
  'ngựa vằn', 'hươu cao cổ', 'sư tử', 'báo', 'hổ', 'gấu trúc', 'khỉ đột'
];

export default function AnimalNamingInterface({
  questionId,
  onAnswer,
  onTimeUp,
  currentTranscript = '',
  isRecording = false
}: AnimalNamingInterfaceProps) {
  const [timeLeft, setTimeLeft] = useState(TIME_LIMIT_SECONDS);
  const [hasStarted, setHasStarted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [animals, setAnimals] = useState<string[]>([]);
  const [lastTranscript, setLastTranscript] = useState('');
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // ✅ AUTO-START: Start countdown immediately when component mounts or when recording starts
  useEffect(() => {
    if (!hasStarted && !isComplete) {
      // Start timer immediately, don't wait for recording
      setHasStarted(true);
      startCountdown();
    }
  }, [hasStarted, isComplete]);

  // Also start when recording starts (if not already started)
  useEffect(() => {
    if (isRecording && !hasStarted && !isComplete) {
      setHasStarted(true);
      startCountdown();
    }
  }, [isRecording, hasStarted, isComplete]);

  // Extract animals from transcript
  useEffect(() => {
    if (!currentTranscript || !hasStarted || isComplete) return;
    if (currentTranscript === lastTranscript) return;

    const newWords = currentTranscript
      .toLowerCase()
      .replace(/[.,!?;]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 0);

    const foundAnimals = newWords.filter(word =>
      ANIMAL_KEYWORDS.some(keyword => word.includes(keyword) || keyword.includes(word))
    );

    if (foundAnimals.length > 0) {
      const uniqueAnimals = [...new Set([...animals, ...foundAnimals])];
      setAnimals(uniqueAnimals);
    }

    setLastTranscript(currentTranscript);
  }, [currentTranscript, hasStarted, isComplete, animals, lastTranscript]);

  const startCountdown = () => {
    if (timerRef.current) return; // Already started
    
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          stopCountdown();
          handleTimeUp();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const stopCountdown = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const handleTimeUp = () => {
    setIsComplete(true);
    stopCountdown();
    // Send final answer and trigger time up callback
    // Parent will handle recording stop and submit
    onAnswer(animals);
    onTimeUp();
  };

  useEffect(() => {
    return () => stopCountdown();
  }, []);

  const progress = (timeLeft / TIME_LIMIT_SECONDS) * 100;
  const isLowTime = timeLeft <= 10;
  const isCriticalTime = timeLeft <= 5;

  return (
    <div className="w-full max-w-3xl mx-auto p-6 space-y-6">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-3">
          <PawPrint className="w-8 h-8 text-green-600" />
          <h3 className="text-xl font-bold text-gray-800">Kể tên con vật</h3>
        </div>
        <p className="text-gray-700 leading-relaxed">
          Bây giờ bạn hãy kể tên các con vật trong 60 giây. Càng nhiều càng tốt nhé! 
          Bất kỳ con vật nào bạn biết. Sẵn sàng chưa? Bắt đầu!
        </p>
      </div>

      {/* Timer Display */}
      <div className={`
        relative overflow-hidden rounded-2xl p-8 transition-all duration-300
        ${isComplete 
          ? 'bg-gray-100' 
          : isCriticalTime 
            ? 'bg-red-100 animate-pulse' 
            : isLowTime 
              ? 'bg-orange-100' 
              : 'bg-blue-100'
        }
      `}>
        
        {/* Circular Progress */}
        <div className="flex justify-center mb-4">
          <div className="relative w-48 h-48">
            {/* Background circle */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="96"
                cy="96"
                r="88"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                className="text-gray-300"
              />
              {/* Progress circle */}
              <circle
                cx="96"
                cy="96"
                r="88"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 88}`}
                strokeDashoffset={`${2 * Math.PI * 88 * (1 - progress / 100)}`}
                className={`
                  transition-all duration-1000 ease-linear
                  ${isComplete 
                    ? 'text-gray-400' 
                    : isCriticalTime 
                      ? 'text-red-500' 
                      : isLowTime 
                        ? 'text-orange-500' 
                        : 'text-blue-500'
                  }
                `}
                strokeLinecap="round"
              />
            </svg>

            {/* Timer number */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <Timer className={`
                w-8 h-8 mb-2
                ${isComplete 
                  ? 'text-gray-400' 
                  : isCriticalTime 
                    ? 'text-red-500' 
                    : isLowTime 
                      ? 'text-orange-500' 
                      : 'text-blue-500'
                }
              `} />
              <span className={`
                text-6xl font-bold tabular-nums
                ${isComplete 
                  ? 'text-gray-600' 
                  : isCriticalTime 
                    ? 'text-red-600' 
                    : isLowTime 
                      ? 'text-orange-600' 
                      : 'text-blue-600'
                }
              `}>
                {timeLeft}
              </span>
              <span className="text-sm text-gray-600 mt-1">giây</span>
            </div>
          </div>
        </div>

        {/* Status Message */}
        {!hasStarted && (
          <div className="text-center text-gray-600 font-medium">
            🎤 Bấm ghi âm để bắt đầu đếm ngược
          </div>
        )}

        {hasStarted && !isComplete && isCriticalTime && (
          <div className="text-center text-red-600 font-bold text-lg animate-bounce">
            ⚠️ Sắp hết giờ!
          </div>
        )}

        {isComplete && (
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-green-100 text-green-700 rounded-full font-medium">
              <Check className="w-5 h-5" />
              Hết giờ!
            </div>
          </div>
        )}
      </div>

      {/* Animals List */}
      <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-bold text-gray-800">
            Các con vật đã kể
          </h4>
          <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full font-bold">
            <PawPrint className="w-5 h-5" />
            {animals.length}
          </div>
        </div>

        {animals.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            Chưa có con vật nào...
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {animals.map((animal, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg animate-fadeIn"
              >
                <div className="w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center text-xs font-bold">
                  {index + 1}
                </div>
                <span className="text-gray-700 font-medium">{animal}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recording Indicator */}
      {isRecording && !isComplete && (
        <div className="text-center">
          <div className="inline-flex items-center gap-2 text-blue-600 font-medium">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            🎤 Đang ghi âm... Hãy kể tên các con vật!
          </div>
        </div>
      )}

      {/* Final Score */}
      {isComplete && (
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-xl p-6 text-center">
          <h4 className="text-xl font-bold text-gray-800 mb-2">
            Kết quả của bạn
          </h4>
          <div className="text-5xl font-bold text-purple-600 mb-2">
            {animals.length}
          </div>
          <div className="text-gray-600">
            con vật trong {TIME_LIMIT_SECONDS} giây
          </div>
          
          {animals.length >= 15 && (
            <div className="mt-4 text-green-600 font-medium">
              🌟 Xuất sắc!
            </div>
          )}
          {animals.length >= 10 && animals.length < 15 && (
            <div className="mt-4 text-blue-600 font-medium">
              👍 Tốt lắm!
            </div>
          )}
          {animals.length < 10 && (
            <div className="mt-4 text-orange-600 font-medium">
              💪 Cố gắng thêm nhé!
            </div>
          )}
        </div>
      )}

    </div>
  );
}

