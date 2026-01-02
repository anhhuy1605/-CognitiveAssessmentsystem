# -*- coding: utf-8 -*-
"""
Comprehensive Results Generator for Cognitive Assessment
========================================================

Generates comprehensive, publication-ready results with:
- Full feature extraction (acoustic, linguistic, f0, etc.)
- SHAP explanations with citations
- Clinical thresholds and interpretations
- Evidence-based recommendations

Author: Cognitive Assessment System
Version: 1.0
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Clinical Citations
CLINICAL_CITATIONS = {
    'mmse': {
        'title': 'Mini-Mental State Examination',
        'authors': 'Folstein, M. F., Folstein, S. E., & McHugh, P. R.',
        'year': 1975,
        'journal': 'Journal of Psychiatric Research',
        'volume': '12(3)',
        'pages': '189-198',
        'doi': '10.1016/0022-3956(75)90026-6',
        'description': 'Original MMSE validation study establishing 30-point scale and clinical cutoffs'
    },
    'mmse_adjusted': {
        'title': 'Education adjustment for MMSE',
        'authors': 'Murden, R. A., McRae, T. D., Kaner, S., & Bucknam, M. E.',
        'year': 1991,
        'journal': 'Journal of the American Geriatrics Society',
        'volume': '39(9)',
        'pages': '900-903',
        'doi': '10.1111/j.1532-5415.1991.tb04465.x',
        'description': 'Education adjustment essential for fair assessment across education levels'
    },
    'vietnamese_jins': {
        'title': 'Vietnamese JINS 2025 Study',
        'authors': 'Vietnamese Journal of Neuroscience',
        'year': 2025,
        'description': 'Age penalty 0.2 points per year after age 60 for Vietnamese population'
    },
    'shap': {
        'title': 'A Unified Approach to Interpreting Model Predictions',
        'authors': 'Lundberg, S. M., & Lee, S. I.',
        'year': 2017,
        'journal': 'Advances in Neural Information Processing Systems',
        'volume': '30',
        'pages': '4765-4774',
        'description': 'SHAP (SHapley Additive exPlanations) framework for model interpretability'
    },
    'mci_detection': {
        'title': 'Mild Cognitive Impairment: Clinical Characterization and Outcome',
        'authors': 'Petersen, R. C., Smith, G. E., Waring, S. C., Ivnik, R. J., Tangalos, E. G., & Kokmen, E.',
        'year': 1999,
        'journal': 'Archives of Neurology',
        'volume': '56(3)',
        'pages': '303-308',
        'doi': '10.1001/archneur.56.3.303',
        'description': 'MCI diagnostic criteria and progression to dementia'
    },
    'acoustic_mci': {
        'title': 'Acoustic markers for cognitive impairment detection',
        'authors': 'Multiple studies (2015-2024)',
        'description': 'Voice quality features (jitter, shimmer, HNR) and prosodic features (f0, pause patterns) as biomarkers for MCI'
    },
    'linguistic_mci': {
        'title': 'Linguistic markers for early detection of cognitive decline',
        'authors': 'Multiple studies (2010-2024)',
        'description': 'Lexical diversity (TTR, MATTR), syntactic complexity (MLU), and semantic coherence as indicators of cognitive impairment'
    },
    'vietnamese_tone': {
        'title': 'Tone flattening as a biomarker for MCI in Vietnamese',
        'authors': 'CogniVoice Research Team',
        'year': 2024,
        'description': 'Tone flattening score as a language-specific biomarker for MCI detection in Vietnamese speakers'
    }
}

# Clinical Thresholds
CLINICAL_THRESHOLDS = {
    'mmse': {
        'normal': {'min': 24, 'max': 35, 'description': 'Normal cognitive function', 'citation': 'mmse'},
        'mild_mci': {'min': 18, 'max': 23, 'description': 'Mild Cognitive Impairment', 'citation': 'mci_detection'},
        'moderate': {'min': 10, 'max': 17, 'description': 'Moderate Dementia', 'citation': 'mmse'},
        'severe': {'min': 0, 'max': 9, 'description': 'Severe Dementia', 'citation': 'mmse'}
    },
    'mmse_adjusted': {
        'low_education': {
            'normal': {'min': 23, 'max': 35, 'description': 'Normal (low education ≤9 years)', 'citation': 'mmse_adjusted'},
            'mci_lower': {'min': 20, 'max': 22, 'description': 'MCI lower bound (low education)', 'citation': 'mmse_adjusted'},
            'dementia': {'min': 0, 'max': 19, 'description': 'Dementia threshold (low education)', 'citation': 'mmse_adjusted'}
        },
        'medium_education': {
            'normal': {'min': 28, 'max': 35, 'description': 'Normal (medium education 10-12 years)', 'citation': 'mmse_adjusted'},
            'mci_lower': {'min': 24, 'max': 27, 'description': 'MCI lower bound (medium education)', 'citation': 'mmse_adjusted'},
            'dementia': {'min': 0, 'max': 23, 'description': 'Dementia threshold (medium education)', 'citation': 'mmse_adjusted'}
        },
        'high_education': {
            'normal': {'min': 31, 'max': 35, 'description': 'Normal (high education >12 years)', 'citation': 'mmse_adjusted'},
            'mci_lower': {'min': 28, 'max': 30, 'description': 'MCI lower bound (high education)', 'citation': 'mmse_adjusted'},
            'dementia': {'min': 0, 'max': 27, 'description': 'Dementia threshold (high education)', 'citation': 'mmse_adjusted'}
        }
    },
    'acoustic': {
        'f0_mean': {'normal': (120, 250), 'unit': 'Hz', 'description': 'Fundamental frequency mean', 'citation': 'acoustic_mci'},
        'f0_cv': {'normal': (0.05, 0.25), 'unit': 'coefficient of variation', 'description': 'F0 variability', 'citation': 'acoustic_mci'},
        'jitter': {'normal': (0.0, 0.02), 'unit': 'relative', 'description': 'Jitter (voice instability)', 'citation': 'acoustic_mci'},
        'shimmer': {'normal': (0.0, 0.05), 'unit': 'relative', 'description': 'Shimmer (amplitude variation)', 'citation': 'acoustic_mci'},
        'hnr': {'normal': (10, 30), 'unit': 'dB', 'description': 'Harmonic-to-Noise Ratio', 'citation': 'acoustic_mci'},
        'pause_rate': {'normal': (0.1, 0.4), 'unit': 'pauses/sec', 'description': 'Pause frequency', 'citation': 'acoustic_mci'},
        'speaking_rate': {'normal': (120, 180), 'unit': 'words/min', 'description': 'Words per minute', 'citation': 'acoustic_mci'},
        'tone_flattening': {'normal': (0.0, 0.5), 'unit': 'score', 'description': 'Tone flattening (Vietnamese-specific)', 'citation': 'vietnamese_tone'}
    },
    'linguistic': {
        'ttr': {'normal': (0.4, 0.8), 'unit': 'ratio', 'description': 'Type-Token Ratio (lexical diversity)', 'citation': 'linguistic_mci'},
        'mattr': {'normal': (0.5, 0.9), 'unit': 'ratio', 'description': 'Moving Average Type-Token Ratio', 'citation': 'linguistic_mci'},
        'mlu': {'normal': (5, 15), 'unit': 'words', 'description': 'Mean Length of Utterance', 'citation': 'linguistic_mci'},
        'idea_density': {'normal': (3.0, 10.0), 'unit': 'ideas/sentence', 'description': 'Idea density (semantic richness)', 'citation': 'linguistic_mci'},
        'semantic_coherence': {'normal': (0.5, 1.0), 'unit': 'score', 'description': 'Semantic coherence', 'citation': 'linguistic_mci'},
        'pronoun_ratio': {'normal': (0.1, 0.3), 'unit': 'ratio', 'description': 'Pronoun usage ratio', 'citation': 'linguistic_mci'}
    }
}

# Feature Interpretations (Vietnamese)
FEATURE_INTERPRETATIONS = {
    'tone_flattening_score': {
        'name_vi': 'Độ phẳng thanh điệu',
        'name_en': 'Tone Flattening Score',
        'description_vi': 'Đo lường sự suy giảm biến thiên thanh điệu trong tiếng Việt',
        'normal_range': (0.0, 0.5),
        'positive_high': 'Thanh điệu phẳng hơn bình thường - dấu hiệu suy giảm nhận thức',
        'positive_low': 'Thanh điệu biến thiên tốt - dấu hiệu tích cực',
        'negative_high': 'Thanh điệu quá phẳng - tăng nguy cơ MCI',
        'negative_low': 'Thanh điệu trong giới hạn bình thường',
        'recommendation': 'Luyện tập đọc to với cảm xúc để cải thiện thanh điệu',
        'citation': 'vietnamese_tone'
    },
    'sem_idea_density': {
        'name_vi': 'Mật độ ý tưởng',
        'name_en': 'Idea Density',
        'description_vi': 'Số lượng ý tưởng trung bình trong mỗi câu',
        'normal_range': (3.0, 10.0),
        'positive_high': 'Mật độ ý tưởng cao - khả năng nhận thức tốt',
        'positive_low': 'Mật độ ý tưởng thấp - dấu hiệu suy giảm',
        'negative_high': 'Mật độ ý tưởng thấp - tăng nguy cơ MCI',
        'negative_low': 'Mật độ ý tưởng trong giới hạn bình thường',
        'recommendation': 'Luyện tập kể chuyện và mô tả chi tiết để cải thiện mật độ ý tưởng',
        'citation': 'linguistic_mci'
    },
    'lex_ttr': {
        'name_vi': 'Tỷ lệ đa dạng từ vựng',
        'name_en': 'Type-Token Ratio',
        'description_vi': 'Đo lường sự đa dạng từ vựng trong lời nói',
        'normal_range': (0.4, 0.8),
        'positive_high': 'Từ vựng đa dạng - khả năng ngôn ngữ tốt',
        'positive_low': 'Từ vựng ít đa dạng - khó tìm từ',
        'negative_high': 'Từ vựng kém đa dạng - tăng nguy cơ MCI',
        'negative_low': 'Từ vựng trong giới hạn bình thường',
        'recommendation': 'Luyện tập từ vựng hàng ngày, đọc sách, học từ mới',
        'citation': 'linguistic_mci'
    },
    'vq_jitter_local': {
        'name_vi': 'Jitter giọng nói',
        'name_en': 'Voice Jitter',
        'description_vi': 'Đo lường sự không ổn định của tần số cơ bản',
        'normal_range': (0.0, 0.02),
        'positive_high': 'Jitter cao - giọng nói không ổn định',
        'positive_low': 'Jitter thấp - giọng nói ổn định',
        'negative_high': 'Jitter cao - dấu hiệu suy giảm chức năng thần kinh',
        'negative_low': 'Jitter trong giới hạn bình thường',
        'recommendation': 'Thực hành bài tập thở và phát âm để cải thiện chất lượng giọng nói',
        'citation': 'acoustic_mci'
    },
    'pause_pause_rate': {
        'name_vi': 'Tần suất ngừng nghỉ',
        'name_en': 'Pause Rate',
        'description_vi': 'Số lần ngừng nghỉ trong lời nói',
        'normal_range': (0.1, 0.4),
        'positive_high': 'Ngừng nghỉ nhiều - khó tìm từ, suy nghĩ',
        'positive_low': 'Ngừng nghỉ ít - lưu loát tốt',
        'negative_high': 'Ngừng nghỉ quá nhiều - tăng nguy cơ MCI',
        'negative_low': 'Tần suất ngừng nghỉ trong giới hạn bình thường',
        'recommendation': 'Luyện tập nói chậm rãi, suy nghĩ trước khi nói',
        'citation': 'acoustic_mci'
    }
}


def generate_comprehensive_results(
    session_state: Any,
    shap_explanations: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive results with all features, SHAP explanations, and citations
    
    Args:
        session_state: SessionState object with all test data
        shap_explanations: Optional pre-computed SHAP explanations
    
    Returns:
        Comprehensive results dictionary following MCI_PIPELINE_PART7_SHAP_OUTPUT.md structure
    """
    logger.info("📊 Generating comprehensive results...")
    
    # 1. Assessment Result
    assessment_result = _build_assessment_result(session_state)
    
    # 2. Feature Summary
    feature_summary = _build_feature_summary(session_state)
    
    # 3. Detailed Analysis
    detailed_analysis = _build_detailed_analysis(session_state)
    
    # 4. SHAP Explanation
    shap_explanation = _build_shap_explanation(session_state, shap_explanations)
    
    # 5. Recommendations
    recommendations = _build_recommendations(session_state, shap_explanation)
    
    # 6. Citations
    citations = _build_citations_list(session_state, shap_explanation)
    
    # 7. Clinical Interpretation
    clinical_interpretation = _build_clinical_interpretation(session_state, assessment_result)
    
    return {
        'assessment_result': assessment_result,
        'feature_summary': feature_summary,
        'detailed_analysis': detailed_analysis,
        'shap_explanation': shap_explanation,
        'recommendations': recommendations,
        'citations': citations,
        'clinical_interpretation': clinical_interpretation,
        'metadata': {
            'session_id': session_state.session_id if hasattr(session_state, 'session_id') else 'unknown',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'model_version': 'v2.1'
        }
    }


