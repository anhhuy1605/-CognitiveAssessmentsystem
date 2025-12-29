# MMSE Chatbot Pipeline v2.1_CORRECTED
## Complete Flow từ Input đến Output

---

## 📋 TỔNG QUAN PIPELINE

Pipeline xử lý đánh giá MMSE từ khi user nhập thông tin đến khi có kết quả cuối cùng, bao gồm:
1. **Session Initialization** - Khởi tạo session
2. **User Input Collection** - Thu thập thông tin người dùng
3. **Question Flow** - Luồng câu hỏi theo domain
4. **Answer Processing** - Xử lý câu trả lời
5. **Feature Extraction** - Trích xuất features (acoustic, linguistic)
6. **Scoring** - Tính điểm rule-based
7. **Multimodal Analysis** - Phân tích đa phương thức
8. **Result Generation** - Tạo kết quả cuối cùng

---

## 🔄 PIPELINE CHI TIẾT

### **BƯỚC 1: SESSION INITIALIZATION**

**Input:**
- User info: name, age, gender, education_years, city, district

**Process:**
```
1. Frontend: User điền form
   - Age: 40-100 (validation)
   - Education: 0-25 năm (validation)
   - Gender: male/female (select)
   - City: required text
   - District: required text

2. Frontend → Backend: POST /api/mmse-chatbot/session
   - Tạo session_id
   - Lưu user_info vào session state
   - Set greeting (Ông/Bà) dựa trên gender

3. Backend: MMSEChatbotService.create_session()
   - Tạo SessionState mới
   - Initialize domain_order
   - Set current_domain = INIT
```

**Output:**
- Session ID
- Greeting message với pronoun (Ông/Bà)
- Ready to start test

---

### **BƯỚC 2: GREETING & INTRODUCTION**

**Process:**
```
1. Backend: get_introduction_message()
   - Load từ JSON v2.1: questions.greeting.messages
   - 4 messages với {pronoun} và {Pronoun} placeholders
   - Format: "Xin chào {pronoun}! Tôi là trợ lý ảo..."

2. Frontend: Hiển thị greeting messages
   - User xác nhận sẵn sàng

3. Backend: start_test()
   - Chuyển domain từ INIT → ORIENTATION
   - Reset question_index = 0
```

**Output:**
- Greeting messages đã format
- Test ready to begin

---

### **BƯỚC 3: QUESTION FLOW (Domain-by-Domain)**

**Domain Order (v2.1_CORRECTED):**
1. **ORIENTATION** (10 points) - 10 questions
2. **REGISTRATION** (3 points) - 1 question (3 words)
3. **ATTENTION_CALCULATION** (5 points) - Serial 7s only
4. **EXECUTIVE_FUNCTION** (3 points) - Verbal fluency + Abstraction
5. **OPEN_QUESTIONS** (0 points) - Feature extraction only
6. **RECALL** (3 points) - Recall 3 words (delay ≥360s)
7. **LANGUAGE** (8 points) - Naming, repetition, comprehension, etc.
8. **VISUOSPATIAL** (3 points) - Clock Drawing Test

**Process cho mỗi question:**
```
1. Backend: get_current_question(session_id)
   - Load question từ JSON v2.1 structure
   - Replace {pronoun} và {Pronoun} placeholders
   - Handle dynamic answers (time, place)
   - Special handling:
     * Registration: instruction_part1 + instruction_part2
     * Serial 7s: Show instruction
     * Clock Drawing: Generate clock image
     * Verbal Fluency: Start timer

2. Frontend: Hiển thị question
   - User record audio hoặc type answer

3. Frontend → Backend: POST /api/mmse-chatbot/submit
   - answer: text transcript
   - audio_file: audio file (optional)
   - session_id: session ID
```

---

### **BƯỚC 4: ANSWER PROCESSING**

**Backend: submit_answer()**

**4.1. Special Handling:**

**Serial 7s (Auto-stop):**
```
- Extract number from answer
- Store in serial_7s_answers[]
- Check: if len(answers) >= 5 → Auto-stop
- Continue asking: "Lấy {value} trừ 7 bằng bao nhiêu?"
- After 5 answers: Move to next domain
```

