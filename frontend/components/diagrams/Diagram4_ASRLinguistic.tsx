"use client";

import React from 'react';

/**
 * Diagram 4: ASR (Gemini) + Linguistic Feature Extraction (DETAILED)
 * 
 * Based on actual implementation in:
 * - backend/vietnamese_transcriber.py (lines 620-840): transcribe_audio_file()
 * - backend/modules/linguistic_analyzer.py (lines 187-900): extract_all_features()
 * 
 * Date: 2025-12-28
 */

export default function Diagram4ASRLinguistic() {
  return (
    <div className="diagram-container p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">ASR + Linguistic Feature Extraction</h2>
      
      <div className="space-y-8">
        {/* Part A: Gemini ASR */}
        <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-blue-800 mb-4">Part A: Gemini ASR Process</h3>
          
          <div className="space-y-4">
            {/* Input */}
            <div className="bg-green-100 rounded p-3">
              <p className="font-semibold">📥 Audio Input</p>
              <p className="text-xs text-gray-600">WAV format, 16kHz, Mono</p>
            </div>

            {/* Preprocessing */}
            <div className="flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl mb-2">↓</div>
                <div className="bg-blue-200 rounded p-3">
                  <p className="font-semibold">Preprocessing for Gemini</p>
                  <div className="text-xs text-gray-600 mt-2 space-y-1">
                    <p>• Format: WAV (required)</p>
                    <p>• Method: File upload API</p>
                    <p>• Encoding: Binary file</p>
                    <p>• Duration check: No limit</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Gemini API Call */}
            <div className="bg-purple-100 rounded p-4">
              <p className="font-semibold text-purple-800 mb-3">🚀 Gemini API Call</p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Model</p>
                  <p className="text-xs text-gray-600">gemini-2.5-flash</p>
                  <p className="text-xs text-gray-500">(from GEMINI_STT_MODEL env var)</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Language</p>
                  <p className="text-xs text-gray-600">'vi' (Vietnamese)</p>
                </div>
                <div className="bg-white rounded p-2 col-span-2">
                  <p className="font-semibold">Prompt</p>
                  <p className="text-xs text-gray-600">
                    Enhanced Vietnamese-focused prompt<br/>
                    Emphasizes: tone marks, special consonants, proper nouns
                  </p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Method</p>
                  <p className="text-xs text-gray-600">genai.upload_file()</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Error Handling</p>
                  <p className="text-xs text-gray-600">
                    Quota exceeded → Skip (no fallback)<br/>
                    Retry: No (disabled)
                  </p>
                </div>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                From: vietnamese_transcriber.py:620-840
              </div>
            </div>

            {/* Output */}
            <div className="bg-green-100 rounded p-3">
              <p className="font-semibold">📤 Output: Vietnamese Transcript</p>
              <div className="text-xs text-gray-600 mt-2">
                <p>• Format: Plain text string</p>
                <p>• Post-processing: Basic cleaning</p>
                <p>• Confidence: Not returned by Gemini</p>
              </div>
            </div>
          </div>
        </div>

        {/* Part B: Linguistic Features */}
        <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-purple-800 mb-4">Part B: Linguistic Feature Extraction</h3>
          
          <div className="space-y-4">
            {/* Input */}
            <div className="bg-green-100 rounded p-3">
              <p className="font-semibold">📥 Input: Vietnamese Transcript</p>
              <p className="text-xs text-gray-600">Plain text from Gemini ASR</p>
            </div>

            {/* Feature Categories */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Lexical */}
              <div className="bg-white border-2 border-blue-300 rounded-lg p-4">
                <h4 className="font-bold text-blue-800 mb-3">1. Lexical Features</h4>
                <div className="space-y-2 text-sm">
                  <div className="bg-blue-50 rounded p-2">
                    <p className="font-semibold">TTR (Type-Token Ratio)</p>
                    <p className="text-xs text-gray-600">Formula: n_unique_words / n_total_words</p>
                  </div>
                  <div className="bg-blue-50 rounded p-2">
                    <p className="font-semibold">MATTR</p>
                    <p className="text-xs text-gray-600">Moving Average TTR (window=50)</p>
                  </div>
                  <div className="bg-blue-50 rounded p-2">
                    <p className="font-semibold">Word Frequency</p>
                    <p className="text-xs text-gray-600">Distribution analysis</p>
                  </div>
                  <div className="bg-blue-50 rounded p-2">
                    <p className="font-semibold">Average Word Length</p>
                    <p className="text-xs text-gray-600">Mean characters per word</p>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  From: linguistic_analyzer.py:187
                </div>
              </div>

              {/* Syntactic */}
              <div className="bg-white border-2 border-green-300 rounded-lg p-4">
                <h4 className="font-bold text-green-800 mb-3">2. Syntactic Features</h4>
                <div className="space-y-2 text-sm">
                  <div className="bg-green-50 rounded p-2">
                    <p className="font-semibold">Sentence Segmentation</p>
                    <p className="text-xs text-gray-600">VnCoreNLP or underthesea</p>
                  </div>
                  <div className="bg-green-50 rounded p-2">
                    <p className="font-semibold">MLU (Mean Length Utterance)</p>
                    <p className="text-xs text-gray-600">Words per sentence</p>
                  </div>
                  <div className="bg-green-50 rounded p-2">
                    <p className="font-semibold">POS Tag Distribution</p>
                    <p className="text-xs text-gray-600">VnCoreNLP POS tags</p>
                  </div>
                  <div className="bg-green-50 rounded p-2">
                    <p className="font-semibold">Dependency Parsing</p>
                    <p className="text-xs text-gray-600">If available</p>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  From: linguistic_analyzer.py:319
                </div>
              </div>

              {/* Semantic */}
              <div className="bg-white border-2 border-orange-300 rounded-lg p-4">
                <h4 className="font-bold text-orange-800 mb-3">3. Semantic Features</h4>
                <div className="space-y-2 text-sm">
                  <div className="bg-orange-50 rounded p-2">
                    <p className="font-semibold">Word Embeddings</p>
                    <p className="text-xs text-gray-600">PhoBERT (if use_phobert=True)</p>
                  </div>
                  <div className="bg-orange-50 rounded p-2">
                    <p className="font-semibold">Sentence Embeddings</p>
                    <p className="text-xs text-gray-600">Mean pooling of word embeddings</p>
                  </div>
                  <div className="bg-orange-50 rounded p-2">
                    <p className="font-semibold">Coherence Score</p>
                    <p className="text-xs text-gray-600">
                      Formula: mean(cos_sim(sent[i], sent[i+1]))<br/>
                      Method: Cosine similarity
                    </p>
                  </div>
                  <div className="bg-orange-50 rounded p-2">
                    <p className="font-semibold">Idea Density</p>
                    <p className="text-xs text-gray-600">Propositions per 10 words</p>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  From: linguistic_analyzer.py:444
                </div>
              </div>

              {/* Vietnamese-Specific */}
              <div className="bg-white border-2 border-red-300 rounded-lg p-4">
                <h4 className="font-bold text-red-800 mb-3">4. Vietnamese-Specific Features</h4>
                <div className="space-y-2 text-sm">
                  <div className="bg-red-50 rounded p-2">
                    <p className="font-semibold">Classifiers</p>
                    <p className="text-xs text-gray-600">Count of classifier words (cái, con, chiếc)</p>
                  </div>
                  <div className="bg-red-50 rounded p-2">
                    <p className="font-semibold">Tense Markers</p>
                    <p className="text-xs text-gray-600">đã, sẽ, đang, vừa, sắp</p>
                  </div>
                  <div className="bg-red-50 rounded p-2">
                    <p className="font-semibold">Aspect Markers</p>
                    <p className="text-xs text-gray-600">xong, được, hết, mất</p>
                  </div>
                  <div className="bg-red-50 rounded p-2">
                    <p className="font-semibold">Reduplications</p>
                    <p className="text-xs text-gray-600">Pattern detection</p>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  From: linguistic_analyzer.py:552
                </div>
              </div>
            </div>

            {/* Pragmatic/Discourse */}
            <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4">
              <h4 className="font-bold text-yellow-800 mb-3">5. Pragmatic/Discourse Features</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Repetition Detection</p>
                  <p className="text-xs text-gray-600">N-gram based</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Filler Words</p>
                  <p className="text-xs text-gray-600">ừ, ờ, à, thì, etc.</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Hesitation Markers</p>
                  <p className="text-xs text-gray-600">If tracked</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="font-semibold">Information Units</p>
                  <p className="text-xs text-gray-600">Proposition counting</p>
                </div>
              </div>
            </div>

            {/* Output */}
            <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4">
              <h3 className="font-bold text-red-800 mb-2">📤 OUTPUT</h3>
              <div className="text-sm text-gray-700">
                <p><strong>Total Features:</strong> ~50+ features</p>
                <p><strong>Format:</strong> Dict[str, float]</p>
                <p><strong>Prefixes:</strong> lex_*, syn_*, sem_*, vi_*</p>
                <p className="mt-3 text-xs text-gray-500">
                  Stored in: result['linguistic_features']<br/>
                  Libraries: VnCoreNLP, underthesea, PhoBERT (transformers)
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-100 rounded p-4 text-xs text-gray-600">
          <p className="font-semibold mb-2">📝 Implementation Notes:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Gemini ASR: No fallback when quota exceeded (disabled Whisper fallback)</li>
            <li>Linguistic analysis: Graceful fallback if VnCoreNLP unavailable (uses underthesea)</li>
            <li>PhoBERT: Optional, only if transformers available</li>
            <li>All features normalized and cleaned for JSON serialization</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