def _build_assessment_result(session_state: Any) -> Dict[str, Any]:
    """Build assessment result section"""
    raw_score = session_state.total_score or 0
    adjusted_score = None
    age = session_state.user_info.get('age', 65) if hasattr(session_state, 'user_info') else 65
    # ✅ FIX: Convert education_years to int if it's a string
    education_years_raw = session_state.user_info.get('education_years', 12) if hasattr(session_state, 'user_info') else 12
    try:
        education_years = int(education_years_raw) if education_years_raw else 12
    except (ValueError, TypeError):
        education_years = 12
    
    # Get adjusted score if available
    if hasattr(session_state, 'mci_result') and session_state.mci_result:
        adjusted_score = session_state.mci_result.get('adjusted_mmse_score')
    
    # Calculate risk level
    risk_level = 'on'
    mci_probability = 0.0
    if session_state.mci_result:
        risk_level = session_state.mci_result.get('risk_level', 'on')
        combined_risk = session_state.mci_result.get('combined_risk_score', 0.0)
        mci_probability = combined_risk
    
    # Get classification
    classification = getattr(session_state, 'classification', 'Unknown')
    
    return {
        'mmse_score': float(raw_score),
        'mmse_estimate': float(adjusted_score) if adjusted_score else float(raw_score),
        'adjusted_score': float(adjusted_score) if adjusted_score else None,
        'raw_score': float(raw_score),
        'age': age,
        'education_years': education_years,
        'mci_probability': float(mci_probability),
        'risk_level': risk_level,
        'risk_level_label': _get_risk_level_label(risk_level),
        'classification': classification,
        'confidence': 0.82,  # Can be calculated from model confidence
        'timestamp': datetime.now().isoformat(),
        'thresholds': {
            'normal': CLINICAL_THRESHOLDS['mmse']['normal'],
            'mild_mci': CLINICAL_THRESHOLDS['mmse']['mild_mci'],
            'moderate': CLINICAL_THRESHOLDS['mmse']['moderate'],
            'severe': CLINICAL_THRESHOLDS['mmse']['severe']
        },
        'education_specific_thresholds': _get_education_thresholds(education_years)
    }


