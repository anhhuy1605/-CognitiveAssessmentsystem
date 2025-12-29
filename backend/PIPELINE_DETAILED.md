# MMSE Assessment Pipeline - Chi Tiết Tổng Thể

**Date:** 2025-12-28  
**Version:** Current Implementation  
**Based on:** Actual codebase analysis

---

## 📋 Tổng Quan Pipeline

Pipeline xử lý đánh giá MMSE từ audio input đến final score, bao gồm:
1. Audio preprocessing
2. ASR (Speech-to-Text)
3. Acoustic feature extraction
4. Linguistic feature extraction
5. GPT-4o evaluation
6. Rule-based scoring
7. Results storage

---

## 🔄 Pipeline Chi Tiết

### **BƯỚC 1: Audio Input & Preprocessing**

**Input:**
- Format: `.webm`, `.wav`, `.mp3` (từ browser MediaRecorder hoặc file upload)
- Sampling rate: Variable
- Channels: Mono hoặc Stereo

**Preprocessing:**
```python
# Location: backend/app.py:4205
processed_path = ensure_wav_mono_16k(audio_path)
```

**Xử lý:**
1. Convert format: `.webm` → `.wav` (nếu cần)
2. Resample: → 16,000 Hz (16kHz)
3. Convert channels: → Mono
4. Normalization: Audio level adjustment

**Output:**
- File: `*.wav`, 16kHz, Mono
- Ready for feature extraction

**Code Reference:**
- `backend/modules/audio_preprocessor.py`: `preprocess_audio_for_analysis()`
- `backend/app.py:4205`: `ensure_wav_mono_16k()`

---

### **BƯỚC 2: Parallel Processing (3 Branches)**

#### **Branch 2A: ASR (Speech-to-Text)**

**Service:** Gemini API  
**Model:** `gemini-2.5-flash`  
**Language:** `'vi'` (Vietnamese)

**Process:**
```python
# Location: backend/vietnamese_transcriber.py:620-840
transcription_result = vietnamese_transcriber.transcribe_audio_file(
    processed_path, 
    target_lang='vi', 
    use_gpt=False, 
    question=question_context
)
```

**Steps:**
1. Load Gemini API key from `config.env` (hot-reload)
2. Upload audio file to Gemini API (`genai.upload_file()`)
3. Call Gemini with Vietnamese-focused prompt
4. Extract transcript from response
5. Basic cleaning (remove extra spaces, normalize)

**Error Handling:**
- Quota exceeded → Skip transcription, return error
- No fallback (Whisper disabled)
- Returns: `"Không có lời thoại"` if failed

**Output:**
- Vietnamese transcript (plain text string)
- Example: `"hôm nay là thứ bảy"`

**Code Reference:**
- `backend/vietnamese_transcriber.py:620`: `transcribe_audio_file()`
- Model: `gemini-2.5-flash` (from `GEMINI_STT_MODEL` env var)

---

#### **Branch 2B: Acoustic Feature Extraction**

**Module:** `AcousticAnalyzer`  
**Libraries:** openSMILE, Parselmouth (Praat), librosa

**Process:**
```python
# Location: backend/modules/acoustic_analyzer.py:705
analyzer = AcousticAnalyzer()
audio_features = analyzer.extract_all_features(processed_path, transcript=transcript_text)
```

**Features Extracted:**

1. **eGeMAPS Features (88 features)**
   - Library: openSMILE
   - Feature set: eGeMAPSv02
   - Categories:
     - Frequency: F0, F1-F3 statistics
     - Energy: RMS, energy statistics
     - Spectral: MFCC 1-13, spectral flux, centroid, rolloff
     - Temporal: Duration, speaking rate
     - Voice quality: Jitter, Shimmer, HNR

2. **F0 Contour Features**
   - Library: Parselmouth (Praat)
   - Method: Autocorrelation
   - Raw data:
     - `f0_values[]`: Array of F0 values (Hz)
     - `timestamps[]`: Array of time points (seconds)
   - Statistics:
     - Mean, Std, Range, CV
     - 5th/95th percentile
     - Skewness, Kurtosis
     - Voiced frames count, voiced ratio

