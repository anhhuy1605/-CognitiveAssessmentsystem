"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { CheckCircle2, HelpCircle, Eye, EyeOff } from 'lucide-react';
import { extractKeywords, matchKeywords } from './utils';

interface WordRecallInterfaceProps {
  questionId: string;
  words: string[]; // ["Con mèo", "Chiếc xe", "Cây lúa"]
  phase: 'registration' | 'recall';
  currentTranscript?: string;
  onComplete: (matchedWords: string[]) => void;
  showWords?: boolean; // Override for registration phase
}

export default function WordRecallInterface({
  questionId,
  words,
  phase,
  currentTranscript = '',
  onComplete,
  showWords: propShowWords
}: WordRecallInterfaceProps) {
  const [matchedWords, setMatchedWords] = useState<string[]>([]);
  const [showWords, setShowWords] = useState(phase === 'registration' || propShowWords === true);
  const keywords = extractKeywords(words);

  // Process transcript for recall phase
  useEffect(() => {
    if (phase === 'recall' && currentTranscript) {
      const matched = matchKeywords(currentTranscript, keywords);
      setMatchedWords(matched);
      
      // Check if all words matched
      if (matched.length === words.length) {
        onComplete(matched);
      }
    }
  }, [currentTranscript, phase, words, keywords, onComplete]);

  // Hide words after 3 seconds in registration phase
  useEffect(() => {
    if (phase === 'registration' && showWords) {
      const timer = setTimeout(() => {
        setShowWords(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [phase, showWords]);

  const getWordStatus = (word: string): 'matched' | 'unmatched' | 'hidden' => {
    if (phase === 'registration' || showWords) {
      return 'hidden'; // Show all words during registration
    }
    
    const keyword = extractKeywords([word])[0];
    const matched = matchKeywords(currentTranscript, [keyword]);
    return matched.length > 0 ? 'matched' : 'unmatched';
  };

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          {phase === 'registration' ? '📝 Hãy nhớ 3 từ này' : '🧠 Nhớ lại 3 từ vừa học'}
        </h3>
      </div>

      {/* Words display */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border-2 border-purple-200">
        {phase === 'registration' || showWords ? (
          // Show words (registration phase)
          <div className="space-y-4">
            {words.map((word, index) => (
              <div
                key={index}
                className={`text-center py-4 px-6 rounded-lg font-bold text-2xl transition-all duration-300 ${
                  showWords
                    ? 'bg-white text-purple-700 shadow-md'
                    : 'bg-gray-100 text-gray-400 opacity-50'
                }`}
              >
                {word}
              </div>
            ))}
          </div>
        ) : (
          // Hide words (recall phase)
          <div className="space-y-4">
            <div className="text-center py-8 text-gray-400 italic">
              [Từ đã được ẩn - Hãy nhớ lại]
            </div>
            
            {/* Progress indicators */}
            <div className="flex justify-center gap-4 mt-6">
              {words.map((word, index) => {
                const keyword = extractKeywords([word])[0];
                const isMatched = matchedWords.includes(keyword);
                
                return (
                  <div
                    key={index}
                    className={`flex flex-col items-center gap-2 p-3 rounded-lg ${
                      isMatched ? 'bg-green-100' : 'bg-gray-100'
                    }`}
                  >
                    {isMatched ? (
                      <>
                        <CheckCircle2 className="w-8 h-8 text-green-600" />
                        <span className="text-xs text-green-700 font-medium">
                          {keyword}
                        </span>
                      </>
                    ) : (
                      <>
                        <HelpCircle className="w-8 h-8 text-gray-400" />
                        <span className="text-xs text-gray-500">?</span>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
            
            {/* Progress text */}
            <div className="text-center mt-4 text-sm text-gray-600">
              Đã nhớ: {matchedWords.length}/{words.length} từ
            </div>
          </div>
        )}
      </div>

      {/* Toggle button for registration phase (if needed) */}
      {phase === 'registration' && (
        <div className="flex justify-center">
          <Button
            variant="secondaryOutline"
            onClick={() => setShowWords(!showWords)}
            className="gap-2"
          >
            {showWords ? (
              <>
                <EyeOff className="w-4 h-4" />
                Ẩn từ
              </>
            ) : (
              <>
                <Eye className="w-4 h-4" />
                Hiện từ
              </>
            )}
          </Button>
        </div>
      )}

      {/* Instructions */}
      <div className="text-center text-sm text-gray-500">
        {phase === 'registration' && 
          'Hãy nhắc lại 3 từ này sau khi nghe xong'}
        {phase === 'recall' && 
          'Hãy nhớ lại và nói 3 từ bạn đã học lúc nãy'}
      </div>
    </div>
  );
}

