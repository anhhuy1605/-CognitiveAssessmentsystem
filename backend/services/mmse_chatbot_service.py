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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

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
    """MMSE Test Domains following clinical protocol (v2.1_CORRECTED)"""
    INIT = "init"
    ORIENTATION = "orientation"
    REGISTRATION = "registration"
    ATTENTION_CALCULATION = "attention_calculation"
    EXECUTIVE_FUNCTION = "executive_function"  # ✅ v2.1: Added Executive Function domain
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
    recall_allowed_after: Optional[str] = None  # ✅ v2.1: 360 seconds (6 minutes) after registration
    
    # ✅ v2.1: Serial 7s tracking
    serial_7s_answers: List[int] = field(default_factory=list)
    serial_7s_started: bool = False
    serial_7s_stopped: bool = False
    serial_7s_current_value: int = 100  # Start from 100
    
    # ✅ v2.1: Executive Function - Verbal Fluency tracking
    verbal_fluency_started: bool = False
    verbal_fluency_start_time: Optional[float] = None
    verbal_fluency_animals: List[str] = field(default_factory=list)
    verbal_fluency_completed: bool = False
    
    # ✅ v2.1: Clock Drawing state
    clock_drawing_mode: str = "visual"  # "visual" or "verbal"
    clock_drawing_data: Optional[Dict] = None  # For storing clock image/coordinates
    clock_drawing_target_time: str = "11:10"  # Target time for clock drawing
    
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
        if questions_path is None:
            # Try to find file in multiple locations
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "mmse_audio_questions_standardized.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "mmse_audio_questions_standardized.json"),
                os.path.join(os.path.dirname(__file__), "mmse_audio_questions_standardized.json"),
                "/app/mmse_audio_questions_standardized.json",
                "/app/backend/mmse_audio_questions_standardized.json",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    questions_path = path
                    logger.info(f"✅ Found questions file at: {questions_path}")
                    break
            else:
                # Default fallback
                questions_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "mmse_audio_questions_standardized.json"
                )
                logger.warning(f"⚠️ Questions file not found in any expected location, using default: {questions_path}")
        
        self.questions_path = questions_path
        self.questions_data = self._load_questions()
        self.sessions: Dict[str, SessionState] = {}
        
        # Domain order (clinical protocol) - v2.1_CORRECTED
        self.domain_order = [
            TestDomain.ORIENTATION,        # 10 points
            TestDomain.REGISTRATION,       # 3 points
            TestDomain.ATTENTION_CALCULATION,  # 5 points
            TestDomain.EXECUTIVE_FUNCTION,  # ✅ v2.1: 3 points (verbal fluency 2 + abstraction 1)
            TestDomain.OPEN_QUESTIONS,     # 0 points (feature extraction only)
            TestDomain.RECALL,             # 3 points
            TestDomain.LANGUAGE,           # 8 points
            TestDomain.VISUOSPATIAL,      # 3 points
            # Total: 35 points (v2.1_CORRECTED)
        ]
        
        # Initialize linguistic analyzer from MCI modules
        self.linguistic_analyzer = None
        try:
            from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
            self.linguistic_analyzer = VietnameseLinguisticAnalyzer(use_phobert=True)
            logger.info("✅ Linguistic Analyzer initialized")
        except Exception as e:
            logger.warning(f"⚠️ Linguistic Analyzer not available: {e}")
        
        # ✅ v2.1: Initialize Clock Drawing Generator
        self.clock_generator = None
        try:
            from services.clock_drawing_generator import ClockDrawingGenerator
            self.clock_generator = ClockDrawingGenerator()
            logger.info("✅ Clock Drawing Generator initialized")
        except Exception as e:
            logger.warning(f"⚠️ Clock Drawing Generator not available: {e}")
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
        
        # ✅ OPTIMIZATION: Thread pool for parallel feature extraction
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="feature_extraction")
        logger.info("✅ Thread pool initialized for parallel feature extraction")
        
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
        """
        ✅ v2.1_CORRECTED: Set addressee term (ông/bà) based on gender
        
        Pronoun mapping from JSON:
        - male → "Ông"
        - female → "Bà"
        - default → "Bạn"
        """
        state = self.get_session(session_id)
        if not state:
            return False
        
        # Normalize greeting
        greeting_lower = greeting.lower().strip()
        if "ông" in greeting_lower or "ong" in greeting_lower or greeting_lower == "male":
            state.greeting = "Ông"
        elif "bà" in greeting_lower or "ba" in greeting_lower or greeting_lower == "female":
            state.greeting = "Bà"
        else:
            # Default
            state.greeting = "Bạn"
        
        logger.info(f"✅ Session {session_id}: Greeting set to '{state.greeting}'")
        return True
    
    def get_pronoun(self, session_id: str, capitalize: bool = False) -> str:
        """
        ✅ v2.1_CORRECTED: Get pronoun based on user gender
        
        Args:
            session_id: Session ID
            capitalize: Whether to return capitalized version (Ông/Bà) or lowercase (ông/bà)
        
        Returns:
            Pronoun string
        """
        state = self.get_session(session_id)
        if not state:
            return "Bạn" if capitalize else "bạn"
        
        pronoun = state.greeting if state.greeting else "Bạn"
        return pronoun if capitalize else pronoun.lower()
    
    def get_introduction_message(self, session_id: Optional[str] = None) -> str:
        """
        ✅ v2.1_CORRECTED: Get greeting messages from JSON
        
        Returns greeting flow with 4 messages as per JSON specification
        """
        # Get pronoun from session if available
        pronoun = "Bạn"
        pronoun_lower = "bạn"
        if session_id:
            state = self.get_session(session_id)
            if state and state.greeting:
                pronoun = state.greeting
                pronoun_lower = state.greeting.lower()
        
        # Try to load from JSON v2.1 structure
        if 'questions' in self.questions_data:
            greeting_data = self.questions_data.get('questions', {}).get('greeting', {})
            messages = greeting_data.get('messages', [])
            if messages:
                # Format messages with pronouns
                formatted_messages = []
                for msg in messages:
                    formatted = self._replace_greeting(msg, pronoun)
                    formatted_messages.append(formatted)
                return "\n\n".join(formatted_messages)
        
        # Fallback: Default greeting from JSON structure
        return (
            f"Xin chào {pronoun}! Tôi là trợ lý ảo, sẽ giúp {pronoun} làm bài kiểm tra sức khỏe nhận thức hôm nay.\n\n"
            f"Bài kiểm tra này gồm nhiều câu hỏi về thời gian, địa điểm, trí nhớ, và một số câu tính toán đơn giản.\n\n"
            f"Toàn bộ bài kiểm tra sẽ mất khoảng 15-20 phút. {pronoun} cứ thư giãn và trả lời tự nhiên nhé!\n\n"
            f"Chúng ta bắt đầu nhé {pronoun}!"
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
        
        # ✅ FIX: Initialize metadata at the start to avoid "cannot access local variable" error
        metadata = {}

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
        # ✅ v2.1_CORRECTED: Use "question" field from new JSON structure, fallback to old fields
        question_text = self._replace_greeting(
            question.get("question", question.get("chatbot_message", question.get("question_text", ""))), 
            state.greeting
        )
        
        # ✅ v2.1_CORRECTED: Handle instruction fields (instruction_part1, instruction_part2)
        # For registration domain, combine instruction_part1 and instruction_part2
        actual_question_id = question.get("question_id", f"{domain.value}_{index}")
        if domain == TestDomain.REGISTRATION and index == 0:
            message_parts = []
            
            # 1. Instruction
            instruction = question.get("instruction", "")
            if instruction:
                instruction = self._replace_greeting(instruction, state.greeting)
                message_parts.append(instruction)
            
            # 2. Question (main question text)
            if question_text:
                message_parts.append(question_text)
            
            # 3. Words announcement (for registration)
            words_announcement = question.get("words_announcement", "")
            if words_announcement:
                # Remove markdown bold if present (safety check)
                words_announcement = words_announcement.replace("**", "")
                words_announcement = self._replace_greeting(words_announcement, state.greeting)
                message_parts.append(words_announcement)
            
            # 4. Instruction after (for registration)
            instruction_after = question.get("instruction_after", "")
            if instruction_after:
                instruction_after = self._replace_greeting(instruction_after, state.greeting)
                message_parts.append(instruction_after)
            
            # Join with double newline for clear separation
            question_text = "\n\n".join(part for part in message_parts if part)
        elif index == 0:
            # For other domains, use single instruction field
            instruction = question.get("instruction", "")
            if instruction and instruction not in question_text:
                instruction = self._replace_greeting(instruction, state.greeting)
                question_text = f"{instruction}\n\n{question_text}"
        
        # ✅ FIX: Get actual question_id from JSON
        if domain != TestDomain.REGISTRATION or index != 0:
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
        
        # ✅ v2.1_CORRECTED: Special handling for Registration
        if domain == TestDomain.REGISTRATION:
            # v2.1 uses "words" field instead of "word_list"
            registration_words = question.get("words", question.get("word_list", state.registration_words))
            metadata["words"] = registration_words
            # Store words for recall later
            if "words" in question:
                state.registration_words = registration_words
            metadata["instruction_after"] = self._replace_greeting(
                question.get("instruction_after", ""), state.greeting
            )
        
        # ✅ v2.1_CORRECTED: Check if Recall is allowed (6 min = 360 seconds minimum delay)
        if domain == TestDomain.RECALL:
            if not self._check_recall_allowed(state):
                remaining = self._get_recall_wait_time(state)
                minutes = remaining // 60
                seconds = remaining % 60
                return (
                    f"Vui lòng chờ thêm {minutes} phút {seconds} giây trước khi tiếp tục phần nhớ lại.",
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
        
        # ✅ FIX: Initialize metadata at the start to avoid "cannot access local variable" error
        metadata = {}

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
                
                # ✅ Calculate total score in real-time (v2.1: 35-point scale)
                if state.total_score is None:
                    state.total_score = 0
                state.total_score += score_result['points_earned']
                
                logger.info(f"✅ Scored question {actual_question_id}: {score_result['points_earned']}/{score_result['points_possible']} → Total: {state.total_score}/35")
            except ValueError as ve:
                # Question not found in JSON - skip scoring for this question
                logger.warning(f"⚠️ Question {actual_question_id} not found in JSON: {ve}")
                score_result = {'points_earned': 0, 'points_possible': 0, 'is_correct': False, 'feedback': ''}
            except Exception as e:
                logger.error(f"❌ Scoring failed: {e}")
                import traceback
                traceback.print_exc()
                score_result = {'points_earned': 0, 'points_possible': 0, 'is_correct': False, 'feedback': ''}
        
        # ✅ OPTIMIZATION: Extract acoustic & linguistic features in parallel (if audio provided)
        if audio_file:
            try:
                logger.info(f"🚀 Starting PARALLEL feature extraction for {audio_file}")
                acoustic_features, linguistic_features_dict = self._extract_features_parallel(
                    audio_path=audio_file,
                    transcript=answer,
                    timeout=60
                )
                
                # Store acoustic features
                if acoustic_features:
                    state.acoustic_features[f"{domain.value}_{index}"] = acoustic_features
                    logger.info(f"✅ Stored {len(acoustic_features)} acoustic features")
                
            except Exception as e:
                logger.error(f"⚠️ Parallel feature extraction failed: {e}", exc_info=True)
                # Continue without features - not critical for scoring
                # Pipeline should continue even if feature extraction fails

                

                # FIX: Dont append to responses if domain is COMPLETED

                if domain != TestDomain.COMPLETED:

                    # Ensure domain exists in responses dict

                    if domain.value not in state.responses:

                        state.responses[domain.value] = []

                    state.responses[domain.value].append(response)
        
        # ✅ v2.1: Special handling for Serial 7s (auto-stop after 5 answers)
        if domain == TestDomain.ATTENTION_CALCULATION and actual_question_id == "attn_serial_sub":
            if not state.serial_7s_started:
                state.serial_7s_started = True
                state.serial_7s_current_value = 100
                state.serial_7s_answers = []
            
            # Try to extract number from answer
            import re
            numbers = re.findall(r'\d+', answer)
            if numbers:
                try:
                    user_value = int(numbers[0])
                    state.serial_7s_answers.append(user_value)
                    state.serial_7s_current_value -= 7
                    
                    # Check if we have 5 answers (auto-stop)
                    if len(state.serial_7s_answers) >= 5:
                        state.serial_7s_stopped = True
                        logger.info(f"✅ Serial 7s COMPLETED: {state.serial_7s_answers}")
                        
                        # ✅ Calculate correct count
                        correct_count = self._count_correct_serial7s_answers(state.serial_7s_answers)
                        logger.info(f"✅ Serial 7s Score: {correct_count}/5 correct")
                        
                        # ✅ Get appropriate completion message based on score
                        pronoun = self.get_pronoun(session_id, True)
                        pronoun_lower = self.get_pronoun(session_id, False)
                        
                        if correct_count == 5:
                            completion_message = f"Xuất sắc! {pronoun} tính đúng cả 5 số!"
                        elif correct_count >= 4:
                            completion_message = f"Rất tốt! {pronoun} tính đúng {correct_count}/5 số."
                        elif correct_count >= 3:
                            completion_message = f"Được rồi! {pronoun} tính đúng {correct_count} số."
                        elif correct_count >= 2:
                            completion_message = f"Không sao {pronoun_lower}, phép tính này hơi khó."
                        else:
                            completion_message = f"Không sao {pronoun_lower}, chúng ta tiếp tục phần tiếp theo nhé."
                        
                        # ✅ Move to next question
                        state.current_question_index += 1
                        logger.info(f"➡️ Moving to next question: index {state.current_question_index}")
                        
                        # ✅ Return completion metadata so frontend knows to stop
                        metadata['serial_7s_stopped'] = True
                        metadata['serial_7s_completed'] = True
                        metadata['serial_7s_answers'] = state.serial_7s_answers
                        metadata['serial_7s_correct_count'] = correct_count
                        metadata['serial_7s_score'] = correct_count
                        metadata['move_to_next_question'] = True
                        metadata['auto_stopped'] = True
                        
                        # ✅ Return completion message, then advance to next question
                        next_question_text, next_metadata = self._advance_to_next_domain(session_id)
                        # Merge metadata
                        next_metadata.update(metadata)
                        return completion_message, next_metadata
                    else:
                        # Continue asking for next number
                        state.serial_7s_current_value = user_value  # Update current value to user's answer
                        next_value_to_subtract = state.serial_7s_current_value - 7
                        pronoun = self.get_pronoun(session_id, False)
                        
                        remaining = 5 - len(state.serial_7s_answers)
                        next_question = f"Tiếp tục nhé {pronoun}! Lấy {user_value} trừ 7 bằng bao nhiêu?"
                        
                        logger.info(f"➡️ Serial 7s: Asking for next ({remaining} remaining)")
                        
                        metadata['serial_7s'] = {
                            'answers_so_far': state.serial_7s_answers,
                            'current_value': user_value,
                            'next_expected': next_value_to_subtract,
                            'remaining': remaining,
                            'stopped': False
                        }
                        
                        return next_question, metadata
                except ValueError:
                    pass
        
        # ✅ v2.1: Special handling for Executive Function - Verbal Fluency
        if domain == TestDomain.EXECUTIVE_FUNCTION and actual_question_id == "exec_verbal_fluency":
            if not state.verbal_fluency_started:
                state.verbal_fluency_started = True
                state.verbal_fluency_start_time = time.time()
                state.verbal_fluency_animals = []
            
            # Extract animal names from answer
            # Simple extraction - in production, use NLP
            animals = self._extract_animals_from_text(answer)
            state.verbal_fluency_animals.extend(animals)
            
            elapsed = time.time() - (state.verbal_fluency_start_time or 0)
            remaining = max(0, 60 - elapsed)
            
            if remaining <= 0:
                state.verbal_fluency_completed = True
                # Score based on count
                count = len(set(state.verbal_fluency_animals))  # Unique animals
                if count >= 15:
                    score = 2
                elif count >= 9:
                    score = 1
                else:
                    score = 0
                
                state.question_scores[actual_question_id] = score
                if state.total_score is None:
                    state.total_score = 0
                state.total_score += score
                
                pronoun = self.get_pronoun(session_id, True)
                feedback = f"Cảm ơn {pronoun}! {pronoun} đã kể được {count} con vật."
                state.current_question_index += 1
                return feedback, {'verbal_fluency_completed': True, 'count': count, 'score': score}
            else:
                # Continue - prompt if silent
                if elapsed > 5 and len(state.verbal_fluency_animals) == 0:
                    pronoun = self.get_pronoun(session_id, False)
                    return f"Còn con gì nữa không {pronoun}?", {'verbal_fluency_ongoing': True, 'remaining': remaining}
                elif elapsed >= 30 and elapsed < 50:
                    return "Rất tốt! Hãy tiếp tục nhé!", {'verbal_fluency_ongoing': True, 'remaining': remaining}
                elif elapsed >= 50:
                    pronoun = self.get_pronoun(session_id, False)
                    return f"Còn 10 giây nữa {pronoun}!", {'verbal_fluency_ongoing': True, 'remaining': remaining}
        
        # ✅ v2.1: Special handling for Clock Drawing
        if domain == TestDomain.VISUOSPATIAL and actual_question_id == "visual_clock_drawing":
            if not state.clock_drawing_data and self.clock_generator:
                # Generate clock image
                target_time = state.clock_drawing_target_time
                img_base64, clock_data = self.clock_generator.generate_clock_image(target_time)
                state.clock_drawing_data = clock_data
                metadata['clock_image'] = img_base64
                metadata['clock_data'] = clock_data
                metadata['target_time'] = target_time
                logger.info(f"✅ Generated clock image for {target_time}")
        
        # Special handling for Registration
        if domain == TestDomain.REGISTRATION:
            state.registration_time = datetime.now().isoformat()
            # ✅ v2.1_CORRECTED: Set recall allowed time (6 minutes = 360 seconds minimum)
            recall_time = datetime.now().timestamp() + 360  # 6 minutes minimum
            state.recall_allowed_after = datetime.fromtimestamp(recall_time).isoformat()
            logger.info(f"✅ Registration completed. Recall allowed after {state.recall_allowed_after} (6 min delay)")
        
        # Move to next question
        state.current_question_index += 1
        
        # Check if need to move to next domain
        questions = self._get_domain_questions(domain.value)
        if not questions or state.current_question_index >= len(questions):
            return self._advance_to_next_domain(session_id)
        
        # ✅ REAL-TIME: Get next question
        next_question, metadata = self.get_current_question(session_id)
        
        # ✅ REAL-TIME: Add score update to metadata (v2.1: 35-point scale)
        if score_result:
            metadata['score_update'] = {
                'question_id': actual_question_id,
                'points_earned': score_result['points_earned'],
                'points_possible': score_result['points_possible'],
                'total_score': state.total_score or 0,
                'max_score': 35,  # ✅ v2.1_CORRECTED: 35 points total
                'percentage': round(((state.total_score or 0) / 35) * 100, 1),
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
        
        # ✅ v2.1: Calculate adjusted score with age & education
        adjusted_score_result = None
        if state.total_score is not None and state.user_info:
            try:
                from services.mmse_scoring_v21 import calculate_adjusted_score, get_risk_from_adjusted_score
                
                age = int(state.user_info.get('age', 65))
                education_years = int(state.user_info.get('education_years', 12))
                raw_score = float(state.total_score)
                
                # Calculate adjusted score
                adjusted_score_result = calculate_adjusted_score(
                    raw_score=raw_score,
                    age=age,
                    education_years=education_years
                )
                
                # Get risk classification from adjusted score
                risk_classification = get_risk_from_adjusted_score(
                    adjusted_score_result.adjusted_score,
                    education_years
                )
                
                logger.info(f"✅ v2.1 Adjusted Score: {adjusted_score_result.adjusted_score:.1f} (raw: {raw_score:.1f})")
                logger.info(f"   Risk Classification: {risk_classification}")
                
            except Exception as e:
                logger.warning(f"⚠️ Adjusted score calculation failed: {e}")
                adjusted_score_result = None
        
        # ✅ v2.1: Perform multimodal MCI analysis with NEW pipeline
        if self.mci_service:
            try:
                logger.info("🧬 Running multimodal MCI analysis (v2.1 pipeline)...")
                
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
                
                # ✅ v2.1: Use NEW multimodal integration pipeline
                from services.mmse_scoring_v21 import calculate_multimodal_risk
                
                # Prepare MMSE data for multimodal integration
                mmse_data = {
                    'raw_score': float(state.total_score or 0),
                    'adjusted_score': adjusted_score_result.adjusted_score if adjusted_score_result else float(state.total_score or 0),
                    'education_years': int(state.user_info.get('education_years', 12)),
                    'age': int(state.user_info.get('age', 65))
                }
                
                # Calculate multimodal risk using v2.1 pipeline
                multimodal_result = calculate_multimodal_risk(
                    mmse_data=mmse_data,
                    acoustic_features=avg_acoustic if avg_acoustic else None,
                    linguistic_features=linguistic_features if linguistic_features else None
                )
                
                # Store comprehensive result
                state.mci_result = {
                    'version': 'v2.1',
                    'raw_mmse_score': mmse_data['raw_score'],
                    'adjusted_mmse_score': mmse_data['adjusted_score'],
                    'age_penalty': adjusted_score_result.age_penalty if adjusted_score_result else 0.0,
                    'education_bonus': adjusted_score_result.education_bonus if adjusted_score_result else 0.0,
                    'education_group': adjusted_score_result.education_group if adjusted_score_result else 'medium_education',
                    'acoustic_feature_count': len(avg_acoustic),
                    'linguistic_feature_count': len(linguistic_features),
                    'combined_risk_score': multimodal_result.combined_risk_score,
                    'risk_level': multimodal_result.risk_level,
                    'risk_components': {
                        'mmse': multimodal_result.mmse_risk_score,
                        'acoustic': multimodal_result.acoustic_risk_score,
                        'linguistic': multimodal_result.linguistic_risk_score
                    },
                    'risk_weights': {
                        'mmse': 0.30,
                        'acoustic': 0.30,
                        'linguistic': 0.40
                    },
                    'interpretation': self._interpret_risk_level_v21(multimodal_result.risk_level),
                    'model_used': 'v2.1 Multimodal Integration (MMSE + Acoustic + Linguistic)'
                }
                
                logger.info(f"✅ v2.1 Multimodal analysis complete:")
                logger.info(f"   Combined Risk: {multimodal_result.combined_risk_score:.3f}")
                logger.info(f"   Risk Level: {multimodal_result.risk_level}")
                
            except Exception as e:
                logger.warning(f"⚠️ v2.1 Multimodal analysis failed: {e}")
                import traceback
                traceback.print_exc()
                state.mci_result = None
        
        # ✅ v2.1: Get classification from adjusted score if available
        if adjusted_score_result:
            classification = get_risk_from_adjusted_score(
                adjusted_score_result.adjusted_score,
                int(state.user_info.get('education_years', 12))
            )
            # Convert to readable format
            classification_map = {
                'on': 'Ổn - Chức năng nhận thức bình thường',
                'nguy_co_nhe': 'Nguy cơ nhẹ - Suy giảm nhận thức nhẹ (MCI)',
                'nguy_co_cao': 'Nguy cơ cao - Suy giảm nhận thức trung bình đến nặng'
            }
            classification = classification_map.get(classification, classification)
        else:
            # Fallback to old classification
            classification = self._classify_score(state.total_score or 0)
        state.classification = classification
        
        # ✅ v2.1_CORRECTED: Generate completion message from JSON format
        pronoun = state.greeting if state.greeting else "Bạn"
        pronoun_lower = pronoun.lower()
        
        # Try to load completion message format from JSON
        completion_format = None
        if 'completion_message' in self.questions_data:
            completion_format = self.questions_data['completion_message']
        
        # Build message according to JSON format
        if completion_format:
            # Greeting
            greeting_msg = self._replace_greeting(completion_format.get('greeting', ''), pronoun)
            summary_intro = self._replace_greeting(completion_format.get('summary_intro', ''), pronoun)
            message = f"{greeting_msg}\n\n{summary_intro}\n\n"
        else:
            # Fallback
            message = (
                f"🎉 Chúc mừng {pronoun_lower}! Chúng ta đã hoàn thành bài kiểm tra rồi!\n\n"
                f"Đây là kết quả của {pronoun_lower} nhé:\n\n"
            )
        
        # Score format
        score_format = completion_format.get('score_format', {}) if completion_format else {}
        raw_score = adjusted_score_result.raw_score if adjusted_score_result else (state.total_score or 0)
        adjusted_score = adjusted_score_result.adjusted_score if adjusted_score_result else raw_score
        
        # Get risk level label
        risk_level = state.mci_result.get('risk_level', 'on') if state.mci_result else 'on'
        risk_level_labels = {
            'on': "✅ Ổn (Normal/Healthy Aging)",
            'nguy_co_nhe': "⚠️ Nguy cơ nhẹ (Mild Risk/Possible MCI)",
            'nguy_co_cao': "🚨 Nguy cơ cao (High Risk/Probable MCI or Dementia)"
        }
        risk_level_label = risk_level_labels.get(risk_level, classification)
        
        # Total score
        total_score_msg = score_format.get('total', '**Tổng điểm MMSE:** {total_score}/35 điểm')
        message += total_score_msg.replace('{total_score}', f"{raw_score:.1f}")
        message += "\n"
        
        # Adjusted score
        if adjusted_score_result:
            adjusted_msg = score_format.get('adjusted', '**Điểm sau điều chỉnh:** {adjusted_score} điểm (điều chỉnh theo tuổi và học vấn)')
            adjusted_msg = adjusted_msg.replace('{adjusted_score}', f"{adjusted_score:.1f}")
            age = int(state.user_info.get('age', 65))
            education_years = int(state.user_info.get('education_years', 12))
            adjusted_msg = adjusted_msg.replace('{age}', str(age))
            adjusted_msg = adjusted_msg.replace('{education_years}', str(education_years))
            message += adjusted_msg + "\n"
        
        # Classification
        classification_msg = score_format.get('classification', '**Phân loại:** {risk_level}')
        message += classification_msg.replace('{risk_level}', risk_level_label)
        message += "\n\n"
        
        # Domain breakdown
        domain_breakdown = completion_format.get('domain_breakdown', {}) if completion_format else {}
        domain_title = domain_breakdown.get('title', '**Chi tiết từng phần:**')
        message += f"{domain_title}\n"
        
        domain_names = {
            "orientation": "Định hướng",
            "registration": "Ghi nhận",
            "attention_calculation": "Chú ý & Tính toán",
            "executive_function": "Chức năng điều hành",  # ✅ v2.1: Added
            "recall": "Nhớ lại",
            "language": "Ngôn ngữ",
            "visuospatial": "Hình dung không gian"
        }
        
        # ✅ v2.1_CORRECTED: Domain max points (35-point scale)
        domain_max = {
            "orientation": 10,
            "registration": 3,
            "attention_calculation": 5,
            "executive_function": 3,  # ✅ v2.1: Added
            "recall": 3,
            "language": 8,
            "visuospatial": 3
        }
        
        domain_format = domain_breakdown.get('format', '• {domain_name}: {score}/{max_points} điểm')
        for domain, score in state.domain_scores.items():
            name = domain_names.get(domain, domain)
            max_score = domain_max.get(domain, 1)
            domain_line = domain_format.replace('{domain_name}', name)
            domain_line = domain_line.replace('{score}', str(score))
            domain_line = domain_line.replace('{max_points}', str(max_score))
            message += domain_line + "\n"
        
        # ✅ v2.1: Multimodal analysis
        if state.mci_result:
            multimodal = completion_format.get('multimodal_analysis', {}) if completion_format else {}
            multimodal_title = multimodal.get('title', '**🧬 Phân tích đa phương thức (Multimodal Analysis):**')
            message += f"\n{multimodal_title}\n"
            
            # Acoustic features
            acoustic_msg = multimodal.get('acoustic', '• Đặc trưng âm thanh: {acoustic_feature_count} features')
            acoustic_count = state.mci_result.get('acoustic_feature_count', 0)
            message += acoustic_msg.replace('{acoustic_feature_count}', str(acoustic_count)) + "\n"
            
            # Linguistic features
            linguistic_msg = multimodal.get('linguistic', '• Đặc trưng ngôn ngữ: {linguistic_feature_count} features')
            linguistic_count = state.mci_result.get('linguistic_feature_count', 0)
            message += linguistic_msg.replace('{linguistic_feature_count}', str(linguistic_count)) + "\n"
            
            # Combined risk score
            if 'combined_risk_score' in state.mci_result:
                combined_risk = state.mci_result['combined_risk_score']
                mci_risk_msg = multimodal.get('mci_risk', '• Ước tính nguy cơ MCI: **{mci_probability}%**')
                message += mci_risk_msg.replace('{mci_probability}', f"{combined_risk * 100:.1f}") + "\n"
                
                # Risk components
                if 'risk_components' in state.mci_result:
                    components = state.mci_result['risk_components']
                    message += f"• Điểm MMSE đóng góp: {(components.get('mmse', 0) * 100):.1f}%\n"
                    message += f"• Đặc trưng âm thanh: {(components.get('acoustic', 0) * 100):.1f}%\n"
                    message += f"• Đặc trưng ngôn ngữ: {(components.get('linguistic', 0) * 100):.1f}%\n"
                    message += f"• **Nguy cơ tổng hợp: {(combined_risk * 100):.1f}%**\n"
            
            # Interpretation
            if 'interpretation' in state.mci_result:
                interpretation_msg = multimodal.get('interpretation', '• Diễn giải: {risk_interpretation}')
                interpretation = state.mci_result['interpretation']
                message += interpretation_msg.replace('{risk_interpretation}', interpretation) + "\n"
        
        # ✅ v2.1: Recommendations based on risk level
        recommendations = completion_format.get('recommendations', {}) if completion_format else {}
        if risk_level in recommendations:
            rec_data = recommendations[risk_level]
            rec_title = self._replace_greeting(rec_data.get('title', ''), pronoun)
            rec_message = self._replace_greeting(rec_data.get('message', ''), pronoun)
            message += f"\n{rec_title}\n{rec_message}\n"
        
        # ✅ v2.1: Add doctor-style SHAP explanation if available
        if state.mci_result and state.mci_result.get('risk_components'):
            try:
                from modules.doctor_style_explanation import generate_doctor_style_explanation
                
                # Prepare SHAP values from risk components
                shap_values = {}
                risk_components = state.mci_result.get('risk_components', {})
                
                # Convert risk components to SHAP-like format
                for component_name, component_value in risk_components.items():
                    # Map component names to feature names
                    feature_map = {
                        'mmse': 'mmse_adjusted_score',
                        'acoustic': 'pause_ratio',  # Representative acoustic feature
                        'linguistic': 'TTR'  # Representative linguistic feature
                    }
                    feature_name = feature_map.get(component_name, component_name)
                    shap_values[feature_name] = {'value': component_value}
                
                # Add domain-specific SHAP values if available
                if state.domain_scores:
                    for domain, score in state.domain_scores.items():
                        domain_max = {
                            "orientation": 10,
                            "registration": 3,
                            "attention_calculation": 5,
                            "executive_function": 3,
                            "recall": 3,
                            "language": 8,
                            "visuospatial": 3
                        }
                        max_score = domain_max.get(domain, 1)
                        normalized_score = score / max_score if max_score > 0 else 0
                        # Lower score = higher risk (positive SHAP)
                        shap_value = 1.0 - normalized_score
                        shap_values[f'mmse_{domain}'] = {'value': shap_value}
                
                # Generate doctor-style explanation
                doctor_explanation = generate_doctor_style_explanation(
                    shap_values=shap_values,
                    multimodal_result=state.mci_result,
                    user_info=state.user_info
                )
                
                message += doctor_explanation
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate doctor-style explanation: {e}")
                import traceback
                traceback.print_exc()
        
        # Closing
        closing = completion_format.get('closing', '') if completion_format else ''
        if closing:
            message += f"\n{self._replace_greeting(closing, pronoun)}"
        else:
            message += f"\n💝 Cảm ơn {pronoun_lower} đã tham gia bài kiểm tra!\n"
            message += f"Kết quả này sẽ giúp bác sĩ đánh giá tình trạng sức khỏe của {pronoun_lower} tốt hơn."
        
        # ✅ v2.1: Enhanced metadata with all results
        metadata = {
            "completed": True,
            "total_score": state.total_score,
            "raw_score": raw_score,
            "adjusted_score": adjusted_score if adjusted_score_result else None,
            "domain_scores": state.domain_scores,
            "classification": classification,
            "risk_level": risk_level,
            "risk_level_label": risk_level_label,
            "session_id": session_id,
            "mci_result": state.mci_result,
            "adjusted_score_result": {
                "raw_score": adjusted_score_result.raw_score if adjusted_score_result else None,
                "age_penalty": adjusted_score_result.age_penalty if adjusted_score_result else None,
                "education_bonus": adjusted_score_result.education_bonus if adjusted_score_result else None,
                "adjusted_score": adjusted_score_result.adjusted_score if adjusted_score_result else None,
                "education_group": adjusted_score_result.education_group if adjusted_score_result else None
            } if adjusted_score_result else None
        }
        try:
            from services.comprehensive_results_generator import generate_comprehensive_results
            
            # Generate SHAP explanations if available
            shap_explanations = None
            if state.mci_result:
                # Try to get SHAP from risk components
                shap_explanations = {
                    'feature_contributions': {},
                    'grouped_contributions': state.mci_result.get('risk_components', {})
                }
            
            # Generate comprehensive results
            comprehensive_results = generate_comprehensive_results(
                session_state=state,
                shap_explanations=shap_explanations
            )
            
            # Add to metadata
            metadata['comprehensive_results'] = comprehensive_results
            logger.info("✅ Comprehensive results generated with SHAP, citations, and thresholds")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate comprehensive results: {e}")
            import traceback
            traceback.print_exc()
        
        return message, metadata
    
    def _calculate_all_scores(self, state: SessionState):
        """
        Calculate all domain scores using rule-based scoring from JSON
        Scores are already calculated per-question in submit_answer()
        This function aggregates them by domain
        """
        
        # ✅ v2.1_CORRECTED: Use rule-based scores already calculated
        if hasattr(state, 'question_scores') and state.question_scores:
            # Aggregate scores by domain (35-point scale)
            state.domain_scores = {
                "orientation": 0,
                "registration": 0,
                "attention_calculation": 0,
                "recall": 0,
                "language": 0,
                "visuospatial": 0,
                "executive_function": 0  # ✅ v2.1: Added executive function domain
            }
            
            # Map question IDs to domains (v2.1_CORRECTED structure)
            for q_id, score in state.question_scores.items():
                if q_id.startswith('ori_'):
                    state.domain_scores["orientation"] += score
                elif q_id.startswith('reg_'):
                    state.domain_scores["registration"] += score
                elif q_id.startswith('attn_') or q_id.startswith('att_'):
                    state.domain_scores["attention_calculation"] += score
                elif q_id.startswith('recall_'):
                    state.domain_scores["recall"] += score
                elif q_id.startswith('lang_') or q_id.startswith('name_') or q_id.startswith('rep_'):
                    state.domain_scores["language"] += score
                elif q_id.startswith('vis_') or q_id.startswith('draw_') or q_id.startswith('visual_'):
                    state.domain_scores["visuospatial"] += score
                elif q_id.startswith('exec_') or q_id.startswith('flu_'):
                    state.domain_scores["executive_function"] += score
            
            # Calculate total from question scores (should be 0-35)
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
                "visuospatial": 0,
                "executive_function": 0  # ✅ v2.1: Added executive function
            }
            state.total_score = 0
        
        # Extract linguistic features from all responses
        state.linguistic_features = self._extract_linguistic_features(state)
        
        logger.info(f"✅ Scores calculated (rule-based v2.1): Total={state.total_score}/35")
    
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
    
    def _extract_features_parallel(
        self,
        audio_path: str,
        transcript: str,
        timeout: int = 60
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        ✅ OPTIMIZATION: Extract acoustic & linguistic features in parallel
        
        Args:
            audio_path: Path to audio file
            transcript: Transcribed text
            timeout: Maximum time to wait (seconds)
        
        Returns:
            Tuple of (acoustic_features, linguistic_features_dict)
        """
        start_time = time.time()
        logger.info("🚀 Starting PARALLEL feature extraction...")
        
        try:
            # Submit both tasks simultaneously
            acoustic_future = None
            linguistic_future = None
            
            if self.acoustic_analyzer:
                logger.info(f"  📤 Submitting acoustic analysis task...")
                acoustic_future = self.executor.submit(
                    self._extract_acoustic_safe,
                    audio_path,
                    transcript
                )
            else:
                logger.warning("  ⚠️ Acoustic analyzer not available")
            
            if self.linguistic_analyzer and transcript:
                logger.info(f"  📤 Submitting linguistic analysis task...")
                linguistic_future = self.executor.submit(
                    self._extract_linguistic_safe,
                    transcript
                )
            else:
                if not self.linguistic_analyzer:
                    logger.warning("  ⚠️ Linguistic analyzer not available")
                if not transcript:
                    logger.warning("  ⚠️ No transcript provided for linguistic analysis")
            
            # Wait for both to complete (with timeout)
            acoustic_features = {}
            linguistic_features = {}
            
            if acoustic_future:
                logger.info(f"  ⏳ Waiting for acoustic analysis (timeout: {timeout}s)...")
                acoustic_features = acoustic_future.result(timeout=timeout)
                logger.info(f"  ✅ Acoustic analysis completed: {len(acoustic_features)} features")
            
            if linguistic_future:
                logger.info(f"  ⏳ Waiting for linguistic analysis (timeout: {timeout}s)...")
                linguistic_features = linguistic_future.result(timeout=timeout)
                logger.info(f"  ✅ Linguistic analysis completed: {len(linguistic_features)} features")
            
            elapsed = time.time() - start_time
            logger.info(f"✅ PARALLEL feature extraction completed in {elapsed:.2f}s")
            logger.info(f"   - Acoustic: {len(acoustic_features)} features")
            logger.info(f"   - Linguistic: {len(linguistic_features)} features")
            
            return acoustic_features, linguistic_features
            
        except FuturesTimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"❌ Feature extraction timeout after {elapsed:.0f}s")
            # Return empty features instead of crashing
            return {}, {}
        
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Feature extraction failed after {elapsed:.2f}s: {e}", exc_info=True)
            # Return empty features instead of crashing
            return {}, {}
    
    def _extract_acoustic_safe(self, audio_path: str, transcript: str = "") -> Dict[str, Any]:
        """
        Safe wrapper for acoustic analysis with error handling
        """
        try:
            start = time.time()
            logger.info(f"  🔊 Starting acoustic analysis: {audio_path}")
            features = self.acoustic_analyzer.extract_all_features(
                audio_path,
                transcript=transcript
            )
            elapsed = time.time() - start
            logger.info(f"  ✅ Acoustic analysis: {elapsed:.2f}s, {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"  ❌ Acoustic analysis failed: {e}", exc_info=True)
            # Return empty features instead of crashing
            return {}
    
    def _extract_linguistic_safe(self, transcript: str) -> Dict[str, float]:
        """
        Safe wrapper for linguistic analysis with error handling
        """
        try:
            start = time.time()
            logger.info(f"  📝 Starting linguistic analysis: {len(transcript)} chars")
            features = self.linguistic_analyzer.extract_all_features(
                transcript,
                task_type='mmse_assessment'
            )
            elapsed = time.time() - start
            logger.info(f"  ✅ Linguistic analysis: {elapsed:.2f}s, {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"  ❌ Linguistic analysis failed: {e}", exc_info=True)
            # Return empty features instead of crashing
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
    
    def _interpret_risk_level_v21(self, risk_level: str) -> str:
        """
        Interpret v2.1 risk level as clinical description
        
        Args:
            risk_level: 'on', 'nguy_co_nhe', or 'nguy_co_cao'
        
        Returns:
            str: Risk interpretation in Vietnamese
        """
        interpretations = {
            'on': 'Ổn - Chức năng nhận thức bình thường',
            'nguy_co_nhe': 'Nguy cơ nhẹ - Nên theo dõi định kỳ và tái khám',
            'nguy_co_cao': 'Nguy cơ cao - Khuyến nghị khám chuyên khoa sớm'
        }
        return interpretations.get(risk_level, 'Không xác định')
    
    def _get_domain_questions(self, domain: str) -> List[Dict]:
        """Get questions for a domain (v2.1_CORRECTED structure)"""
        # ✅ v2.1_CORRECTED: New JSON structure uses "questions" key with domain keys
        if 'questions' in self.questions_data:
            # New v2.1 structure
            questions_data = self.questions_data.get('questions', {})
            
            domain_mapping = {
                "orientation": "1_orientation",
                "registration": "2_registration",
                "attention_calculation": "3_attention_calculation",
                "open_questions": "5_open_questions",
                "recall": "6_recall",
                "language": "7_language",
                "visuospatial": "8_visuospatial",
                "executive_function": "4_executive_function"  # ✅ v2.1: Added executive function
            }
            
            domain_key = domain_mapping.get(domain)
            if domain_key and domain_key in questions_data:
                domain_obj = questions_data[domain_key]
                questions = domain_obj.get('questions', {})
                
                # Convert dict to list format expected by code
                question_list = []
                for q_id, q_data in questions.items():
                    q_item = q_data.copy()
                    q_item['question_id'] = q_id
                    question_list.append(q_item)
                
                logger.debug(f"✅ Loaded {len(question_list)} questions from v2.1 structure for domain {domain}")
                return question_list
        
        # Fallback: Old structure (v2.0)
        domain_mapping = {
            "orientation": "ORIENTATION",
            "registration": "REGISTRATION",
            "attention_calculation": "ATTENTION_CALCULATION",
            "recall": "RECALL",
            "language": "LANGUAGE",
            "visuospatial": "VISUOSPATIAL",
            "open_questions": "SUPPLEMENTARY_OPEN_QUESTIONS"
        }
        
        domain_code = domain_mapping.get(domain)
        
        # Old structure fallback
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
    
    def _extract_animals_from_text(self, text: str) -> List[str]:
        """
        Extract potential animal names from Vietnamese text
        
        Simple extraction - split text and filter out common stop words
        In production, use NLP or named entity recognition for better accuracy
        
        Args:
            text: Input text containing animal names
            
        Returns:
            List of potential animal names (words)
        """
        if not text or not text.strip():
            return []
        
        # Split by common separators
        words = re.split(r'[,\s]+', text.lower().strip())
        
        # Filter out empty strings and very short words
        words = [w.strip() for w in words if w.strip() and len(w.strip()) > 1]
        
        # Filter out common stop words and classifiers
        stop_words = {'con', 'cái', 'chiếc', 'cây', 'bài', 'của', 'và', 'hoặc', 'là', 'có', 'được', 'sẽ', 'đã', 'đang', 'rồi', 'nhé', 'ạ', 'ơi', 'nào', 'đó', 'này', 'khi', 'nếu', 'với', 'theo', 'từ', 'về', 'trong', 'ngoài', 'trên', 'dưới', 'sau', 'trước', 'giữa', 'bên'}
        animals = [w for w in words if w not in stop_words]
        
        return animals
    
    def _count_correct_serial7s_answers(self, answers: List[int]) -> int:
        """
        Count how many Serial 7s answers are objectively correct.
        Expected sequence: [93, 86, 79, 72, 65]
        
        Args:
            answers: List of user answers (integers)
            
        Returns:
            Number of correct answers
        """
        expected = [93, 86, 79, 72, 65]
        correct_count = 0
        
        for i, answer in enumerate(answers):
            if i < len(expected) and answer == expected[i]:
                correct_count += 1
                logger.debug(f"✓ Serial 7s Answer {i+1}: {answer} is correct (expected {expected[i]})")
            elif i < len(expected):
                logger.debug(f"✗ Serial 7s Answer {i+1}: {answer} is incorrect (expected {expected[i]})")
        
        logger.info(f"✅ Serial 7s correct count: {correct_count}/{len(answers)}")
        return correct_count
    
    def _replace_greeting(self, text: str, greeting: str) -> str:
        """
        ✅ v2.1_CORRECTED: Replace pronoun placeholders
        
        Supports:
        - {pronoun} → lowercase (ông/bà)
        - {Pronoun} → capitalized (Ông/Bà)
        - {greeting} → legacy support
        """
        # v2.1 uses {pronoun} and {Pronoun}
        text = text.replace("{pronoun}", greeting.lower() if greeting else "bạn")
        text = text.replace("{Pronoun}", greeting if greeting else "Bạn")
        # Legacy support
        text = text.replace("{greeting}", greeting if greeting else "Bạn")
        return text
    
    def _check_recall_allowed(self, state: SessionState) -> bool:
        """✅ v2.1_CORRECTED: Check if 6-minute (360 seconds) delay has passed for recall"""
        if not state.recall_allowed_after:
            return True  # No registration done yet
        
        allowed_time = datetime.fromisoformat(state.recall_allowed_after)
        return datetime.now() >= allowed_time
    
    def _get_recall_wait_time(self, state: SessionState) -> int:
        """✅ v2.1_CORRECTED: Get remaining seconds until recall is allowed (minimum 360 seconds)"""
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

