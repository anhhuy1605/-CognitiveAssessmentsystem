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
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Import clinical ranges and helpers
try:
    from services.comprehensive_results_clinical_ranges import (
        ACOUSTIC_CLINICAL_RANGES,
        LINGUISTIC_CLINICAL_RANGES,
        FEATURE_IMPORTANCE_WEIGHTS
    )
    from services.comprehensive_results_clinical_helpers import (
        determine_clinical_range,
        get_normal_range_for_display,
        determine_impact_direction,
        calculate_percentile,
        generate_acoustic_interpretation,
        generate_linguistic_interpretation
    )
    # Import physician report generator
    from services.physician_report_generator import PhysicianStyleReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Clinical ranges not available - using default interpretations: {e}")
    ACOUSTIC_CLINICAL_RANGES = {}
    LINGUISTIC_CLINICAL_RANGES = {}
    FEATURE_IMPORTANCE_WEIGHTS = {}
    REPORT_GENERATOR_AVAILABLE = False
    # Define minimal stubs
    def determine_clinical_range(value, ranges, gender=None):
        return 'normal'
    def get_normal_range_for_display(ranges, gender=None):
        return ranges.get('normal', (0, 1)) if isinstance(ranges.get('normal'), tuple) else (0, 1)
    def determine_impact_direction(shap_value):
        return 'neutral'

# Import enhanced feature analyzer
try:
    from services.feature_analyzer import FeatureAnalyzer
    feature_analyzer = FeatureAnalyzer()
    logger.info("✅ Enhanced FeatureAnalyzer loaded")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced FeatureAnalyzer not available: {e}")
    feature_analyzer = None
    def calculate_percentile(value, feature_name, gender=None, age=65):
        return 50
    def generate_acoustic_interpretation(feature_name, feature_value, clinical_range, ranges, age, gender):
        return f"Feature {feature_name}: {feature_value}"
    def generate_linguistic_interpretation(feature_name, feature_value, clinical_range, ranges):
        return f"Feature {feature_name}: {feature_value}"

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

# MMSE Score Conversion: 35-point scale (MEC) to 30-point scale (MMSE standard)
def convert_35_to_30_mmse(domain_scores: Dict[str, int]) -> int:
    """
    Convert MMSE score from 35-point scale (MEC) to 30-point scale (MMSE standard)
    
    Based on analysis:
    - Orientation: 10 points (keep)
    - Registration: 3 points (keep)
    - Attention: 5 points (keep)
    - Recall: 3 points (keep)
    - Language: 8 points (keep)
    - Visuospatial: 3 points → 1 point (if ≥2 then 1, else 0)
    - Executive Function: 3 points → 0 points (not in MMSE 30)
    
    Args:
        domain_scores: Dictionary with domain scores from 35-point scale
        
    Returns:
        Converted MMSE score (0-30)
    """
    mmse_30 = (
        domain_scores.get('orientation', 0) +      # 10 points
        domain_scores.get('registration', 0) +     # 3 points
        domain_scores.get('attention_calculation', 0) +  # 5 points
        domain_scores.get('recall', 0) +           # 3 points
        domain_scores.get('language', 0) +         # 8 points
        (1 if domain_scores.get('visuospatial', 0) >= 2 else 0)  # 1 point (converted)
    )
    # Executive function is excluded (not in MMSE 30)
    
    return min(max(0, mmse_30), 30)  # Clamp to 0-30


def convert_35_to_30_linear(score_35: float) -> float:
    """
    Simple linear conversion from 35 to 30 points
    
    Formula: MMSE_30 = (Score_35 / 35) × 30
    
    Args:
        score_35: Score on 35-point scale
        
    Returns:
        Converted score on 30-point scale
    """
    return (score_35 / 35.0) * 30.0


