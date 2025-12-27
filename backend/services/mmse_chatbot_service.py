# -*- coding: utf-8 -*-
"""
MMSE Audio-First Chatbot Service
Based on Folstein et al. (1975) and Da Nang Hospital Protocol (2019)

This service implements a state machine for conducting MMSE tests via audio,
with proper addressee handling (ông/bà) and clinical protocol compliance.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import difflib
import numpy as np

logger = logging.getLogger(__name__)

# Import OpenAI client
try:
    from openai import OpenAI
    openai_client = None
    # Initialize OpenAI client if API key is available
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info("✅ OpenAI client initialized for MMSE scoring")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found - GPT-4o scoring will not be available")
except ImportError:
    logger.warning("⚠️ OpenAI library not available - GPT-4o scoring will not be available")
    openai_client = None


class TestDomain(Enum):
    """MMSE Test Domains following clinical protocol"""
    INIT = "init"
    ORIENTATION = "orientation"
    REGISTRATION = "registration"
    ATTENTION_CALCULATION = "attention_calculation"
    OPEN_QUESTIONS = "open_questions"  # Supplementary for linguistic analysis
    RECALL = "recall"
    LANGUAGE = "language"
    VISUOSPATIAL = "visuospatial"
    COMPLETED = "completed"


@dataclass
class QuestionResponse:
    """Single question response"""
    question_id: str
    question_text: str
    user_answer: str
    timestamp: str
    audio_file: Optional[str] = None
    transcription_confidence: float = 0.0
    score: Optional[int] = None  # Only calculated at end
    domain: str = ""
    

@dataclass
class SessionState:
    """Complete session state for MMSE test"""
    session_id: str
    greeting: str = ""  # "ông" or "bà"
    current_domain: TestDomain = TestDomain.INIT
    current_question_index: int = 0
    
    # Responses by domain
    responses: Dict[str, List[QuestionResponse]] = field(default_factory=dict)
    
    # Registration words - needed for Recall
    registration_words: List[str] = field(default_factory=lambda: ["Con mèo", "Chiếc xe", "Cây lúa"])
    registration_time: Optional[str] = None
    registration_repetitions: int = 0
    
    # Domain scores - only calculated at end
    domain_scores: Dict[str, int] = field(default_factory=dict)
    question_scores: Dict[str, int] = field(default_factory=dict)  # ✅ FIX: Store per-question scores
    total_score: Optional[int] = None
    classification: str = ""
    
    # Linguistic features (calculated from responses)
    linguistic_features: Dict[str, float] = field(default_factory=dict)
    
    # Acoustic features (per question)
    acoustic_features: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # MCI multimodal result (calculated at end)
    mci_result: Optional[Dict[str, Any]] = None
    
    # Timestamps
    started_at: str = ""
    completed_at: Optional[str] = None
    recall_allowed_after: Optional[str] = None  # 5 minutes after registration
    
    # User info
    user_info: Dict[str, Any] = field(default_factory=dict)


class MMSEChatbotService:
    """
    MMSE Audio-First Chatbot Service
    
    Implements clinical MMSE protocol via audio:
    - State machine for test flow
    - Addressee handling (ông/bà)
    - 5-minute delay enforcement for Recall
    - No individual score disclosure during test
    - Linguistic feature extraction (integrated with MCI modules)
    """
    
    def __init__(self, questions_path: Optional[str] = None):
        """Initialize chatbot service"""
        # Initialize scoring service
        try:
            from services.mmse_scoring_service import MMSEScoringService
            self.scoring_service = MMSEScoringService()
            logger.info("✅ MMSE Scoring Service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize scoring service: {e}")
            self.scoring_service = None
        self.questions_path = questions_path or os.path.join(
            os.path.dirname(__file__),
            "..",
            "mmse_audio_questions_standardized.json"
        )
        self.questions_data = self._load_questions()
        self.sessions: Dict[str, SessionState] = {}
        
        # Domain order (clinical protocol)
        self.domain_order = [
            TestDomain.ORIENTATION,
            TestDomain.REGISTRATION,
            TestDomain.ATTENTION_CALCULATION,
            TestDomain.OPEN_QUESTIONS,
            TestDomain.RECALL,
            TestDomain.LANGUAGE,
            TestDomain.VISUOSPATIAL,
        ]
        
        # Initialize linguistic analyzer from MCI modules
        self.linguistic_analyzer = None
        try:
            from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
            self.linguistic_analyzer = VietnameseLinguisticAnalyzer(use_phobert=True)
            logger.info("✅ Linguistic Analyzer integrated")
        except ImportError as e:
            logger.warning(f"⚠️ Linguistic Analyzer not available: {e}")
        
        # Initialize acoustic analyzer
        self.acoustic_analyzer = None
        try:
            from modules.acoustic_analyzer import AcousticAnalyzer
            self.acoustic_analyzer = AcousticAnalyzer()
            logger.info("✅ Acoustic Analyzer integrated")
        except ImportError as e:
            logger.warning(f"⚠️ Acoustic Analyzer not available: {e}")
        
        # Initialize MCI service for multimodal fusion
        self.mci_service = None
        try:
            from modules.integration_service import MCIScreeningService
            self.mci_service = MCIScreeningService(use_phobert=True)
            logger.info("✅ MCI Screening Service integrated")
        except ImportError as e:
            logger.warning(f"⚠️ MCI Service not available: {e}")
        
        logger.info("✅ MMSEChatbotService initialized with FULL multimodal support")
    
    def _load_questions(self) -> Dict:
        """Load questions from JSON file"""
        try:
            with open(self.questions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded MMSE questions from {self.questions_path}")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to load questions: {e}")
            return {}
    
    def create_session(self, session_id: str, user_info: Optional[Dict] = None) -> SessionState:
        """Create new MMSE test session"""
        state = SessionState(
            session_id=session_id,
            started_at=datetime.now().isoformat(),
            user_info=user_info or {},
            current_domain=TestDomain.INIT,  # Start at INIT state
            current_question_index=0
        )
        
        # Initialize response containers for each domain
        for domain in self.domain_order:
            state.responses[domain.value] = []
        
        self.sessions[session_id] = state
        logger.info(f"✅ Created session: {session_id}")
        return state
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def set_greeting(self, session_id: str, greeting: str) -> bool:
        """Set addressee term (ông/bà)"""
        state = self.get_session(session_id)
        if not state:
            return False
        
        # Normalize greeting
        greeting_lower = greeting.lower().strip()
        if "ông" in greeting_lower or "ong" in greeting_lower:
            state.greeting = "Ông"
        elif "bà" in greeting_lower or "ba" in greeting_lower:
            state.greeting = "Bà"
        else:
            # Default based on common usage
            state.greeting = "Anh/chị"
        
        logger.info(f"✅ Session {session_id}: Greeting set to '{state.greeting}'")
        return True
    
    def get_introduction_message(self) -> str:
        """Get chatbot introduction message - more natural and friendly"""
        return (
            "Chào bạn nhé! Mình là Cá Vàng, bạn bè ảo của bạn đây. "
            "Hôm nay chúng ta sẽ cùng nhau làm một bài kiểm tra nhỏ về trí nhớ và khả năng suy nghĩ thôi. "
            "Mình sẽ hỏi bạn vài câu hỏi đơn giản lắm, bạn chỉ cần trả lời bằng giọng nói bình thường là được. "
            "Đừng lo lắng gì cả, mình sẽ hướng dẫn bạn từng bước một cách nhẹ nhàng nhé!"
        )
    
    def get_greeting_question(self) -> str:
        """Get question to determine addressee term - more natural"""
        return "Để mình tiện xưng hô hơn, mình nên gọi bạn là Ông hay Bà nhỉ?"

    def get_ready_confirmation(self, session_id: str) -> str:
        """Get ready confirmation message - more natural"""
        state = self.get_session(session_id)
        greeting = state.greeting if state else "Bạn"
        return f"{greeting} đã sẵn sàng để bắt đầu bài kiểm tra chưa ạ?"
    
    def start_test(self, session_id: str) -> Tuple[str, Dict]:
        """Start the test and return first question"""
        state = self.get_session(session_id)
        if not state:
            return "Lỗi: Không tìm thấy phiên làm việc", {}
        
        state.current_domain = TestDomain.ORIENTATION
        state.current_question_index = 0
        
        return self.get_current_question(session_id)
    
    def get_current_question(self, session_id: str) -> Tuple[str, Dict]:
        """Get current question with metadata"""
        state = self.get_session(session_id)
        if not state:
            return "Lỗi: Không tìm thấy phiên làm việc", {}
        
        domain = state.current_domain
        index = state.current_question_index
        
        if domain == TestDomain.COMPLETED:
            return "Bài kiểm tra đã hoàn thành.", {"completed": True}
        
        # Get domain questions
        questions = self._get_domain_questions(domain.value)
        
        if not questions or index >= len(questions):
            # Move to next domain
            return self._advance_to_next_domain(session_id)
        
        question = questions[index]
        # ✅ FIX: Use chatbot_message from JSON (not question_text)
        question_text = self._replace_greeting(
            question.get("chatbot_message", question.get("question_text", "")), 
            state.greeting
        )
        
        # ✅ FIX: Only add separate instruction field for FIRST question in domain
        # Most questions already have instruction in chatbot_message, so we don't duplicate
        # Only add separate instruction if it exists AND it's the first question
        if index == 0:
            instruction = question.get("instruction", "")
            if instruction and instruction not in question_text:
                instruction = self._replace_greeting(instruction, state.greeting)
                question_text = f"{instruction}\n\n{question_text}"
        
        # ✅ FIX: Get actual question_id from JSON
        actual_question_id = question.get("question_id", f"{domain.value}_{index}")
        
        metadata = {
            "domain": domain.value,
            "question_index": index,
            "total_questions": len(questions),
            "question_id": actual_question_id,  # ✅ Use actual question_id from JSON
            "points": question.get("points", 1),
            "category": question.get("question_category", ""),
            "completed": False
        }
        
        # Special handling for Registration
        if domain == TestDomain.REGISTRATION:
            metadata["words"] = question.get("word_list", state.registration_words)
            metadata["instruction_after"] = self._replace_greeting(
                question.get("instruction_after", ""), state.greeting
            )
        
        # Check if Recall is allowed (5 min delay)
        if domain == TestDomain.RECALL:
            if not self._check_recall_allowed(state):
                remaining = self._get_recall_wait_time(state)
                return (
                    f"Vui lòng chờ thêm {remaining} giây trước khi tiếp tục phần nhớ lại.",
                    {"waiting_for_recall": True, "wait_seconds": remaining}
                )
        
        return question_text, metadata
    
    def submit_answer(self, session_id: str, answer: str, 
                     audio_file: Optional[str] = None,
                     confidence: float = 1.0) -> Tuple[str, Dict]:
        """
        Submit answer for current question
        
        Returns: (response_message, metadata)
        - NEVER reveals score during test
        - Returns neutral acknowledgment
        """
        state = self.get_session(session_id)
        if not state:
            return "Lỗi: Không tìm thấy phiên làm việc", {}
        
        domain = state.current_domain
        index = state.current_question_index
        
        # If session is in INIT state and user says ready, start the test
        if domain == TestDomain.INIT:
            if any(keyword in answer.lower() for keyword in ['sẵn sàng', 'sẵn sàng', 'có', 'ok', 'okay', 'bắt đầu', 'ready']):
                state.current_domain = TestDomain.ORIENTATION
                state.current_question_index = 0
                logger.info(f"✅ Test started for session {session_id}")
                return self.get_current_question(session_id)
            else:
                # User not ready yet, return encouragement message
                greeting = state.greeting if state.greeting else "bạn"
                return f"Không sao cả, {greeting} cứ từ từ. Khi nào {greeting} sẵn sàng, hãy cho tôi biết nhé!", {}
        
        # Create response record
        questions = self._get_domain_questions(domain.value)
        if questions and index < len(questions):
            question = questions[index]
            question_text = self._replace_greeting(question.get("question_text", ""), state.greeting)
        else:
            question_text = ""
        
        # ✅ FIX: Get actual question_id from JSON
        questions = self._get_domain_questions(domain.value)
        actual_question_id = f"{domain.value}_{index}"  # Default fallback
        if questions and index < len(questions):
            actual_question_id = questions[index].get("question_id", actual_question_id)
        
        response = QuestionResponse(
            question_id=actual_question_id,  # ✅ Use actual question_id
            question_text=question_text,
            user_answer=answer,
            timestamp=datetime.now().isoformat(),
            audio_file=audio_file,
            transcription_confidence=confidence,
            domain=domain.value
        )
        
        # ✅ REAL-TIME SCORING: Score answer immediately
        score_result = None
        if self.scoring_service:
            try:
                # Score the answer using actual question_id
                score_result = self.scoring_service.score_answer(actual_question_id, answer)
                
                # Store score in state
                state.question_scores[actual_question_id] = score_result['points_earned']
                
                # ✅ Calculate total score in real-time
                if state.total_score is None:
                    state.total_score = 0
                state.total_score += score_result['points_earned']
                
                logger.info(f"✅ Scored question {actual_question_id}: {score_result['points_earned']}/{score_result['points_possible']} → Total: {state.total_score}/30")
            except ValueError as ve:
                # Question not found in JSON - skip scoring for this question
                logger.warning(f"⚠️ Question {actual_question_id} not found in JSON: {ve}")
                score_result = {'points_earned': 0, 'points_possible': 0, 'is_correct': False, 'feedback': ''}
            except Exception as e:
                logger.error(f"❌ Scoring failed: {e}")
                import traceback
                traceback.print_exc()
                score_result = {'points_earned': 0, 'points_possible': 0, 'is_correct': False, 'feedback': ''}
        
        # Extract acoustic features if audio file provided (for risk assessment, not scoring)
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
        
        # Special handling for Registration
        if domain == TestDomain.REGISTRATION:
            state.registration_time = datetime.now().isoformat()
            # Set recall allowed time (5 minutes later)
            recall_time = datetime.now().timestamp() + 5 * 60
            state.recall_allowed_after = datetime.fromtimestamp(recall_time).isoformat()
            logger.info(f"✅ Registration completed. Recall allowed after {state.recall_allowed_after}")
        
        # Move to next question
        state.current_question_index += 1
        
        # Check if need to move to next domain
        questions = self._get_domain_questions(domain.value)
        if not questions or state.current_question_index >= len(questions):
            return self._advance_to_next_domain(session_id)
        
        # ✅ REAL-TIME: Get next question
        next_question, metadata = self.get_current_question(session_id)
        
        # ✅ REAL-TIME: Add score update to metadata
        if score_result:
            metadata['score_update'] = {
                'question_id': actual_question_id,
                'points_earned': score_result['points_earned'],
                'points_possible': score_result['points_possible'],
                'total_score': state.total_score or 0,
                'max_score': 30,
                'percentage': round(((state.total_score or 0) / 30) * 100, 1),
                'is_correct': score_result.get('is_correct', False),
                'feedback': score_result.get('feedback', '')
            }
        
        # Add progress info
        total_questions = sum(len(self._get_domain_questions(d.value)) for d in self.domain_order if d != TestDomain.OPEN_QUESTIONS)
        current_progress = sum(len(state.responses.get(d.value, [])) for d in self.domain_order if d != TestDomain.OPEN_QUESTIONS)
        metadata['progress'] = {
            'current': current_progress,
            'total': total_questions,
            'completed': False
        }
        
        return next_question, metadata
    
    def _advance_to_next_domain(self, session_id: str) -> Tuple[str, Dict]:
        """Advance to next domain"""
        state = self.get_session(session_id)
        if not state:
            return "Lỗi", {}
        
        current_idx = self.domain_order.index(state.current_domain)
        
        if current_idx + 1 >= len(self.domain_order):
            # Test completed
            state.current_domain = TestDomain.COMPLETED
            state.completed_at = datetime.now().isoformat()
            return self._complete_test(session_id)
        
        # Move to next domain
        next_domain = self.domain_order[current_idx + 1]
        state.current_domain = next_domain
        state.current_question_index = 0
        
        # Domain transition messages
        transition_messages = {
            TestDomain.REGISTRATION: f"Bây giờ {state.greeting} hãy ghi nhớ 3 từ mà tôi sắp đọc.",
            TestDomain.ATTENTION_CALCULATION: f"Bây giờ chúng ta sẽ làm một bài tập tính toán đơn giản.",
            TestDomain.OPEN_QUESTIONS: f"Bây giờ {state.greeting} hãy kể cho tôi nghe một số điều về cuộc sống hàng ngày.",
            TestDomain.RECALL: f"Bây giờ {state.greeting} hãy nhắc lại 3 từ mà tôi đã đọc lúc nãy.",
            TestDomain.LANGUAGE: f"Bây giờ chúng ta sẽ kiểm tra về ngôn ngữ.",
            TestDomain.VISUOSPATIAL: f"Cuối cùng, {state.greeting} hãy tưởng tượng một hình.",
        }
        
        transition = transition_messages.get(next_domain, "")
        next_question, metadata = self.get_current_question(session_id)
        
        if transition:
            return f"{transition}\n\n{next_question}", metadata
        return next_question, metadata
    
    def _complete_test(self, session_id: str) -> Tuple[str, Dict]:
        """Complete test and calculate scores"""
        state = self.get_session(session_id)
        if not state:
            return "Lỗi", {}
        
        # Calculate all scores NOW
        self._calculate_all_scores(state)
        
        # Perform multimodal MCI analysis using NEW MCIScreeningService
        if self.mci_service:
            try:
                logger.info("🧬 Running multimodal MCI analysis with MCIScreeningService...")
                
                # Aggregate all acoustic features (take mean across all questions)
                all_acoustic = {}
                if state.acoustic_features:
                    for question_id, features in state.acoustic_features.items():
                        for key, value in features.items():
                            if key not in all_acoustic:
                                all_acoustic[key] = []
                            if isinstance(value, (int, float, np.number)):
                                all_acoustic[key].append(value)
                    
                    # Average acoustic features
                    avg_acoustic = {
                        k: float(np.mean(v)) for k, v in all_acoustic.items() if v
                    }
                else:
                    avg_acoustic = {}
                
                # Collect linguistic features
                linguistic_features = state.linguistic_features or {}
                
                # Use MCIScreeningService for prediction (NEW method)
                # Combine all user responses for transcript
                all_responses = []
                for domain_responses in state.responses.values():
                    for response in domain_responses:
                        if response.user_answer:
                            all_responses.append(response.user_answer)
                combined_transcript = " ".join(all_responses)
                
                # Use MCI service to analyze (if we have audio or transcript)
                if combined_transcript or avg_acoustic:
                    # Try to find audio file from responses
                    audio_file_path = None
                    for domain_responses in state.responses.values():
                        for response in domain_responses:
                            if response.audio_file and os.path.exists(response.audio_file):
                                audio_file_path = response.audio_file
                                break
                        if audio_file_path:
                            break
                    
                    # Use MCIScreeningService for full analysis
                    mci_result = self.mci_service.analyze(
                        audio_path=audio_file_path,
                        transcript=combined_transcript if combined_transcript else None,
                        task_type='mmse_assessment',
                        user_info=state.user_info
                    )
                    
                    if mci_result.success and mci_result.mci_prediction:
                        mci_probability = mci_result.mci_prediction.get('mci_probability', 0.5)
                        mmse_estimate = mci_result.mmse_estimate
                        logger.info(f"✅ MCI service prediction: prob={mci_probability:.2f}, MMSE={mmse_estimate:.1f}")
                    else:
                        # Fallback to rule-based if service failed
                        logger.warning("⚠️ MCI service analysis failed, using rule-based fallback")
                        mci_probability = self._estimate_mci_probability(
                            avg_acoustic, linguistic_features, state.total_score or 0
                        )
                        mmse_estimate = state.total_score or 0
                else:
                    # No data, use rule-based
                    logger.warning("⚠️ No transcript or acoustic features, using rule-based")
                    mci_probability = self._estimate_mci_probability(
                        avg_acoustic, linguistic_features, state.total_score or 0
                    )
                    mmse_estimate = state.total_score or 0
                
                # Store comprehensive MCI result from MCIScreeningService
                if mci_result.success and mci_result.mci_prediction:
                    state.mci_result = {
                        'acoustic_feature_count': len(mci_result.acoustic_features),
                        'linguistic_feature_count': len(mci_result.linguistic_features),
                        'mmse_score': state.total_score,
                        'mmse_estimate_from_mci': mmse_estimate,
                        'mci_probability': mci_probability,
                        'mci_class': mci_result.mci_prediction.get('mci_class', 'Unknown'),
                        'confidence': mci_result.confidence,
                        'severity': mci_result.severity,
                        'risk_level': 'HIGH' if mci_probability > 0.6 else 'MODERATE' if mci_probability > 0.3 else 'LOW',
                        'risk_factors': mci_result.risk_factors,
                        'recommendations': mci_result.recommendations,
                        'interpretation': self._interpret_mci_probability(mci_probability),
                        'model_used': 'MCIScreeningService (newest modules)'
                    }
                else:
                    # Fallback result
                    state.mci_result = {
                        'acoustic_feature_count': len(avg_acoustic),
                        'linguistic_feature_count': len(linguistic_features),
                        'mmse_score': state.total_score,
                        'mci_probability': mci_probability,
                        'risk_level': 'HIGH' if mci_probability > 0.6 else 'MODERATE' if mci_probability > 0.3 else 'LOW',
                        'interpretation': self._interpret_mci_probability(mci_probability),
                        'model_used': 'Rule-based (fallback)'
                    }
                
                logger.info(f"✅ MCI analysis complete: {mci_probability:.1%} probability, {state.mci_result.get('risk_level', 'UNKNOWN')} risk")
            except Exception as e:
                logger.warning(f"⚠️ MCI analysis failed: {e}")
                state.mci_result = None
        
        # Get classification
        classification = self._classify_score(state.total_score or 0)
        state.classification = classification
        
        # Generate completion message - more natural and friendly
        greeting_term = state.greeting.lower() if state.greeting else "bạn"

        message = (
            f"🎉 Chúc mừng {greeting_term}! Chúng ta đã hoàn thành bài kiểm tra rồi!\n\n"
            f"Đây là kết quả của {greeting_term} nhé:\n\n"
            f"**Tổng điểm MMSE:** {state.total_score}/30 điểm\n"
            f"**Phân loại:** {classification}\n\n"
            f"Chi tiết từng phần:\n"
        )
        
        domain_names = {
            "orientation": "Định hướng",
            "registration": "Ghi nhận",
            "attention_calculation": "Chú ý & Tính toán",
            "recall": "Nhớ lại",
            "language": "Ngôn ngữ",
            "visuospatial": "Hình dung không gian"
        }
        
        domain_max = {
            "orientation": 10,
            "registration": 3,
            "attention_calculation": 5,
            "recall": 3,
            "language": 8,
            "visuospatial": 1
        }
        
        for domain, score in state.domain_scores.items():
            name = domain_names.get(domain, domain)
            max_score = domain_max.get(domain, 1)
            message += f"• {name}: {score}/{max_score} điểm\n"
        
        # Add MCI multimodal analysis if available
        if state.mci_result:
            message += f"\n**🧬 Phân tích đa phương thức (Multimodal Analysis):**\n"
            message += f"• Đặc trưng âm thanh: {state.mci_result['acoustic_feature_count']} features\n"
            message += f"• Đặc trưng ngôn ngữ: {state.mci_result['linguistic_feature_count']} features\n"
            message += f"• Ước tính nguy cơ MCI: **{state.mci_result['mci_probability']:.1%}**\n"
            if 'interpretation' in state.mci_result:
                message += f"• Diễn giải: {state.mci_result['interpretation']}\n"

        message += f"\n💝 Cảm ơn {greeting_term} đã tham gia bài kiểm tra!\n"
        message += "Kết quả này sẽ giúp bác sĩ đánh giá tình trạng sức khỏe của bạn tốt hơn."
        
        metadata = {
            "completed": True,
            "total_score": state.total_score,
            "domain_scores": state.domain_scores,
            "classification": classification,
            "session_id": session_id
        }
        
        return message, metadata
    
    def _calculate_all_scores(self, state: SessionState):
        """
        Calculate all domain scores using rule-based scoring from JSON
        Scores are already calculated per-question in submit_answer()
        This function aggregates them by domain
        """
        
        # ✅ FIX: Use rule-based scores already calculated
        if hasattr(state, 'question_scores') and state.question_scores:
            # Aggregate scores by domain
            state.domain_scores = {
                "orientation": 0,
                "registration": 0,
                "attention_calculation": 0,
                "recall": 0,
                "language": 0,
                "visuospatial": 0
            }
            
            # Map question IDs to domains
            for q_id, score in state.question_scores.items():
                if q_id.startswith('ori_'):
                    state.domain_scores["orientation"] += score
                elif q_id.startswith('reg_'):
                    state.domain_scores["registration"] += score
                elif q_id.startswith('attn_'):
                    state.domain_scores["attention_calculation"] += score
                elif q_id.startswith('recall_'):
                    state.domain_scores["recall"] += score
                elif q_id.startswith('lang_') or q_id.startswith('name_') or q_id.startswith('rep_') or q_id.startswith('flu_'):
                    state.domain_scores["language"] += score
                elif q_id.startswith('vis_') or q_id.startswith('draw_'):
                    state.domain_scores["visuospatial"] += score
            
            # Calculate total from question scores
            state.total_score = sum(state.question_scores.values())
        else:
            # Fallback: calculate from responses if scoring service not available
            logger.warning("⚠️ No question scores found, using fallback calculation")
            state.domain_scores = {
                "orientation": 0,
                "registration": 0,
                "attention_calculation": 0,
                "recall": 0,
                "language": 0,
                "visuospatial": 0
            }
            state.total_score = 0
        
        # Extract linguistic features from all responses
        state.linguistic_features = self._extract_linguistic_features(state)
        
        logger.info(f"✅ Scores calculated (rule-based): Total={state.total_score}/30")
    
    def _extract_linguistic_features(self, state: SessionState) -> Dict[str, float]:
        """
        Extract 7 linguistic features from all responses
        Based on Fraser et al. (2016) and Luz et al. (2020)
        
        Features:
        1. Type-Token Ratio (TTR)
        2. Pronoun Ratio
        3. Concrete Noun Rate
        4. Mean Length of Utterance (MLU)
        5. Incomplete Sentence Ratio
        6. Semantic Coherence
        7. Idea Density
        """
        if not self.linguistic_analyzer:
            logger.warning("⚠️ Linguistic analyzer not available")
            return {}
        
        try:
            # Collect all user responses
            all_text = []
            for domain_responses in state.responses.values():
                for response in domain_responses:
                    if response.user_answer:
                        all_text.append(response.user_answer)
            
            combined_text = " ".join(all_text)
            
            if not combined_text.strip():
                return {}
            
            # Extract features using MCI linguistic analyzer
            features = self.linguistic_analyzer.extract_all_features(
                combined_text,
                task_type='mmse_assessment'
            )
            
            # Return features directly (keep original keys from analyzer)
            # This ensures compatibility with _estimate_mci_probability()
            logger.info(f"✅ Linguistic features extracted: {len(features)} features")
            logger.debug(f"   Sample features: {list(features.keys())[:5]}")
            return features
            
        except Exception as e:
            logger.error(f"❌ Failed to extract linguistic features: {e}")
            return {}
    
    def _evaluate_domain_with_gpt4o(self, state: SessionState, domain: str, max_score: int) -> int:
        """
        Evaluate domain using GPT-4o instead of old pattern matching
        This is the NEW scoring method using advanced AI evaluation
        """
        responses = state.responses.get(domain, [])
        if not responses:
            return 0
        
        # Fallback to old method if GPT-4o not available
        if not openai_client:
            logger.warning(f"⚠️ GPT-4o not available, using fallback scoring for {domain}")
            return self._score_domain_fallback(state, domain, max_score)
        
        try:
            # Collect all responses for this domain
            all_answers = [r.user_answer for r in responses if r.user_answer]
            combined_answer = " ".join(all_answers)
            
            if not combined_answer.strip():
                return 0
            
            # Get question context
            domain_questions = self._get_domain_questions(domain)
            question_context = ""
            if domain_questions:
                question_context = domain_questions[0].get("chatbot_message", "")
            
            # Build evaluation prompt with domain-specific instructions
            user_info = state.user_info
            age = user_info.get("age", "")
            gender = user_info.get("gender", "")
            education = user_info.get("education_years", "")
            
            # Domain-specific evaluation instructions
            domain_instructions = {
                "orientation": """Đánh giá định hướng thời gian và không gian:
- Thời gian: Ngày trong tuần, ngày, tháng, năm, thời điểm trong ngày (5 điểm)
- Không gian: Quốc gia, tỉnh/thành, quận/huyện, địa điểm, tầng (5 điểm)
- Cho điểm dựa trên độ chính xác, không cần hoàn hảo 100%""",
                "registration": """Đánh giá khả năng ghi nhận và lặp lại từ:
- Người dùng cần lặp lại 3 từ đã được đọc: {registration_words}
- Cho 1 điểm cho mỗi từ được lặp lại đúng (tổng 3 điểm)
- Chấp nhận từ đồng nghĩa hoặc phát âm gần đúng""",
                "attention_calculation": """Đánh giá khả năng chú ý và tính toán:
- Yêu cầu: Đếm ngược từ 100 trừ đi 7 (93, 86, 79, 72, 65)
- Cho 1 điểm cho mỗi số đúng (tổng 5 điểm)
- Chấp nhận nếu tính đúng từ số trước đó""",
                "recall": """Đánh giá khả năng nhớ lại sau 5 phút:
- Người dùng cần nhớ lại 3 từ đã được đọc trước đó: {registration_words}
- Cho 1 điểm cho mỗi từ nhớ lại đúng (tổng 3 điểm)
- Điều chỉnh kỳ vọng theo tuổi (người cao tuổi có thể giảm 10-15%)""",
                "language": """Đánh giá khả năng ngôn ngữ:
- Đặt tên đồ vật (2 điểm): đồng hồ, bút
- Lặp lại câu (1 điểm): "Không có nếu và hoặc nhưng gì cả"
- Làm theo lệnh 3 bước (3 điểm): hiểu, thực hiện, hoàn thành
- Đọc hiểu (1 điểm): đọc và làm theo lệnh
- Viết câu (1 điểm): viết một câu hoàn chỉnh""",
                "visuospatial": """Đánh giá khả năng không gian thị giác:
- Yêu cầu: Vẽ hoặc mô tả hình vẽ (ví dụ: ngôi sao 5 cánh)
- Cho điểm nếu thể hiện hiểu biết về không gian, hình dạng, góc độ (1 điểm)"""
            }
            
            instruction = domain_instructions.get(domain, "Đánh giá câu trả lời dựa trên độ chính xác và đầy đủ.")
            
            # Add registration words if needed
            if domain in ["registration", "recall"]:
                reg_words = ", ".join(state.registration_words)
                instruction = instruction.replace("{registration_words}", reg_words)
            
            prompt = f"""Bạn là chuyên gia đánh giá MMSE với nhiều năm kinh nghiệm. Đánh giá câu trả lời cho domain {domain} (tối đa {max_score} điểm).

**THÔNG TIN DOMAIN:**
Domain: {domain}
Câu hỏi đã hỏi: {question_context}
Câu trả lời của người dùng: {combined_answer}