3. **Voice Quality Features (15+ features)**
   - Jitter: Local, Local (absolute), RAP, PPQ5, DDP
   - Shimmer: Local (%), Local (dB), APQ3, APQ5, APQ11
   - HNR: Harmonics-to-Noise Ratio (dB)

4. **Pause Statistics (8+ features)**
   - Detection: Energy-based VAD (threshold: -40 dB)
   - Metrics:
     - Mean pause duration
     - Total pause time
     - Pause count
     - Pause ratio = Σ(pause_durations) / total_duration

5. **Speaking Rate (3+ features)**
   - Calculation: Requires transcript
   - Formula: `Speaking_rate = n_syllables / duration`
   - Metrics: Syllables/second, words/second

6. **Vietnamese Tone Analysis (5+ features)**
   - 6 tones: ngang, huyền, sắc, hỏi, ngã, nặng
   - Tone slope analysis
   - Contour flattening detection (MCI biomarker)

**Output:**
- Total: ~100+ features
- Format: `Dict[str, float]`
- Structure:
  ```python
  {
    "egemaps_*": 88 features,
    "f0_contour": {
      "f0_values": [...],  # Raw array
      "timestamps": [...],  # Raw array
      "f0_mean": float,
      "f0_std": float,
      ...
    },
    "f0_*": 10+ metrics,
    "vq_*": 15+ features,
    "pause_*": 8+ features,
    "rate_*": 3+ features,
    "tone_*": 5+ features
  }
  ```

**Code Reference:**
- `backend/modules/acoustic_analyzer.py:705`: `extract_all_features()`
- `backend/modules/acoustic_analyzer.py:96`: `extract_egemaps()`
- `backend/modules/acoustic_analyzer.py:185`: `extract_f0_contour()`
- `backend/modules/acoustic_analyzer.py:300`: `extract_voice_quality()`

---

#### **Branch 2C: Linguistic Feature Extraction**

**Module:** `VietnameseLinguisticAnalyzer`  
**Libraries:** underthesea, PhoBERT (transformers)  
**Note:** VnCoreNLP removed - using underthesea + PhoBERT only

**Process:**
```python
# Location: backend/modules/linguistic_analyzer.py:838
# No vncorenlp_path parameter - only uses underthesea + PhoBERT
linguistic_analyzer = VietnameseLinguisticAnalyzer(use_phobert=True)
linguistic_features = linguistic_analyzer.extract_all_features(transcript_text)
```

**Features Extracted:**

1. **Lexical Features**
   - **TTR (Type-Token Ratio)**
     - Formula: `TTR = n_unique_words / n_total_words`
     - Range: 0-1 (higher = richer vocabulary)
   - **MATTR (Moving Average TTR)**
     - Window: 50 words
     - More stable than simple TTR
   - **Brunet's Index**
     - Formula: `W = N^(V^(-0.165))`
     - Lower = richer vocabulary
   - **Word Frequency Distribution**
   - **Average Word Length**
   - **Pronoun Ratio** (MCI indicator: increases)

2. **Syntactic Features**
   - **Sentence Segmentation**
     - Tool: underthesea
   - **MLU (Mean Length Utterance)**
     - Words per sentence
   - **POS Tag Distribution**
     - underthesea POS tags: NOUN, VERB, ADJ, ADV, PRON, etc.
     - (Backward compatible with VnCoreNLP format: N, V, A, R, P)
   - **Clause Density**
     - Conjunction markers analysis

3. **Semantic Features**
   - **Word Embeddings**
     - Model: PhoBERT (if `use_phobert=True`)
     - Dimension: 768
   - **Sentence Embeddings**
     - Method: Mean pooling of word embeddings
   - **Coherence Score**
     - Formula: `mean(cos_sim(sent[i], sent[i+1]))`
     - Method: Cosine similarity between consecutive sentences
   - **Idea Density**
     - Propositions per 10 words

