"""
MMSE Scoring Service v2.1 FINAL - Rule-Based + GPT-4o
Perfectly aligned with mmse_audio_questions_standardized.json v2.1
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Import OpenAI client
try:
    from app import openai_client
    OPENAI_AVAILABLE = openai_client is not None
    if OPENAI_AVAILABLE:
        logger.info("✅ OpenAI client available for GPT-4o scoring")
except:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️ OpenAI client not available")


class MMSEScoringService:
    """
    MMSE Scoring Service with JSON-based validation
    
    Features:
    - Loads from v2.1 JSON structure
    - Rule-based validation with fuzzy matching
    - GPT-4o fallback for complex questions
    - Dynamic answer resolution
    """
    
    def __init__(self, questions_file: Optional[str] = None):
        if questions_file is None:
            questions_file = self._find_questions_file()
        
        self.questions_file = Path(questions_file)
        self.questions_db = {}
        
        self._load_questions()
        logger.info(f"✅ MMSEScoringService initialized with {len(self.questions_db)} questions")
    
    def _find_questions_file(self) -> str:
        """Find questions JSON in multiple locations"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'mmse_audio_questions_standardized.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'mmse_audio_questions_standardized.json'),
            os.path.join(os.path.dirname(__file__), 'mmse_audio_questions_standardized.json'),
            '/app/mmse_audio_questions_standardized.json',
            '/app/backend/mmse_audio_questions_standardized.json',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found questions: {path}")
                return path
        
        raise FileNotFoundError("❌ mmse_audio_questions_standardized.json not found")
    
    def _load_questions(self):
        """Load questions from v2.1 JSON structure"""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # v2.1: questions -> 1_orientation -> questions -> ori_time_01
            if 'questions' in data:
                questions_obj = data['questions']
                
                for domain_key, domain_data in questions_obj.items():
                    if domain_key == 'greeting':
                        continue
                    
                    domain_questions = domain_data.get('questions', {})
                    
                    for q_id, q_data in domain_questions.items():
                        q_data['question_id'] = q_id
                        self.questions_db[q_id] = q_data
                        logger.debug(f"✅ Indexed: {q_id} ({q_data.get('points', 0)} pts)")
            
            logger.info(f"✅ Loaded {len(self.questions_db)} questions")
            
        except Exception as e:
            logger.error(f"❌ Failed to load questions: {e}")
            raise
    
    def get_question_data(self, question_id: str) -> Optional[Dict]:
        """Get question by ID (with normalization)"""
        question_id = self._normalize_question_id(question_id)
        return self.questions_db.get(question_id)
    
    def _normalize_question_id(self, question_id: str) -> str:
        """
        ✅ Normalize question_id to fix typos
        ori_ttime_01 → ori_time_01
        """
        normalized = re.sub(r'(.)\1+', r'\1', question_id)
        
        typo_map = {
            'ori_ttime': 'ori_time',
            'att_': 'attn_',
        }
        
        for typo, correct in typo_map.items():
            if typo in normalized:
                normalized = normalized.replace(typo, correct)
        
        if normalized != question_id:
            logger.warning(f"⚠️ Normalized: {question_id} → {normalized}")
        
        return normalized
    
    def score_answer(self, question_id: str, transcript: str, user_info: Optional[Dict] = None) -> Dict:
        """
        Score answer using JSON rules + GPT-4o validation
        
        Returns:
            {
                'question_id': str,
                'transcript': str,
                'is_correct': bool,
                'points_earned': int,
                'points_possible': int,
                'feedback': str,
                'matched_elements': list
            }
        """
        question_id = self._normalize_question_id(question_id)
        
        question = self.questions_db.get(question_id)
        if not question:
            logger.error(f"❌ Question not found: {question_id}")
            logger.error(f"   Available: {list(self.questions_db.keys())[:10]}...")
            raise ValueError(f"Question not found: {question_id}")
        
        points_possible = question.get('points', 1)
        
        # Validate answer
        validation = self._validate_answer(transcript, question, user_info)
        
        # Calculate points
        scoring_method = question.get('scoring', {}).get('method', 'binary')
        
        if scoring_method == 'count_matched_keywords':
            # For recall/registration
            matched = validation.get('matched_elements', [])
            points_earned = len(matched)
        elif scoring_method == 'count_objectively_correct':
            # For serial 7s
            matched = validation.get('matched_elements', [])
            points_earned = len(matched)
        elif scoring_method == 'count_unique_animals':
            # For verbal fluency
            count = validation.get('animal_count', 0)
            scoring_rules = question.get('scoring', {})
            if count >= 15:
                points_earned = 2
            elif count >= 9:
                points_earned = 1
            else:
                points_earned = 0
        elif scoring_method == 'count_steps_completed':
            # For 3-step command
            matched = validation.get('matched_elements', [])
            points_earned = len(matched)
        else:
            # Binary scoring
            points_earned = points_possible if validation.get('is_correct', False) else 0
        
        # Generate feedback
        feedback = self._generate_feedback(question, validation, points_earned, points_possible)
        
        logger.info(f"✅ Scored {question_id}: {points_earned}/{points_possible}")
        
        return {
            'question_id': question_id,
            'transcript': transcript,
            'is_correct': validation.get('is_correct', False),
            'points_earned': points_earned,
            'points_possible': points_possible,
            'feedback': feedback,
            'matched_elements': validation.get('matched_elements', [])
        }
    
    def _validate_answer(self, transcript: str, question: dict, user_info: Optional[Dict] = None) -> Dict:
        """
        Validate answer using rules + GPT-4o
        
        Priority:
        1. Rule-based validation (fast, accurate for simple questions)
        2. GPT-4o validation (for complex questions)
        """
        question_id = question.get('question_id', '')
        
        # Try rule-based first
        rule_result = self._rule_based_validation(transcript, question, user_info)
        
        # If high confidence, return immediately
        if rule_result.get('confidence', 0) >= 0.9:
            logger.debug(f"✅ Rule-based validation (high confidence): {question_id}")
            return rule_result
        
        # Otherwise, use GPT-4o for better accuracy
        if OPENAI_AVAILABLE:
            try:
                gpt_result = self._validate_with_gpt(transcript, question, user_info)
                logger.debug(f"✅ GPT-4o validation: {question_id}")
                return gpt_result
            except Exception as e:
                logger.warning(f"⚠️ GPT-4o failed, using rule-based: {e}")
                return rule_result
        else:
            return rule_result
    
    def _rule_based_validation(self, transcript: str, question: dict, user_info: Optional[Dict] = None) -> Dict:
        """
        Fast rule-based validation
        Returns: {is_correct, matched_elements, confidence}
        """
        transcript_lower = transcript.lower().strip()
        
        # Resolve correct answer
        correct_answer = self._resolve_dynamic_answer(
            question.get('correct_answer', ''),
            user_info
        )
        
        acceptable_variations = question.get('acceptable_variations', [])
        
        # 1. Direct match
        if correct_answer and transcript_lower == correct_answer.lower():
            return {'is_correct': True, 'matched_elements': [], 'confidence': 1.0}
        
        # 2. Check acceptable variations
        for variation in acceptable_variations:
            if self._fuzzy_match(transcript_lower, variation.lower(), threshold=0.85):
                return {'is_correct': True, 'matched_elements': [], 'confidence': 0.95}
        
        # 3. Special handling for recall/registration
        if 'words_to_recall' in question or 'keywords' in question:
            keywords = question.get('keywords', [])
            if not keywords:
                words = question.get('words_to_recall', question.get('words', []))
                keywords = self._extract_keywords(words)
            
            matched = []
            for keyword in keywords:
                if keyword.lower() in transcript_lower or self._fuzzy_match(transcript_lower, keyword, 0.8):
                    matched.append(keyword)
            
            is_correct = len(matched) == len(keywords)
            return {
                'is_correct': is_correct,
                'matched_elements': matched,
                'confidence': 0.9
            }
        
        # 4. Number extraction (for date/year)
        if correct_answer and correct_answer.isdigit():
            numbers = re.findall(r'\d+', transcript)
            if numbers and numbers[0] == correct_answer:
                return {'is_correct': True, 'matched_elements': [], 'confidence': 1.0}
        
        # 5. Fuzzy match with correct answer
        if correct_answer and self._fuzzy_match(transcript_lower, correct_answer.lower(), 0.8):
            return {'is_correct': True, 'matched_elements': [], 'confidence': 0.85}
        
        # Default: uncertain, needs GPT-4o
        return {'is_correct': False, 'matched_elements': [], 'confidence': 0.5}
    
    def _validate_with_gpt(self, transcript: str, question: dict, user_info: Optional[Dict] = None) -> Dict:
        """GPT-4o validation (kept from original - too long to repeat here)"""
        # [Keep the original GPT-4o validation code from your document]
        # This is the same implementation as before
        
        question_text = question.get('question', '')
        question_id = question.get('question_id', '')
        correct_answer = self._resolve_dynamic_answer(question.get('correct_answer', ''), user_info)
        acceptable_variations = question.get('acceptable_variations', [])
        words = question.get('words_to_recall', question.get('words', []))
        
        now = datetime.now()
        current_date = {
            'day': now.day,
            'month': now.month,
            'year': now.year,
            'weekday_vn': ['thứ hai', 'thứ ba', 'thứ tư', 'thứ năm', 'thứ sáu', 'thứ bảy', 'chủ nhật'][now.weekday()],
            'time_of_day': 'sáng' if now.hour < 12 else 'trưa' if now.hour < 14 else 'chiều' if now.hour < 18 else 'tối'
        }
        
        user_context = ""
        if user_info:
            city = user_info.get('city', '')
            district = user_info.get('district', '')
            if city or district:
                user_context = f"\n📍 THÔNG TIN NGƯỜI DÙNG:\n"
                if city:
                    user_context += f"Thành phố: {city}\n"
                if district:
                    user_context += f"Quận/Huyện: {district}\n"
        
        prompt = f"""Bạn là chuyên gia MMSE. Đánh giá câu trả lời sau:

CÂU HỎI: {question_text}
CÂU TRẢ LỜI: "{transcript}"

ĐÁP ÁN CHUẨN: {correct_answer if correct_answer else 'Không cố định'}
BIẾN THỂ CHẤP NHẬN: {', '.join(acceptable_variations) if acceptable_variations else 'Không có'}
TỪ CẦN NHỚ: {', '.join(words) if words else 'Không có'}

THÔNG TIN THỜI GIAN HIỆN TẠI:
- Ngày: {current_date['day']}
- Tháng: {current_date['month']}
- Năm: {current_date['year']}
- Thứ: {current_date['weekday_vn']}
- Buổi: {current_date['time_of_day']}

{user_context}

QUY TẮC:
1. Bỏ qua dấu thanh, HOA/thường
2. Bỏ qua filler words (ừ, ờ, à, thì, đó, nhé, ạ)
3. Tập trung vào ý nghĩa, không phải từ ngữ chính xác
4. Chấp nhận biến thể hợp lý (thứ 6 = thứ sáu = t6)
5. Nếu ý nghĩa đúng → CHO ĐIỂM

Trả về JSON:
{{
  "is_correct": true/false,
  "matched_elements": ["keyword1", "keyword2"],
  "explanation": "Giải thích ngắn gọn"
}}

- matched_elements: CHỈ cho recall/registration (liệt kê TỪ KHÓA)
- Với câu khác: matched_elements = []"""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Vietnamese MMSE expert. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ GPT: {question_id} → correct={result.get('is_correct')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT failed: {e}")
            return {'is_correct': False, 'matched_elements': [], 'explanation': f'Error: {e}'}
    
    def _resolve_dynamic_answer(self, correct_answer: str, user_info: Optional[Dict] = None) -> str:
        """Resolve dynamic answers like dynamic_current_year"""
        if not correct_answer or not correct_answer.startswith('dynamic_'):
            return correct_answer
        
        now = datetime.now()
        
        if correct_answer == 'dynamic_current_year':
            return str(now.year)
        elif correct_answer == 'dynamic_current_month':
            return f"tháng {now.month}"
        elif correct_answer == 'dynamic_current_date':
            return str(now.day)
        elif correct_answer == 'dynamic_current_weekday':
            weekdays = ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"]
            return weekdays[now.weekday()]
        elif correct_answer == 'dynamic_current_time_period':
            hour = now.hour
            if 5 <= hour < 12:
                return "sáng"
            elif 12 <= hour < 14:
                return "trưa"
            elif 14 <= hour < 18:
                return "chiều"
            else:
                return "tối"
        elif correct_answer == 'dynamic_from_user_region' and user_info:
            city = user_info.get('city', '').lower()
            north = ['hà nội', 'hải phòng', 'quảng ninh']
            central = ['đà nẵng', 'huế', 'quảng nam']
            south = ['tp.hcm', 'hồ chí minh', 'cần thơ']
            
            if any(c in city for c in north):
                return "miền bắc"
            elif any(c in city for c in central):
                return "miền trung"
            elif any(c in city for c in south):
                return "miền nam"
        elif correct_answer.startswith('dynamic_from_user_') and user_info:
            field = correct_answer.replace('dynamic_from_user_', '')
            return user_info.get(field, '')
        
        return correct_answer
    
    def _extract_keywords(self, words: List[str]) -> List[str]:
        """Extract keywords from word list (remove classifiers)"""
        keywords = []
        for word in words:
            parts = word.strip().split()
            if parts:
                keywords.append(parts[-1].lower())
        return keywords
    
    def _fuzzy_match(self, text: str, target: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching"""
        if not text or not target:
            return False
        
        if target in text or text in target:
            return True
        
        import difflib
        ratio = difflib.SequenceMatcher(None, text, target).ratio()
        return ratio >= threshold
    
    def _generate_feedback(self, question: dict, validation: dict, points_earned: int, points_possible: int) -> str:
        """Generate feedback based on score"""
        feedback_templates = question.get('feedback', {})
        
        # ✅ FIX: Ensure feedback_templates is a dict, not a string
        if not isinstance(feedback_templates, dict):
            logger.warning(f"⚠️ feedback_templates is not a dict (type: {type(feedback_templates)}), using default")
            feedback_templates = {}
        
        # Map points to feedback key
        if points_earned == points_possible:
            key = f"{points_possible}_correct" if points_possible > 1 else "correct"
        elif points_earned == 0:
            key = "0_correct" if points_possible > 1 else "incorrect"
        else:
            key = f"{points_earned}_correct"
        
        # ✅ FIX: Safe get with fallback
        feedback = feedback_templates.get(key)
        if not feedback:
            fallback_key = 'correct' if validation.get('is_correct') else 'incorrect'
            feedback = feedback_templates.get(fallback_key, 'Cảm ơn!')
        
        # ✅ FIX: Ensure feedback is a string
        if not isinstance(feedback, str):
            feedback = str(feedback) if feedback else 'Cảm ơn!'
        
        # Replace placeholders
        correct_answer = question.get('correct_answer', '')
        feedback = feedback.replace('{correct_answer}', str(correct_answer))
        feedback = feedback.replace('{points_earned}', str(points_earned))
        feedback = feedback.replace('{points_possible}', str(points_possible))
        feedback = feedback.replace('{count}', str(validation.get('animal_count', 0)))
        
        return feedback


# Global instance
_scoring_service: Optional[MMSEScoringService] = None

def get_mmse_scoring_service() -> MMSEScoringService:
    """Get or create global scoring service"""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = MMSEScoringService()
    return _scoring_service