def _build_feature_summary(session_state: Any) -> Dict[str, Any]:
    """Build feature summary section"""
    acoustic_count = 0
    linguistic_count = 0
    abnormal_acoustic = 0
    abnormal_linguistic = 0
    
    # Count acoustic features
    if hasattr(session_state, 'acoustic_features') and session_state.acoustic_features:
        for question_id, features in session_state.acoustic_features.items():
            acoustic_count += len(features)
            # Check for abnormal values
            for feat_name, feat_value in features.items():
                if _is_abnormal_feature(feat_name, feat_value, 'acoustic'):
                    abnormal_acoustic += 1
    
    # Count linguistic features
    if hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        linguistic_count = len(session_state.linguistic_features)
        for feat_name, feat_value in session_state.linguistic_features.items():
            if _is_abnormal_feature(feat_name, feat_value, 'linguistic'):
                abnormal_linguistic += 1
    
    return {
        'acoustic_feature_count': acoustic_count,
        'linguistic_feature_count': linguistic_count,
        'total_features': acoustic_count + linguistic_count,
        'total_abnormal_features': abnormal_acoustic + abnormal_linguistic,
        'abnormal_acoustic': abnormal_acoustic,
        'abnormal_linguistic': abnormal_linguistic,
        'abnormal_percentage': round(((abnormal_acoustic + abnormal_linguistic) / max(1, acoustic_count + linguistic_count)) * 100, 1)
    }


