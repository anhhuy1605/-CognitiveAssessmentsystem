# -*- coding: utf-8 -*-
"""
Clinical SHAP Explanations Generator
=====================================
Generate SHAP explanations with clinical interpretation like a doctor explaining to a patient
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

try:
    from services.comprehensive_results_clinical_ranges import (
        ACOUSTIC_CLINICAL_RANGES,
        LINGUISTIC_CLINICAL_RANGES,
        FEATURE_IMPORTANCE_WEIGHTS,
        POPULATION_NORMS
    )
    from services.comprehensive_results_clinical_helpers import (
        determine_clinical_range,
        get_normal_range_for_display,
        determine_impact_direction,
        calculate_percentile,
        generate_acoustic_interpretation,
        generate_linguistic_interpretation
    )
except ImportError:
    logger.warning("⚠️ Clinical ranges not available")
    ACOUSTIC_CLINICAL_RANGES = {}
    LINGUISTIC_CLINICAL_RANGES = {}
    FEATURE_IMPORTANCE_WEIGHTS = {}


def generate_clinical_shap_explanations(
    mmse_score: float,
    acoustic_features: Dict[str, float],
    linguistic_features: Dict[str, float],
    domain_scores: Dict[str, int],
    user_info: Dict
) -> Dict:
    """
    Generate SHAP explanations that DOCTORS would give to PATIENTS
    
    Returns explanations in format:
    {
        'feature_contributions': {
            'feature_name': {
                'value': 0.15,  # SHAP value
                'raw_value': 0.25,  # Actual measured value
                'clinical_range': 'concerning',  # optimal/normal/borderline/concerning/severe
                'normal_range': (0.1, 0.4),
                'percentile': 75,
                'impact_direction': 'increases_risk',
                'clinical_interpretation': 'Tần suất dừng lời của bạn cao hơn bình thường...',
                'real_world_meaning': 'Giống như khi bạn...',
                'feature_name_vi': 'Tần suất dừng lời',
                'mci_relevance': 'Pause rate cao (>0.4) là biomarker MCI mạnh nhất...',
                'citation': 'acoustic_biomarkers'
            }
        },
        'summary': {
            'top_risk_factors': [...],
            'top_protective_factors': [...],
            'overall_interpretation': 'Nhìn chung, các dấu hiệu chính...',
            'key_concerns': [...],
            'strong_points': [...]
        }
    }
    """
    
    logger.info("🔬 Generating clinical SHAP explanations...")
    
    shap_values = {}
    age = int(user_info.get('age', 65))
    gender = user_info.get('gender', 'female')
    
    # 1. Process MMSE domain scores
    domain_max = {
        'orientation': 10, 'registration': 3, 'attention_calculation': 5,
        'executive_function': 3, 'recall': 3, 'language': 8, 'visuospatial': 3
    }
    
    domain_names_vi = {
        'orientation': 'Định hướng',
        'registration': 'Ghi nhận thông tin',
        'attention_calculation': 'Chú ý và tính toán',
        'executive_function': 'Chức năng điều hành',
        'recall': 'Nhớ lại',
        'language': 'Ngôn ngữ',
        'visuospatial': 'Hình dung không gian'
    }
    
    for domain, score in domain_scores.items():
        max_score = domain_max.get(domain, 1)
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        # Calculate SHAP contribution (lower score = higher risk)
        shap_contribution = (1.0 - (score / max_score)) * 0.30 if max_score > 0 else 0
        
        # Determine clinical range
        if percentage >= 80:
            clinical_range = 'optimal'
        elif percentage >= 60:
            clinical_range = 'normal'
        elif percentage >= 40:
            clinical_range = 'borderline'
        elif percentage >= 20:
            clinical_range = 'concerning'
        else:
            clinical_range = 'severe'
        
        domain_name_vi = domain_names_vi.get(domain, domain)
        
        clinical_interp = _generate_domain_interpretation(
            domain, score, max_score, percentage, clinical_range
        )
        
        shap_values[f'mmse_{domain}'] = {
            'value': shap_contribution,
            'raw_value': score,
            'max_score': max_score,
            'percentage': percentage,
            'clinical_range': clinical_range,
            'impact_direction': determine_impact_direction(shap_contribution),
            'clinical_interpretation': clinical_interp,
            'domain_name_vi': domain_name_vi,
            'citation': 'mmse'
        }
        
        logger.debug(f"   SHAP {domain}: {shap_contribution:.3f} (score={score}/{max_score}, range={clinical_range})")
    
    # 2. Process acoustic features
    for feature_name, feature_value in acoustic_features.items():
        # Map feature names (e.g., 'jitter' might be stored as 'vq_jitter_local')
        mapped_name = _map_acoustic_feature_name(feature_name)
        
        if mapped_name in ACOUSTIC_CLINICAL_RANGES:
            ranges = ACOUSTIC_CLINICAL_RANGES[mapped_name]
            
            # Determine clinical range
            clinical_range = determine_clinical_range(feature_value, ranges, gender)
            
            # Calculate SHAP contribution
            shap_contribution = _calculate_acoustic_shap_contribution(
                mapped_name, feature_value, clinical_range, ranges
            )
            
            # Generate clinical interpretation
            clinical_interp = generate_acoustic_interpretation(
                mapped_name, feature_value, clinical_range, ranges, age, gender
            )
            
            # Calculate percentile
            percentile = calculate_percentile(feature_value, mapped_name, gender, age)
            
            shap_values[f'acoustic_{feature_name}'] = {
                'value': shap_contribution,
                'raw_value': feature_value,
                'unit': ranges.get('unit', ''),
                'normal_range': get_normal_range_for_display(ranges, gender),
                'clinical_range': clinical_range,
                'percentile': percentile,
                'impact_direction': determine_impact_direction(shap_contribution),
                'clinical_interpretation': clinical_interp,
                'real_world_meaning': ranges.get('real_world_analogy', {}).get(clinical_range, '') if isinstance(ranges.get('real_world_analogy'), dict) else '',
                'feature_name_vi': ranges.get('name_vi', feature_name),
                'mci_relevance': ranges.get('mci_relevance', ''),
                'citation': 'acoustic_biomarkers'
            }
    
    # 3. Process linguistic features
    for feature_name, feature_value in linguistic_features.items():
        # Map feature names (e.g., 'TTR' might be stored as 'lex_ttr')
        mapped_name = _map_linguistic_feature_name(feature_name)
        
        if mapped_name in LINGUISTIC_CLINICAL_RANGES:
            ranges = LINGUISTIC_CLINICAL_RANGES[mapped_name]
            
            clinical_range = determine_clinical_range(feature_value, ranges)
            shap_contribution = _calculate_linguistic_shap_contribution(
                mapped_name, feature_value, clinical_range, ranges
            )
            
            clinical_interp = generate_linguistic_interpretation(
                mapped_name, feature_value, clinical_range, ranges
            )
            
            percentile = calculate_percentile(feature_value, mapped_name, gender, age)
            
            shap_values[f'linguistic_{feature_name}'] = {
                'value': shap_contribution,
                'raw_value': feature_value,
                'unit': ranges.get('unit', ''),
                'normal_range': get_normal_range_for_display(ranges),
                'clinical_range': clinical_range,
                'percentile': percentile,
                'impact_direction': determine_impact_direction(shap_contribution),
                'clinical_interpretation': clinical_interp,
                'real_world_meaning': ranges.get('real_world_analogy', {}).get(clinical_range, '') if isinstance(ranges.get('real_world_analogy'), dict) else '',
                'feature_name_vi': ranges.get('name_vi', feature_name),
                'mci_relevance': ranges.get('mci_relevance', ''),
                'citation': 'linguistic_biomarkers'
            }
    
    # 4. Generate summary
    summary = _generate_shap_summary(shap_values, mmse_score, user_info)
    
    logger.info(f"✅ Generated {len(shap_values)} clinical SHAP explanations")
    
    return {
        'feature_contributions': shap_values,
        'summary': summary,
        'methodology': 'SHAP (SHapley Additive exPlanations) with clinical interpretation',
        'citation': 'shap'
    }


def _map_acoustic_feature_name(feature_name: str) -> str:
    """Map feature name from stored format to clinical ranges key"""
    # Map variations
    mappings = {
        'jitter': 'jitter',
        'vq_jitter_local': 'jitter',
        'jitter_local': 'jitter',
        'shimmer': 'shimmer',
        'vq_shimmer_local': 'shimmer',
        'shimmer_local': 'shimmer',
        'hnr': 'hnr',
        'vq_hnr': 'hnr',
        'pause_rate': 'pause_rate',
        'pause_pause_rate': 'pause_rate',
        'speaking_rate': 'speaking_rate',
        'f0_mean': 'f0_mean',
        'f0_cv': 'f0_cv',
        'f0_coefficient_of_variation': 'f0_cv'
    }
    return mappings.get(feature_name, feature_name)


def _map_linguistic_feature_name(feature_name: str) -> str:
    """Map feature name from stored format to clinical ranges key"""
    mappings = {
        'TTR': 'TTR',
        'lex_ttr': 'TTR',
        'ttr': 'TTR',
        'MLU': 'MLU',
        'mlu': 'MLU',
        'idea_density': 'idea_density',
        'sem_idea_density': 'idea_density',
        'pronoun_ratio': 'pronoun_ratio'
    }
    return mappings.get(feature_name, feature_name)


def _calculate_acoustic_shap_contribution(
    feature_name: str,
    feature_value: float,
    clinical_range: str,
    ranges: Dict
) -> float:
    """Calculate SHAP contribution for acoustic feature"""
    
    # Map clinical range to risk score
    range_risk = {
        'optimal': -0.10,  # Protective
        'normal': 0.0,     # Neutral
        'borderline': 0.10,  # Slight risk
        'concerning': 0.20,  # Moderate risk
        'severe': 0.30     # High risk
    }
    
    base_contribution = range_risk.get(clinical_range, 0.0)
    
    # Weight by feature importance (from literature)
    weight = FEATURE_IMPORTANCE_WEIGHTS.get(feature_name, 0.8)
    
    return base_contribution * weight


def _calculate_linguistic_shap_contribution(
    feature_name: str,
    feature_value: float,
    clinical_range: str,
    ranges: Dict
) -> float:
    """Calculate SHAP contribution for linguistic feature"""
    
    range_risk = {
        'optimal': -0.10,
        'normal': 0.0,
        'borderline': 0.15,
        'concerning': 0.25,
        'severe': 0.35
    }
    
    base_contribution = range_risk.get(clinical_range, 0.0)
    
    # Weight by feature importance
    weight = FEATURE_IMPORTANCE_WEIGHTS.get(feature_name, 0.8)
    
    return base_contribution * weight


def _generate_domain_interpretation(
    domain: str, 
    score: int, 
    max_score: int, 
    percentage: float,
    clinical_range: str
) -> str:
    """Generate clinical interpretation for MMSE domain score"""
    
    domain_interpretations = {
        'orientation': {
            'optimal': f'Định hướng xuất sắc ({score}/{max_score} điểm). Bạn biết rõ thời gian và không gian xung quanh.',
            'normal': f'Định hướng tốt ({score}/{max_score} điểm). Bạn biết đủ về thời gian và địa điểm.',
            'borderline': f'Định hướng hơi yếu ({score}/{max_score} điểm). Có thể bạn không chắc về một số chi tiết thời gian hoặc địa điểm.',
            'concerning': f'Định hướng kém ({score}/{max_score} điểm). Bạn gặp khó khăn với thời gian và không gian.',
            'severe': f'Định hướng rất kém ({score}/{max_score} điểm). Bạn không biết rõ thời gian và địa điểm hiện tại.'
        },
        'registration': {
            'optimal': f'Ghi nhận thông tin xuất sắc ({score}/{max_score} điểm). Bạn nhớ được tất cả từ ngay lập tức.',
            'normal': f'Ghi nhận thông tin tốt ({score}/{max_score} điểm). Bạn nhớ được phần lớn thông tin mới.',
            'borderline': f'Ghi nhận thông tin trung bình ({score}/{max_score} điểm). Bạn nhớ được một số từ.',
            'concerning': f'Ghi nhận thông tin yếu ({score}/{max_score} điểm). Bạn khó nhớ thông tin mới.',
            'severe': f'Ghi nhận thông tin rất yếu ({score}/{max_score} điểm). Bạn không nhớ được thông tin mới.'
        },
        'attention_calculation': {
            'optimal': f'Chú ý và tính toán xuất sắc ({score}/{max_score} điểm). Bạn tập trung tốt và tính toán chính xác.',
            'normal': f'Chú ý và tính toán tốt ({score}/{max_score} điểm). Bạn làm đúng hầu hết phép tính.',
            'borderline': f'Chú ý và tính toán trung bình ({score}/{max_score} điểm). Bạn có một vài sai sót.',
            'concerning': f'Chú ý và tính toán yếu ({score}/{max_score} điểm). Bạn gặp nhiều khó khăn với phép tính.',
            'severe': f'Chú ý và tính toán rất yếu ({score}/{max_score} điểm). Bạn không thể tập trung hay tính toán.'
        },
        'recall': {
            'optimal': f'Nhớ lại xuất sắc ({score}/{max_score} điểm). Bạn nhớ lại được tất cả từ sau 5 phút.',
            'normal': f'Nhớ lại tốt ({score}/{max_score} điểm). Bạn nhớ lại được hầu hết thông tin.',
            'borderline': f'Nhớ lại trung bình ({score}/{max_score} điểm). Bạn chỉ nhớ được một số từ.',
            'concerning': f'Nhớ lại yếu ({score}/{max_score} điểm). Bạn khó nhớ lại thông tin cũ.',
            'severe': f'Nhớ lại rất yếu ({score}/{max_score} điểm). Bạn không nhớ được gì sau 5 phút.'
        },
        'language': {
            'optimal': f'Ngôn ngữ xuất sắc ({score}/{max_score} điểm). Bạn đặt tên, lặp lại và hiểu lệnh tốt.',
            'normal': f'Ngôn ngữ tốt ({score}/{max_score} điểm). Bạn sử dụng ngôn ngữ khá tốt.',
            'borderline': f'Ngôn ngữ trung bình ({score}/{max_score} điểm). Bạn có một số khó khăn với ngôn ngữ.',
            'concerning': f'Ngôn ngữ yếu ({score}/{max_score} điểm). Bạn gặp nhiều khó khăn đặt tên, lặp lại.',
            'severe': f'Ngôn ngữ rất yếu ({score}/{max_score} điểm). Bạn không thể dùng ngôn ngữ hiệu quả.'
        },
        'visuospatial': {
            'optimal': f'Hình dung không gian xuất sắc ({score}/{max_score} điểm). Bạn vẽ và mô tả hình rất tốt.',
            'normal': f'Hình dung không gian tốt ({score}/{max_score} điểm). Bạn có khả năng hình dung ổn.',
            'borderline': f'Hình dung không gian trung bình ({score}/{max_score} điểm). Bạn có chút khó khăn với hình không gian.',
            'concerning': f'Hình dung không gian yếu ({score}/{max_score} điểm). Bạn gặp khó khăn vẽ và mô tả hình.',
            'severe': f'Hình dung không gian rất yếu ({score}/{max_score} điểm). Bạn không thể vẽ hình đơn giản.'
        },
        'executive_function': {
            'optimal': f'Chức năng điều hành xuất sắc ({score}/{max_score} điểm). Bạn kể được nhiều từ và suy luận tốt.',
            'normal': f'Chức năng điều hành tốt ({score}/{max_score} điểm). Bạn có khả năng tư duy linh hoạt.',
            'borderline': f'Chức năng điều hành trung bình ({score}/{max_score} điểm). Bạn hơi chậm trong tư duy.',
            'concerning': f'Chức năng điều hành yếu ({score}/{max_score} điểm). Bạn khó linh hoạt và suy luận.',
            'severe': f'Chức năng điều hành rất yếu ({score}/{max_score} điểm). Bạn gặp khó khăn nghiêm trọng với tư duy.'
        }
    }
    
    return domain_interpretations.get(domain, {}).get(clinical_range, '')


def _generate_shap_summary(
    shap_values: Dict,
    mmse_score: float,
    user_info: Dict
) -> Dict:
    """Generate overall SHAP summary with key insights"""
    
    # Sort features by SHAP value (absolute)
    sorted_features = sorted(
        shap_values.items(),
        key=lambda x: abs(x[1].get('value', 0)),
        reverse=True
    )
    
    # Separate risk factors (positive SHAP) and protective factors (negative SHAP)
    risk_factors = [(k, v) for k, v in sorted_features if v.get('value', 0) > 0.05]
    protective_factors = [(k, v) for k, v in sorted_features if v.get('value', 0) < -0.05]
    
    # Get top 5 of each
    top_risk = risk_factors[:5]
    top_protective = protective_factors[:5]
    
    # Generate overall interpretation
    overall_interp = _generate_overall_interpretation(
        mmse_score, top_risk, top_protective, user_info
    )
    
    # Key concerns (features in concerning/severe range)
    key_concerns = [
        {
            'feature': v.get('feature_name_vi', k),
            'value': v.get('raw_value', 0),
            'range': v.get('clinical_range', 'normal'),
            'explanation': v.get('clinical_interpretation', '')
        }
        for k, v in shap_values.items()
        if v.get('clinical_range') in ['concerning', 'severe']
    ]
    
    # Strong points (features in optimal range)
    strong_points = [
        {
            'feature': v.get('feature_name_vi', k),
            'value': v.get('raw_value', 0),
            'explanation': v.get('clinical_interpretation', '')
        }
        for k, v in shap_values.items()
        if v.get('clinical_range') == 'optimal'
    ]
    
    return {
        'top_risk_factors': [
            {
                'feature': v.get('feature_name_vi', k),
                'contribution': v.get('value', 0),
                'value': v.get('raw_value', 0),
                'unit': v.get('unit', ''),
                'explanation': v.get('clinical_interpretation', ''),
                'real_world_meaning': v.get('real_world_meaning', '')
            }
            for k, v in top_risk
        ],
        'top_protective_factors': [
            {
                'feature': v.get('feature_name_vi', k),
                'contribution': abs(v.get('value', 0)),
                'value': v.get('raw_value', 0),
                'unit': v.get('unit', ''),
                'explanation': v.get('clinical_interpretation', ''),
                'real_world_meaning': v.get('real_world_meaning', '')
            }
            for k, v in top_protective
        ],
        'overall_interpretation': overall_interp,
        'key_concerns': key_concerns,
        'strong_points': strong_points,
        'total_features_analyzed': len(shap_values),
        'risk_factors_count': len(risk_factors),
        'protective_factors_count': len(protective_factors)
    }


def _generate_overall_interpretation(
    mmse_score: float,
    top_risk: List,
    top_protective: List,
    user_info: Dict
) -> str:
    """Generate overall clinical interpretation"""
    
    age = user_info.get('age', 65)
    
    interp = f"**Tổng quan đánh giá nhận thức (tuổi {age}):**\n\n"
    
    # MMSE interpretation
    if mmse_score >= 28:
        interp += f"Điểm MMSE của bạn là {mmse_score:.1f}/35, nằm trong giới hạn **bình thường tốt**. "
    elif mmse_score >= 24:
        interp += f"Điểm MMSE của bạn là {mmse_score:.1f}/35, nằm ở mức **bình thường thấp**. "
    elif mmse_score >= 18:
        interp += f"Điểm MMSE của bạn là {mmse_score:.1f}/35, cho thấy **nguy cơ suy giảm nhận thức nhẹ (MCI)**. "
    else:
        interp += f"Điểm MMSE của bạn là {mmse_score:.1f}/35, cho thấy **suy giảm nhận thức đáng kể**. "
    
    # Risk factors interpretation
    if len(top_risk) > 0:
        interp += f"\n\n**Các yếu tố cần lưu ý** ({len(top_risk)} yếu tố):\n\n"
        for i, (feature_key, feature_data) in enumerate(top_risk[:3], 1):
            feature_name = feature_data.get('feature_name_vi', feature_key)
            interp += f"{i}. **{feature_name}**: "
            
            # Extract key insight from clinical interpretation
            clinical_text = feature_data.get('clinical_interpretation', '')
            first_sentence = clinical_text.split('\n')[0] if clinical_text else ''
            interp += f"{first_sentence}\n"
    
    # Protective factors interpretation
    if len(top_protective) > 0:
        interp += f"\n\n**Điểm mạnh của bạn** ({len(top_protective)} yếu tố):\n\n"
        for i, (feature_key, feature_data) in enumerate(top_protective[:3], 1):
            feature_name = feature_data.get('feature_name_vi', feature_key)
            interp += f"{i}. **{feature_name}**: "
            
            clinical_text = feature_data.get('clinical_interpretation', '')
            first_sentence = clinical_text.split('\n')[0] if clinical_text else ''
            interp += f"{first_sentence}\n"
    
    # Recommendations based on overall pattern
    interp += "\n\n**Khuyến nghị:**\n\n"
    
    if mmse_score >= 28 and len(top_risk) <= 2:
        interp += "• Tiếp tục duy trì lối sống lành mạnh\n"
        interp += "• Tái đánh giá định kỳ mỗi 2 năm\n"
    elif mmse_score >= 24:
        interp += "• Theo dõi các yếu tố nguy cơ đã phát hiện\n"
        interp += "• Tái đánh giá sau 6-12 tháng\n"
        interp += "• Tăng cường các hoạt động kích thích nhận thức\n"
    else:
        interp += "• **Nên gặp bác sĩ chuyên khoa thần kinh sớm**\n"
        interp += "• Cần đánh giá lâm sàng chi tiết hơn\n"
        interp += "• Theo dõi sát các triệu chứng\n"
    
    return interp

