# 🔧 FIX: Tích hợp Acoustic Analysis vào MMSE Chatbot

## ❌ Vấn đề hiện tại:

MMSE Chatbot chỉ sử dụng **linguistic analysis**, bỏ qua **acoustic analysis**!

### Files cần sửa:

1. **`backend/services/mmse_chatbot_service.py`**
2. **`backend/services/mmse_chatbot_api.py`**

---

## ✅ Giải pháp:

### **1. Update `mmse_chatbot_service.py`:**

#### **A. Thêm acoustic analyzer trong `__init__`:**

```python
def __init__(self, questions_path: Optional[str] = None):
    """Initialize chatbot service"""
    # ... existing code ...
    
    # Initialize linguistic analyzer from MCI modules
    self.linguistic_analyzer = None
    try:
        from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
        self.linguistic_analyzer = VietnameseLinguisticAnalyzer(use_phobert=True)
        logger.info("✅ Linguistic Analyzer integrated")
    except ImportError as e:
        logger.warning(f"⚠️ Linguistic Analyzer not available: {e}")
    
    # ADD THIS: Initialize acoustic analyzer
    self.acoustic_analyzer = None
    try:
        from modules.acoustic_analyzer import AcousticAnalyzer
        self.acoustic_analyzer = AcousticAnalyzer()
        logger.info("✅ Acoustic Analyzer integrated")
    except ImportError as e:
        logger.warning(f"⚠️ Acoustic Analyzer not available: {e}")
    
    # ADD THIS: Initialize MCI service for full integration
    self.mci_service = None
    try:
        from modules.integration_service import MCIScreeningService
        self.mci_service = MCIScreeningService(use_phobert=True)
        logger.info("✅ MCI Screening Service integrated")
    except ImportError as e:
        logger.warning(f"⚠️ MCI Service not available: {e}")
```

#### **B. Update `SessionState` dataclass để lưu acoustic features:**

```python
@dataclass
class SessionState:
    session_id: str
    greeting: str = ""
    current_domain: TestDomain = TestDomain.INIT
    current_question_index: int = 0
    
    # Responses by domain
    responses: Dict[str, List[QuestionResponse]] = field(default_factory=dict)
    
    # ADD THIS: Acoustic features by question
    acoustic_features: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # ... rest of fields ...
```

#### **C. Update `submit_answer()` để extract acoustic features:**

```python
def submit_answer(self, session_id: str, answer: str, 
                 audio_file: Optional[str] = None,
                 confidence: float = 1.0) -> Tuple[str, Dict]:
    """Submit answer for current question"""
    state = self.get_session(session_id)
    if not state:
        return "Lỗi: Không tìm thấy phiên làm việc", {}
    
    domain = state.current_domain
    index = state.current_question_index
    
    # Create response record
    questions = self._get_domain_questions(domain.value)
    if questions and index < len(questions):
        question = questions[index]
        question_text = self._replace_greeting(question.get("question_text", ""), state.greeting)
    else:
        question_text = ""
    
    response = QuestionResponse(
        question_id=f"{domain.value}_{index}",
        question_text=question_text,
        user_answer=answer,
        timestamp=datetime.now().isoformat(),
        audio_file=audio_file,
        transcription_confidence=confidence,
        domain=domain.value
    )
    
    # ADD THIS: Extract acoustic features if audio file provided
    if audio_file and self.acoustic_analyzer:
        try:
            logger.info(f"🔊 Extracting acoustic features for {audio_file}")
            acoustic_features = self.acoustic_analyzer.extract_all_features(
                audio_file, 
                transcript=answer
            )
            state.acoustic_features[f"{domain.value}_{index}"] = acoustic_features
            logger.info(f"✅ Extracted {len(acoustic_features)} acoustic features")
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract acoustic features: {e}")
    
    state.responses[domain.value].append(response)
    
    # ... rest of method ...
```

#### **D. Update `_complete_test()` để tính toán multimodal analysis:**