**THÔNG TIN NGƯỜI DÙNG:**
- Tuổi: {age}
- Giới tính: {gender}
- Số năm học: {education}

**HƯỚNG DẪN ĐÁNH GIÁ:**
{instruction}

**NGUYÊN TẮC:**
1. Điều chỉnh tiêu chuẩn theo tuổi: Người cao tuổi (65+) có thể được đánh giá linh hoạt hơn
2. Điều chỉnh theo trình độ học vấn: Người có trình độ thấp có thể được đánh giá phù hợp hơn
3. Chấp nhận các biến thể hợp lý: Từ đồng nghĩa, phát âm gần đúng, cách diễn đạt khác nhưng đúng nghĩa
4. Đánh giá công bằng: Không quá khắt khe cũng không quá dễ dãi

**YÊU CẦU:**
Trả về JSON với format:
{{
  "score": <số nguyên từ 0 đến {max_score}>,
  "reasoning": "<giải thích chi tiết bằng tiếng Việt, ít nhất 50 từ, giải thích tại sao cho điểm này>",
  "details": "<chi tiết đánh giá từng phần nếu có>"
}}

**QUAN TRỌNG:**
- Điểm số phải là số nguyên từ 0 đến {max_score}
- Reasoning phải chi tiết và giải thích rõ ràng
- Phải xem xét tuổi tác và trình độ học vấn khi đánh giá"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia đánh giá MMSE. Luôn trả về JSON hợp lệ."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            score = int(result.get("score", 0))
            score = max(0, min(max_score, score))  # Clamp to valid range
            
            logger.info(f"✅ GPT-4o evaluated {domain}: {score}/{max_score} - {result.get('reasoning', '')[:50]}")
            return score
            
        except Exception as e:
            logger.error(f"❌ GPT-4o evaluation failed for {domain}: {e}")
            logger.warning(f"⚠️ Falling back to old scoring method for {domain}")
            return self._score_domain_fallback(state, domain, max_score)
    
    def _score_domain_fallback(self, state: SessionState, domain: str, max_score: int) -> int:
        """Fallback to old scoring methods if GPT-4o fails"""
        if domain == "orientation":
            return self._score_orientation_old(state)
        elif domain == "registration":
            return self._score_registration_old(state)
        elif domain == "attention_calculation":
            return self._score_attention_old(state)
        elif domain == "recall":
            return self._score_recall_old(state)
        elif domain == "language":
            return self._score_language_old(state)
        elif domain == "visuospatial":
            return self._score_visuospatial_old(state)
        return 0
    
    def _score_orientation_old(self, state: SessionState) -> int:
        """Score orientation domain (10 points)"""
        score = 0
        responses = state.responses.get("orientation", [])
        
        now = datetime.now()
        
        for i, response in enumerate(responses):
            answer = response.user_answer.lower().strip()
            
            if i == 0:  # Day of week
                weekdays = {
                    0: ["thứ hai", "thứ 2", "hai"],
                    1: ["thứ ba", "thứ 3", "ba"],
                    2: ["thứ tư", "thứ 4", "tư"],
                    3: ["thứ năm", "thứ 5", "năm"],
                    4: ["thứ sáu", "thứ 6", "sáu"],
                    5: ["thứ bảy", "thứ 7", "bảy"],
                    6: ["chủ nhật", "cn"]
                }
                for name in weekdays.get(now.weekday(), []):
                    if name in answer:
                        score += 1
                        break
            
            elif i == 1:  # Date
                if str(now.day) in answer:
                    score += 1
            
            elif i == 2:  # Month
                month_names = {
                    1: ["tháng 1", "tháng một", "tháng giêng"],
                    2: ["tháng 2", "tháng hai"],
                    3: ["tháng 3", "tháng ba"],
                    4: ["tháng 4", "tháng tư"],
                    5: ["tháng 5", "tháng năm"],
                    6: ["tháng 6", "tháng sáu"],
                    7: ["tháng 7", "tháng bảy"],
                    8: ["tháng 8", "tháng tám"],
                    9: ["tháng 9", "tháng chín"],
                    10: ["tháng 10", "tháng mười"],
                    11: ["tháng 11", "tháng mười một"],
                    12: ["tháng 12", "tháng mười hai", "chạp"]
                }
                for name in month_names.get(now.month, []):
                    if name in answer or str(now.month) in answer:
                        score += 1
                        break
            
            elif i == 3:  # Year
                if str(now.year) in answer:
                    score += 1
            
            elif i == 4:  # Time of day
                hour = now.hour
                time_periods = {
                    "sáng": range(5, 11),
                    "trưa": range(11, 14),
                    "chiều": range(14, 18),
                    "tối": range(18, 22),
                    "đêm": range(22, 24)
                }
                for period, hours in time_periods.items():
                    if period in answer and hour in hours:
                        score += 1
                        break
            
            elif i >= 5:  # Place orientation (5 questions)
                # Simpler check - if they provide a reasonable answer
                if len(answer) > 2 and answer not in ["không biết", "không nhớ"]:
                    score += 1
        
        return min(score, 10)
    
    def _score_registration_old(self, state: SessionState) -> int:
        """Score registration domain (3 points)"""
        responses = state.responses.get("registration", [])
        if not responses:
            return 0
        
        answer = responses[0].user_answer.lower()
        words = state.registration_words
        score = 0
        
        for word in words:
            word_lower = word.lower()
            # Extract key word (e.g., "mèo" from "Con mèo")
            key_word = word_lower.split()[-1]
            
            if key_word in answer or self._fuzzy_match(answer, key_word, 0.8):
                score += 1
        
        return min(score, 3)
    
    def _score_attention_old(self, state: SessionState) -> int:
        """Score attention/calculation domain (5 points)"""
        responses = state.responses.get("attention_calculation", [])
        if not responses:
            return 0
        
        answer = responses[0].user_answer
        
        # Extract numbers from answer
        numbers = re.findall(r'\d+', answer)
        numbers = [int(n) for n in numbers]
        
        # Correct sequence: 93, 86, 79, 72, 65
        correct = [93, 86, 79, 72, 65]
        score = 0
        
        for i, correct_num in enumerate(correct):
            if i < len(numbers):
                if numbers[i] == correct_num:
                    score += 1
                # Also accept if they're calculating from their previous answer correctly
                elif i > 0 and len(numbers) > i:
                    if numbers[i] == numbers[i-1] - 7:
                        score += 1
        
        return min(score, 5)
    
    def _score_recall_old(self, state: SessionState) -> int:
        """Score recall domain (3 points)"""
        responses = state.responses.get("recall", [])
        if not responses:
            return 0
        
        answer = responses[0].user_answer.lower()
        words = state.registration_words
        score = 0
        
        for word in words:
            word_lower = word.lower()
            key_word = word_lower.split()[-1]
            
            if key_word in answer or self._fuzzy_match(answer, key_word, 0.8):
                score += 1
        
        return min(score, 3)
    
    def _score_language_old(self, state: SessionState) -> int:
        """Score language domain (8 points)"""
        responses = state.responses.get("language", [])
        score = 0
        
        for i, response in enumerate(responses):
            answer = response.user_answer.lower().strip()
            
            if i == 0:  # Naming - clock
                if any(word in answer for word in ["đồng hồ", "dong ho"]):
                    score += 1
            
            elif i == 1:  # Naming - pen
                if any(word in answer for word in ["bút", "viết", "but"]):
                    score += 1
            
            elif i == 2:  # Repetition
                target = "không có nếu và hoặc nhưng gì cả"
                if self._fuzzy_match(answer, target, 0.85):
                    score += 1
            
            elif i == 3:  # 3-step command (3 points)
                # Check for "tôi hiểu rồi", "1 2 3", "xong rồi" in order
                if "hiểu" in answer:
                    score += 1
                if any(num in answer for num in ["1", "2", "3", "một", "hai", "ba"]):
                    score += 1
                if "xong" in answer:
                    score += 1
            
            elif i == 4:  # Reading comprehension
                if any(word in answer for word in ["bay", "vườn", "hoa", "ong"]):
                    score += 1
            
            elif i == 5:  # Sentence construction
                # Check if sentence has subject and verb
                words = answer.split()
                if len(words) >= 3:
                    score += 1
        
        return min(score, 8)
    
    def _score_visuospatial_old(self, state: SessionState) -> int:
        """Score visuospatial domain (1 point)"""
        responses = state.responses.get("visuospatial", [])
        if not responses:
            return 0
        
        answer = responses[0].user_answer.lower()
        
        # Check for spatial understanding
        spatial_words = ["sao", "ngôi sao", "nhiều góc", "góc nhọn", "kim cương", "chồng"]
        
        for word in spatial_words:
            if word in answer:
                return 1
        
        return 0
    
    def _fuzzy_match(self, text: str, target: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching"""
        text_lower = text.lower()
        target_lower = target.lower()
        
        # Check direct containment
        if target_lower in text_lower:
            return True
        
        # Check similarity ratio
        ratio = difflib.SequenceMatcher(None, text_lower, target_lower).ratio()
        return ratio >= threshold
    
    def _classify_score(self, score: int) -> str:
        """Classify MMSE score"""
        if score >= 24:
            return "Nhận thức bình thường"
        elif score >= 18:
            return "Suy giảm nhận thức nhẹ (MCI)"
        elif score >= 10:
            return "Suy giảm nhận thức trung bình"
        else:
            return "Suy giảm nhận thức nặng"
    
    def _estimate_mci_probability(self, acoustic_features: Dict[str, float], 
                                   linguistic_features: Dict[str, float], 
                                   mmse_score: int) -> float:
        """
        Estimate MCI probability from multimodal features
        Rule-based approach (simplified without trained model)
        """
        probability = 0.0
        
        # 1. MMSE score component (strongest indicator) - 50% weight
        if mmse_score >= 24:
            probability += 0.1  # Low risk
        elif mmse_score >= 18:
            probability += 0.5  # Moderate risk (MCI range)
        else:
            probability += 0.8  # High risk
        
        # 2. Acoustic indicators - 25% weight
        if acoustic_features:
            acoustic_risk = 0.0
            
            # F0 variability (low = potential indicator)
            f0_cv = acoustic_features.get('f0_f0_cv', 0.5)
            if f0_cv < 0.15:
                acoustic_risk += 0.3
            
            # Voice quality (high jitter/shimmer = potential indicator)
            jitter = acoustic_features.get('vq_jitter_local', 0.01)
            if jitter > 0.02:
                acoustic_risk += 0.2
            
            # Pause rate (high = potential indicator)
            pause_rate = acoustic_features.get('pause_pause_rate', 0.3)
            if pause_rate > 0.4:
                acoustic_risk += 0.2
            
            # HNR (low = potential indicator)
            hnr = acoustic_features.get('vq_hnr_mean', 15.0)
            if hnr < 10.0:
                acoustic_risk += 0.3
            
            probability += min(1.0, acoustic_risk) * 0.25
        
        # 3. Linguistic indicators - 25% weight
        if linguistic_features:
            linguistic_risk = 0.0
            
            # Low TTR = potential indicator
            ttr = linguistic_features.get('lex_ttr', 0.7)
            if ttr < 0.5:
                linguistic_risk += 0.3
            
            # Low word count = potential indicator
            word_count = linguistic_features.get('lex_total_words', 100)
            if word_count < 50:
                linguistic_risk += 0.2
            
            # High pronoun ratio = potential indicator
            pronoun_ratio = linguistic_features.get('lex_pronoun_ratio', 0.2)
            if pronoun_ratio > 0.3:
                linguistic_risk += 0.2
            
            # Low idea density = potential indicator
            idea_density = linguistic_features.get('sem_idea_density', 0.5)
            if idea_density < 0.3:
                linguistic_risk += 0.3
            
            probability += min(1.0, linguistic_risk) * 0.25
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, probability))
    
    def _interpret_mci_probability(self, probability: float) -> str:
        """
        Interpret MCI probability as clinical risk level
        
        Args:
            probability: MCI probability (0-1)
        
        Returns:
            str: Risk interpretation in Vietnamese
        """
        if probability < 0.20:
            return "Nguy cơ thấp (Low risk) - Chức năng nhận thức bình thường"
        elif probability < 0.40:
            return "Nguy cơ trung bình thấp (Low-moderate risk) - Nên theo dõi định kỳ"
        elif probability < 0.60:
            return "Nguy cơ trung bình (Moderate risk) - Khuyến nghị đánh giá lâm sàng"
        elif probability < 0.80:
            return "Nguy cơ cao (High risk) - Nên khám chuyên khoa sớm"
        else:
            return "Nguy cơ rất cao (Very high risk) - Cần khám chuyên khoa ngay"
    
    def _get_domain_questions(self, domain: str) -> List[Dict]:
        """Get questions for a domain"""
        domain_mapping = {
            "orientation": "ORIENTATION",
            "registration": "REGISTRATION",
            "attention_calculation": "ATTENTION_CALCULATION",
            "recall": "RECALL",
            "language": "LANGUAGE",
            "visuospatial": "VISUOSPATIAL",
            "open_questions": "SUPPLEMENTARY_OPEN_QUESTIONS"  # Supplementary
        }
        
        domain_code = domain_mapping.get(domain)
        
        # ✅ FIX: Load from correct JSON structure
        mmse_data = self.questions_data.get('mmse_vietnamese_chatbot', {})
        domains = mmse_data.get('domains', [])
        
        if domain == "open_questions":
            # Supplementary questions for linguistic analysis
            for d in domains:
                if d.get("domain_code") == "SUPPLEMENTARY_OPEN_QUESTIONS":
                    return d.get("questions", [])
            return []
        
        # Find domain by code
        for d in domains:
            if d.get("domain_code") == domain_code:
                questions = d.get("questions", [])
                # ✅ FIX: Handle conversation_sequence structure
                processed_questions = []
                for q in questions:
                    # If question has conversation_sequence, extract the actual question
                    if 'conversation_sequence' in q:
                        # Find the prompt_recall or similar step
                        for step in q.get('conversation_sequence', []):
                            if step.get('message_type') == 'prompt_recall':
                                processed_q = q.copy()
                                processed_q['chatbot_message'] = step.get('chatbot_message', q.get('chatbot_message', ''))
                                processed_questions.append(processed_q)
                                break
                        else:
                            # Use first visible message
                            for step in q.get('conversation_sequence', []):
                                if step.get('display_mode') == 'visible':
                                    processed_q = q.copy()
                                    processed_q['chatbot_message'] = step.get('chatbot_message', q.get('chatbot_message', ''))
                                    processed_questions.append(processed_q)
                                    break
                            else:
                                processed_questions.append(q)
                    else:
                        processed_questions.append(q)
                return processed_questions
        
        return []
    
    def _replace_greeting(self, text: str, greeting: str) -> str:
        """Replace {greeting} placeholder"""
        return text.replace("{greeting}", greeting)
    
    def _check_recall_allowed(self, state: SessionState) -> bool:
        """Check if 5-minute delay has passed for recall"""
        if not state.recall_allowed_after:
            return True  # No registration done yet
        
        allowed_time = datetime.fromisoformat(state.recall_allowed_after)
        return datetime.now() >= allowed_time
    
    def _get_recall_wait_time(self, state: SessionState) -> int:
        """Get remaining seconds until recall is allowed"""
        if not state.recall_allowed_after:
            return 0
        
        allowed_time = datetime.fromisoformat(state.recall_allowed_after)
        remaining = (allowed_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def get_test_results(self, session_id: str) -> Optional[Dict]:
        """Get complete test results"""
        state = self.get_session(session_id)
        if not state or state.current_domain != TestDomain.COMPLETED:
            return None
        
        return {
            "session_id": session_id,
            "user_info": state.user_info,
            "total_score": state.total_score,
            "domain_scores": state.domain_scores,
            "classification": state.classification,
            "started_at": state.started_at,
            "completed_at": state.completed_at,
            "responses": {
                domain: [asdict(r) for r in responses]
                for domain, responses in state.responses.items()
            },
            "linguistic_features": state.linguistic_features
        }
    
    def export_session_data(self, session_id: str) -> Optional[Dict]:
        """Export session data for analysis"""
        state = self.get_session(session_id)
        if not state:
            return None
        
        return asdict(state)


# Global instance
_chatbot_service: Optional[MMSEChatbotService] = None


def get_mmse_chatbot_service() -> MMSEChatbotService:
    """Get or create global chatbot service instance"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = MMSEChatbotService()
    return _chatbot_service

