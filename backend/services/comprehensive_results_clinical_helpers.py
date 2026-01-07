# -*- coding: utf-8 -*-
"""
Clinical Interpretation Helper Functions
=========================================
Helper functions for generating clinical interpretations from feature values
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

def determine_clinical_range(value: float, ranges: Dict, gender: str = None) -> str:
    """Determine which clinical range a value falls into"""
    
    if gender and isinstance(ranges.get('optimal'), dict):
        # Gender-specific ranges
        optimal = ranges['optimal'].get(gender, ranges['optimal'].get('female', (0, 1)))
        normal = ranges['normal'].get(gender, ranges['normal'].get('female', (0, 1)))
    else:
        optimal = ranges.get('optimal', (0, 1))
        normal = ranges.get('normal', (0, 1))
    
    borderline = ranges.get('borderline', (0, 1))
    concerning = ranges.get('concerning', (0, 1))
    severe = ranges.get('severe', (0, 1))
    
    if optimal[0] <= value <= optimal[1]:
        return 'optimal'
    elif normal[0] <= value <= normal[1]:
        return 'normal'
    elif borderline[0] <= value <= borderline[1]:
        return 'borderline'
    elif concerning[0] <= value <= concerning[1]:
        return 'concerning'
    else:
        return 'severe'


def get_normal_range_for_display(ranges: Dict, gender: str = None) -> tuple:
    """Get normal range for display purposes"""
    if gender and isinstance(ranges.get('normal'), dict):
        return ranges['normal'].get(gender, ranges['normal'].get('female', (0, 1)))
    return ranges.get('normal', (0, 1))


def determine_impact_direction(shap_value: float) -> str:
    """Determine if feature increases or decreases risk"""
    if shap_value > 0.05:
        return 'increases_risk'
    elif shap_value < -0.05:
        return 'decreases_risk'
    else:
        return 'neutral'


def calculate_percentile(value: float, feature_name: str, gender: str = None, age: int = 65) -> int:
    """
    Calculate accurate percentile based on population norms
    
    Returns: Percentile (0-100) indicating where user stands in population
    
    Example:
        - Percentile 25 = "Bạn thấp hơn 75% người cùng độ tuổi"
        - Percentile 75 = "Bạn cao hơn 75% người cùng độ tuổi"
    """
    try:
        from services.comprehensive_results_clinical_ranges import POPULATION_NORMS
        
        # Get feature norms
        if feature_name in POPULATION_NORMS.get('acoustic', {}):
            norms = POPULATION_NORMS['acoustic'][feature_name]
        elif feature_name in POPULATION_NORMS.get('linguistic', {}):
            norms = POPULATION_NORMS['linguistic'][feature_name]
        else:
            return 50  # Default to median if no norms
        
        percentiles = norms.get('percentiles', {})
        
        # Handle gender-specific percentiles (e.g., f0_mean)
        if isinstance(percentiles, dict) and gender in percentiles:
            percentiles = percentiles[gender]
        
        # Calculate percentile using linear interpolation
        if not percentiles:
            return 50
        
        # Sort percentile points
        p_values = sorted([(int(k[1:]), v) for k, v in percentiles.items() if k.startswith('p')])
        
        if not p_values:
            return 50
        
        # Edge cases
        if value <= p_values[0][1]:
            return p_values[0][0]
        if value >= p_values[-1][1]:
            return p_values[-1][0]
        
        # Linear interpolation between percentile points
        for i in range(len(p_values) - 1):
            p1, v1 = p_values[i]
            p2, v2 = p_values[i + 1]
            
            if v1 <= value <= v2:
                # Linear interpolation
                percentile = p1 + (p2 - p1) * (value - v1) / (v2 - v1) if (v2 - v1) > 0 else p1
                return int(round(percentile))
        
        return 50  # Fallback
    except ImportError:
        return 50  # Fallback if POPULATION_NORMS not available
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error calculating percentile: {e}")
        return 50  # Fallback on error


def generate_acoustic_interpretation(
    feature_name: str,
    feature_value: float,
    clinical_range: str,
    ranges: Dict,
    age: int,
    gender: str
) -> str:
    """Generate clinical interpretation for acoustic feature"""
    
    feature_name_vi = ranges.get('name_vi', feature_name)
    unit = ranges.get('unit', '')
    clinical_meaning = ranges.get('clinical_meaning', {})
    
    if isinstance(clinical_meaning, dict):
        clinical_text = clinical_meaning.get(clinical_range, '')
    else:
        clinical_text = clinical_meaning
    
    real_world = ranges.get('real_world_analogy', {})
    if isinstance(real_world, dict):
        real_world_text = real_world.get(clinical_range, '')
    else:
        real_world_text = real_world
    
    # Format value with appropriate precision
    if feature_value < 1:
        value_str = f"{feature_value:.3f}"
    elif feature_value < 10:
        value_str = f"{feature_value:.2f}"
    else:
        value_str = f"{feature_value:.1f}"
    
    interpretation = f"**{feature_name_vi}**: {value_str} {unit}\n\n"
    
    if clinical_text:
        interpretation += f"• **Đánh giá**: {clinical_text}\n"
    
    if real_world_text:
        interpretation += f"• **Giống như**: {real_world_text}\n"
    
    # Add MCI relevance
    mci_relevance = ranges.get('mci_relevance', '')
    if mci_relevance and clinical_range in ['concerning', 'severe']:
        interpretation += f"• **Ý nghĩa lâm sàng**: {mci_relevance}\n"
    
    return interpretation


def generate_linguistic_interpretation(
    feature_name: str,
    feature_value: float,
    clinical_range: str,
    ranges: Dict
) -> str:
    """Generate clinical interpretation for linguistic feature"""
    
    feature_name_vi = ranges.get('name_vi', feature_name)
    unit = ranges.get('unit', '')
    clinical_meaning = ranges.get('clinical_meaning', {})
    
    if isinstance(clinical_meaning, dict):
        clinical_text = clinical_meaning.get(clinical_range, '')
    else:
        clinical_text = clinical_meaning
    
    real_world = ranges.get('real_world_analogy', {})
    if isinstance(real_world, dict):
        real_world_text = real_world.get(clinical_range, '')
    else:
        real_world_text = real_world
    
    # Format value
    if feature_value < 1:
        value_str = f"{feature_value:.2f}"
    elif feature_value < 10:
        value_str = f"{feature_value:.1f}"
    else:
        value_str = f"{int(feature_value)}"
    
    interpretation = f"**{feature_name_vi}**: {value_str} {unit}\n\n"
    
    if clinical_text:
        interpretation += f"• **Đánh giá**: {clinical_text}\n"
    
    if real_world_text:
        interpretation += f"• **Ví dụ thực tế**: {real_world_text}\n"
    
    # Add MCI relevance
    mci_relevance = ranges.get('mci_relevance', '')
    if mci_relevance and clinical_range in ['concerning', 'severe']:
        interpretation += f"• **Ý nghĩa lâm sàng**: {mci_relevance}\n"
    
    return interpretation

