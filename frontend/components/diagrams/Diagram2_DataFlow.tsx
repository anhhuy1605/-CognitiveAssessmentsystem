"use client";

import React from 'react';

/**
 * Diagram 2: Complete Data Flow Pipeline
 * 
 * Based on actual implementation in:
 * - backend/app.py (lines 4200-4350): /auto-transcribe endpoint
 * - backend/modules/acoustic_analyzer.py: extract_all_features()
 * - backend/modules/linguistic_analyzer.py: extract_all_features()
 * - backend/vietnamese_transcriber.py: transcribe_audio_file()
 * 
 * Date: 2025-12-28
 */

export default function Diagram2DataFlow() {
  return (
    <div className="diagram-container p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">Complete Data Flow Pipeline</h2>
      
      <div className="space-y-6">
        {/* Input */}
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
          <h3 className="font-bold text-green-800 mb-2">📥 INPUT</h3>
          <div className="text-sm text-gray-700">
            <p><strong>Raw Audio:</strong> .webm, .wav, .mp3</p>
            <p><strong>Sampling Rate:</strong> Variable → Resampled to 16kHz</p>
            <p><strong>Channels:</strong> Mono (converted from stereo if needed)</p>
            <p className="text-xs mt-2 text-gray-500">From: frontend MediaRecorder API</p>
          </div>
        </div>

        {/* Audio Preprocessing */}
        <div className="flex items-center justify-center">
          <div className="text-center">
            <div className="bg-blue-100 border-2 border-blue-500 rounded-lg p-3 inline-block">
              <p className="font-semibold text-blue-800">Audio Preprocessing</p>
              <p className="text-xs text-gray-600 mt-1">
                webm → wav conversion<br/>
                Resample to 16kHz, Mono<br/>
                Normalization
              </p>
            </div>
            <div className="text-2xl mt-2">↓</div>
          </div>
        </div>

        {/* Parallel Processing Branches */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Branch 1: Acoustic Analysis */}
          <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-4">
            <h3 className="font-bold text-blue-800 mb-3">🔊 Branch 1: Acoustic Analysis</h3>
            <div className="space-y-2 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">eGeMAPS (88 features)</p>
                <p className="text-xs text-gray-600">openSMILE library</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">F0 Contour</p>
                <p className="text-xs text-gray-600">Parselmouth (Praat)<br/>
                Mean, Std, Range, CV<br/>
                Raw: f0_values[], timestamps[]</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Voice Quality</p>
                <p className="text-xs text-gray-600">Jitter, Shimmer, HNR</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Pause Statistics</p>
                <p className="text-xs text-gray-600">Duration, Frequency, Ratio</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Speaking Rate</p>
                <p className="text-xs text-gray-600">Syllables/second</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Tone Analysis</p>
                <p className="text-xs text-gray-600">Vietnamese-specific</p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              Output: ~100+ features<br/>
              From: acoustic_analyzer.py:705
            </div>
          </div>

          {/* Branch 2: ASR + Linguistic */}
          <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-4">
            <h3 className="font-bold text-purple-800 mb-3">🎤 Branch 2: ASR + Linguistic</h3>
            
            {/* ASR Sub-process */}
            <div className="bg-white rounded p-2 mb-3 border border-purple-300">
              <p className="font-semibold text-purple-700">ASR: Gemini API</p>
              <div className="text-xs text-gray-600 mt-1">
                <p>Model: gemini-2.5-flash</p>
                <p>Language: 'vi'</p>
                <p>Method: File upload API</p>
                <p>Output: Vietnamese transcript</p>
              </div>
            </div>

            {/* Linguistic Features */}
            <div className="space-y-2 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Lexical Features</p>
                <p className="text-xs text-gray-600">TTR, MATTR, Word freq</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Syntactic Features</p>
                <p className="text-xs text-gray-600">MLU, Sentence length</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Semantic Features</p>
                <p className="text-xs text-gray-600">Coherence, Idea density</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Vietnamese-Specific</p>
                <p className="text-xs text-gray-600">POS tags, Classifiers</p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              Output: ~50+ features<br/>
              From: linguistic_analyzer.py:838
            </div>
          </div>

          {/* Branch 3: GPT-4o Evaluation */}
          <div className="bg-indigo-50 border-2 border-indigo-500 rounded-lg p-4">
            <h3 className="font-bold text-indigo-800 mb-3">🤖 Branch 3: GPT-4o Evaluation</h3>
            <div className="space-y-2 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Input</p>
                <p className="text-xs text-gray-600">Transcript + Question context</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Model</p>
                <p className="text-xs text-gray-600">gpt-4o</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Output</p>
                <p className="text-xs text-gray-600">
                  Analysis, Feedback<br/>
                  Validation (is_correct)<br/>
                  No scores (removed)
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: app.py:evaluate_with_gpt4o()
            </div>
          </div>
        </div>

        {/* Feature Concatenation */}
        <div className="flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl mb-2">↓</div>
            <div className="bg-yellow-100 border-2 border-yellow-500 rounded-lg p-3 inline-block">
              <p className="font-semibold text-yellow-800">Feature Concatenation</p>
              <p className="text-xs text-gray-600 mt-1">
                Acoustic (~100) + Linguistic (~50)<br/>
                Total: ~150 features<br/>
                Format: Dict[str, float]
              </p>
            </div>
          </div>
        </div>

        {/* Output */}
        <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4">
          <h3 className="font-bold text-red-800 mb-2">📤 OUTPUT</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Transcription</p>
              <p className="text-xs text-gray-600">Vietnamese text</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Audio Features</p>
              <p className="text-xs text-gray-600">F0 contour, eGeMAPS, etc.</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Linguistic Features</p>
              <p className="text-xs text-gray-600">TTR, MLU, coherence, etc.</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">GPT Evaluation</p>
              <p className="text-xs text-gray-600">Analysis, feedback</p>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            Stored in: result['audio_features'], result['linguistic_features']<br/>
            For: SHAP analysis, Results visualization
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-100 rounded p-4 text-xs text-gray-600">
          <p className="font-semibold mb-2">📝 Implementation Notes:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>ML model scoring removed (lines 638-804 in app.py)</li>
            <li>Only GPT evaluation kept for answer validation</li>
            <li>Features stored for SHAP explainability</li>
            <li>Audio preprocessing: webm → wav conversion required</li>
            <li>Parallel processing: Acoustic + ASR run concurrently</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

