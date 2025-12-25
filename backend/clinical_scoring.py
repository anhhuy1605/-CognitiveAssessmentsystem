#!/usr/bin/env python3
"""
Unified Clinical Scoring Logic - V2.0
=====================================
Giải quyết: Scoring logic hỗn loạn, không đúng clinical standards

Lưu ý:
- Đây là module độc lập, chưa gắn vào pipeline hiện tại.
- Có thể import trong backend khi cần:
      from backend.clinical_scoring import create_scoring_engine, MMSEScore, CognitiveLevel
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CognitiveLevel(Enum):
    """Standard MMSE cognitive levels"""

    NORMAL = "normal"  # ≥24
    MILD_IMPAIRMENT = "mild"  # 18-23
    MODERATE_IMPAIRMENT = "moderate"  # 10-17
    SEVERE_IMPAIRMENT = "severe"  # <10


@dataclass
class MMSEScore:
    """Standardized MMSE score với clinical interpretation"""

    total_score: float  # 0-30 scale
    cognitive_level: CognitiveLevel
    confidence: float  # 0-1
    source: str  # 'ml_model', 'gpt_eval', 'combined'

    # Component scores (optional)
    ml_score: Optional[float] = None
    gpt_score: Optional[float] = None

    # Quality indicators
    audio_quality_score: Optional[float] = None
    transcript_quality_score: Optional[float] = None

    # Clinical notes
    notes: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"MMSE Score: {self.total_score:.1f}/30\n"
            f"Level: {self.cognitive_level.value}\n"
            f"Confidence: {self.confidence:.2f}\n"
            f"Source: {self.source}"
        )


class ClinicalScoringEngine:
    """
    Unified scoring engine theo clinical standards
    - MMSE scale: 0-30 points (KHÔNG scale khác)
    - GPT evaluation: chỉ dùng để QA, không dùng để predict MMSE
    - ML model: primary source cho MMSE score
    """

    # Clinical thresholds từ MMSE standard
    THRESHOLDS = {"normal": 24.0, "mild": 18.0, "moderate": 10.0}

    def score_from_ml_model(self, ml_prediction: float, audio_quality: float = 1.0) -> MMSEScore:
        """
        Score từ ML model - PRIMARY method
        Args:
            ml_prediction: Model output (0-30 scale)
            audio_quality: Audio quality score (0-1)
        """
        if not (0 <= ml_prediction <= 30):
            logger.warning("ML prediction %s outside [0,30], clipping", ml_prediction)
            ml_prediction = float(np.clip(ml_prediction, 0.0, 30.0))

        confidence = audio_quality * 0.9  # Max 0.9 for ML alone
        cognitive_level = self._determine_cognitive_level(ml_prediction)

        return MMSEScore(
            total_score=float(ml_prediction),
            cognitive_level=cognitive_level,
            confidence=confidence,
            source="ml_model",
            ml_score=ml_prediction,
            audio_quality_score=audio_quality,
            notes="Score from trained ML model based on audio features",
        )

    def score_with_quality_check(
        self, ml_prediction: float, gpt_quality_score: float, audio_quality: float, transcript: str
    ) -> MMSEScore:
        """
        Score với quality check từ GPT
        ⚠️ GPT chỉ đánh giá QUALITY của transcript (0-10), không predict MMSE
        """
        base_score = self.score_from_ml_model(ml_prediction, audio_quality)

        transcript_quality = self._assess_transcript_quality(transcript, gpt_quality_score)
        quality_factor = (transcript_quality / 10.0) * 0.2  # Max 0.2 boost
        adjusted_confidence = min(1.0, base_score.confidence + quality_factor)

        notes = base_score.notes or ""
        if transcript_quality < 4.0:
            notes += "\n⚠️ Low transcript quality - consider retesting"

        return MMSEScore(
            total_score=base_score.total_score,  # Score KHÔNG đổi
            cognitive_level=base_score.cognitive_level,
            confidence=adjusted_confidence,  # Chỉ adjust confidence
            source="combined_with_qa",
            ml_score=ml_prediction,
            gpt_score=gpt_quality_score,
            audio_quality_score=audio_quality,
            transcript_quality_score=transcript_quality,
            notes=notes,
        )

    def _assess_transcript_quality(self, transcript: str, gpt_quality_score: float) -> float:
        """Đánh giá chất lượng transcript (GPT score + basic checks)"""
        word_count = len(transcript.split())
        quality = gpt_quality_score  # start 0-10

        if word_count < 3:
            quality *= 0.3
        elif word_count < 10:
            quality *= 0.6

        if transcript.lower().strip() in ["", "không có lời thoại", "no speech"]:
            quality = 0.0

        return float(np.clip(quality, 0.0, 10.0))

    def _determine_cognitive_level(self, mmse_score: float) -> CognitiveLevel:
        """Map MMSE score to cognitive level theo clinical standards"""
        if mmse_score >= self.THRESHOLDS["normal"]:
            return CognitiveLevel.NORMAL
        if mmse_score >= self.THRESHOLDS["mild"]:
            return CognitiveLevel.MILD_IMPAIRMENT
        if mmse_score >= self.THRESHOLDS["moderate"]:
            return CognitiveLevel.MODERATE_IMPAIRMENT
        return CognitiveLevel.SEVERE_IMPAIRMENT

    def get_clinical_recommendations(self, score: MMSEScore) -> Dict[str, object]:
        """Generate clinical recommendations dựa trên score"""
        recommendations = {
            "cognitive_level": score.cognitive_level.value,
            "score": score.total_score,
            "confidence": score.confidence,
            "actions": [],
            "follow_up": "",
            "warnings": [],
        }

        if score.cognitive_level == CognitiveLevel.NORMAL:
            recommendations["actions"] = [
                "Tiếp tục theo dõi định kỳ hàng năm",
                "Duy trì lối sống lành mạnh",
                "Hoạt động trí óc thường xuyên",
            ]
            recommendations["follow_up"] = "Khám lại sau 12 tháng"

        elif score.cognitive_level == CognitiveLevel.MILD_IMPAIRMENT:
            recommendations["actions"] = [
                "Khám chuyên khoa thần kinh/tâm thần",
                "Đánh giá nhận thức toàn diện",
                "Theo dõi tiến triển",
                "Can thiệp sớm (nếu cần)",
            ]
            recommendations["follow_up"] = "Khám lại sau 6 tháng"
            recommendations["warnings"].append("Suy giảm nhận thức nhẹ - cần theo dõi chặt chẽ")

        elif score.cognitive_level == CognitiveLevel.MODERATE_IMPAIRMENT:
            recommendations["actions"] = [
                "KHẨN CẤP: Khám bác sĩ chuyên khoa ngay",
                "Đánh giá toàn diện (MRI, xét nghiệm)",
                "Xem xét điều trị",
                "Hỗ trợ từ gia đình/người chăm sóc",
            ]
            recommendations["follow_up"] = "Khám lại sau 3 tháng"
            recommendations["warnings"].append("⚠️ Suy giảm trung bình - cần can thiệp y tế")

        else:  # SEVERE
            recommendations["actions"] = [
                "KHẨN CẤP: Đến bệnh viện ngay",
                "Cần chăm sóc chuyên biệt 24/7",
                "Đánh giá và điều trị tích cực",
                "Hỗ trợ tâm lý cho gia đình",
            ]
            recommendations["follow_up"] = "Theo dõi liên tục"
            recommendations["warnings"].append("🚨 Suy giảm nặng - cần chăm sóc y tế ngay lập tức")

        if score.confidence < 0.6:
            recommendations["warnings"].append(
                f"⚠️ Độ tin cậy thấp ({score.confidence:.2f}) - Nên đánh giá lại bằng phương pháp khác"
            )

        return recommendations


def create_scoring_engine() -> ClinicalScoringEngine:
    """Factory để tạo scoring engine"""
    return ClinicalScoringEngine()


def main():
    """Test scoring engine"""
    engine = create_scoring_engine()

    # Test case 1: Normal cognition
    print("\n" + "=" * 60)
    print("TEST 1: Normal Cognition")
    print("=" * 60)

    score1 = engine.score_from_ml_model(ml_prediction=27.5, audio_quality=0.9)
    print(score1)
    recommendations1 = engine.get_clinical_recommendations(score1)
    print("\nRecommendations:")
    for action in recommendations1["actions"]:
        print(f"  - {action}")

    # Test case 2: Mild impairment with quality check
    print("\n" + "=" * 60)
    print("TEST 2: Mild Impairment with Quality Check")
    print("=" * 60)

    score2 = engine.score_with_quality_check(
        ml_prediction=20.5,
        gpt_quality_score=6.5,
        audio_quality=0.8,
        transcript="Tôi không nhớ rõ lắm... ừm... có lẽ là...",
    )
    print(score2)
    recommendations2 = engine.get_clinical_recommendations(score2)
    print("\nRecommendations:")
    for action in recommendations2["actions"]:
        print(f"  - {action}")
    if recommendations2["warnings"]:
        print("\nWarnings:")
        for warning in recommendations2["warnings"]:
            print(f"  {warning}")

    # Test case 3: Severe impairment with poor quality
    print("\n" + "=" * 60)
    print("TEST 3: Severe Impairment with Poor Quality")
    print("=" * 60)

    score3 = engine.score_with_quality_check(
        ml_prediction=8.0,
        gpt_quality_score=2.0,
        audio_quality=0.5,
        transcript="ừ... à...",
    )
    print(score3)
    recommendations3 = engine.get_clinical_recommendations(score3)
    print("\nRecommendations:")
    for action in recommendations3["actions"]:
        print(f"  - {action}")
    if recommendations3["warnings"]:
        print("\nWarnings:")
        for warning in recommendations3["warnings"]:
            print(f"  {warning}")


if __name__ == "__main__":
    main()