4. **Vietnamese-Specific Features**
   - **Classifiers**
     - Count: cái, con, chiếc, etc.
   - **Tense Markers**
     - đã, sẽ, đang, vừa, sắp, hãy, chưa, rồi
   - **Aspect Markers**
     - xong, được, hết, mất, ra, vào, lên, xuống
   - **Reduplications**
     - Pattern detection

5. **Pragmatic/Discourse Features**
   - **Repetition Detection**
     - N-gram based
   - **Filler Words**
     - ừ, ờ, à, thì, etc.
   - **Hesitation Markers** (if tracked)
   - **Information Units**
     - Proposition counting

**Output:**
- Total: ~50+ features
- Format: `Dict[str, float]`
- Prefixes: `lex_*`, `syn_*`, `sem_*`, `vi_*`

**Code Reference:**
- `backend/modules/linguistic_analyzer.py:838`: `extract_all_features()`
- `backend/modules/linguistic_analyzer.py:187`: `extract_lexical_features()`
- `backend/modules/linguistic_analyzer.py:319`: `extract_syntactic_features()`
- `backend/modules/linguistic_analyzer.py:444`: `extract_semantic_features()`

**Note:** 
- Tokenization: `underthesea.word_tokenize()`
- POS tagging: `underthesea.pos_tag()`
- Semantic embeddings: PhoBERT (`vinai/phobert-base`)
- No VnCoreNLP dependency

---

### **BƯỚC 3: GPT-4o Evaluation**

**Purpose:** Answer validation (NOT scoring)  
**Model:** `gpt-4o`

**Process:**
```python
# Location: backend/app.py:1765
gpt_evaluation = evaluate_with_gpt4o(transcript_text, question, language='vi')
```

**Prompt Structure:**
```
System: "You are an MMSE answer validator. Only validate answers, do not provide scores."

User Prompt:
- Question: {question_text}
- Transcript: {user_transcript}
- Word count: {word_count}

Task: Only analyze and provide feedback on answer relevance. DO NOT provide scores.

Output Format (JSON):
{
  "analysis": "DETAILED_ANALYSIS_IN_VIETNAMESE",
  "feedback": "IMPROVEMENT_SUGGESTIONS_IF_NEEDED",
  "transcript_info": {
    "word_count": int,
    "is_short_transcript": bool
  }
}
```

**API Call:**
```python
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    temperature=0.2,
    max_tokens=500,
    response_format={"type": "json_object"}
)
```

**Output:**
```python
{
  "analysis": "Phân tích chi tiết về mức độ phù hợp của câu trả lời",
  "feedback": "Gợi ý cải thiện nếu cần",
  "transcript_info": {
    "word_count": int,
    "is_short_transcript": bool
  }
}
```

**Note:** 
- ❌ NO scores (vocabulary_score, context_relevance_score, overall_score removed)
- ✅ Only validation and feedback

**Code Reference:**
- `backend/app.py:1765`: `evaluate_with_gpt4o()`
- `backend/app.py:4297`: GPT evaluation call in pipeline

---

### **BƯỚC 4: Feature Concatenation**

**Process:**
```python
# Location: backend/app.py:4321-4329
result = {
    'success': True,
    'transcription': transcription_result,
    'audio_features': audio_features,      # ~100+ features
    'linguistic_features': linguistic_features,  # ~50+ features
    'gpt_evaluation': gpt_evaluation,
    'language': language,
    'timestamp': datetime.now().isoformat()
}
```

**Method:**
- Dict merge (Python `dict.update()`)
- No array concatenation needed
- Total: ~150 features stored separately

**NaN/Inf Cleaning:**
```python
# Location: backend/app.py:4344
def clean_for_json(obj):
    """Recursively clean NaN, Inf, and other non-serializable values"""
    # Converts NaN → None, Inf → None
    # Converts numpy types → native Python types
```