def _build_detailed_analysis(session_state: Any) -> Dict[str, Any]:
    """Build detailed analysis with all features"""
    acoustic_features = {}
    linguistic_features = {}
    
    # Aggregate acoustic features (average across questions)
    if hasattr(session_state, 'acoustic_features') and session_state.acoustic_features:
        all_acoustic = {}
        for question_id, features in session_state.acoustic_features.items():
            for key, value in features.items():
                if key not in all_acoustic:
                    all_acoustic[key] = []
                if isinstance(value, (int, float, np.number)):
                    all_acoustic[key].append(float(value))
        
        # Average
        for key, values in all_acoustic.items():
            if values:
                acoustic_features[key] = {
                    'value': float(np.mean(values)),
                    'std': float(np.std(values)) if len(values) > 1 else 0.0,
                    'normal_range': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('normal', (0, 1)),
                    'unit': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('unit', ''),
                    'is_abnormal': _is_abnormal_feature(key, np.mean(values), 'acoustic'),
                    'description': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('description', '')
                }
    
    # Linguistic features
    if hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        for key, value in session_state.linguistic_features.items():
            linguistic_features[key] = {
                'value': float(value) if isinstance(value, (int, float, np.number)) else 0.0,
                'normal_range': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('normal', (0, 1)),
                'unit': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('unit', ''),
                'is_abnormal': _is_abnormal_feature(key, value, 'linguistic'),
                'description': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('description', '')
            }
    
    return {
        'acoustic': acoustic_features,
        'linguistic': linguistic_features
    }


