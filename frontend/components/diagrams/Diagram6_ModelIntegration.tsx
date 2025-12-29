"use client";

import React from 'react';

/**
 * Diagram 6: Model Integration & Final Decision
 * 
 * Based on actual implementation in:
 * - backend/app.py: /auto-transcribe endpoint (ML scoring removed)
 * - backend/services/mmse_scoring_service.py: Rule-based scoring
 * 
 * Date: 2025-12-28
 * 
 * NOTE: ML model scoring has been REMOVED. Only GPT evaluation and rule-based scoring remain.
 */

export default function Diagram6ModelIntegration() {
  return (
    <div className="diagram-container p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">Model Integration & Final Decision</h2>
      
      <div className="space-y-6">
        {/* Feature Fusion */}
        <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-4">
          <h3 className="font-bold text-blue-800 mb-3">🔗 Feature Fusion</h3>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Acoustic</p>
              <p className="text-xs text-gray-600">~100 features</p>
              <p className="text-xs text-gray-500">From Diagram 3</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Linguistic</p>
              <p className="text-xs text-gray-600">~50 features</p>
              <p className="text-xs text-gray-500">From Diagram 4</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">GPT Evaluation</p>
              <p className="text-xs text-gray-600">Analysis + Feedback</p>
              <p className="text-xs text-gray-500">From Diagram 5</p>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-600">
            <p><strong>Concatenation Method:</strong> Dict merge (Python dict.update())</p>
            <p><strong>Total Features:</strong> ~150 features</p>
            <p><strong>Format:</strong> Dict[str, float] (no array concatenation needed)</p>
          </div>
        </div>

        {/* Feature Engineering - REMOVED */}
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4">
          <h3 className="font-bold text-yellow-800 mb-2">⚠️ Feature Engineering</h3>
          <p className="text-sm text-gray-700">
            <strong>Status:</strong> Not applied in current pipeline
          </p>
          <p className="text-xs text-gray-600 mt-2">
            Features stored as-is for SHAP analysis<br/>
            No feature selection, scaling, or dimensionality reduction
          </p>
        </div>

        {/* ML Models Pipeline - REMOVED */}
        <div className="bg-red-50 border-2 border-red-400 rounded-lg p-4">
          <h3 className="font-bold text-red-800 mb-2">❌ ML Models Pipeline</h3>
          <p className="text-sm text-gray-700 mb-2">
            <strong>Status:</strong> REMOVED from pipeline
          </p>
          <div className="bg-white rounded p-3 text-xs text-gray-600">
            <p className="font-semibold mb-2">Removed Components:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>ML model predictions (predict_cognitive_score)</li>
              <li>Fusion scoring (weighted combination)</li>
              <li>Random Forest, XGBoost models</li>
              <li>Ensemble methods</li>
            </ul>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            From: app.py lines 638-804 (removed)
          </p>
        </div>

        {/* Rule-Based Scoring */}
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
          <h3 className="font-bold text-green-800 mb-3">✅ Rule-Based Scoring (Current)</h3>
          <div className="space-y-3 text-sm">
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Source</p>
              <p className="text-xs text-gray-600">
                mmse_audio_questions_standardized.json<br/>
                Each question has explicit scoring rules
              </p>
            </div>
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Process</p>
              <div className="text-xs text-gray-600 space-y-1">
                <p>1. Load question data from JSON</p>
                <p>2. GPT-4o validates answer (is_correct)</p>
                <p>3. Apply rule-based scoring:</p>
                <ul className="list-disc list-inside ml-4 mt-1">
                  <li>Binary: points if correct, 0 if wrong</li>
                  <li>Multi-element: Count matched words (e.g., 3-word recall)</li>
                  <li>Partial credit: If logic_based_scoring enabled</li>
                </ul>
              </div>
            </div>
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Example</p>
              <div className="text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded">
                {`Question: "Hôm nay là thứ mấy?"
Points: 1
Rule: Đúng = 1 điểm; Sai = 0 điểm
GPT validation: is_correct = true
→ Score: 1 point`}
              </div>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            From: services/mmse_scoring_service.py
          </div>
        </div>

        {/* Final Output */}
        <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4">
          <h3 className="font-bold text-red-800 mb-2">📤 Final Output Package</h3>
          <div className="space-y-3 text-sm">
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Structure</p>
              <div className="text-xs font-mono bg-gray-50 p-2 rounded">
                {`{
  "success": true,
  "transcription": {...},
  "audio_features": {
    "f0_contour": {...},  // Raw arrays for SHAP
    "egemaps_*": {...},
    ...
  },
  "linguistic_features": {
    "lex_*": {...},
    "syn_*": {...},
    ...
  },
  "gpt_evaluation": {
    "analysis": "...",
    "feedback": "...",
    "is_correct": true/false
  },
  "language": "vi",
  "timestamp": "ISO format"
}`}
              </div>
            </div>
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Note</p>
              <p className="text-xs text-gray-600">
                <strong>No MMSE score in /auto-transcribe endpoint</strong><br/>
                Score calculated separately in chatbot service using rule-based method<br/>
                Final score = sum of all question scores (0-30)
              </p>
            </div>
          </div>
        </div>

        {/* SHAP Explainability */}
        <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-4">
          <h3 className="font-bold text-purple-800 mb-3">🔍 SHAP Explainability (Future)</h3>
          <div className="space-y-2 text-sm">
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Purpose</p>
              <p className="text-xs text-gray-600">
                Explain clinical risk assessments<br/>
                Feature importance for MCI/dementia prediction
              </p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Available Data</p>
              <p className="text-xs text-gray-600">
                ✅ All acoustic features (including raw F0 contour)<br/>
                ✅ All linguistic features<br/>
                ✅ Stored in result['audio_features'] and result['linguistic_features']
              </p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Status</p>
              <p className="text-xs text-gray-600">
                Features ready for SHAP analysis<br/>
                Implementation pending (requires trained model)
              </p>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-100 rounded p-4 text-xs text-gray-600">
          <p className="font-semibold mb-2">📝 Implementation Notes:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>ML model scoring completely removed from pipeline</li>
            <li>Only rule-based scoring from JSON remains</li>
            <li>GPT-4o used for validation only, not scoring</li>
            <li>Features stored for future SHAP analysis</li>
            <li>No ensemble or voting methods</li>
            <li>Final MMSE score calculated by summing question scores</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

