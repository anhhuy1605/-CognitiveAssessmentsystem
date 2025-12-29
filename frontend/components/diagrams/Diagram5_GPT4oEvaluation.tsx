"use client";

import React from 'react';

/**
 * Diagram 5: GPT-4o Evaluation Module
 * 
 * Based on actual implementation in:
 * - backend/app.py: evaluate_with_gpt4o() function
 * 
 * Date: 2025-12-28
 */

export default function Diagram5GPT4oEvaluation() {
  return (
    <div className="diagram-container p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">GPT-4o Evaluation Module</h2>
      
      <div className="space-y-6">
        {/* Input */}
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
          <h3 className="font-bold text-green-800 mb-2">📥 INPUT</h3>
          <div className="text-sm text-gray-700 space-y-2">
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Transcript</p>
              <p className="text-xs text-gray-600">Vietnamese text from Gemini ASR</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Question Context</p>
              <p className="text-xs text-gray-600">Current MMSE question text</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Language</p>
              <p className="text-xs text-gray-600">'vi' (Vietnamese)</p>
            </div>
          </div>
        </div>

        {/* Prompt Engineering */}
        <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-4">
          <h3 className="font-bold text-blue-800 mb-3">📝 Prompt Engineering</h3>
          <div className="space-y-3 text-sm">
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">System Prompt</p>
              <p className="text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded">
                "You are an MMSE answer validator for Vietnamese language."
              </p>
            </div>
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">User Prompt Structure</p>
              <div className="text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded">
                {`QUESTION: {question_text}
EXPECTED ANSWER: {expected_answer}
ACCEPTABLE VARIATIONS: {acceptable_answers}
USER TRANSCRIPT: {user_transcript}

Task: Determine if the user's answer matches.`}
              </div>
            </div>
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Output Format</p>
              <p className="text-xs text-gray-600">JSON only (response_format: json_object)</p>
            </div>
            <div className="bg-white rounded p-3">
              <p className="font-semibold mb-2">Rules</p>
              <ul className="text-xs text-gray-600 list-disc list-inside space-y-1">
                <li>Lenient with Vietnamese accent marks</li>
                <li>Allow synonyms if listed</li>
                <li>Ignore filler words (ừ, à, thì)</li>
                <li>Focus on semantic match</li>
              </ul>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            From: app.py:evaluate_with_gpt4o()
          </div>
        </div>

        {/* GPT-4o API Call */}
        <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-4">
          <h3 className="font-bold text-purple-800 mb-3">🚀 GPT-4o API Call</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Model</p>
              <p className="text-xs text-gray-600">gpt-4o</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">API</p>
              <p className="text-xs text-gray-600">OpenAI ChatCompletion</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Response Format</p>
              <p className="text-xs text-gray-600">JSON object</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Temperature</p>
              <p className="text-xs text-gray-600">Default (0.7)</p>
            </div>
            <div className="bg-white rounded p-2 col-span-2">
              <p className="font-semibold">Error Handling</p>
              <p className="text-xs text-gray-600">
                Try-except with fallback<br/>
                Returns default dict on error
              </p>
            </div>
          </div>
        </div>

        {/* Output Processing */}
        <div className="bg-indigo-50 border-2 border-indigo-500 rounded-lg p-4">
          <h3 className="font-bold text-indigo-800 mb-3">⚙️ Output Processing</h3>
          <div className="space-y-2 text-sm">
            <div className="bg-white rounded p-2">
              <p className="font-semibold">JSON Parsing</p>
              <p className="text-xs text-gray-600">json.loads(response.choices[0].message.content)</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Validation</p>
              <p className="text-xs text-gray-600">Check required fields exist</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="font-semibold">Structure</p>
              <div className="text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded mt-1">
                {`{
  "analysis": string,
  "feedback": string,
  "is_correct": bool (for validation)
}`}
              </div>
            </div>
          </div>
        </div>

        {/* Output */}
        <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4">
          <h3 className="font-bold text-red-800 mb-2">📤 OUTPUT</h3>
          <div className="text-sm text-gray-700">
            <p><strong>Format:</strong> Dict[str, Any]</p>
            <p><strong>Fields:</strong></p>
            <div className="bg-white rounded p-3 mt-2 text-xs font-mono">
              {`{
  "analysis": "Detailed analysis in Vietnamese",
  "feedback": "User-friendly feedback",
  "is_correct": true/false,  // For validation only
  // Note: No scores (vocabulary_score, etc. removed)
}`}
            </div>
            <p className="mt-3 text-xs text-gray-500">
              Stored in: result['gpt_evaluation']<br/>
              Full JSON logged to console for debugging<br/>
              No scoring - only validation and feedback
            </p>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-100 rounded p-4 text-xs text-gray-600">
          <p className="font-semibold mb-2">📝 Implementation Notes:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>GPT-4o used ONLY for answer validation, NOT for scoring</li>
            <li>All score generation removed (vocabulary_score, context_relevance_score, overall_score)</li>
            <li>Full evaluation result logged to console for debugging</li>
            <li>Error handling: Returns safe default dict if API fails</li>
            <li>No rate limiting implemented</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