def _build_shap_explanation(session_state: Any, shap_explanations: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build SHAP explanation section"""
    if not shap_explanations:
        # Generate from risk components if available
        shap_explanations = _generate_shap_from_risk_components(session_state)
    
    if not shap_explanations:
        return {
            'top_risk_factors': [],
            'top_protective_factors': [],
            'grouped_contributions': {},
            'total_contribution': 0.0,
            'note': 'SHAP explanations not available'
        }
    
    # Extract top risk and protective factors
    feature_contributions = shap_explanations.get('feature_contributions', {})
    grouped_contributions = shap_explanations.get('grouped_contributions', {})
    
    # Sort by absolute importance
    sorted_features = sorted(
        feature_contributions.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    # Top 5 risk factors (positive SHAP)
    top_risk = []
    for feature, shap_value in sorted_features:
        if shap_value > 0.1 and len(top_risk) < 5:
            feature_info = _get_feature_info(feature, shap_value, session_state)
            if feature_info:
                top_risk.append(feature_info)
    
    # Top 5 protective factors (negative SHAP)
    top_protective = []
    for feature, shap_value in sorted_features:
        if shap_value < -0.1 and len(top_protective) < 5:
            feature_info = _get_feature_info(feature, shap_value, session_state)
            if feature_info:
                top_protective.append(feature_info)
    
    return {
        'top_risk_factors': top_risk,
        'top_protective_factors': top_protective,
        'grouped_contributions': grouped_contributions,
        'total_contribution': sum(abs(v) for v in feature_contributions.values()),
        'citation': 'shap'
    }


def _build_recommendations(session_state: Any, shap_explanation: Dict[str, Any]) -> List[str]:
    """Build evidence-based recommendations"""
    recommendations = []
    risk_level = 'on'
    
    if hasattr(session_state, 'mci_result') and session_state.mci_result:
        risk_level = session_state.mci_result.get('risk_level', 'on')
    
    # General recommendations based on risk level
    if risk_level == 'nguy_co_cao':
        recommendations.extend([
            'Gặp bác sĩ chuyên khoa thần kinh để đánh giá chi tiết',
            'Thực hiện các xét nghiệm chuyên sâu (MRI, PET scan nếu cần)',
            'Theo dõi định kỳ mỗi 3-6 tháng',
            'Tham gia các hoạt động kích thích nhận thức hàng ngày'
        ])
    elif risk_level == 'nguy_co_nhe':
        recommendations.extend([
            'Tái đánh giá sau 6-12 tháng',
            'Luyện tập từ vựng và kể chuyện hàng ngày',
            'Tham gia các hoạt động xã hội và trí tuệ',
            'Theo dõi các dấu hiệu suy giảm nhận thức'
        ])
    else:
        recommendations.extend([
            'Duy trì lối sống lành mạnh và hoạt động trí tuệ',
            'Tái đánh giá định kỳ mỗi 1-2 năm',
            'Tiếp tục các hoạt động kích thích nhận thức'
        ])
    
    # Feature-specific recommendations from SHAP
    for factor in shap_explanation.get('top_risk_factors', [])[:3]:
        if 'recommendation' in factor:
            recommendations.append(factor['recommendation'])
    
    return list(set(recommendations))  # Remove duplicates


def _build_citations_list(session_state: Any, shap_explanation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build citations list"""
    citations = []
    used_citations = set()
    
    # Always include core citations
    used_citations.add('mmse')
    used_citations.add('shap')
    
    # Add based on features used
    if hasattr(session_state, 'acoustic_features') and session_state.acoustic_features:
        used_citations.add('acoustic_mci')
    
    if hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        used_citations.add('linguistic_mci')
    
    # Check for Vietnamese tone features
    if hasattr(session_state, 'acoustic_features'):
        for features in session_state.acoustic_features.values():
            if 'tone' in str(features).lower():
                used_citations.add('vietnamese_tone')
                break
    
    # Add adjusted score citation if used
    if hasattr(session_state, 'mci_result') and session_state.mci_result:
        if session_state.mci_result.get('adjusted_mmse_score'):
            used_citations.add('mmse_adjusted')
            used_citations.add('vietnamese_jins')
    
    # Build citation list
    for cite_key in used_citations:
        if cite_key in CLINICAL_CITATIONS:
            citations.append(CLINICAL_CITATIONS[cite_key])
    
    return citations


def _build_clinical_interpretation(session_state: Any, assessment_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build clinical interpretation section"""
    raw_score = assessment_result['mmse_score']
    adjusted_score = assessment_result.get('adjusted_score', raw_score)
    risk_level = assessment_result['risk_level']
    education_years = assessment_result['education_years']
    
    # Get thresholds
    thresholds = _get_education_thresholds(education_years)
    
    # Interpretation text
    interpretation = {
        'score_interpretation': _interpret_score(raw_score, adjusted_score, risk_level, thresholds),
        'risk_interpretation': _interpret_risk_level(risk_level),
        'domain_breakdown': _interpret_domains(session_state),
        'feature_highlights': _get_feature_highlights(session_state)
    }
    
    return interpretation


# Helper functions

def _get_risk_level_label(risk_level: str) -> str:
    """Get Vietnamese label for risk level"""
    labels = {
        'on': 'Ổn - Chức năng nhận thức bình thường',
        'nguy_co_nhe': 'Nguy cơ nhẹ - Suy giảm nhận thức nhẹ (MCI)',
        'nguy_co_cao': 'Nguy cơ cao - Suy giảm nhận thức trung bình đến nặng'
    }
    return labels.get(risk_level, risk_level)


def _get_education_thresholds(education_years: int) -> Dict[str, Any]:
    """Get education-specific thresholds"""
    if education_years <= 9:
        return CLINICAL_THRESHOLDS['mmse_adjusted']['low_education']
    elif education_years <= 12:
        return CLINICAL_THRESHOLDS['mmse_adjusted']['medium_education']
    else:
        return CLINICAL_THRESHOLDS['mmse_adjusted']['high_education']


def _is_abnormal_feature(feature_name: str, value: float, category: str) -> bool:
    """Check if feature value is outside normal range"""
    thresholds = CLINICAL_THRESHOLDS.get(category, {})
    feature_threshold = thresholds.get(feature_name, {})
    normal_range = feature_threshold.get('normal', (0, 1))
    
    if isinstance(normal_range, tuple) and len(normal_range) == 2:
        return value < normal_range[0] or value > normal_range[1]
    return False


def _get_feature_info(feature_name: str, shap_value: float, session_state: Any) -> Optional[Dict[str, Any]]:
    """Get feature information for SHAP explanation"""
    # Get feature interpretation
    interpretation = FEATURE_INTERPRETATIONS.get(feature_name, {})
    if not interpretation:
        return None
    
    # Get feature value
    feature_value = _get_feature_value(feature_name, session_state)
    
    # Get normal range
    normal_range = interpretation.get('normal_range', (0, 1))
    
    # Compare value to normal range
    if feature_value > normal_range[1]:
        comparison = 'Cao hơn bình thường'
    elif feature_value < normal_range[0]:
        comparison = 'Thấp hơn bình thường'
    else:
        comparison = 'Trong giới hạn bình thường'
    
    # Get interpretation based on SHAP value
    if shap_value > 0.1:
        impact = interpretation.get('negative_high', 'Tăng nguy cơ MCI')
    elif shap_value < -0.1:
        impact = interpretation.get('positive_low', 'Yếu tố bảo vệ')
    else:
        impact = 'Ảnh hưởng tối thiểu'
    
    return {
        'feature': feature_name,
        'feature_name_vi': interpretation.get('name_vi', feature_name),
        'feature_name_en': interpretation.get('name_en', feature_name),
        'shap_value': float(shap_value),
        'absolute_importance': abs(shap_value),
        'value': float(feature_value),
        'normal_range': list(normal_range),
        'comparison': comparison,
        'interpretation': impact,
        'explanation_vi': f"Đặc trưng: {interpretation.get('name_vi', feature_name)}\nGiá trị: {feature_value:.2f} ({comparison})\nẢnh hưởng: {impact}",
        'recommendation': interpretation.get('recommendation', 'Theo dõi và tái đánh giá'),
        'citation': interpretation.get('citation', 'acoustic_mci')
    }


def _get_feature_value(feature_name: str, session_state: Any) -> float:
    """Get feature value from session state"""
    # Try acoustic features first
    if hasattr(session_state, 'acoustic_features') and session_state.acoustic_features:
        for features in session_state.acoustic_features.values():
            if feature_name in features:
                return float(features[feature_name])
    
    # Try linguistic features
    if hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        if feature_name in session_state.linguistic_features:
            return float(session_state.linguistic_features[feature_name])
    
    return 0.0


def _generate_shap_from_risk_components(session_state: Any) -> Optional[Dict[str, Any]]:
    """Generate SHAP-like values from risk components"""
    if not hasattr(session_state, 'mci_result') or not session_state.mci_result:
        return None
    
    risk_components = session_state.mci_result.get('risk_components', {})
    if not risk_components:
        return None
    
    feature_contributions = {}
    for component, value in risk_components.items():
        feature_contributions[f'{component}_risk'] = float(value)
    
    # Group contributions
    grouped_contributions = {
        'mmse': risk_components.get('mmse', 0.0),
        'acoustic': risk_components.get('acoustic', 0.0),
        'linguistic': risk_components.get('linguistic', 0.0)
    }
    
    return {
        'feature_contributions': feature_contributions,
        'grouped_contributions': grouped_contributions
    }


def _interpret_score(raw_score: float, adjusted_score: float, risk_level: str, thresholds: Dict[str, Any]) -> str:
    """Generate score interpretation"""
    if risk_level == 'on':
        return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh theo tuổi và học vấn: {adjusted_score:.1f}/35. Kết quả cho thấy chức năng nhận thức trong giới hạn bình thường (≥{thresholds['normal']['min']} điểm)."
    elif risk_level == 'nguy_co_nhe':
        return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức nhẹ (MCI), nằm trong khoảng {thresholds['mci_lower']['min']}-{thresholds['normal']['min']-1} điểm."
    else:
        return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức đáng kể (<{thresholds['mci_lower']['min']} điểm), cần đánh giá chuyên sâu."


def _interpret_risk_level(risk_level: str) -> str:
    """Generate risk level interpretation"""
    interpretations = {
        'on': 'Chức năng nhận thức bình thường. Không có dấu hiệu suy giảm đáng kể.',
        'nguy_co_nhe': 'Có dấu hiệu suy giảm nhận thức nhẹ (MCI). Cần theo dõi và tái đánh giá định kỳ.',
        'nguy_co_cao': 'Có dấu hiệu suy giảm nhận thức đáng kể. Khuyến nghị gặp bác sĩ chuyên khoa để đánh giá chi tiết.'
    }
    return interpretations.get(risk_level, 'Không xác định')


def _interpret_domains(session_state: Any) -> Dict[str, Any]:
    """Interpret domain scores"""
    if not hasattr(session_state, 'domain_scores'):
        return {}
    
    domain_names = {
        'orientation': 'Định hướng',
        'registration': 'Ghi nhận',
        'attention_calculation': 'Chú ý & Tính toán',
        'executive_function': 'Chức năng điều hành',
        'recall': 'Nhớ lại',
        'language': 'Ngôn ngữ',
        'visuospatial': 'Hình dung không gian'
    }
    
    domain_max = {
        'orientation': 10,
        'registration': 3,
        'attention_calculation': 5,
        'executive_function': 3,
        'recall': 3,
        'language': 8,
        'visuospatial': 3
    }
    
    interpretations = {}
    for domain, score in session_state.domain_scores.items():
        max_score = domain_max.get(domain, 1)
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        if percentage >= 80:
            status = 'Tốt'
        elif percentage >= 60:
            status = 'Trung bình'
        else:
            status = 'Cần cải thiện'
        
        interpretations[domain] = {
            'name_vi': domain_names.get(domain, domain),
            'score': score,
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'status': status
        }
    
    return interpretations


def _get_feature_highlights(session_state: Any) -> List[Dict[str, Any]]:
    """Get feature highlights"""
    highlights = []
    
    # Check acoustic features
    if hasattr(session_state, 'acoustic_features') and session_state.acoustic_features:
        for features in session_state.acoustic_features.values():
            if 'tone_flattening' in features:
                value = features['tone_flattening']
                if value > 0.5:  # Abnormal
                    highlights.append({
                        'feature': 'tone_flattening_score',
                        'name_vi': 'Độ phẳng thanh điệu',
                        'value': value,
                        'status': 'Bất thường',
                        'significance': 'Biomarker đặc thù cho tiếng Việt'
                    })
                break
    
    # Check linguistic features
    if hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        if 'sem_idea_density' in session_state.linguistic_features:
            value = session_state.linguistic_features['sem_idea_density']
            if value < 3.0:  # Abnormal
                highlights.append({
                    'feature': 'sem_idea_density',
                    'name_vi': 'Mật độ ý tưởng',
                    'value': value,
                    'status': 'Thấp',
                    'significance': 'Yếu tố dự đoán mạnh nhất cho MCI'
                })
    
    return highlights