**Code Reference:**
- `backend/app.py:4321-4344`: Result assembly and cleaning

---

### **BƯỚC 5: Rule-Based Scoring**

**Service:** `MMSEScoringService`  
**Source:** `mmse_audio_questions_standardized.json`

**Process:**
```python
# Location: backend/services/mmse_scoring_service.py:92
scorer = MMSEScoringService()
score_result = scorer.score_answer(question_id, transcript)
```

**Scoring Logic:**

1. **Load Question Data**
   ```python
   question_data = scorer.get_question_data(question_id)
   # From: mmse_audio_questions_standardized.json
   ```

2. **GPT Validation**
   ```python
   validation = validate_answer_with_gpt(question_data, transcript)
   # Returns: {"is_correct": bool, "matched_elements": [...], "explanation": "..."}
   ```

3. **Apply Scoring Rules**

   **Binary Scoring:**
   ```python
   if 'scoring_details' not in question_data:
       return max_points if validation['is_correct'] else 0
   ```

   **Multi-Element Scoring (e.g., 3-word recall):**
   ```python
   if 'scoring_details' in question_data:
       matched = validation.get('matched_elements', [])
       score = sum(scoring_details[element] for element in matched)
       return min(score, max_points)
   ```

   **Example:**
   - Question: "Nhắc lại 3 từ: Con mèo, Chiếc xe, Cây lúa"
   - Points: 3 (1 point per word)
   - User says: "con mèo, xe, cây lúa"
   - Matched: ["Con mèo", "Chiếc xe", "Cây lúa"]
   - Score: 3 points

4. **Calculate Total MMSE Score**
   ```python
   total_score = sum(question_scores.values())  # 0-30
   ```

**Output:**
```python
{
    "points_earned": int,      # Points for this question
    "points_possible": int,    # Max points for this question
    "is_correct": bool,
    "feedback": str,
    "total_score": int         # Cumulative score (0-30)
}
```

**Code Reference:**
- `backend/services/mmse_scoring_service.py:92`: `score_answer()`
- `backend/mmse_audio_questions_standardized.json`: Question definitions

---

### **BƯỚC 6: Results Storage**

**Storage Locations:**

1. **Backend Memory (Session-based)**
   ```python
   # Location: backend/services/mmse_chatbot_api.py:344
   state.acoustic_features[question_id] = audio_features
   state.linguistic_features[question_id] = linguistic_features
   state.answers[question_id] = {
       'transcript': transcript,
       'score': score_result['points_earned'],
       'acoustic_features': audio_features
   }
   ```

2. **Frontend Database (PostgreSQL/Neon)**
   ```python
   # Location: frontend/app/api/save-cognitive-assessment-results/route.ts
   # Via: /api/save-cognitive-assessment-results endpoint
   {
       'sessionId': session_id,
       'finalMmseScore': total_score,
       'questionResults': question_results_json,
       'audioFeatures': audio_features_json,
       'linguisticFeatures': linguistic_features_json,
       ...
   }
   ```

3. **Backend File System**
   ```python
   # Location: backend/services/mmse_chatbot_api.py:415
   result_file = os.path.join(results_dir, f"{session_id}.json")
   with open(result_file, 'w', encoding='utf-8') as f:
       json.dump(full_data, f, ensure_ascii=False, indent=2)
   ```

**Final Result Structure:**
```python
{
    "success": True,
    "transcription": {
        "transcript": "hôm nay là thứ bảy",
        "confidence": 0.95
    },
    "audio_features": {
        "f0_contour": {
            "f0_values": [...],  # Raw array for SHAP
            "timestamps": [...],
            "f0_mean": 150.5,
            ...
        },
        "egemaps_*": {...},  # 88 features
        "vq_*": {...},       # 15+ features
        ...
    },
    "linguistic_features": {
        "lex_ttr": 0.65,
        "lex_mattr": 0.62,
        "syn_mlu": 8.5,
        "sem_coherence": 0.78,
        ...
    },
    "gpt_evaluation": {
        "analysis": "...",
        "feedback": "...",
        "is_correct": true
    },
    "score": {
        "points_earned": 1,
        "points_possible": 1,
        "total_score": 10,
        "feedback": "Đúng rồi!"
    },
    "timestamp": "2025-12-28T10:30:00"
}
```

