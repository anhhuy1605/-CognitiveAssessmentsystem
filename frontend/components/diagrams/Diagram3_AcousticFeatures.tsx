"use client";

import React from 'react';

/**
 * Diagram 3: Acoustic Feature Extraction Block (DETAILED)
 * 
 * Based on actual implementation in:
 * - backend/modules/acoustic_analyzer.py (lines 705-803): extract_all_features()
 * - backend/modules/acoustic_analyzer.py: extract_egemaps() (line 96)
 * - backend/modules/acoustic_analyzer.py: extract_f0_contour() (line 185)
 * - backend/modules/acoustic_analyzer.py: extract_voice_quality() (line 300)
 * 
 * Date: 2025-12-28
 */

export default function Diagram3AcousticFeatures() {
  return (
    <div className="diagram-container p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">Acoustic Feature Extraction (Detailed)</h2>
      
      <div className="space-y-6">
        {/* Input */}
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
          <h3 className="font-bold text-green-800 mb-2">📥 INPUT</h3>
          <div className="text-sm text-gray-700">
            <p><strong>Preprocessed Audio:</strong> WAV format</p>
            <p><strong>Sampling Rate:</strong> 16,000 Hz (16kHz)</p>
            <p><strong>Channels:</strong> Mono</p>
            <p><strong>Duration:</strong> Variable (typically 1-30 seconds)</p>
            <p className="text-xs mt-2 text-gray-500">From: audio_preprocessor.py</p>
          </div>
        </div>

        {/* Processing Steps */}
        <div className="space-y-4">
          {/* eGeMAPS */}
          <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-4">
            <h3 className="font-bold text-blue-800 mb-3">📊 1. eGeMAPS Features (88 features)</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Library</p>
                <p className="text-xs text-gray-600">openSMILE</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Feature Set</p>
                <p className="text-xs text-gray-600">eGeMAPSv02</p>
              </div>
              <div className="bg-white rounded p-2 col-span-2">
                <p className="font-semibold">Categories</p>
                <p className="text-xs text-gray-600">
                  Frequency (F0, F1-F3), Energy, Spectral, Temporal, Voice Quality
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: acoustic_analyzer.py:96 (extract_egemaps)
            </div>
          </div>

          {/* F0 Contour */}
          <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-4">
            <h3 className="font-bold text-purple-800 mb-3">📈 2. F0 Contour Features (Pitch Analysis)</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Library</p>
                <p className="text-xs text-gray-600">Parselmouth (Praat)</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Method</p>
                <p className="text-xs text-gray-600">Autocorrelation</p>
              </div>
              <div className="bg-white rounded p-2 col-span-2">
                <p className="font-semibold">Raw Data</p>
                <p className="text-xs text-gray-600">
                  f0_values[]: Array of F0 values (Hz)<br/>
                  timestamps[]: Array of time points (seconds)
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Statistics</p>
                <p className="text-xs text-gray-600">
                  Mean, Std, Range, CV<br/>
                  5th/95th percentile<br/>
                  Skewness, Kurtosis
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Voicing</p>
                <p className="text-xs text-gray-600">
                  Voiced frames count<br/>
                  Voiced ratio
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: acoustic_analyzer.py:185 (extract_f0_contour)<br/>
              Formula: F0 = autocorrelation(signal, min_pitch=75Hz, max_pitch=500Hz)
            </div>
          </div>

          {/* Voice Quality */}
          <div className="bg-indigo-50 border-2 border-indigo-500 rounded-lg p-4">
            <h3 className="font-bold text-indigo-800 mb-3">🔊 3. Voice Quality Features</h3>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Jitter</p>
                <p className="text-xs text-gray-600">
                  Local: %<br/>
                  Local (absolute): ms<br/>
                  RAP, PPQ5, DDP
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Shimmer</p>
                <p className="text-xs text-gray-600">
                  Local: %<br/>
                  Local (dB): dB<br/>
                  APQ3, APQ5, APQ11
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">HNR</p>
                <p className="text-xs text-gray-600">
                  Harmonics-to-Noise Ratio<br/>
                  Mean HNR (dB)
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: acoustic_analyzer.py:300 (extract_voice_quality)<br/>
              Library: Parselmouth (Praat)
            </div>
          </div>

          {/* Pause Statistics */}
          <div className="bg-teal-50 border-2 border-teal-500 rounded-lg p-4">
            <h3 className="font-bold text-teal-800 mb-3">⏸️ 4. Pause Statistics</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Detection Method</p>
                <p className="text-xs text-gray-600">Energy-based VAD</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Threshold</p>
                <p className="text-xs text-gray-600">-40 dB (default)</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Metrics</p>
                <p className="text-xs text-gray-600">
                  Mean pause duration<br/>
                  Total pause time<br/>
                  Pause count<br/>
                  Pause ratio
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Formula</p>
                <p className="text-xs text-gray-600">
                  Pause_ratio = Σ(pause_durations) / total_duration
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: acoustic_analyzer.py:450 (extract_pause_statistics)
            </div>
          </div>

          {/* Speaking Rate */}
          <div className="bg-orange-50 border-2 border-orange-500 rounded-lg p-4">
            <h3 className="font-bold text-orange-800 mb-3">⏱️ 5. Speaking Rate</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Calculation</p>
                <p className="text-xs text-gray-600">
                  Requires transcript<br/>
                  Syllables/second
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Formula</p>
                <p className="text-xs text-gray-600">
                  Speaking_rate = n_syllables / duration
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: acoustic_analyzer.py:550 (extract_speaking_rate)
            </div>
          </div>

          {/* Tone Analysis */}
          <div className="bg-pink-50 border-2 border-pink-500 rounded-lg p-4">
            <h3 className="font-bold text-pink-800 mb-3">🇻🇳 6. Vietnamese Tone Flattening Analysis</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Tones</p>
                <p className="text-xs text-gray-600">
                  6 tones: ngang, huyền, sắc, hỏi, ngã, nặng
                </p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="font-semibold">Features</p>
                <p className="text-xs text-gray-600">
                  Tone slope analysis<br/>
                  Contour flattening detection
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              From: acoustic_analyzer.py:650 (analyze_tone_flattening)<br/>
              Vietnamese-specific biomarker for MCI
            </div>
          </div>
        </div>

        {/* Output */}
        <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4">
          <h3 className="font-bold text-red-800 mb-2">📤 OUTPUT</h3>
          <div className="text-sm text-gray-700">
            <p><strong>Total Features:</strong> ~100+ features</p>
            <p><strong>Format:</strong> Dict[str, float]</p>
            <p><strong>Key Structure:</strong></p>
            <div className="bg-white rounded p-3 mt-2 text-xs font-mono">
              {`{
  "egemaps_*": 88 features,
  "f0_contour": {
    "f0_values": [...],  // Raw array
    "timestamps": [...], // Raw array
    "f0_mean": float,
    "f0_std": float,
    ...
  },
  "f0_*": 10+ metrics,
  "vq_*": 15+ features,
  "pause_*": 8+ features,
  "rate_*": 3+ features,
  "tone_*": 5+ features
}`}
            </div>
            <p className="mt-3 text-xs text-gray-500">
              Stored in: result['audio_features']<br/>
              For SHAP: All features + raw F0 contour arrays
            </p>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-100 rounded p-4 text-xs text-gray-600">
          <p className="font-semibold mb-2">📝 Implementation Details:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Preprocessing: webm → wav conversion required before extraction</li>
            <li>Libraries: openSMILE (eGeMAPS), Parselmouth (F0, VQ), librosa (audio I/O)</li>
            <li>F0 contour includes raw arrays for visualization and SHAP analysis</li>
            <li>All features cleaned for JSON (NaN → None) before serialization</li>
            <li>Error handling: Graceful fallback if library unavailable</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

