#!/usr/bin/env python3
"""
ASR Processor for Speech-based MMSE Assessment
==============================================

Handles automatic speech recognition and word matching for MMSE evaluation:
- Whisper/Gemini ASR integration
- Fuzzy string matching for word recognition
- Confidence scoring and uncertainty estimation
- Vietnamese language support
- Automatic scoring for registration/recall items

Author: AI Assistant
Date: September 2025
"""

import logging
from typing import Dict, List, Tuple, Optional, Union, Any
import re
import unicodedata
from difflib import SequenceMatcher
# import jellyfish  # For advanced string similarity (optional)
import numpy as np

logger = logging.getLogger(__name__)


class ASRProcessor:
    """
    Comprehensive ASR processor for MMSE assessment with fuzzy matching.

    Handles:
    - Speech-to-text transcription
    - Word-level fuzzy matching
    - Confidence scoring
    - Vietnamese language processing
    - Automatic item scoring
    """

    # Vietnamese word lists for MMSE items
    VIETNAMESE_WORDS = {
        'registration': ['cái bàn', 'đồng hồ', 'bút chì'],  # Table, watch, pencil
        'recall': ['cái bàn', 'đồng hồ', 'bút chì'],       # Same as registration
        'naming': ['đồng hồ', 'bút chì'],                  # Watch, pencil
        'semantic_fluency': []  # Will be filled based on task
    }

    # English fallbacks (if needed)
    ENGLISH_WORDS = {
        'registration': ['table', 'watch', 'pencil'],
        'recall': ['table', 'watch', 'pencil'],
        'naming': ['watch', 'pencil'],
        'semantic_fluency': []
    }

    def __init__(self,
                 language: str = 'vi',
                 use_whisper: bool = True,
                 use_gemini: bool = False,
                 similarity_threshold: float = 0.8,
                 confidence_threshold: float = 0.6):
        """
        Initialize ASR processor.

        Args:
            language: Language code ('vi' for Vietnamese, 'en' for English)
            use_whisper: Whether to use Whisper for ASR
            use_gemini: Whether to use Gemini as backup ASR
            similarity_threshold: Minimum similarity for word matching
            confidence_threshold: Minimum confidence for auto-scoring
        """
        self.language = language
        self.use_whisper = use_whisper
        self.use_gemini = use_gemini
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold

        # Initialize ASR models
        self.whisper_model = None
        self.gemini_client = None

        if self.use_whisper:
            self._init_whisper()
        if self.use_gemini:
            self._init_gemini()

        # Word lists based on language
        self.word_lists = self.VIETNAMESE_WORDS if language == 'vi' else self.ENGLISH_WORDS

        # Compile regex patterns for better matching
        self._compile_patterns()

        logger.info("✅ ASR Processor initialized")

    def _init_whisper(self):
        """Initialize Whisper model for ASR."""
        try:
            import whisper
            # Use smaller model for speed, can upgrade to larger model later
            self.whisper_model = whisper.load_model("base")
            logger.info("✅ Whisper model loaded (base model)")
        except ImportError:
            logger.warning("⚠️ Whisper not available, ASR will be limited")
            self.use_whisper = False

    def _init_gemini(self):
        """Initialize Gemini client for ASR."""
        try:
            import google.generativeai as genai
            # Will be configured with API key when available
            self.gemini_client = None  # Placeholder
            logger.info("✅ Gemini ASR ready (API key needed)")
        except ImportError:
            logger.warning("⚠️ Gemini not available")
            self.use_gemini = False

    def _compile_patterns(self):
        """Compile regex patterns for word matching."""
        self.patterns = {}

        for category, words in self.word_lists.items():
            self.patterns[category] = []
            for word in words:
                # Create flexible pattern with word boundaries
                # Handle Vietnamese diacritics and case insensitivity
                pattern = r'\b' + re.escape(self._normalize_text(word)) + r'\b'
                self.patterns[category].append(re.compile(pattern, re.IGNORECASE | re.UNICODE))

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching (remove accents, lowercase, etc.)."""
        # Convert to lowercase
        text = text.lower()

        # Normalize Unicode (handle Vietnamese diacritics)
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with transcription results
        """
        result = {
            'transcription': '',
            'confidence': 0.0,
            'language': self.language,
            'duration': 0.0,
            'method': 'none'
        }

        try:
            # Try Whisper first
            if self.use_whisper and self.whisper_model:
                whisper_result = self.whisper_model.transcribe(
                    audio_path,
                    language=self.language if self.language == 'vi' else None
                )

                result['transcription'] = whisper_result['text'].strip()
                result['confidence'] = float(np.mean([seg.get('confidence', 0.8)
                                                    for seg in whisper_result.get('segments', [])]))
                result['method'] = 'whisper'

                # Get audio duration
                try:
                    import librosa
                    duration = librosa.get_duration(filename=audio_path)
                    result['duration'] = duration
                except:
                    result['duration'] = 0.0

                logger.info(f"✅ Whisper transcription: '{result['transcription'][:50]}...' (conf: {result['confidence']:.2f})")

            # Fallback to Gemini if Whisper fails or confidence is low
            elif self.use_gemini and self.gemini_client and result['confidence'] < 0.5:
                # Gemini ASR implementation would go here
                # For now, return placeholder
                logger.info("ℹ️ Gemini ASR not implemented yet")
                result['method'] = 'gemini_fallback'

            else:
                logger.warning("⚠️ No ASR method available")
                result['transcription'] = "[ASR not available]"
                result['confidence'] = 0.0

        except Exception as e:
            logger.error(f"❌ ASR transcription failed: {e}")
            result['transcription'] = "[ASR error]"
            result['confidence'] = 0.0

        return result

    def fuzzy_match_word(self, transcription: str, target_word: str) -> Dict[str, Any]:
        """
        Perform fuzzy matching between transcription and target word.

        Args:
            transcription: Full transcription text
            target_word: Target word to match

        Returns:
            Dictionary with matching results
        """
        # Normalize both texts
        norm_transcription = self._normalize_text(transcription)
        norm_target = self._normalize_text(target_word)

        # Multiple similarity measures
        similarities = {}

        # SequenceMatcher (edit distance based)
        seq_sim = SequenceMatcher(None, norm_transcription, norm_target).ratio()
        similarities['sequence'] = seq_sim

        # Jaro-Winkler distance approximation (simplified)
        try:
            # Simple Jaro-Winkler approximation using SequenceMatcher
            jaro_sim = SequenceMatcher(None, norm_transcription, norm_target).ratio()
            similarities['jaro_winkler'] = jaro_sim * 0.9  # Slight penalty for approximation
        except:
            similarities['jaro_winkler'] = 0.0

        # Levenshtein distance approximation using SequenceMatcher
        lev_sim = SequenceMatcher(None, norm_transcription, norm_target).ratio()
        similarities['levenshtein'] = lev_sim

        # Check for exact substring match
        substring_match = norm_target in norm_transcription
        similarities['substring'] = 1.0 if substring_match else 0.0

        # Regex pattern matching
        pattern_match = bool(re.search(r'\b' + re.escape(norm_target) + r'\b',
                                     norm_transcription, re.IGNORECASE))
        similarities['pattern'] = 1.0 if pattern_match else 0.0

        # Ensemble similarity (weighted average)
        weights = {
            'sequence': 0.2,
            'jaro_winkler': 0.3,
            'levenshtein': 0.2,
            'substring': 0.15,
            'pattern': 0.15
        }

        ensemble_sim = sum(similarities[metric] * weights[metric] for metric in weights.keys())

        # Determine match result
        is_match = ensemble_sim >= self.similarity_threshold

        result = {
            'target_word': target_word,
            'is_match': is_match,
            'ensemble_similarity': ensemble_sim,
            'individual_similarities': similarities,
            'normalized_transcription': norm_transcription,
            'normalized_target': norm_target
        }

        return result

    def score_mmse_item(self, transcription: str, item_id: int,
                       gold_score: Optional[int] = None) -> Dict[str, Any]:
        """
        Score MMSE item based on transcription and fuzzy matching.

        Args:
            transcription: ASR transcription
            item_id: MMSE item ID (1-12)
            gold_score: Gold standard score (if available for comparison)

        Returns:
            Dictionary with scoring results
        """
        result = {
            'item_id': item_id,
            'predicted_score': 0,
            'confidence': 0.0,
            'matching_details': {},
            'scoring_method': 'manual',  # Default to manual
            'auto_scoring_possible': False
        }

        # Map item_id to category
        item_categories = {
            1: 'orientation_time',    # T-OR (complex, manual scoring)
            2: 'orientation_place',   # P-OR (complex, manual scoring)
            3: 'registration',        # REG1 (word matching)
            4: 'registration',        # REG2 (word matching)
            5: 'registration',        # REG3 (word matching)
            6: 'attention',          # ATT (complex arithmetic, manual)
            7: 'recall',             # REC1 (word matching)
            8: 'recall',             # REC2 (word matching)
            9: 'recall',             # REC3 (word matching)
            10: 'naming',            # NAME (word matching)
            11: 'repetition',        # REP (sentence matching, manual)
            12: 'fluency'            # FLU (word count, semi-automatic)
        }

        category = item_categories.get(item_id, 'unknown')

        # Automatic scoring for word-based items
        if category in ['registration', 'recall', 'naming']:
            result['auto_scoring_possible'] = True

            # Get target words for this category
            target_words = self.word_lists.get(category, [])

            if target_words:
                # Determine which word this item corresponds to
                word_index = (item_id - 3) % 3 if category == 'registration' else \
                           (item_id - 7) % 3 if category == 'recall' else \
                           (item_id - 10)  # naming

                if 0 <= word_index < len(target_words):
                    target_word = target_words[word_index]

                    # Fuzzy match
                    match_result = self.fuzzy_match_word(transcription, target_word)
                    result['matching_details'] = match_result

                    # Determine score based on match
                    if match_result['is_match']:
                        result['predicted_score'] = 1
                        result['confidence'] = match_result['ensemble_similarity']
                        result['scoring_method'] = 'auto_word_match'
                    else:
                        result['predicted_score'] = 0
                        result['confidence'] = 1.0 - match_result['ensemble_similarity']
                        result['scoring_method'] = 'auto_no_match'

        elif category == 'fluency':
            # Semantic fluency scoring (word count based)
            result['auto_scoring_possible'] = True

            # Count unique words in transcription
            words = re.findall(r'\b\w+\b', transcription.lower())
            unique_words = set(words)

            # Remove common stop words (Vietnamese/English)
            stop_words = {'là', 'cái', 'của', 'và', 'có', 'the', 'a', 'an', 'is', 'are'}
            filtered_words = [w for w in unique_words if w not in stop_words]

            word_count = len(filtered_words)

            # Score based on word count thresholds
            if word_count >= 15:  # Excellent fluency
                result['predicted_score'] = 2
            elif word_count >= 10:  # Good fluency
                result['predicted_score'] = 1
            else:  # Poor fluency
                result['predicted_score'] = 0

            result['confidence'] = min(word_count / 15.0, 1.0)  # Normalize confidence
            result['scoring_method'] = 'auto_fluency_count'
            result['matching_details'] = {
                'total_words': len(words),
                'unique_words': word_count,
                'filtered_words': filtered_words
            }

        else:
            # Manual scoring required for complex items
            result['scoring_method'] = 'manual_required'
            result['predicted_score'] = 0  # Default
            result['confidence'] = 0.0

        # Compare with gold standard if available
        if gold_score is not None:
            result['gold_score'] = gold_score
            result['score_match'] = (result['predicted_score'] == gold_score)

        return result

    def process_complete_assessment(self, audio_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process complete MMSE assessment with all items.

        Args:
            audio_segments: List of audio segments with metadata

        Returns:
            Complete assessment results
        """
        assessment_results = {
            'total_score': 0,
            'item_scores': {},
            'transcriptions': {},
            'confidence_scores': {},
            'auto_scored_items': 0,
            'manual_required_items': 0,
            'overall_confidence': 0.0
        }

        total_confidence = 0.0
        valid_items = 0

        for segment in audio_segments:
            item_id = segment.get('item_id')
            audio_path = segment.get('audio_path')

            if not item_id or not audio_path:
                continue

            try:
                # Transcribe audio
                transcription_result = self.transcribe_audio(audio_path)
                transcription = transcription_result['transcription']

                # Score item
                scoring_result = self.score_mmse_item(
                    transcription,
                    item_id,
                    segment.get('gold_score')
                )

                # Store results
                assessment_results['item_scores'][item_id] = scoring_result['predicted_score']
                assessment_results['transcriptions'][item_id] = transcription
                assessment_results['confidence_scores'][item_id] = scoring_result['confidence']

                # Update counters
                if scoring_result['auto_scoring_possible']:
                    assessment_results['auto_scored_items'] += 1
                else:
                    assessment_results['manual_required_items'] += 1

                # Accumulate total score and confidence
                assessment_results['total_score'] += scoring_result['predicted_score']
                total_confidence += scoring_result['confidence']
                valid_items += 1

            except Exception as e:
                logger.error(f"❌ Failed to process item {item_id}: {e}")
                # Use default values
                assessment_results['item_scores'][item_id] = 0
                assessment_results['transcriptions'][item_id] = "[processing error]"
                assessment_results['confidence_scores'][item_id] = 0.0

        # Calculate overall confidence
        if valid_items > 0:
            assessment_results['overall_confidence'] = total_confidence / valid_items

        logger.info(f"✅ Assessment processed: {assessment_results['total_score']}/30 points, "
                   f"{assessment_results['auto_scored_items']} auto-scored items")

        return assessment_results

    def get_similarity_report(self, transcription: str, target_words: List[str]) -> Dict[str, Any]:
        """
        Generate detailed similarity report for debugging.

        Args:
            transcription: Full transcription
            target_words: List of target words to match

        Returns:
            Detailed similarity analysis
        """
        report = {
            'transcription': transcription,
            'normalized_transcription': self._normalize_text(transcription),
            'word_matches': []
        }

        for word in target_words:
            match_result = self.fuzzy_match_word(transcription, word)
            report['word_matches'].append({
                'target_word': word,
                'normalized_target': match_result['normalized_target'],
                'similarity': match_result['ensemble_similarity'],
                'is_match': match_result['is_match'],
                'individual_scores': match_result['individual_similarities']
            })

        return report


# Utility functions for MMSE scoring
def calculate_mmse_total(item_scores: Dict[int, int]) -> int:
    """
    Calculate total MMSE score from item scores.

    Args:
        item_scores: Dictionary mapping item_id to score

    Returns:
        Total MMSE score (0-30)
    """
    return sum(item_scores.values())


def get_cognitive_level(total_score: int) -> str:
    """
    Determine cognitive level based on total MMSE score.

    Args:
        total_score: Total MMSE score

    Returns:
        Cognitive level description
    """
    if total_score >= 25:
        return "Normal cognition"
    elif total_score >= 18:
        return "Mild cognitive impairment (MCI)"
    else:
        return "Dementia"


def get_mmse_interpretation(total_score: int, age: Optional[int] = None,
                          education: Optional[int] = None) -> Dict[str, Any]:
    """
    Provide clinical interpretation of MMSE score.

    Args:
        total_score: Total MMSE score
        age: Patient age (for age-adjusted interpretation)
        education: Years of education (for education-adjusted interpretation)

    Returns:
        Interpretation dictionary
    """
    interpretation = {
        'total_score': total_score,
        'cognitive_level': get_cognitive_level(total_score),
        'severity': 'unknown',
        'recommendations': []
    }

    # Basic severity classification
    if total_score >= 25:
        interpretation['severity'] = 'normal'
        interpretation['recommendations'] = [
            "Regular cognitive monitoring",
            "Healthy lifestyle maintenance"
        ]
    elif total_score >= 18:
        interpretation['severity'] = 'mild'
        interpretation['recommendations'] = [
            "Neuropsychological evaluation",
            "Monitor for progression",
            "Consider lifestyle interventions"
        ]
    else:
        interpretation['severity'] = 'severe'
        interpretation['recommendations'] = [
            "Comprehensive neurological assessment",
            "Consider dementia workup",
            "Caregiver support and planning"
        ]

    # Age-adjusted considerations
    if age is not None:
        if age >= 80 and total_score >= 24:
            interpretation['notes'] = "Score may be normal for advanced age"
        elif age < 60 and total_score < 25:
            interpretation['notes'] = "Lower than expected for younger age"

    return interpretation


if __name__ == "__main__":
    # Test ASR Processor
    print("🧪 Testing ASR Processor...")

    processor = ASRProcessor(language='vi')

    # Test fuzzy matching
    test_transcription = "Tôi có cái bàn, cái đồng hồ và cái bút chì"
    target_words = ["cái bàn", "đồng hồ", "bút chì"]

    print("🔍 Fuzzy Matching Test:")
    for word in target_words:
        result = processor.fuzzy_match_word(test_transcription, word)
        print(f"  '{word}': similarity={result['ensemble_similarity']:.2f}, match={result['is_match']}")

    # Test item scoring
    print("\n📊 Item Scoring Test:")
    for item_id in [3, 4, 5, 7, 8, 9]:  # Registration and recall items
        score_result = processor.score_mmse_item(test_transcription, item_id)
        print(f"  Item {item_id}: predicted={score_result['predicted_score']}, "
              f"confidence={score_result['confidence']:.2f}, method={score_result['scoring_method']}")

    # Test fluency scoring
    fluency_text = "hoa quả táo cam lê chuối dừa mãng cầu xoài bơ"
    fluency_result = processor.score_mmse_item(fluency_text, 12)  # Fluency item
    print(f"\n🗣️ Fluency Scoring: predicted={fluency_result['predicted_score']}, "
          f"word_count={fluency_result['matching_details']['unique_words']}")

    print("✅ ASR Processor test completed!")