---

## 🔄 Complete Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    AUDIO INPUT (.webm)                      │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  AUDIO PREPROCESSING │
        │  - webm → wav        │
        │  - Resample: 16kHz   │
        │  - Mono channel      │
        └──────────┬────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
┌─────────────────────┐  ┌─────────────────────────────────┐
│ GEMINI ASR ✅       │  │ ACOUSTIC ANALYZER ✅            │
│ - Speech→Text       │  │ - 117 acoustic features         │
│ - Vietnamese        │  │ - eGeMAPS (88)                  │
│ - Model: gemini-2.5 │  │ - F0/Pitch (10)                │
│   -flash            │  │ - Pause (8)                     │
└──────────┬──────────┘  │ - Tone (6)                      │
           │             │ - Voice quality (5)             │
           │             └────────────┬────────────────────┘
           │                          │
           ▼                          │
┌─────────────────────────────────────┴────────────────────┐
│              TRANSCRIPT + ACOUSTIC FEATURES              │
└──────────────────┬──────────────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
┌────────────────────┐  ┌─────────────────────────────────┐
│ GPT-4O EVAL ✅     │  │ LINGUISTIC ANALYZER ✅          │
│ - Validation only  │  │ - 42 linguistic features        │
│ - Answer feedback  │  │ - underthesea + PhoBERT        │
│ - NO scoring       │  │ - Lexical (TTR, MATTR)          │
└──────────┬─────────┘  │ - Syntactic (MLU, POS)          │
           │             │ - Semantic (coherence)          │
           │             │ - Vietnamese-specific           │
           │             └────────────┬────────────────────┘
           │                          │
           │                          │
           ▼                          ▼
┌─────────────────────────────────────┴────────────────────┐
│         FEATURES + GPT EVALUATION + TRANSCRIPT            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  RULE-BASED SCORING  │
        │  - Load from JSON    │
        │  - Apply rules        │
        │  - Calculate points   │
        │  - Sum MMSE (0-30)    │
        └──────────┬────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
┌────────────────────┐  ┌─────────────────────────────────┐
│ RESULTS STORAGE ✅ │  │ SHAP EXPLAINABILITY ✅         │
│ - Session state    │  │ - Feature contributions        │
│ - Frontend DB      │  │ - Human-readable explanations  │
│ - Backend files    │  │ - Visualizations              │
└────────────────────┘  │ - Reports (PDF/HTML)          │
                        └────────────┬────────────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                        ▼                         ▼
              ┌──────────────────┐  ┌──────────────────────┐
              │   FINAL OUTPUT   │  │  SHAP DASHBOARD      │
              │ - MMSE Score /30 │  │ - Risk assessment   │
              │ - Transcript     │  │ - Recommendations   │
              │ - Features       │  │ - Visualizations    │
              │ - GPT feedback   │  │ - Reports           │
              └──────────────────┘  └──────────────────────┘