**Verbal Fluency (60-second timer):**
```
- Start timer: verbal_fluency_start_time
- Extract animals from answer
- Track elapsed time
- Prompts:
  * 5s silence → "Còn con gì nữa không?"
  * 30s → "Rất tốt! Hãy tiếp tục nhé!"
  * 50s → "Còn 10 giây nữa!"
- After 60s: Score based on unique animal count
```

**Clock Drawing:**
```
- Generate clock image (11:10) if not exists
- Return base64 image + clock_data
- User describes or draws clock
- Validate: hour hand (11-12), minute hand (2)
- Score: Shulman 6-point → MMSE 3-point
```

**4.2. Real-time Scoring:**
```
- MMSEScoringService.score_answer(question_id, answer)
- Rule-based scoring từ JSON
- Store score in state.question_scores[question_id]
- Update state.total_score (0-35)
- NEVER reveal score during test
```

**4.3. Feature Extraction (if audio provided):**
```
Parallel processing:
├─ Acoustic Analyzer
│  └─ Extract: pause_rate, speech_rate, f0_variability, etc.
│  └─ Store in: state.acoustic_features[question_id]
│
└─ Linguistic Analyzer
   └─ Extract: TTR, MLU, idea_density, semantic_coherence, etc.
   └─ Store in: state.linguistic_features
```

**4.4. Domain Transition:**
```
- After last question in domain:
  ├─ Registration: Set recall_allowed_after (360s later)
  ├─ Move to next domain
  └─ Return next question
```

---

### **BƯỚC 5: TEST COMPLETION**

**Trigger:** Khi hoàn thành domain cuối cùng (VISUOSPATIAL)

**Process: _complete_test()**

**5.1. Calculate All Scores:**
```
- _calculate_all_scores(state)
- Aggregate domain_scores từ question_scores
- Total score = sum of all domain scores (0-35)
```

**5.2. Calculate Adjusted Score (v2.1):**
```
- Input: raw_score, age, education_years
- Age penalty: 0.2 × max(0, age - 60)
- Education bonus:
  * ≤9 years: 0
  * 10-12 years: +1
  * >12 years: +2
- Adjusted = Raw - AgePenalty + EduBonus
```

**5.3. Risk Classification:**
```
- get_risk_from_adjusted_score(adjusted_score, education_years)
- Education-specific cutoffs (35-point scale):
  * Low (≤9yr): ≥23=Ổn, 20-22=Nhẹ, <20=Cao
  * Medium (10-12yr): ≥28=Ổn, 24-27=Nhẹ, <24=Cao
  * High (>12yr): ≥31=Ổn, 28-30=Nhẹ, <28=Cao
```

**5.4. Multimodal MCI Analysis (v2.1):**
```
- Aggregate acoustic features (average across questions)
- Collect linguistic features
- calculate_multimodal_risk():
  ├─ MMSE risk (30% weight)
  ├─ Acoustic risk (30% weight)
  └─ Linguistic risk (40% weight)
- Combined risk score (0-1)
- Risk level: <0.4=Ổn, 0.4-0.7=Nhẹ, ≥0.7=Cao
```

**5.5. Generate Completion Message:**
```
Structure:
├─ Greeting: "🎉 Chúc mừng {pronoun}!"
├─ Summary intro
├─ Scores:
│  ├─ Raw MMSE: {raw}/35
│  ├─ Adjusted: {adjusted} (điều chỉnh theo tuổi và học vấn)
│  └─ Classification: {risk_level}
├─ Domain breakdown (7 domains)
├─ Multimodal analysis:
│  ├─ Acoustic features count
│  ├─ Linguistic features count
│  ├─ Risk components (MMSE/Acoustic/Linguistic %)
│  └─ Combined risk score
├─ Recommendations (theo risk level)
└─ Doctor-style SHAP explanation (nếu có)
```

---

### **BƯỚC 6: DOCTOR-STYLE SHAP EXPLANATION**

