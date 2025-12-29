# System Architecture Diagrams

This directory contains 6 professional block diagrams documenting the MMSE Assessment System architecture.

## Diagrams Overview

### Diagram 1: Overall System Architecture
**File:** `Diagram1_SystemOverview.tsx`  
**Description:** High-level overview showing input, processing modules, scoring system, and output layers.  
**Key Files Referenced:**
- `frontend/app/(main)/mmse-chatbot/page.tsx`: Frontend UI
- `backend/app.py`: Main backend API
- `backend/services/mmse_chatbot_api.py`: Chatbot service

### Diagram 2: Complete Data Flow Pipeline
**File:** `Diagram2_DataFlow.tsx`  
**Description:** End-to-end data flow from audio input to final output, showing parallel processing branches.  
**Key Files Referenced:**
- `backend/app.py` (lines 4200-4350): `/auto-transcribe` endpoint
- `backend/modules/acoustic_analyzer.py`: `extract_all_features()`
- `backend/modules/linguistic_analyzer.py`: `extract_all_features()`
- `backend/vietnamese_transcriber.py`: `transcribe_audio_file()`

### Diagram 3: Acoustic Feature Extraction (Detailed)
**File:** `Diagram3_AcousticFeatures.tsx`  
**Description:** Comprehensive breakdown of acoustic feature extraction methods and libraries.  
**Key Files Referenced:**
- `backend/modules/acoustic_analyzer.py` (line 705): `extract_all_features()`
- `backend/modules/acoustic_analyzer.py` (line 96): `extract_egemaps()`
- `backend/modules/acoustic_analyzer.py` (line 185): `extract_f0_contour()`
- `backend/modules/acoustic_analyzer.py` (line 300): `extract_voice_quality()`
- `backend/modules/acoustic_analyzer.py` (line 450): `extract_pause_statistics()`

**Actual Features Extracted:**
- eGeMAPS: 88 features (openSMILE)
- F0 Contour: Raw arrays + 10+ statistics (Parselmouth/Praat)
- Voice Quality: 15+ features (Jitter, Shimmer, HNR)
- Pause Statistics: 8+ features
- Speaking Rate: 3+ features
- Tone Analysis: 5+ features (Vietnamese-specific)

### Diagram 4: ASR + Linguistic Feature Extraction
**File:** `Diagram4_ASRLinguistic.tsx`  
**Description:** Detailed Gemini ASR process and Vietnamese linguistic feature extraction.  
**Key Files Referenced:**
- `backend/vietnamese_transcriber.py` (line 620): `transcribe_audio_file()`
- `backend/modules/linguistic_analyzer.py` (line 187): `extract_lexical_features()`
- `backend/modules/linguistic_analyzer.py` (line 319): `extract_syntactic_features()`
- `backend/modules/linguistic_analyzer.py` (line 444): `extract_semantic_features()`
- `backend/modules/linguistic_analyzer.py` (line 552): `extract_vietnamese_specific_features()`

**Actual ASR Details:**
- Model: `gemini-2.5-flash` (from `GEMINI_STT_MODEL` env var)
- Method: File upload API (`genai.upload_file()`)
- Language: `'vi'` (Vietnamese)
- Error Handling: Quota exceeded → Skip (no fallback)

**Actual Linguistic Features:**
- Lexical: TTR, MATTR, word frequency, average word length
- Syntactic: MLU, sentence length, POS tags, dependency parsing
- Semantic: Coherence (cosine similarity), idea density, embeddings (PhoBERT)
- Vietnamese-Specific: Classifiers, tense markers, aspect markers, reduplications

### Diagram 5: GPT-4o Evaluation Module
**File:** `Diagram5_GPT4oEvaluation.tsx`  
**Description:** GPT-4o answer validation and feedback generation.  
**Key Files Referenced:**
- `backend/app.py`: `evaluate_with_gpt4o()` function

**Actual Implementation:**
- Model: `gpt-4o`
- Purpose: Answer validation only (NOT scoring)
- Output: `analysis`, `feedback`, `is_correct`
- Removed: All score generation (vocabulary_score, context_relevance_score, overall_score)

### Diagram 6: Model Integration & Final Decision
**File:** `Diagram6_ModelIntegration.tsx`  
**Description:** Feature fusion, scoring system, and final output structure.  
**Key Files Referenced:**
- `backend/app.py`: `/auto-transcribe` endpoint (ML scoring removed)
- `backend/services/mmse_scoring_service.py`: Rule-based scoring

**Important Notes:**
- ML model scoring has been REMOVED from pipeline
- Only rule-based scoring from JSON remains
- Features stored for SHAP analysis (future use)
- Final MMSE score = sum of question scores (0-30)

## Viewing the Diagrams

Access all diagrams at: `http://localhost:3000/diagrams`

Or import individual components:
```tsx
import Diagram2DataFlow from '@/components/diagrams/Diagram2_DataFlow';
```

## Regenerating Diagrams

All diagrams are React/TSX components. To modify:

1. Edit the corresponding `.tsx` file in `frontend/components/diagrams/`
2. Changes will hot-reload in development
3. Diagrams are responsive and styled with Tailwind CSS

## Code References

All diagrams include:
- Actual file paths and line numbers
- Real parameter values from code
- Actual library names and versions
- True implementation details (not assumptions)

## Date & Version

- Created: 2025-12-28
- Based on: Current codebase implementation
- Status: All diagrams reflect actual code (not theoretical)

