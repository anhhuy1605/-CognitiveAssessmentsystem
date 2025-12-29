# -*- coding: utf-8 -*-
"""
MMSE Scoring System v2.1 - Adjusted Scores & Multimodal Integration
Based on MMSE-VN-2.1-CORRECTED specification

Key Changes from v2.0:
1. Age & Education Adjustment Formula
2. Education-Specific Cutoffs (35-point scale)
3. Multimodal Risk Integration (MMSE + Acoustic + Linguistic)

References:
- Murden et al. (1991): Education adjustment
- Vietnamese JINS 2025: Age penalty 0.2/year after 60
- CogniVoice 2024: Multimodal weights
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AdjustedScoreResult:
    """Result of adjusted score calculation"""
    raw_score: float  # Raw MMSE score (0-35)
    age_penalty: float  # Age penalty (0.2 per year after 60)
    education_bonus: float  # Education bonus (0/1/2)
    adjusted_score: float  # Final adjusted score
    education_group: str  # 'low_education', 'medium_education', 'high_education'


@dataclass
class MultimodalRiskResult:
    """Result of multimodal risk calculation"""
    combined_risk_score: float  # 0-1 scale
    risk_level: str  # 'on', 'nguy_co_nhe', 'nguy_co_cao'
    components: Dict[str, float]  # Individual component scores
    mmse_risk_score: float
    acoustic_risk_score: float
    linguistic_risk_score: float


def calculate_adjusted_score(raw_score: float, age: int, education_years: int) -> AdjustedScoreResult:
    """
    Calculate adjusted MMSE score with age and education adjustments
    
    Formula (v2.1_CORRECTED from mmse_audio_questions_standardized.json):
    Adjusted Score = Raw Score - Age Penalty + Education Bonus
    
    Age Penalty:
    - 0.2 points per year after age 60
    - Formula: 0.2 × max(0, age - 60)
    - Example: Age 72 → Penalty = 0.2 × (72 - 60) = 2.4
    - Citation: Vietnamese JINS 2025 study
    
    Education Bonus:
    - ≤ 9 years: 0 bonus (low education)
    - 10-12 years: +1 bonus (medium education)
    - > 12 years: +2 bonus (high education)
    - Citation: Murden et al. (1991) - Education adjustment essential for fair assessment
    
    Args:
        raw_score: Raw MMSE score (0-35 for v2.1_CORRECTED)
        age: Patient age (40-100)
        education_years: Years of education (0-25)
    
    Returns:
        AdjustedScoreResult with all components
    
    Example:
        >>> result = calculate_adjusted_score(26, 72, 16)
        >>> result.adjusted_score
        25.6
        >>> result.age_penalty
        2.4
        >>> result.education_bonus
        2.0
        >>> result.education_group
        'high_education'
    """
    # Step 1: Calculate age penalty
    age_penalty = 0.0
    if age >= 60:
        age_penalty = 0.2 * (age - 60)
    
    # Step 2: Determine education bonus
    education_bonus = 0.0
    if education_years <= 9:
        education_bonus = 0
        education_group = "low_education"
    elif education_years >= 10 and education_years <= 12:
        education_bonus = 1
        education_group = "medium_education"
    else:  # education_years > 12
        education_bonus = 2
        education_group = "high_education"
    
    # Step 3: Calculate adjusted score
    adjusted_score = raw_score - age_penalty + education_bonus
    
    # Clamp to valid range (0-35 for v2.1_CORRECTED)
    adjusted_score = max(0.0, min(35.0, adjusted_score))
    
    logger.info(f"📊 Adjusted Score Calculation:")
    logger.info(f"   Raw Score: {raw_score:.1f}")
    logger.info(f"   Age: {age}, Penalty: {age_penalty:.1f}")
    logger.info(f"   Education: {education_years} years, Bonus: {education_bonus:.1f}, Group: {education_group}")
    logger.info(f"   Adjusted Score: {adjusted_score:.1f}")
    
    return AdjustedScoreResult(
        raw_score=raw_score,
        age_penalty=age_penalty,
        education_bonus=education_bonus,
        adjusted_score=adjusted_score,
        education_group=education_group
    )


def get_education_group(education_years: int) -> str:
    """
    Get education group classification
    
    Args:
        education_years: Years of education
    
    Returns:
        'low_education', 'medium_education', or 'high_education'
    """
    if education_years <= 9:
        return "low_education"
    elif education_years >= 10 and education_years <= 12:
        return "medium_education"
    else:
        return "high_education"


def get_risk_from_adjusted_score(adjusted_score: float, education_years: int) -> str:
    """
    Get risk classification from adjusted score using education-specific cutoffs
    
    Cutoffs (35-point scale):
    - Low education (≤9 years):
      * Normal: ≥ 23
      * MCI lower: ≥ 20
      * Dementia: < 20
    
    - Medium education (10-12 years):
      * Normal: ≥ 28
      * MCI lower: ≥ 24
      * Dementia: < 24
    
    - High education (>12 years):
      * Normal: ≥ 31
      * MCI lower: ≥ 28
      * Dementia: < 28
    
    Args:
        adjusted_score: Adjusted MMSE score
        education_years: Years of education
    
    Returns:
        'on' (Ổn), 'nguy_co_nhe' (Nguy cơ nhẹ), or 'nguy_co_cao' (Nguy cơ cao)
    """
    edu_group = get_education_group(education_years)
    
    cutoffs = {
        "low_education": {
            "normal": 23,
            "mci_lower": 20,
            "dementia_threshold": 20
        },
        "medium_education": {
            "normal": 28,
            "mci_lower": 24,
            "dementia_threshold": 24
        },
        "high_education": {
            "normal": 31,
            "mci_lower": 28,
            "dementia_threshold": 28
        }
    }
    
    thresholds = cutoffs[edu_group]
    
    if adjusted_score >= thresholds["normal"]:
        return "on"  # Ổn
    elif adjusted_score >= thresholds["mci_lower"]:
        return "nguy_co_nhe"  # Nguy cơ nhẹ
    else:
        return "nguy_co_cao"  # Nguy cơ cao


def convert_mmse_to_risk_score(adjusted_score: float, education_years: int) -> float:
    """
    Convert adjusted MMSE score to 0-1 risk scale
    
    This is used for multimodal integration where all components
    need to be on the same 0-1 scale.
    
    Args:
        adjusted_score: Adjusted MMSE score
        education_years: Years of education
    
    Returns:
        Risk score (0.0 = no risk, 1.0 = high risk)
    """
    edu_group = get_education_group(education_years)
    
    normal_threshold = {
        "low_education": 23,
        "medium_education": 28,
        "high_education": 31
    }[edu_group]
    
    dementia_threshold = normal_threshold - 3
    
    # Linear interpolation
    if adjusted_score >= normal_threshold:
        return 0.0  # No risk
    elif adjusted_score <= dementia_threshold:
        return 1.0  # High risk
    else:
        # Linear between thresholds
        return 1.0 - (adjusted_score - dementia_threshold) / (normal_threshold - dementia_threshold)


def calculate_multimodal_risk(
    mmse_data: Dict[str, Any],
    acoustic_features: Optional[Dict[str, float]] = None,
    linguistic_features: Optional[Dict[str, float]] = None
) -> MultimodalRiskResult:
    """
    Calculate multimodal risk score combining MMSE, Acoustic, and Linguistic features
    
    Weights (from CogniVoice 2024):
    - MMSE: 30%
    - Acoustic: 30%
    - Linguistic: 40%
    
    Pipeline:
    1. Convert MMSE adjusted score to 0-1 risk scale
    2. Get acoustic risk (0-1 scale) from features
    3. Get linguistic risk (0-1 scale) from features
    4. Weighted combination
    5. Threshold-based classification
    
    Args:
        mmse_data: {
            'raw_score': float,
            'adjusted_score': float,
            'education_years': int,
            'age': int
        }
        acoustic_features: Acoustic features dict (optional)
        linguistic_features: Linguistic features dict (optional)
    
    Returns:
        MultimodalRiskResult with combined risk score and classification
    """
    # Step 1: Get MMSE risk component (0-1 scale)
    mmse_risk_score = convert_mmse_to_risk_score(
        mmse_data['adjusted_score'],
        mmse_data['education_years']
    )
    
    # Step 2: Get acoustic risk (0-1 scale)
    # If acoustic features have risk_score, use it; otherwise calculate from features
    if acoustic_features and 'risk_score' in acoustic_features:
        acoustic_risk_score = acoustic_features['risk_score']
    elif acoustic_features:
        # Calculate from acoustic features if risk_score not available
        acoustic_risk_score = _calculate_acoustic_risk(acoustic_features)
    else:
        acoustic_risk_score = 0.5  # Default neutral if no acoustic data
    
    # Step 3: Get linguistic risk (0-1 scale)
    # If linguistic features have risk_score, use it; otherwise calculate from features
    if linguistic_features and 'risk_score' in linguistic_features:
        linguistic_risk_score = linguistic_features['risk_score']
    elif linguistic_features:
        # Calculate from linguistic features if risk_score not available
        linguistic_risk_score = _calculate_linguistic_risk(linguistic_features)
    else:
        linguistic_risk_score = 0.5  # Default neutral if no linguistic data
    
    # Step 4: Weighted combination
    # Weights from CogniVoice (2024) paper
    weights = {
        'mmse': 0.30,
        'acoustic': 0.30,
        'linguistic': 0.40
    }
    
    combined_risk_score = (
        weights['mmse'] * mmse_risk_score +
        weights['acoustic'] * acoustic_risk_score +
        weights['linguistic'] * linguistic_risk_score
    )
    
    # Step 5: Threshold-based classification
    if combined_risk_score < 0.4:
        risk_level = "on"  # Ổn
    elif combined_risk_score >= 0.4 and combined_risk_score < 0.7:
        risk_level = "nguy_co_nhe"  # Nguy cơ nhẹ
    else:
        risk_level = "nguy_co_cao"  # Nguy cơ cao
    
    logger.info(f"🧬 Multimodal Risk Calculation:")
    logger.info(f"   MMSE Risk: {mmse_risk_score:.3f} (weight: {weights['mmse']:.0%})")
    logger.info(f"   Acoustic Risk: {acoustic_risk_score:.3f} (weight: {weights['acoustic']:.0%})")
    logger.info(f"   Linguistic Risk: {linguistic_risk_score:.3f} (weight: {weights['linguistic']:.0%})")
    logger.info(f"   Combined Risk: {combined_risk_score:.3f}")
    logger.info(f"   Risk Level: {risk_level}")
    
    return MultimodalRiskResult(
        combined_risk_score=combined_risk_score,
        risk_level=risk_level,
        components={
            'mmse': mmse_risk_score,
            'acoustic': acoustic_risk_score,
            'linguistic': linguistic_risk_score
        },
        mmse_risk_score=mmse_risk_score,
        acoustic_risk_score=acoustic_risk_score,
        linguistic_risk_score=linguistic_risk_score
    )


def _calculate_acoustic_risk(acoustic_features: Dict[str, float]) -> float:
    """
    Calculate acoustic risk score from features (0-1 scale)
    
    Uses key acoustic indicators:
    - F0 variability (low = risk)
    - Jitter/Shimmer (high = risk)
    - Pause rate (high = risk)
    - HNR (low = risk)
    - Tone flattening (high = risk)
    """
    risk_score = 0.0
    indicators = 0
    
    # F0 variability (low = risk)
    f0_cv = acoustic_features.get('f0_f0_cv', 25.0)
    if f0_cv < 15.0:
        risk_score += 0.3
        indicators += 1
    elif f0_cv < 20.0:
        risk_score += 0.15
        indicators += 1
    
    # Jitter (high = risk)
    jitter = acoustic_features.get('vq_jitter_local', 0.01)
    if jitter > 0.02:
        risk_score += 0.25
        indicators += 1
    elif jitter > 0.015:
        risk_score += 0.12
        indicators += 1
    
    # Pause rate (high = risk)
    pause_rate = acoustic_features.get('pause_pause_rate', 0.2)
    if pause_rate > 0.4:
        risk_score += 0.25
        indicators += 1
    elif pause_rate > 0.3:
        risk_score += 0.12
        indicators += 1
    
    # HNR (low = risk)
    hnr = acoustic_features.get('vq_hnr_mean', 15.0)
    if hnr < 10.0:
        risk_score += 0.2
        indicators += 1
    elif hnr < 12.0:
        risk_score += 0.1
        indicators += 1
    
    # Tone flattening (Vietnamese-specific, high = risk)
    tone_flat = acoustic_features.get('tone_flattening_score', 0.2)
    if tone_flat > 0.5:
        risk_score += 0.3
        indicators += 1
    elif tone_flat > 0.35:
        risk_score += 0.15
        indicators += 1
    
    # Normalize by number of indicators
    if indicators > 0:
        risk_score = risk_score / indicators
    
    # Clamp to [0, 1]
    return min(1.0, max(0.0, risk_score))


def _calculate_linguistic_risk(linguistic_features: Dict[str, float]) -> float:
    """
    Calculate linguistic risk score from features (0-1 scale)
    
    Uses key linguistic indicators:
    - TTR (low = risk)
    - Pronoun ratio (high = risk)
    - MLU (low = risk)
    - Idea density (low = risk)
    - Semantic coherence (low = risk)
    """
    risk_score = 0.0
    indicators = 0
    
    # TTR (low = risk)
    ttr = linguistic_features.get('lex_ttr', 0.6)
    if ttr < 0.4:
        risk_score += 0.25
        indicators += 1
    elif ttr < 0.5:
        risk_score += 0.12
        indicators += 1
    
    # Pronoun ratio (high = risk)
    pronoun_ratio = linguistic_features.get('lex_pronoun_ratio', 0.1)
    if pronoun_ratio > 0.2:
        risk_score += 0.25
        indicators += 1
    elif pronoun_ratio > 0.15:
        risk_score += 0.12
        indicators += 1
    
    # MLU (low = risk)
    mlu = linguistic_features.get('syn_mlu_words', 10.0)
    if mlu < 5.0:
        risk_score += 0.2
        indicators += 1
    elif mlu < 7.0:
        risk_score += 0.1
        indicators += 1
    
    # Idea density (low = risk)
    idea_density = linguistic_features.get('sem_idea_density', 4.0)
    if idea_density < 3.0:
        risk_score += 0.3
        indicators += 1
    elif idea_density < 3.5:
        risk_score += 0.15
        indicators += 1
    
    # Semantic coherence (low = risk)
    coherence = linguistic_features.get('sem_semantic_coherence', 0.7)
    if coherence < 0.5:
        risk_score += 0.2
        indicators += 1
    elif coherence < 0.6:
        risk_score += 0.1
        indicators += 1
    
    # Normalize by number of indicators
    if indicators > 0:
        risk_score = risk_score / indicators
    
    # Clamp to [0, 1]
    return min(1.0, max(0.0, risk_score))

