"use client";

import React from 'react';

/**
 * Diagram 1: Overall System Architecture
 * 
 * High-level overview of the complete MMSE assessment system
 * 
 * Based on:
 * - Frontend: frontend/app/(main)/mmse-chatbot/page.tsx
 * - Backend: backend/app.py, backend/services/mmse_chatbot_api.py
 * - Modules: backend/modules/acoustic_analyzer.py, linguistic_analyzer.py
 * 
 * Date: 2025-12-28
 */

export default function Diagram1SystemOverview() {
  return (
    <div className="diagram-container p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">Overall System Architecture</h2>
      
      <div className="space-y-6">
        {/* Input Layer */}
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-green-800 mb-4">📥 INPUT LAYER</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded p-4 text-center">
              <p className="text-4xl mb-2">🎤</p>
              <p className="font-semibold">Voice Recording</p>
              <p className="text-xs text-gray-600 mt-2">
                Format: WebM, WAV, MP3<br/>
                Source: Browser MediaRecorder<br/>
                Or: File upload
              </p>
            </div>
            <div className="bg-white rounded p-4 text-center">
              <p className="text-4xl mb-2">👤</p>
              <p className="font-semibold">User Info</p>
              <p className="text-xs text-gray-600 mt-2">
                Age, Gender, Education<br/>
                City, District
              </p>
            </div>
            <div className="bg-white rounded p-4 text-center">
              <p className="text-4xl mb-2">❓</p>
              <p className="font-semibold">MMSE Questions</p>
              <p className="text-xs text-gray-600 mt-2">
                From: mmse_audio_questions_standardized.json<br/>
                25 questions across 6 domains
              </p>
            </div>
          </div>
        </div>

        {/* Processing Modules */}
        <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-blue-800 mb-4">⚙️ PROCESSING MODULES</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* ASR Module */}
            <div className="bg-white border-2 border-blue-300 rounded-lg p-4">
              <h4 className="font-bold text-blue-800 mb-2">🎤 ASR Module</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>Service:</strong> Gemini API</p>
                <p><strong>Model:</strong> gemini-2.5-flash</p>
                <p><strong>Language:</strong> Vietnamese</p>
                <p><strong>Output:</strong> Transcript</p>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                vietnamese_transcriber.py:620
              </p>
            </div>

            {/* Acoustic Features */}
            <div className="bg-white border-2 border-purple-300 rounded-lg p-4">
              <h4 className="font-bold text-purple-800 mb-2">🔊 Acoustic Features</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>eGeMAPS:</strong> 88 features</p>
                <p><strong>F0 Contour:</strong> Raw + stats</p>
                <p><strong>Voice Quality:</strong> Jitter, Shimmer, HNR</p>
                <p><strong>Pause Stats:</strong> Duration, frequency</p>
                <p><strong>Speaking Rate:</strong> Syllables/sec</p>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                acoustic_analyzer.py:705
              </p>
            </div>

            {/* Linguistic Features */}
            <div className="bg-white border-2 border-indigo-300 rounded-lg p-4">
              <h4 className="font-bold text-indigo-800 mb-2">📝 Linguistic Features</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>Lexical:</strong> TTR, MATTR, vocab</p>
                <p><strong>Syntactic:</strong> MLU, sentence length</p>
                <p><strong>Semantic:</strong> Coherence, idea density</p>
                <p><strong>Vietnamese:</strong> POS, classifiers</p>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                linguistic_analyzer.py:838
              </p>
            </div>

            {/* GPT Evaluation */}
            <div className="bg-white border-2 border-orange-300 rounded-lg p-4">
              <h4 className="font-bold text-orange-800 mb-2">🤖 GPT-4o Evaluation</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>Model:</strong> gpt-4o</p>
                <p><strong>Purpose:</strong> Answer validation</p>
                <p><strong>Output:</strong> Analysis, feedback</p>
                <p><strong>No Scoring:</strong> Removed</p>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                app.py:evaluate_with_gpt4o
              </p>
            </div>
          </div>
        </div>

        {/* Scoring System */}
        <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-purple-800 mb-4">📊 SCORING SYSTEM</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border-2 border-green-300 rounded-lg p-4">
              <h4 className="font-bold text-green-800 mb-2">✅ Rule-Based Scoring</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>Source:</strong> mmse_audio_questions_standardized.json</p>
                <p><strong>Method:</strong> Per-question points</p>
                <p><strong>Validation:</strong> GPT-4o (is_correct)</p>
                <p><strong>Total:</strong> Sum of question scores (0-30)</p>
              </div>
            </div>
            <div className="bg-white border-2 border-red-300 rounded-lg p-4">
              <h4 className="font-bold text-red-800 mb-2">❌ ML Model Scoring</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>Status:</strong> REMOVED</p>
                <p><strong>Reason:</strong> Replaced with rule-based</p>
                <p><strong>Models:</strong> Random Forest, XGBoost (removed)</p>
              </div>
            </div>
          </div>
        </div>

        {/* Output Layer */}
        <div className="bg-red-50 border-2 border-red-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-red-800 mb-4">📤 OUTPUT LAYER</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded p-4 text-center">
              <p className="text-3xl mb-2">📝</p>
              <p className="font-semibold">Transcript</p>
              <p className="text-xs text-gray-600 mt-2">Vietnamese text</p>
            </div>
            <div className="bg-white rounded p-4 text-center">
              <p className="text-3xl mb-2">📊</p>
              <p className="font-semibold">Features</p>
              <p className="text-xs text-gray-600 mt-2">
                Acoustic + Linguistic<br/>
                For SHAP analysis
              </p>
            </div>
            <div className="bg-white rounded p-4 text-center">
              <p className="text-3xl mb-2">💬</p>
              <p className="font-semibold">GPT Evaluation</p>
              <p className="text-xs text-gray-600 mt-2">
                Analysis & feedback<br/>
                Validation result
              </p>
            </div>
            <div className="bg-white rounded p-4 text-center">
              <p className="text-3xl mb-2">🎯</p>
              <p className="font-semibold">MMSE Score</p>
              <p className="text-xs text-gray-600 mt-2">
                Rule-based (0-30)<br/>
                Per-question breakdown
              </p>
            </div>
          </div>
        </div>

        {/* System Flow */}
        <div className="bg-gray-50 border-2 border-gray-400 rounded-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">🔄 System Flow</h3>
          <div className="text-sm text-gray-700 space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">1</div>
              <p>User records audio answer → Frontend sends to backend</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">2</div>
              <p>Backend: Audio preprocessing (webm → wav, 16kHz)</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">3</div>
              <p>Parallel: ASR (Gemini) + Acoustic extraction</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">4</div>
              <p>Linguistic features from transcript</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">5</div>
              <p>GPT-4o validates answer</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold">6</div>
              <p>Rule-based scoring from JSON</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white font-bold">7</div>
              <p>Return results: features + evaluation + score</p>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-100 rounded p-4 text-xs text-gray-600">
          <p className="font-semibold mb-2">📝 Architecture Notes:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Frontend: Next.js (React) with TypeScript</li>
            <li>Backend: Flask (Python) REST API</li>
            <li>Database: PostgreSQL (Neon) for results storage</li>
            <li>Real-time: WebSocket for live updates (optional)</li>
            <li>ML Models: Removed, using rule-based scoring only</li>
            <li>Features: Stored for SHAP explainability</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