```

---

## 📊 Data Dimensions

| Stage | Data Type | Dimensions | Format |
|-------|-----------|------------|--------|
| Input Audio | Audio signal | Variable | .webm, .wav, .mp3 |
| Preprocessed | Audio signal | 16kHz, Mono | .wav |
| Transcript | Text | Variable length | String |
| Acoustic Features | Feature vector | ~100+ features | Dict[str, float] |
| Linguistic Features | Feature vector | ~50+ features | Dict[str, float] |
| GPT Evaluation | JSON | 3 fields | Dict[str, Any] |
| Final Score | Integer | 0-30 | int |

---

## ⚙️ Configuration

**Environment Variables:**
- `GEMINI_API_KEY`: Gemini API key (hot-reloaded from `config.env`)
- `GEMINI_STT_MODEL`: Model name (default: `gemini-2.5-flash`)
- `OPENAI_API_KEY`: OpenAI API key for GPT-4o
- `DATABASE_URL`: PostgreSQL connection string

**Key Parameters:**
- Audio sample rate: 16,000 Hz
- F0 extraction: min_pitch=75Hz, max_pitch=500Hz
- Pause detection threshold: -40 dB
- MATTR window: 50 words
- GPT temperature: 0.2
- GPT max_tokens: 500

---

## 🚫 Removed Components

**ML Model Scoring:**
- ❌ Random Forest model
- ❌ XGBoost model
- ❌ Ensemble methods
- ❌ Fusion scoring (weighted combination)
- ❌ ML-based MMSE prediction

**Reason:** Replaced with rule-based scoring from JSON

**NLP Libraries:**
- ❌ VnCoreNLP (removed)
- ✅ underthesea (for tokenization/POS tagging)
- ✅ PhoBERT (for semantic embeddings)

**Current Status:**
- ✅ Rule-based scoring only
- ✅ GPT-4o for validation (not scoring)
- ✅ Features stored for SHAP analysis (future use)

---

## 📝 Code References

**Main Pipeline:**
- `backend/app.py:4200-4350`: `/auto-transcribe` endpoint
- `backend/services/mmse_chatbot_api.py:144`: `/submit` endpoint

**Modules:**
- `backend/modules/acoustic_analyzer.py`: Acoustic features
- `backend/modules/linguistic_analyzer.py`: Linguistic features (underthesea + PhoBERT)
- `backend/vietnamese_transcriber.py`: ASR (Gemini)
- `backend/services/mmse_scoring_service.py`: Rule-based scoring
- `backend/modules/shap_explainer.py`: SHAP explainability
- `backend/modules/explanation_generator.py`: Human-readable explanations
- `backend/modules/shap_visualizations.py`: Visualizations
- `backend/modules/report_generator.py`: PDF/HTML reports

**Data:**
- `backend/mmse_audio_questions_standardized.json`: Question definitions

---

## 🔍 Error Handling

1. **Audio Preprocessing Failure**
   - Fallback: Return default features
   - Log: Warning message

2. **ASR Failure (Gemini quota exceeded)**
   - Action: Skip transcription
   - Return: `"Không có lời thoại"`
   - No fallback (Whisper disabled)

3. **Feature Extraction Failure**
   - Fallback: Return empty dict `{}`
   - Log: Warning message
   - Pipeline continues

4. **GPT Evaluation Failure**
   - Fallback: Return default result
   - Log: Error message
   - Pipeline continues

5. **Scoring Failure**
   - Fallback: Return 0 points
   - Log: Error message

---

## 📈 Performance Metrics

**Typical Processing Times:**
- Audio preprocessing: ~0.5s
- ASR (Gemini): ~2-5s
- Acoustic features: ~1-3s
- Linguistic features: ~0.5-2s
- GPT evaluation: ~1-3s
- **Total: ~5-15s per question**

**Bottlenecks:**
- Gemini API latency (network)
- GPT-4o API latency (network)
- Feature extraction (CPU-intensive)

---

## ✅ Current Status

**Implemented:**
- ✅ Audio preprocessing
- ✅ Gemini ASR
- ✅ Acoustic feature extraction
- ✅ Linguistic feature extraction (underthesea + PhoBERT)
- ✅ GPT-4o evaluation (validation only)
- ✅ Rule-based scoring
- ✅ Results storage
- ✅ SHAP explainability (implemented)
- ✅ SHAP visualizations
- ✅ SHAP reports (PDF/HTML)

**Removed:**
- ❌ ML model scoring
- ❌ Whisper fallback
- ❌ GPT score generation
- ❌ VnCoreNLP (replaced with underthesea)

**Future:**
- 🔄 Clinical risk assessment (features ready)

---

**Last Updated:** 2025-12-28  
**Based on:** Actual codebase implementation