```python
def _complete_test(self, session_id: str) -> Tuple[str, Dict]:
    """Complete test and calculate scores"""
    state = self.get_session(session_id)
    if not state:
        return "Lỗi", {}
    
    # Calculate all scores NOW
    self._calculate_all_scores(state)
    
    # ADD THIS: Multimodal analysis with MCI service
    mci_result = None
    if self.mci_service and state.acoustic_features:
        try:
            # Aggregate all acoustic features
            all_acoustic = {}
            for question_id, features in state.acoustic_features.items():
                for key, value in features.items():
                    if key not in all_acoustic:
                        all_acoustic[key] = []
                    all_acoustic[key].append(value)
            
            # Average acoustic features
            avg_acoustic = {
                k: np.mean(v) if isinstance(v[0], (int, float)) else v[0]
                for k, v in all_acoustic.items()
            }
            
            # Collect all text
            all_text = []
            for domain_responses in state.responses.values():
                for response in domain_responses:
                    if response.user_answer:
                        all_text.append(response.user_answer)
            combined_text = " ".join(all_text)
            
            # Run full MCI analysis
            logger.info("🧬 Running multimodal MCI analysis...")
            # Note: MCI service needs audio file, so we might need to save aggregated features
            # For now, just extract linguistic features
            linguistic_features = state.linguistic_features
            
            # Estimate MCI probability based on features
            # This is a simplified version
            mci_result = {
                'acoustic_feature_count': len(avg_acoustic),
                'linguistic_feature_count': len(linguistic_features),
                'estimated_mci_probability': self._estimate_mci_probability(
                    avg_acoustic, linguistic_features, state.total_score
                )
            }
            
            logger.info(f"✅ MCI analysis: {mci_result['estimated_mci_probability']:.1%} probability")
            
        except Exception as e:
            logger.warning(f"⚠️ MCI analysis failed: {e}")
    
    # Get classification
    classification = self._classify_score(state.total_score or 0)
    state.classification = classification
    
    # Generate completion message (include MCI result if available)
    message = (
        f"🎉 Chúc mừng {state.greeting}! Chúng ta đã hoàn thành bài kiểm tra rồi!\n\n"
        f"**Kết quả MMSE sơ bộ của {state.greeting}:**\n"
        f"Tổng điểm: {state.total_score}/30\n"
        f"Phân loại: {classification}\n"
    )
    
    if mci_result:
        message += f"\n**Phân tích multimodal:**\n"
        message += f"Acoustic features: {mci_result['acoustic_feature_count']}\n"
        message += f"Linguistic features: {mci_result['linguistic_feature_count']}\n"
        message += f"MCI probability: {mci_result['estimated_mci_probability']:.1%}\n"
    
    message += f"\n**Chi tiết theo lĩnh vực:**\n"
    
    # ... rest of message generation ...
```

#### **E. Thêm helper method `_estimate_mci_probability()`:**

```python
def _estimate_mci_probability(self, acoustic_features: Dict, 
                               linguistic_features: Dict, 
                               mmse_score: int) -> float:
    """
    Estimate MCI probability from multimodal features
    Simplified version without trained model
    """
    # Rule-based estimation
    probability = 0.0
    
    # MMSE score component (strongest indicator)
    if mmse_score >= 24:
        probability += 0.1  # Low risk
    elif mmse_score >= 18:
        probability += 0.5  # Moderate risk
    else:
        probability += 0.8  # High risk
    
    # Acoustic indicators (if available)
    if acoustic_features:
        # F0 variability (low = potential indicator)
        f0_cv = acoustic_features.get('f0_f0_cv', 0.5)
        if f0_cv < 0.15:
            probability += 0.1
        
        # Voice quality (high jitter/shimmer = potential indicator)
        jitter = acoustic_features.get('vq_jitter_local', 0.01)
        if jitter > 0.02:
            probability += 0.05
        
        # Pause rate (high = potential indicator)
        pause_rate = acoustic_features.get('pause_pause_rate', 0.3)
        if pause_rate > 0.4:
            probability += 0.05
    
    # Linguistic indicators (if available)
    if linguistic_features:
        # Low TTR = potential indicator
        ttr = linguistic_features.get('lex_ttr', 0.7)
        if ttr < 0.5:
            probability += 0.1
        
        # Low word count = potential indicator
        word_count = linguistic_features.get('lex_total_words', 100)
        if word_count < 50:
            probability += 0.05
    
    # Normalize to [0, 1]
    return min(1.0, probability)
```

---

### **2. Update `mmse_chatbot_api.py`:**

No changes needed! API already passes `audio_file` to service.

---

## ✅ Sau khi sửa:

### **Pipeline hoàn chỉnh:**

```
MMSE Chatbot answer submission:
    ↓
Audio file uploaded
    ↓
┌─────────────────────────────────┐
│  1. TRANSCRIBE (Gemini ASR)     │
│     → transcript                │
└──────────────┬──────────────────┘
               │
               ├─────────────────────┬────────────────────┐
               │                     │                    │
               ▼                     ▼                    ▼
┌───────────────────────┐  ┌────────────────┐  ┌─────────────────┐
│ 2. ACOUSTIC ANALYSIS  │  │ 3. LINGUISTIC  │  │ 4. GPT-4O EVAL  │
│    117 features       │  │    42 features │  │    MMSE scoring │
│    (per question)     │  │    (per Q)     │  │                 │
└───────────────────────┘  └────────────────┘  └─────────────────┘
               │                     │                    │
               └─────────────────────┴────────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ 5. AT TEST END:      │
                          │    - Aggregate all   │
                          │    - Multimodal      │
                          │    - MCI prediction  │
                          └──────────────────────┘
```

---

## 🧪 Testing:

```bash
# 1. Sửa code theo hướng dẫn trên
# 2. Test
cd D:\CognitiveAssessmentsystem\backend
python -c "
from services.mmse_chatbot_service import MMSEChatbotService
service = MMSEChatbotService()
print('Acoustic analyzer:', service.acoustic_analyzer)
print('Linguistic analyzer:', service.linguistic_analyzer)
print('MCI service:', service.mci_service)
"

# 3. Test full flow
# Start backend → Test với frontend
```

---

**Priority:** HIGH - Cần sửa ngay để có multimodal analysis đầy đủ!

