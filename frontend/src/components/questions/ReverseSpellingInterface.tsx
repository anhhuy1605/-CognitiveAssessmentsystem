"use client";

import React, { useState, useEffect } from 'react';
import { parseVietnameseLetter } from '../../utils/vietnameseUtils';

interface ReverseSpellingInterfaceProps {
  questionId: string;
  word: string; // "THỊNH" or "WORLD"
  currentTranscript?: string;
  onComplete: (spelling: string[]) => void;
  showWordDuration?: number; // seconds to show word before hiding (default: 3)
}

export default function ReverseSpellingInterface({
  questionId,
  word,
  currentTranscript = '',
  onComplete,
  showWordDuration = 3
}: ReverseSpellingInterfaceProps) {
  const [phase, setPhase] = useState<'show' | 'hide'>('show');
  const [userSpelling, setUserSpelling] = useState<string[]>([]);
  const [showWord, setShowWord] = useState(true);
  const correctAnswer = word.split('').reverse(); // Reverse spelling

  // Transition from show to hide phase
  useEffect(() => {
    if (phase === 'show') {
      const timer = setTimeout(() => {
        setShowWord(false);
        setPhase('hide');
      }, showWordDuration * 1000);
      return () => clearTimeout(timer);
    }
  }, [phase, showWordDuration]);

  // Process transcript for spelling
  useEffect(() => {
    if (phase === 'hide' && currentTranscript) {
      const letters = currentTranscript
        .trim()
        .split(/[\s\-\.]+/)
        .filter(Boolean);
      
      const parsedLetters: string[] = [];
      for (const letter of letters) {
        const parsed = parseVietnameseLetter(letter);
        if (parsed && parsed.length > 0) {
          parsedLetters.push(...parsed);
        }
      }
      
      if (parsedLetters.length > 0) {
        const newSpelling = [...userSpelling, ...parsedLetters];
        setUserSpelling(newSpelling.slice(0, correctAnswer.length));
        
        // Check if complete
        if (newSpelling.length >= correctAnswer.length) {
          onComplete(newSpelling.slice(0, correctAnswer.length));
        }
      }
    }
  }, [currentTranscript, phase, correctAnswer.length, onComplete]);

  const getLetterStatus = (index: number): 'correct' | 'incorrect' | 'pending' => {
    if (index >= userSpelling.length) return 'pending';
    return userSpelling[index] === correctAnswer[index] ? 'correct' : 'incorrect';
  };

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          🔄 Đánh vần ngược
        </h3>
        {phase === 'hide' && (
          <p className="text-sm text-gray-600">
            Từ: "{word}"
          </p>
        )}
      </div>

      {/* Word display / Spelling area */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-6 border-2 border-amber-200 min-h-[200px] flex items-center justify-center">
        {phase === 'show' && showWord ? (
          // Show word phase
          <div
            className={`text-6xl font-bold text-amber-700 transition-opacity duration-500 ${
              showWord ? 'opacity-100' : 'opacity-0'
            }`}
          >
            {word}
          </div>
        ) : (
          // Hide phase - show spelling progress
          <div className="w-full">
            <div className="text-center mb-4 text-sm text-gray-500 italic">
              [Từ đã được ẩn]
            </div>
            
            {/* Spelling display */}
            <div className="flex justify-center gap-3 flex-wrap">
              {correctAnswer.map((letter, index) => {
                const status = getLetterStatus(index);
                const userLetter = index < userSpelling.length ? userSpelling[index] : '';
                
                return (
                  <div
                    key={index}
                    className={`w-16 h-16 rounded-lg flex items-center justify-center font-bold text-2xl border-2 transition-all ${
                      status === 'correct'
                        ? 'bg-green-500 text-white border-green-600'
                        : status === 'incorrect'
                        ? 'bg-red-400 text-white border-red-500'
                        : 'bg-gray-200 text-gray-400 border-gray-300'
                    }`}
                  >
                    {userLetter || '?'}
                  </div>
                );
              })}
            </div>
            
            {/* Progress */}
            <div className="text-center mt-4 text-sm text-gray-600">
              Tiến độ: {userSpelling.length}/{correctAnswer.length} chữ
            </div>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="text-center text-sm text-gray-500">
        {phase === 'show' && 
          `Hãy quan sát từ này (${showWordDuration} giây), sau đó đánh vần ngược`}
        {phase === 'hide' && 
          'Hãy đánh vần ngược từ này, nói từng chữ cái'}
      </div>
    </div>
  );
}