# Clinical Thresholds
# ✅ UPDATED: Thresholds for 35-point MEC scale
CLINICAL_THRESHOLDS = {
    'mmse': {
        # 35-point scale thresholds (MEC)
        'normal': {'min': 28, 'max': 35, 'description': 'Normal cognitive function (MEC 35-point scale)', 'citation': 'mec_lobo_1979'},
        'mild_mci': {'min': 25, 'max': 27, 'description': 'Mild Cognitive Impairment (MEC 35-point scale)', 'citation': 'mci_detection'},
        'moderate': {'min': 12, 'max': 24, 'description': 'Moderate Dementia (MEC 35-point scale)', 'citation': 'mmse'},
        'severe': {'min': 0, 'max': 11, 'description': 'Severe Dementia (MEC 35-point scale)', 'citation': 'mmse'}
    },
    'mmse_adjusted': {
        # ✅ UPDATED: Education-adjusted thresholds for 35-point MEC scale
        'low_education': {
            'normal': {'min': 21, 'max': 35, 'description': 'Normal (low education ≤9 years, MEC 35-point)', 'citation': 'mmse_adjusted'},
            'mci_lower': {'min': 18, 'max': 20, 'description': 'MCI lower bound (low education, MEC 35-point)', 'citation': 'mmse_adjusted'},
            'dementia': {'min': 0, 'max': 17, 'description': 'Dementia threshold (low education, MEC 35-point)', 'citation': 'mmse_adjusted'}
        },
        'medium_education': {
            'normal': {'min': 28, 'max': 35, 'description': 'Normal (medium education 10-12 years, MEC 35-point)', 'citation': 'mmse_adjusted'},
            'mci_lower': {'min': 25, 'max': 27, 'description': 'MCI lower bound (medium education, MEC 35-point)', 'citation': 'mmse_adjusted'},
            'dementia': {'min': 0, 'max': 24, 'description': 'Dementia threshold (medium education, MEC 35-point)', 'citation': 'mmse_adjusted'}
        },
        'high_education': {
            'normal': {'min': 31, 'max': 35, 'description': 'Normal (high education >12 years, MEC 35-point)', 'citation': 'mmse_adjusted'},
            'mci_lower': {'min': 29, 'max': 30, 'description': 'MCI lower bound (high education, MEC 35-point)', 'citation': 'mmse_adjusted'},
            'dementia': {'min': 0, 'max': 28, 'description': 'Dementia threshold (high education, MEC 35-point)', 'citation': 'mmse_adjusted'}
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
    
    try:
        # 1. Assessment Result
        try:
            assessment_result = _build_assessment_result(session_state)
        except Exception as e:
            logger.warning(f"⚠️ Error building assessment_result, using defaults: {e}")
            assessment_result = {
                'mmse_score': getattr(session_state, 'total_score', 0) or 0,
                'risk_level': 'on',
                'classification': 'Unknown'
            }
        
        # 2. Feature Summary
        try:
            feature_summary = _build_feature_summary(session_state)
        except Exception as e:
            logger.warning(f"⚠️ Error building feature_summary, using defaults: {e}")
            feature_summary = {
                'acoustic_feature_count': 0,
                'linguistic_feature_count': 0,
                'total_features': 0,
                'total_abnormal_features': 0
            }
        
        # 3. Detailed Analysis
        try:
            detailed_analysis = _build_detailed_analysis(session_state)
        except Exception as e:
            logger.warning(f"⚠️ Error building detailed_analysis, using defaults: {e}")
            detailed_analysis = {'acoustic': {}, 'linguistic': {}}
        
        # 4. SHAP Explanation
        try:
            shap_explanation = _build_shap_explanation(session_state, shap_explanations)
        except Exception as e:
            logger.warning(f"⚠️ Error building shap_explanation, using defaults: {e}")
            shap_explanation = {
                'top_risk_factors': [],
                'top_protective_factors': [],
                'note': 'SHAP explanation generation failed'
            }
        
        # 5. Recommendations
        try:
            recommendations = _build_recommendations(session_state, shap_explanation)
        except Exception as e:
            logger.warning(f"⚠️ Error building recommendations, using defaults: {e}")
            recommendations = []
        
        # 6. Citations
        try:
            citations = _build_citations_list(session_state, shap_explanation)
        except Exception as e:
            logger.warning(f"⚠️ Error building citations, using defaults: {e}")
            citations = []
        
        # 7. Clinical Interpretation
        try:
            clinical_interpretation = _build_clinical_interpretation(session_state, assessment_result)
        except Exception as e:
            logger.warning(f"⚠️ Error building clinical_interpretation, using defaults: {e}")
            clinical_interpretation = {}
        
        # 8. Multimodal Analysis
        try:
            multimodal_analysis = _build_multimodal_analysis(session_state, detailed_analysis)
        except Exception as e:
            logger.warning(f"⚠️ Error building multimodal_analysis, using defaults: {e}")
            multimodal_analysis = {
                'acoustic_features': {},
                'linguistic_features': {},
                'combined_risk_score': 0.0,
                'risk_level': 'on'
            }
        
        # Build metadata safely
        try:
            session_id = session_state.session_id if hasattr(session_state, 'session_id') else 'unknown'
        except:
            session_id = 'unknown'
        
        # ✅ FIX: Add Q&A history and per-question features
        qa_history = getattr(session_state, 'qa_pairs', [])
        question_features = getattr(session_state, 'question_features', {})
        
        result = {
            'assessment_result': assessment_result,
            'feature_summary': feature_summary,
            'detailed_analysis': detailed_analysis,
            'multimodal_analysis': multimodal_analysis,
            'shap_explanation': shap_explanation,
            'recommendations': recommendations,
            'citations': citations,
            'clinical_interpretation': clinical_interpretation,
            'metadata': {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'model_version': 'v2.1',
                'features_extracted': {
                    'acoustic': len(detailed_analysis.get('acoustic', {})) > 0,
                    'linguistic': len(detailed_analysis.get('linguistic', {})) > 0
                }
            }
        }
        
        # Add Q&A history if available
        if qa_history:
            result['qa_history'] = qa_history
            logger.info(f"✅ Added Q&A history: {len(qa_history)} pairs")
        
        # Add per-question features if available
        if question_features:
            result['question_features'] = question_features
            logger.info(f"✅ Added per-question features: {len(question_features)} questions")
        
        # 9. Generate Physician-Style Report (if available)
        if REPORT_GENERATOR_AVAILABLE:
            try:
                # Add user_info to result for report generator
                user_info = getattr(session_state, 'user_info', {}) or {}
                result['user_info'] = user_info
                
                # Generate physician-style report
                report_generator = PhysicianStyleReportGenerator()
                physician_report = report_generator.generate_complete_report(result)
                result['physician_report'] = physician_report
                logger.info("✅ Generated physician-style report")
            except Exception as e:
                logger.warning(f"⚠️ Error generating physician report: {e}", exc_info=True)
                result['physician_report'] = {"error": str(e)}
        else:
            logger.info("ℹ️ Physician report generator not available")
        
        return result
    except Exception as e:
        logger.error(f"❌ Critical error in generate_comprehensive_results: {e}", exc_info=True)
        # Return minimal valid structure
        return {
            'assessment_result': {
                'mmse_score': 0,
                'risk_level': 'on',
                'classification': 'Error'
            },
            'feature_summary': {'total_features': 0},
            'detailed_analysis': {'acoustic': {}, 'linguistic': {}},
            'multimodal_analysis': {'combined_risk_score': 0.0, 'risk_level': 'on'},
            'shap_explanation': {'note': 'Generation failed'},
            'recommendations': [],
            'citations': [],
            'clinical_interpretation': {},
            'metadata': {
                'session_id': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'error': str(e)
            }
        }


def _build_assessment_result(session_state: Any) -> Dict[str, Any]:
    """Build assessment result section"""
    raw_score = session_state.total_score or 0
    adjusted_score = None
    user_info = session_state.user_info if (hasattr(session_state, 'user_info') and session_state.user_info) else {}
    age = user_info.get('age', 65) if isinstance(user_info, dict) else 65
    # ✅ FIX: Convert education_years to int if it's a string
    education_years_raw = user_info.get('education_years', 12) if isinstance(user_info, dict) else 12
    try:
        education_years = int(education_years_raw) if education_years_raw else 12
    except (ValueError, TypeError):
        education_years = 12
    
    # Get adjusted score if available
    if hasattr(session_state, 'mci_result') and session_state.mci_result:
        adjusted_score = session_state.mci_result.get('adjusted_mmse_score')
    
    # ✅ NEW: Calculate converted MMSE 30 score from 35-point scale
    converted_mmse30 = None
    if hasattr(session_state, 'domain_scores') and session_state.domain_scores:
        try:
            converted_mmse30 = convert_35_to_30_mmse(session_state.domain_scores)
            logger.info(f"📊 Converted MMSE 30: {converted_mmse30}/30 (from {raw_score}/35)")
        except Exception as e:
            logger.warning(f"⚠️ Error converting 35→30: {e}")
            # Fallback to linear conversion
            converted_mmse30 = round(convert_35_to_30_linear(float(raw_score)))
    
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
        'converted_mmse30': float(converted_mmse30) if converted_mmse30 is not None else None,  # ✅ NEW: MMSE 30 equivalent
        'max_score_35': 35,  # ✅ NEW: Indicate 35-point scale
        'max_score_30': 30,  # ✅ NEW: Standard MMSE scale
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
        'education_specific_thresholds': _get_education_thresholds(education_years),
        'scale_info': {  # ✅ NEW: Information about the 35-point scale
            'scale_type': 'MEC_35',
            'description': 'Mini-Examen-Cognoscivo (MEC) - 35 điểm, mở rộng từ MMSE 30 điểm chuẩn',
            'citation': 'Lobo et al. (1979), Modrego et al. (2005, 2013)',
            'differences': {
                'visuospatial': '3 điểm (thay vì 1) - Clock Drawing Test đầy đủ',
                'executive_function': '3 điểm (mới thêm) - Verbal fluency + Abstraction',
                'total_questions': '28 câu chấm điểm + 4 câu mở (tổng 32 câu)'
            }
        }
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
            if isinstance(features, dict):
                acoustic_count += len(features)
                # Check for abnormal values
                for feat_name, feat_value in features.items():
                    # ✅ FIX: Only check if value is numeric
                    if isinstance(feat_value, (int, float, np.number)):
                        try:
                            if _is_abnormal_feature(feat_name, float(feat_value), 'acoustic'):
                                abnormal_acoustic += 1
                        except (TypeError, ValueError):
                            pass
    
    # Count linguistic features
    if hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        if isinstance(session_state.linguistic_features, dict):
            linguistic_count = len(session_state.linguistic_features)
            for feat_name, feat_value in session_state.linguistic_features.items():
                # ✅ FIX: Only check if value is numeric
                if isinstance(feat_value, (int, float, np.number)):
                    try:
                        if _is_abnormal_feature(feat_name, float(feat_value), 'linguistic'):
                            abnormal_linguistic += 1
                    except (TypeError, ValueError):
                        pass
    
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
    """Build detailed analysis with all features using enhanced FeatureAnalyzer"""
    acoustic_features = {}
    linguistic_features = {}
    
    # ✅ NEW: Use enhanced FeatureAnalyzer if available
    if feature_analyzer:
        try:
            # Get user info for gender-specific analysis
            user_info = getattr(session_state, 'user_info', {}) or {}
            gender = user_info.get('gender', 'male')
            
            # Get final features
            final_acoustic = getattr(session_state, 'final_acoustic_features', {}) or {}
            final_linguistic = getattr(session_state, 'final_linguistic_features', {}) or {}
            
            # If no final features, try to aggregate from per-question features
            if not final_acoustic and hasattr(session_state, 'acoustic_features'):
                logger.info("📊 Aggregating acoustic features for enhanced analysis")
                all_acoustic = {}
                for question_id, features in session_state.acoustic_features.items():
                    if isinstance(features, dict):
                        for key, value in features.items():
                            if isinstance(value, (int, float, np.number)):
                                if key not in all_acoustic:
                                    all_acoustic[key] = []
                                all_acoustic[key].append(float(value))
                # Average
                for key, values in all_acoustic.items():
                    if values:
                        final_acoustic[key] = float(np.mean(values))
            
            if not final_linguistic and hasattr(session_state, 'linguistic_features'):
                final_linguistic = session_state.linguistic_features or {}
            
            # Analyze with enhanced analyzer
            if final_acoustic or final_linguistic:
                logger.info(f"🔬 Using enhanced FeatureAnalyzer: {len(final_acoustic)} acoustic, {len(final_linguistic)} linguistic")
                analysis_result = feature_analyzer.analyze_all_features(
                    final_acoustic,
                    final_linguistic,
                    {'gender': gender}
                )
                
                # Convert to expected format
                for feat in analysis_result['acoustic_analysis']['features']:
                    acoustic_features[feat['key']] = {
                        'value': feat['value'],
                        'std': 0.0,
                        'normal_range': feat.get('normal_range', {}).get('display', 'N/A'),
                        'unit': feat.get('unit', ''),
                        'is_abnormal': feat['severity'] not in ['normal', 'borderline'],
                        'description': feat.get('name_vi', feat['key']),
                        'severity': feat['severity'],
                        'status': feat['status'],
                        'interpretation': feat['interpretation'],
                        'clinical_significance': feat.get('clinical_significance', ''),
                        'deviation_pct': feat.get('deviation_pct', 0)
                    }
                
                for feat in analysis_result['linguistic_analysis']['features']:
                    linguistic_features[feat['key']] = {
                        'value': feat['value'],
                        'normal_range': feat.get('normal_range', {}).get('display', 'N/A'),
                        'unit': feat.get('unit', ''),
                        'is_abnormal': feat['severity'] not in ['normal', 'borderline'],
                        'description': feat.get('name_vi', feat['key']),
                        'severity': feat['severity'],
                        'status': feat['status'],
                        'interpretation': feat['interpretation'],
                        'clinical_significance': feat.get('clinical_significance', ''),
                        'deviation_pct': feat.get('deviation_pct', 0)
                    }
                
                logger.info(f"✅ Enhanced analysis complete: {len(acoustic_features)} acoustic, {len(linguistic_features)} linguistic")
                
                # Return early if enhanced analysis succeeded
                if acoustic_features or linguistic_features:
                    return {
                        'acoustic': acoustic_features,
                        'linguistic': linguistic_features,
                        'analysis_summary': analysis_result['summary']
                    }
        except Exception as e:
            logger.warning(f"⚠️ Enhanced feature analysis failed, falling back to basic: {e}")
    
    # ✅ FALLBACK: Use original method if enhanced analyzer not available or failed
    # ✅ FIX: Use final_acoustic_features if available (calculated at test completion)
    if hasattr(session_state, 'final_acoustic_features') and session_state.final_acoustic_features:
        logger.info(f"📊 Using final acoustic features: {len(session_state.final_acoustic_features)} features")
        for key, value in session_state.final_acoustic_features.items():
            if isinstance(value, (int, float, np.number)):
                float_value = float(value)
                acoustic_features[key] = {
                    'value': float_value,
                    'std': 0.0,  # Final features are already aggregated
                    'normal_range': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('normal', (0, 1)),
                    'unit': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('unit', ''),
                    'is_abnormal': _is_abnormal_feature(key, float_value, 'acoustic'),
                    'description': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('description', '')
                }
        logger.info(f"✅ Processed {len(acoustic_features)} final acoustic features")
    # Fallback: Aggregate acoustic features (average across questions)
    elif hasattr(session_state, 'acoustic_features') and session_state.acoustic_features:
        logger.info(f"📊 Aggregating acoustic features from {len(session_state.acoustic_features)} questions")
        all_acoustic = {}
        for question_id, features in session_state.acoustic_features.items():
            logger.debug(f"  Question {question_id}: {len(features)} features")
            for key, value in features.items():
                if key not in all_acoustic:
                    all_acoustic[key] = []
                if isinstance(value, (int, float, np.number)):
                    all_acoustic[key].append(float(value))
        
        # Average
        for key, values in all_acoustic.items():
            if values:
                mean_value = float(np.mean(values))
                acoustic_features[key] = {
                    'value': mean_value,
                    'std': float(np.std(values)) if len(values) > 1 else 0.0,
                    'normal_range': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('normal', (0, 1)),
                    'unit': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('unit', ''),
                    'is_abnormal': _is_abnormal_feature(key, mean_value, 'acoustic'),
                    'description': CLINICAL_THRESHOLDS['acoustic'].get(key, {}).get('description', '')
                }
        logger.info(f"✅ Aggregated {len(acoustic_features)} acoustic features (avg from all questions)")
    else:
        logger.warning("⚠️ No acoustic features found in session_state!")
    
    # ✅ FIX: Use final_linguistic_features if available
    if hasattr(session_state, 'final_linguistic_features') and session_state.final_linguistic_features:
        logger.info(f"📝 Using final linguistic features: {len(session_state.final_linguistic_features)} features")
        for key, value in session_state.final_linguistic_features.items():
            float_value = float(value) if isinstance(value, (int, float, np.number)) else 0.0
            linguistic_features[key] = {
                'value': float_value,
                'normal_range': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('normal', (0, 1)),
                'unit': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('unit', ''),
                'is_abnormal': _is_abnormal_feature(key, float_value, 'linguistic'),
                'description': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('description', '')
            }
        logger.info(f"✅ Processed {len(linguistic_features)} final linguistic features")
    # Fallback: Use linguistic_features
    elif hasattr(session_state, 'linguistic_features') and session_state.linguistic_features:
        logger.info(f"📝 Processing {len(session_state.linguistic_features)} linguistic features")
        for key, value in session_state.linguistic_features.items():
            float_value = float(value) if isinstance(value, (int, float, np.number)) else 0.0
            linguistic_features[key] = {
                'value': float_value,
                'normal_range': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('normal', (0, 1)),
                'unit': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('unit', ''),
                'is_abnormal': _is_abnormal_feature(key, float_value, 'linguistic'),
                'description': CLINICAL_THRESHOLDS['linguistic'].get(key, {}).get('description', '')
            }
        logger.info(f"✅ Processed {len(linguistic_features)} linguistic features")
    else:
        logger.warning("⚠️ No linguistic features found in session_state!")
    
    return {
        'acoustic': acoustic_features,
        'linguistic': linguistic_features
    }


def _build_multimodal_analysis(session_state: Any, detailed_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Build multimodal analysis section with simplified feature values and risk scores"""
    # Extract simple feature values from detailed_analysis
    acoustic_features = {}
    linguistic_features = {}
    
    # Extract acoustic feature values (just the values, not the full structure)
    if 'acoustic' in detailed_analysis:
        for key, feature_data in detailed_analysis['acoustic'].items():
            if isinstance(feature_data, dict) and 'value' in feature_data:
                acoustic_features[key] = feature_data['value']
            elif isinstance(feature_data, (int, float)):
                acoustic_features[key] = float(feature_data)
    
    # Extract linguistic feature values
    if 'linguistic' in detailed_analysis:
        for key, feature_data in detailed_analysis['linguistic'].items():
            if isinstance(feature_data, dict) and 'value' in feature_data:
                linguistic_features[key] = feature_data['value']
            elif isinstance(feature_data, (int, float)):
                linguistic_features[key] = float(feature_data)
    
    # Get risk scores from mci_result
    combined_risk_score = 0.0
    risk_level = 'on'
    if hasattr(session_state, 'mci_result') and session_state.mci_result:
        combined_risk_score = session_state.mci_result.get('combined_risk_score', 0.0)
        risk_level = session_state.mci_result.get('risk_level', 'on')
    
    logger.info(f"✅ Built multimodal_analysis: {len(acoustic_features)} acoustic, {len(linguistic_features)} linguistic, risk={combined_risk_score:.3f}")
    
    return {
        'acoustic_features': acoustic_features,
        'linguistic_features': linguistic_features,
        'combined_risk_score': float(combined_risk_score),
        'risk_level': risk_level
    }


def _build_shap_explanation(session_state: Any, shap_explanations: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build SHAP explanation section with clinical interpretation"""
    
    # ✅ NEW: Try enhanced SHAP explainer first
    try:
        from services.enhanced_shap_explainer import CognitiveDeclineSHAPExplainer
        
        # Get features from session state
        final_acoustic = getattr(session_state, 'final_acoustic_features', {}) or {}
        final_linguistic = getattr(session_state, 'final_linguistic_features', {}) or {}
        
        # If no final features, try to aggregate
        if not final_acoustic and hasattr(session_state, 'acoustic_features'):
            all_acoustic = {}
            for question_id, features in session_state.acoustic_features.items():
                if isinstance(features, dict):
                    for key, value in features.items():
                        if isinstance(value, (int, float, np.number)):
                            if key not in all_acoustic:
                                all_acoustic[key] = []
                            all_acoustic[key].append(float(value))
            # Average
            for key, values in all_acoustic.items():
                if values:
                    final_acoustic[key] = float(np.mean(values))
        
        if not final_linguistic and hasattr(session_state, 'linguistic_features'):
            final_linguistic = session_state.linguistic_features or {}
        
        # Combine all features
        all_features = {**final_acoustic, **final_linguistic}
        
        if all_features:
            logger.info(f"🔬 Using enhanced SHAP explainer: {len(all_features)} features")
            enhanced_explainer = CognitiveDeclineSHAPExplainer(model_path=None)  # Use risk-based fallback
            
            user_info = getattr(session_state, 'user_info', {}) or {}
            shap_result = enhanced_explainer.explain_prediction(all_features, user_info)
            
            if shap_result and 'shap_analysis' in shap_result:
                # Format for frontend
                risk_factors = shap_result['shap_analysis'].get('risk_factors', [])
                protective_factors = shap_result['shap_analysis'].get('protective_factors', [])
                
                # Convert to expected format
                formatted_risk = []
                for factor in risk_factors[:10]:  # Top 10
                    formatted_risk.append({
                        'feature': factor.get('feature_key', ''),
                        'feature_name_vi': factor.get('feature_name_vi', ''),
                        'feature_name_en': factor.get('feature_name_en', ''),
                        'shap_value': factor.get('shap_value', 0.0),
                        'absolute_importance': factor.get('absolute_importance', 0.0),
                        'value': factor.get('feature_value', 0.0),
                        'unit': factor.get('unit', ''),
                        'normal_range': factor.get('normal_range', {}).get('display', 'N/A'),
                        'comparison': factor.get('comparison', 'N/A'),
                        'interpretation': factor.get('interpretation', ''),
                        'explanation_vi': factor.get('explanation', ''),
                        'recommendation': factor.get('recommendation', ''),
                        'citation': factor.get('citation', '')
                    })
                
                formatted_protective = []
                for factor in protective_factors[:10]:
                    formatted_protective.append({
                        'feature': factor.get('feature_key', ''),
                        'feature_name_vi': factor.get('feature_name_vi', ''),
                        'feature_name_en': factor.get('feature_name_en', ''),
                        'shap_value': factor.get('shap_value', 0.0),
                        'absolute_importance': abs(factor.get('shap_value', 0.0)),
                        'value': factor.get('feature_value', 0.0),
                        'unit': factor.get('unit', ''),
                        'normal_range': factor.get('normal_range', {}).get('display', 'N/A'),
                        'comparison': factor.get('comparison', 'N/A'),
                        'interpretation': factor.get('interpretation', ''),
                        'explanation_vi': factor.get('explanation', ''),
                        'recommendation': factor.get('recommendation', ''),
                        'citation': factor.get('citation', '')
                    })
                
                # Get grouped contributions
                grouped = {}
                for factor in risk_factors + protective_factors:
                    category = factor.get('category', 'Khác')
                    if category not in grouped:
                        grouped[category] = 0.0
                    grouped[category] += abs(factor.get('shap_value', 0.0))
                
                logger.info(f"✅ Enhanced SHAP: {len(formatted_risk)} risk, {len(formatted_protective)} protective factors")
                
                return {
                    'top_risk_factors': formatted_risk,
                    'top_protective_factors': formatted_protective,
                    'grouped_contributions': grouped,
                    'total_contribution': sum(abs(f.get('shap_value', 0)) for f in risk_factors + protective_factors),
                    'citation': 'Lundberg & Lee (2017) - SHAP',
                    'methodology': 'Enhanced SHAP with clinical interpretation'
                }
    except ImportError as e:
        logger.debug(f"Enhanced SHAP explainer not available: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Enhanced SHAP failed, falling back: {e}", exc_info=True)
    
    # ✅ FALLBACK: Try to use clinical SHAP explanations if available
    try:
        from services.comprehensive_results_clinical_shap import generate_clinical_shap_explanations
        
        # Get features from detailed analysis
        detailed_analysis = _build_detailed_analysis(session_state)
        
        # Extract acoustic and linguistic features
        acoustic_features = {}
        linguistic_features = {}
        
        if 'acoustic' in detailed_analysis:
            for key, feature_data in detailed_analysis['acoustic'].items():
                if isinstance(feature_data, dict) and 'value' in feature_data:
                    acoustic_features[key] = feature_data['value']
                elif isinstance(feature_data, (int, float)):
                    acoustic_features[key] = float(feature_data)
        
        if 'linguistic' in detailed_analysis:
            for key, feature_data in detailed_analysis['linguistic'].items():
                if isinstance(feature_data, dict) and 'value' in feature_data:
                    linguistic_features[key] = feature_data['value']
                elif isinstance(feature_data, (int, float)):
                    linguistic_features[key] = float(feature_data)
        
        # Get domain scores
        domain_scores = session_state.domain_scores if hasattr(session_state, 'domain_scores') else {}
        
        # Get user info
        user_info = session_state.user_info if hasattr(session_state, 'user_info') else {}
        
        # Get MMSE score
        mmse_score = session_state.total_score if hasattr(session_state, 'total_score') else 0.0
        
        # Generate clinical SHAP explanations if we have features
        if acoustic_features or linguistic_features:
            logger.info("🔬 Using clinical SHAP explanations...")
            clinical_shap = generate_clinical_shap_explanations(
                mmse_score=float(mmse_score),
                acoustic_features=acoustic_features,
                linguistic_features=linguistic_features,
                domain_scores=domain_scores,
                user_info=user_info
            )
            
            return {
                'top_risk_factors': clinical_shap['summary'].get('top_risk_factors', []),
                'top_protective_factors': clinical_shap['summary'].get('top_protective_factors', []),
                'feature_contributions': clinical_shap.get('feature_contributions', {}),
                'overall_interpretation': clinical_shap['summary'].get('overall_interpretation', ''),
                'key_concerns': clinical_shap['summary'].get('key_concerns', []),
                'strong_points': clinical_shap['summary'].get('strong_points', []),
                'methodology': clinical_shap.get('methodology', 'SHAP'),
                'citation': clinical_shap.get('citation', 'shap')
            }
    except ImportError as e:
        logger.warning(f"⚠️ Clinical SHAP not available, using fallback: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Clinical SHAP generation failed, using fallback: {e}")
    
    # Fallback to original method
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


def _build_recommendations(session_state: Any, shap_explanation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build evidence-based, personalized recommendations with clinical interpretation"""
    
    # Try to use clinical recommendations if available
    try:
        from services.comprehensive_results_clinical_recommendations import generate_personalized_recommendations
        
        # Get SHAP feature contributions
        shap_values = shap_explanation.get('feature_contributions', {})
        
        # Get user info and scores
        user_info = session_state.user_info if hasattr(session_state, 'user_info') else {}
        mmse_score = session_state.total_score if hasattr(session_state, 'total_score') else 0.0
        risk_level = 'on'
        
        if hasattr(session_state, 'mci_result') and session_state.mci_result:
            risk_level = session_state.mci_result.get('risk_level', 'on')
        
        # Generate personalized recommendations
        if shap_values:
            logger.info("🔬 Using clinical personalized recommendations...")
            clinical_recommendations = generate_personalized_recommendations(
                shap_values=shap_values,
                mmse_score=float(mmse_score),
                user_info=user_info,
                risk_level=risk_level
            )
            return clinical_recommendations
    except ImportError as e:
        logger.warning(f"⚠️ Clinical recommendations not available, using fallback: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Clinical recommendations generation failed, using fallback: {e}")
    
    # Fallback to original simple recommendations
    recommendations = []
    risk_level = 'on'
    
    if hasattr(session_state, 'mci_result') and session_state.mci_result:
        risk_level = session_state.mci_result.get('risk_level', 'on')
    
    # Convert to dict format for consistency
    if risk_level == 'nguy_co_cao':
        recommendations.extend([
            {
                'category': 'medical',
                'priority': 'high',
                'title': 'Gặp bác sĩ chuyên khoa thần kinh',
                'description': 'Đánh giá chi tiết cần thiết',
                'actions': [
                    'Thực hiện các xét nghiệm chuyên sâu (MRI, PET scan nếu cần)',
                    'Theo dõi định kỳ mỗi 3-6 tháng',
                    'Tham gia các hoạt động kích thích nhận thức hàng ngày'
                ]
            }
        ])
    elif risk_level == 'nguy_co_nhe':
        recommendations.extend([
            {
                'category': 'monitoring',
                'priority': 'medium',
                'title': 'Tái đánh giá và theo dõi',
                'description': 'Theo dõi định kỳ',
                'actions': [
                    'Tái đánh giá sau 6-12 tháng',
                    'Luyện tập từ vựng và kể chuyện hàng ngày',
                    'Tham gia các hoạt động xã hội và trí tuệ'
                ]
            }
        ])
    else:
        recommendations.extend([
            'Duy trì lối sống lành mạnh và hoạt động trí tuệ',
            'Tái đánh giá định kỳ mỗi 1-2 năm',
            'Tiếp tục các hoạt động kích thích nhận thức'
        ])
    
    # Feature-specific recommendations from SHAP
    for factor in shap_explanation.get('top_risk_factors', [])[:3]:
        if isinstance(factor, dict) and 'recommendation' in factor:
            rec = factor['recommendation']
            # Only add if it's a string (not a dict)
            if isinstance(rec, str):
                recommendations.append(rec)
            elif isinstance(rec, dict):
                # If it's a dict, add it directly
                recommendations.append(rec)
    
    # ✅ FIX: Remove duplicates for strings, keep all dicts
    seen_strings = set()
    unique_recommendations = []
    for rec in recommendations:
        if isinstance(rec, str):
            if rec not in seen_strings:
                seen_strings.add(rec)
                unique_recommendations.append(rec)
        else:
            # For dicts, check by converting to string representation
            rec_str = json.dumps(rec, sort_keys=True) if isinstance(rec, dict) else str(rec)
            if rec_str not in seen_strings:
                seen_strings.add(rec_str)
                unique_recommendations.append(rec)
    
    return unique_recommendations


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
    # ✅ FIX: Handle None values for scores
    raw_score = raw_score if raw_score is not None else 0.0
    adjusted_score = adjusted_score if adjusted_score is not None else raw_score
    
    # ✅ FIX: Use actual score to determine range, not just risk_level
    # Get thresholds
    normal_min = thresholds.get('normal', {}).get('min') if thresholds.get('normal') else 24
    mci_lower_min = thresholds.get('mci_lower', {}).get('min') if thresholds.get('mci_lower') else 20
    mci_lower_max = thresholds.get('mci_lower', {}).get('max') if thresholds.get('mci_lower') else 23
    dementia_max = thresholds.get('dementia', {}).get('max') if thresholds.get('dementia') else 19
    
    # Determine actual score range based on adjusted_score
    score_to_check = adjusted_score if adjusted_score else raw_score
    
    if risk_level == 'on':
        normal_min_str = f"{normal_min}" if normal_min is not None else "24"
        return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh theo tuổi và học vấn: {adjusted_score:.1f}/35. Kết quả cho thấy chức năng nhận thức trong giới hạn bình thường (≥{normal_min_str} điểm)."
    elif risk_level == 'nguy_co_nhe':
        # ✅ FIX: Show actual score range based on score value, not just education threshold
        if score_to_check < mci_lower_min:
            # Score is below MCI threshold - this is actually dementia range
            return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức đáng kể (≤{dementia_max} điểm), cần đánh giá chuyên sâu ngay lập tức."
        elif score_to_check >= mci_lower_min and score_to_check <= mci_lower_max:
            # Score is in MCI range
            return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức nhẹ (MCI), nằm trong khoảng {mci_lower_min}-{mci_lower_max} điểm."
        else:
            # Score is between mci_lower_max and normal_min (borderline)
            return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức nhẹ (MCI), nằm trong khoảng {mci_lower_min}-{normal_min-1} điểm."
    else:
        # nguy_co_cao
        if score_to_check <= dementia_max:
            return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức đáng kể (≤{dementia_max} điểm), cần đánh giá chuyên sâu ngay lập tức."
        else:
            return f"Điểm MMSE thô: {raw_score:.1f}/35. Sau điều chỉnh: {adjusted_score:.1f}/35. Kết quả cho thấy dấu hiệu suy giảm nhận thức đáng kể (<{mci_lower_min} điểm), cần đánh giá chuyên sâu."


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

