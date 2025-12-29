"use client";

import React from 'react';
import Diagram1SystemOverview from '@/components/diagrams/Diagram1_SystemOverview';
import Diagram2DataFlow from '@/components/diagrams/Diagram2_DataFlow';
import Diagram3AcousticFeatures from '@/components/diagrams/Diagram3_AcousticFeatures';
import Diagram4ASRLinguistic from '@/components/diagrams/Diagram4_ASRLinguistic';
import Diagram5GPT4oEvaluation from '@/components/diagrams/Diagram5_GPT4oEvaluation';
import Diagram6ModelIntegration from '@/components/diagrams/Diagram6_ModelIntegration';

export default function DiagramsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            System Architecture Diagrams
          </h1>
          <p className="text-gray-600">
            Complete technical documentation of MMSE Assessment System
          </p>
        </div>

        <div className="space-y-12">
          {/* Diagram 1 */}
          <section id="diagram-1" className="scroll-mt-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-700">Diagram 1: Overall System Architecture</h2>
              <p className="text-sm text-gray-500">High-level overview of the complete system</p>
            </div>
            <Diagram1SystemOverview />
          </section>

          {/* Diagram 2 */}
          <section id="diagram-2" className="scroll-mt-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-700">Diagram 2: Complete Data Flow Pipeline</h2>
              <p className="text-sm text-gray-500">End-to-end data processing flow</p>
            </div>
            <Diagram2DataFlow />
          </section>

          {/* Diagram 3 */}
          <section id="diagram-3" className="scroll-mt-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-700">Diagram 3: Acoustic Feature Extraction (Detailed)</h2>
              <p className="text-sm text-gray-500">Comprehensive acoustic analysis pipeline</p>
            </div>
            <Diagram3AcousticFeatures />
          </section>

          {/* Diagram 4 */}
          <section id="diagram-4" className="scroll-mt-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-700">Diagram 4: ASR + Linguistic Feature Extraction</h2>
              <p className="text-sm text-gray-500">Gemini ASR and Vietnamese NLP analysis</p>
            </div>
            <Diagram4ASRLinguistic />
          </section>

          {/* Diagram 5 */}
          <section id="diagram-5" className="scroll-mt-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-700">Diagram 5: GPT-4o Evaluation Module</h2>
              <p className="text-sm text-gray-500">Answer validation and feedback generation</p>
            </div>
            <Diagram5GPT4oEvaluation />
          </section>

          {/* Diagram 6 */}
          <section id="diagram-6" className="scroll-mt-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-700">Diagram 6: Model Integration & Final Decision</h2>
              <p className="text-sm text-gray-500">Feature fusion and scoring system</p>
            </div>
            <Diagram6ModelIntegration />
          </section>
        </div>

        {/* Navigation */}
        <div className="fixed bottom-8 right-8 bg-white rounded-lg shadow-lg p-4">
          <h3 className="font-semibold mb-2 text-sm">Quick Navigation</h3>
          <div className="space-y-1 text-xs">
            <a href="#diagram-1" className="block hover:text-blue-600">1. System Overview</a>
            <a href="#diagram-2" className="block hover:text-blue-600">2. Data Flow</a>
            <a href="#diagram-3" className="block hover:text-blue-600">3. Acoustic Features</a>
            <a href="#diagram-4" className="block hover:text-blue-600">4. ASR + Linguistic</a>
            <a href="#diagram-5" className="block hover:text-blue-600">5. GPT-4o Evaluation</a>
            <a href="#diagram-6" className="block hover:text-blue-600">6. Model Integration</a>
          </div>
        </div>
      </div>
    </div>
  );
}

