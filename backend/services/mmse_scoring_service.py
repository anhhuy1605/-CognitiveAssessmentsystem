"""
MMSE Scoring Service - Rule-Based Scoring from JSON
Uses question.points field and GPT-4o validation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

# Try to import OpenAI client
try:
    from app import openai_client
    OPENAI_AVAILABLE = openai_client is not None
except:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI client not available")


class MMSEScoringService:
    """
    Rule-based MMSE scoring service
    
    Loads questions from JSON and scores answers based on:
    - question.points field
    - GPT-4o validation of answer correctness
    """
    
    def __init__(self, questions_file: Optional[str] = None):
        """
        Initialize scoring service
        
        Args:
            questions_file: Path to mmse_audio_questions_standardized.json
        """
        if questions_file is None:
            # Default path
            questions_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'mmse_audio_questions_standardized.json'
            )
        
        self.questions_file = Path(questions_file)
        self.questions_db = {}
        
        self._load_questions()
    
    def _load_questions(self):
        """Load all questions from JSON file"""
        try:
            if not self.questions_file.exists():
                logger.error(f"❌ Questions file not found: {self.questions_file}")
                return
            
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            mmse_data = data.get('mmse_vietnamese_chatbot', {})
            domains = mmse_data.get('domains', [])
            
            # Build question database
            for domain in domains:
                questions = domain.get('questions', [])
                for q in questions:
                    question_id = q.get('question_id')
                    if question_id:
                        self.questions_db[question_id] = q
            
            logger.info(f"✅ Loaded {len(self.questions_db)} MMSE questions from {self.questions_file}")
            
        except Exception as e:
            logger.error(f"❌ Error loading questions: {e}")
            import traceback
            traceback.print_exc()
    
    def get_question_data(self, question_id: str) -> Optional[Dict]:
        """
        Get question data by ID
        
        Args:
            question_id: Question identifier (e.g., 'ori_time_01')
        
        Returns:
            Question data dict or None if not found
        """
        return self.questions_db.get(question_id)
    
    def score_answer(self, question_id: str, transcript: str) -> Dict:
        """
        Score user answer against question
        
        Args:
            question_id: Question identifier
            transcript: User's transcribed answer
        
        Returns:
            {
                'question_id': str,
                'transcript': str,
                'is_correct': bool,
                'points_earned': int,
                'points_possible': int,
                'feedback': str,
                'matched_elements': list  # For multi-part questions
            }
        """
        question = self.questions_db.get(question_id)
        if not question:
            logger.error(f"❌ Question not found: {question_id}")
            raise ValueError(f"Question not found: {question_id}")
        
        # Get validation from GPT-4o
        validation = self._validate_with_gpt(transcript, question)
        
        # Calculate points
        points_possible = question.get('points', 0)
        
        if 'scoring_details' in question:
            # Multi-part scoring (e.g., 3-word recall)
            matched = validation.get('matched_elements', [])
            points_earned = len(matched)
        else:
            # Binary scoring
            points_earned = points_possible if validation.get('is_correct', False) else 0
        
        # Get feedback template
        feedback = self._generate_feedback(question, validation, points_earned)
        
        return {
            'question_id': question_id,
            'transcript': transcript,
            'is_correct': validation.get('is_correct', False),
            'points_earned': points_earned,
            'points_possible': points_possible,
            'feedback': feedback,
            'matched_elements': validation.get('matched_elements', [])
        }
    
    def _validate_with_gpt(self, transcript: str, question: dict) -> Dict:
        """
        GPT-4o validates answer correctness
        
        Args:
            transcript: User's answer
            question: Question data from JSON
        
        Returns:
            {
                'is_correct': bool,
                'matched_elements': list,
                'explanation': str
            }
        """
        if not OPENAI_AVAILABLE:
            logger.warning("⚠️ OpenAI not available, using simple validation")
            # Simple fallback: check if transcript is not empty
            return {
                'is_correct': len(transcript.strip()) > 0,
                'matched_elements': [],
                'explanation': 'Validation unavailable'
            }
        
        # Build validation prompt
        question_text = question.get('chatbot_message', '')
        expected_format = question.get('expected_answer_format', '')
        acceptable_answers = question.get('acceptable_answers', [])
        scoring_details = question.get('scoring_details', {})
        fuzzy_matching = question.get('fuzzy_matching', {})
        
        prompt = f"""Validate this Vietnamese MMSE answer.

QUESTION: {question_text}
EXPECTED FORMAT: {expected_format}
ACCEPTABLE ANSWERS: {acceptable_answers}
USER TRANSCRIPT: {transcript}

For multi-word questions (e.g., recall 3 words), list each matched word in matched_elements.

Return JSON only:
{{
  "is_correct": true/false,
  "matched_elements": ["word1", "word2"],  // if applicable
  "explanation": "brief reason in Vietnamese"
}}

Rules:
- Be lenient with Vietnamese accent marks (mèo = meo)
- Allow synonyms if listed in acceptable_answers
- For multi-word answers, list each matched word separately
- Ignore filler words (ừ, ờ, à, thì, etc.)
- Focus on semantic match, not exact wording
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an MMSE answer validator for Vietnamese. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ GPT validation: is_correct={result.get('is_correct')}, matched={len(result.get('matched_elements', []))}")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT validation failed: {e}")
            # Fallback: simple validation
            return {
                'is_correct': len(transcript.strip()) > 0,
                'matched_elements': [],
                'explanation': f'Validation error: {str(e)[:50]}'
            }
    
    def _generate_feedback(self, question: dict, validation: dict, points_earned: int) -> str:
        """
        Generate user-friendly feedback
        
        Args:
            question: Question data
            validation: Validation result
            points_earned: Points earned for this answer
        
        Returns:
            Feedback message
        """
        templates = question.get('feedback_templates', {})
        
        # For multi-part questions
        if 'scoring_details' in question:
            max_points = question.get('points', 0)
            if points_earned == max_points:
                key = f'correct_{max_points}'
            else:
                key = f'correct_{points_earned}'
            
            feedback = templates.get(key, templates.get('correct_0', ''))
        else:
            # Binary feedback
            if validation.get('is_correct', False):
                feedback = templates.get('correct', 'Đúng rồi!')
            else:
                feedback = templates.get('incorrect', 'Chưa đúng. Hãy thử lại.')
        
        # Replace placeholders
        matched = validation.get('matched_elements', [])
        if matched:
            feedback = feedback.replace('{user_answer}', ', '.join(matched))
        else:
            feedback = feedback.replace('{user_answer}', '')
        
        feedback = feedback.replace('{greeting}', 'bạn')  # Use session greeting if available
        
        return feedback
    
    def calculate_total_score(self, question_scores: Dict[str, int]) -> int:
        """
        Calculate total MMSE score from all question scores
        
        Args:
            question_scores: Dict {question_id: points_earned}
        
        Returns:
            Total score (0-30)
        """
        total = sum(question_scores.values())
        return min(max(0, total), 30)  # Clamp to 0-30