**Process:**
```
1. Extract SHAP values từ state.mci_result.risk_components
2. Map to feature names:
   - mmse → mmse_adjusted_score
   - acoustic → pause_ratio (representative)
   - linguistic → TTR (representative)
3. Add domain-specific SHAP values từ domain_scores
4. generate_doctor_style_explanation():
   ├─ Translate technical terms → patient-friendly
   ├─ Top 3 contributing factors
   ├─ Specific observations
   ├─ "What this means" explanation
   └─ Actionable recommendations
```

**Output:**
- Patient-friendly explanation
- No technical terms
- Doctor-like tone
- Specific advice based on weak areas

---

## 🔀 DECISION POINTS

### **1. ML Model vs Rule-Based Prediction**

**Location:** `backend/modules/mci_predictor.py:166-183`

```
if (model.is_trained AND sklearn_available):
    → Use ML Model (_ml_predict)
    → Gradient Boosting + Ridge Regression
else:
    → Use Rule-Based (_rule_based_predict)
    → Clinical heuristics
```

### **2. Recall Delay Check**

**Location:** `backend/services/mmse_chatbot_service.py:410-419`

```
if (current_domain == RECALL):
    if (time_since_registration < 360 seconds):
        → Return wait message
    else:
        → Continue with recall question
```

### **3. Serial 7s Auto-Stop**

**Location:** `backend/services/mmse_chatbot_service.py:517-550`

```
if (len(serial_7s_answers) >= 5):
    → Stop automatically
    → Score answers
    → Move to next domain
else:
    → Continue asking next number
```

---

## 📊 DATA FLOW

```
User Input
    ↓
Session Creation
    ↓
Question Flow (8 domains)
    ↓
Answer Processing
    ├─ Real-time Scoring (rule-based)
    ├─ Acoustic Feature Extraction
    └─ Linguistic Feature Extraction
    ↓
Test Completion
    ├─ Calculate Adjusted Score
    ├─ Risk Classification
    ├─ Multimodal Analysis
    └─ Generate Results
    ↓
Final Output
    ├─ Completion Message
    ├─ Domain Breakdown
    ├─ Multimodal Analysis
    ├─ Recommendations
    └─ SHAP Explanation
```

---

## 🎯 KEY FEATURES v2.1

1. **35-point scale** (up from 30)
2. **Age & Education adjustment** (formula-based)
3. **Education-specific cutoffs** (3 groups)
4. **Multimodal integration** (MMSE 30% + Acoustic 30% + Linguistic 40%)
5. **Pronoun system** (Ông/Bà throughout)
6. **Serial 7s auto-stop** (5 answers)
7. **Clock Drawing** (visual generation)
8. **Executive Function** (verbal fluency + abstraction)
9. **6-minute recall delay** (360 seconds)
10. **Doctor-style SHAP** (patient-friendly)

---

## ⏱️ TIMING REQUIREMENTS

- **Recall delay:** ≥360 seconds (6 minutes) from registration end
- **Verbal fluency:** Exactly 60 seconds timer
- **Serial 7s:** Auto-stop after 5 answers
- **Open questions:** Natural speech, no rush

---

## 🔄 STATE MANAGEMENT

**SessionState tracks:**
- Current domain & question index
- All responses & scores
- Acoustic & linguistic features
- Special states (Serial 7s, Verbal Fluency, Clock Drawing)
- MCI result (multimodal analysis)
- User info & timestamps

---

## 📝 OUTPUT FORMAT

**Completion Message includes:**
1. Greeting & summary
2. Raw & adjusted scores
3. 7-domain breakdown
4. Multimodal analysis (3 components)
5. Risk-specific recommendations
6. Doctor-style SHAP explanation

**Metadata includes:**
- All scores (raw, adjusted, domains)
- Risk level & classification
- MCI result (full multimodal data)
- Adjusted score components (age penalty, edu bonus)

---

## ✅ VALIDATION CHECKS

1. All 21 main questions attempted
2. Recall delay ≥360 seconds
3. Total score = sum of domain scores
4. Audio recordings exist for required questions
5. User_info complete (age, education_years, gender, city, district)

---

**Version:** v2.1_CORRECTED  
**Last Updated:** 2025-01-XX  
**Based on:** `mmse_audio_questions_standardized.json` v2.1_CORRECTED


