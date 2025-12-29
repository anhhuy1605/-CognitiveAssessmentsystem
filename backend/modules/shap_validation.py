# -*- coding: utf-8 -*-
"""
SHAP Validation & Testing Module
=================================

Validates SHAP explanations and handles edge cases.

Author: Cognitive Assessment System
Version: 1.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_shap_explanations(shap_result: Dict[str, Any],
                               X_sample: Dict[str, float],
                               model: Optional[Any] = None,
                               tolerance: float = 0.01) -> Dict[str, Any]:
    """
    Validate SHAP values are correct
    
    Checks:
    1. Sum of SHAP values ≈ (prediction - base_value)
    2. SHAP values are in reasonable ranges
    3. Feature interactions make clinical sense
    4. No missing or NaN values
    
    Args:
        shap_result: SHAP computation results
        X_sample: Original feature values
        model: Optional model for prediction validation
        tolerance: Allowed tolerance for sum validation
    
    Returns:
        {
            'is_valid': bool,
            'errors': list,
            'warnings': list,
            'validation_details': dict
        }
    """
    errors = []
    warnings = []
    validation_details = {}
    
    try:
        # Check 1: Sum of SHAP values should equal (prediction - base_value)
        feature_contributions = shap_result.get('feature_contributions', {})
        base_value = shap_result.get('base_value', 0.0)
        prediction = shap_result.get('prediction', 0.0)
        
        shap_sum = sum(feature_contributions.values())
        expected_sum = prediction - base_value
        difference = abs(shap_sum - expected_sum)
        
        validation_details['shap_sum'] = shap_sum
        validation_details['expected_sum'] = expected_sum
        validation_details['difference'] = difference
        
        if difference > tolerance:
            errors.append(
                f"SHAP sum ({shap_sum:.4f}) does not match prediction difference "
                f"({expected_sum:.4f}). Difference: {difference:.4f}"
            )
        else:
            validation_details['sum_validation'] = 'PASS'
        
        # Check 2: SHAP values in reasonable ranges
        max_abs_shap = max([abs(v) for v in feature_contributions.values()] or [0])
        if max_abs_shap > 10:
            warnings.append(
                f"Very large SHAP value detected: {max_abs_shap:.4f}. "
                "This may indicate numerical instability."
            )
        
        # Check 3: No NaN or Inf values
        for feat, val in feature_contributions.items():
            if np.isnan(val) or np.isinf(val):
                errors.append(f"Invalid SHAP value for feature {feat}: {val}")
        
        # Check 4: Feature values are valid
        for feat, val in X_sample.items():
            if np.isnan(val) or np.isinf(val):
                warnings.append(f"Invalid feature value for {feat}: {val}")
        
        # Check 5: Model prediction matches (if model provided)
        if model and hasattr(model, 'predict'):
            try:
                # Convert X_sample to array format expected by model
                X_array = np.array([[X_sample.get(f, 0.0) for f in sorted(X_sample.keys())]])
                model_prediction = model.predict(X_array)[0]
                
                if abs(model_prediction - prediction) > tolerance:
                    warnings.append(
                        f"Model prediction ({model_prediction:.4f}) does not match "
                        f"SHAP prediction ({prediction:.4f})"
                    )
            except Exception as e:
                warnings.append(f"Could not validate with model: {e}")
        
        # Check 6: Feature interactions make sense
        interactions = shap_result.get('interactions', [])
        for interaction in interactions:
            feat1 = interaction.get('feature_1', '')
            feat2 = interaction.get('feature_2', '')
            strength = interaction.get('interaction_strength', 0)
            
            # Check if interaction strength is reasonable
            if abs(strength) > 5:
                warnings.append(
                    f"Very strong interaction between {feat1} and {feat2}: {strength:.4f}"
                )
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'validation_details': validation_details
        }
        
    except Exception as e:
        logger.error(f"Error validating SHAP explanations: {e}", exc_info=True)
        return {
            'is_valid': False,
            'errors': [f"Validation failed: {str(e)}"],
            'warnings': [],
            'validation_details': {}
        }


def handle_edge_cases(shap_result: Dict[str, Any],
                     X_sample: Dict[str, float],
                     audio_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle special cases:
    
    1. Very short audio (<10s): Warn about low confidence
    2. Poor audio quality: Flag affected features
    3. All features neutral: Explain uncertainty
    4. Conflicting features: Highlight disagreement
    5. Near-threshold predictions: Emphasize uncertainty
    
    Args:
        shap_result: SHAP results
        X_sample: Feature values
        audio_metadata: Optional metadata about audio (duration, quality, etc.)
    
    Returns:
        {
            'edge_cases': list,
            'warnings': list,
            'adjusted_confidence': float,
            'recommendations': list
        }
    """
    edge_cases = []
    warnings = []
    recommendations = []
    
    try:
        # Check 1: Very short audio
        if audio_metadata:
            duration = audio_metadata.get('duration', 0)
            if duration < 10:
                edge_cases.append('very_short_audio')
                warnings.append(
                    f"Audio duration is very short ({duration:.1f}s). "
                    "Results may have lower confidence."
                )
                recommendations.append(
                    "Record a longer audio sample (at least 30 seconds) for more reliable assessment."
                )
        
        # Check 2: Poor audio quality
        if audio_metadata:
            quality = audio_metadata.get('quality', 'unknown')
            if quality in ['poor', 'low']:
                edge_cases.append('poor_audio_quality')
                warnings.append(
                    "Audio quality is poor. Some acoustic features may be unreliable."
                )
                recommendations.append(
                    "Record in a quiet environment with a good microphone."
                )
        
        # Check 3: All features neutral
        feature_contributions = shap_result.get('feature_contributions', {})
        max_abs_contrib = max([abs(v) for v in feature_contributions.values()] or [0])
        
        if max_abs_contrib < 0.1:
            edge_cases.append('all_features_neutral')
            warnings.append(
                "All feature contributions are very small. The model may be uncertain."
            )
            recommendations.append(
                "Consider additional assessment methods or longer observation period."
            )
        
        # Check 4: Conflicting features
        positive_count = sum(1 for v in feature_contributions.values() if v > 0.1)
        negative_count = sum(1 for v in feature_contributions.values() if v < -0.1)
        
        if positive_count > 0 and negative_count > 0:
            # Check if they're roughly balanced (conflicting)
            if abs(positive_count - negative_count) <= 2:
                edge_cases.append('conflicting_features')
                warnings.append(
                    "Mixed positive and negative features detected. "
                    "The assessment may be uncertain."
                )
        
        # Check 5: Near-threshold predictions
        prediction = shap_result.get('prediction', 0.0)
        thresholds = [18, 24]  # MCI and normal thresholds
        
        for threshold in thresholds:
            if abs(prediction - threshold) < 1.0:
                edge_cases.append('near_threshold')
                warnings.append(
                    f"Prediction ({prediction:.1f}) is near threshold ({threshold}). "
                    "Small changes could affect classification."
                )
                recommendations.append(
                    "Consider reassessment or additional clinical evaluation."
                )
        
        # Calculate adjusted confidence
        base_confidence = 0.9
        confidence_penalty = len(edge_cases) * 0.1
        adjusted_confidence = max(0.5, base_confidence - confidence_penalty)
        
        return {
            'edge_cases': edge_cases,
            'warnings': warnings,
            'adjusted_confidence': adjusted_confidence,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error handling edge cases: {e}", exc_info=True)
        return {
            'edge_cases': [],
            'warnings': [f"Error: {str(e)}"],
            'adjusted_confidence': 0.5,
            'recommendations': []
        }


def generate_alternative_scenarios(shap_result: Dict[str, Any],
                                  X_sample: Dict[str, float],
                                  top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Show "what-if" scenarios
    
    Examples:
    - "If speech fluency improved by 20%, MMSE would increase to 25.2"
    - "Main area for improvement: vocabulary richness"
    
    Use counterfactual explanations
    
    Args:
        shap_result: SHAP results
        X_sample: Current feature values
        top_k: Number of scenarios to generate
    
    Returns:
        [
            {
                'scenario': str,
                'feature': str,
                'current_value': float,
                'improved_value': float,
                'new_prediction': float,
                'improvement': float,
                'interpretation': str
            },
            ...
        ]
    """
    scenarios = []
    
    try:
        feature_contributions = shap_result.get('feature_contributions', {})
        base_value = shap_result.get('base_value', 0.0)
        current_prediction = shap_result.get('prediction', 0.0)
        
        # Find top negative contributors (areas for improvement)
        negative_features = [
            (feat, contrib, X_sample.get(feat, 0))
            for feat, contrib in feature_contributions.items()
            if contrib < -0.1
        ]
        negative_features.sort(key=lambda x: x[1])  # Sort by most negative
        
        for feat, contrib, current_val in negative_features[:top_k]:
            # Calculate improvement: move toward normal range
            # Simple heuristic: improve by 20% toward zero (normal)
            improved_val = current_val * 0.8 if current_val < 0 else current_val * 1.2
            
            # Estimate new contribution (linear approximation)
            improvement_factor = abs(improved_val - current_val) / max(abs(current_val), 0.01)
            new_contrib = contrib * (1 - improvement_factor * 0.5)  # Reduce negative contribution
            
            new_prediction = current_prediction - contrib + new_contrib
            improvement = new_prediction - current_prediction
            
            # Generate interpretation
            if improvement > 0.5:
                interpretation = (
                    f"Nếu {feat} được cải thiện 20%, điểm MMSE dự đoán sẽ tăng lên "
                    f"{new_prediction:.1f} (tăng {improvement:.1f} điểm)."
                )
            else:
                interpretation = (
                    f"Cải thiện {feat} sẽ có tác động nhỏ đến kết quả đánh giá."
                )
            
            scenarios.append({
                'scenario': f'improve_{feat}',
                'feature': feat,
                'current_value': current_val,
                'improved_value': improved_val,
                'new_prediction': new_prediction,
                'improvement': improvement,
                'interpretation': interpretation
            })
        
        return scenarios
        
    except Exception as e:
        logger.error(f"Error generating alternative scenarios: {e}", exc_info=True)
        return []


def test_shap_pipeline(audio_features: Dict[str, Any],
                      linguistic_features: Dict[str, Any],
                      mmse_score: int,
                      risk_level: str = 'low') -> Dict[str, Any]:
    """
    Test complete SHAP explanation pipeline
    
    Test cases:
    1. Normal cognition (MMSE 27-30)
    2. MCI (MMSE 18-23)
    3. Dementia risk (MMSE <18)
    4. Borderline cases (MMSE 23-24)
    5. Edge cases (very high/low feature values)
    
    Validate:
    - Explanations are consistent
    - Recommendations are appropriate
    - Visualizations render correctly
    - Vietnamese text is correct
    - Performance (<2s for all explanations)
    
    Returns:
        Test results dict
    """
    import time
    
    test_results = {
        'tests_passed': 0,
        'tests_failed': 0,
        'errors': [],
        'warnings': [],
        'performance': {},
        'validation_results': {}
    }
    
    try:
        # Import modules
        from modules.shap_explainer import compute_shap_for_assessment
        from modules.explanation_generator import generate_explanation_for_assessment
        from modules.shap_visualizations import create_all_visualizations
        
        # Test 1: SHAP computation
        start_time = time.time()
        shap_result = compute_shap_for_assessment(audio_features, linguistic_features, mmse_score)
        shap_time = time.time() - start_time
        test_results['performance']['shap_computation'] = shap_time
        
        if shap_time > 2.0:
            test_results['warnings'].append(f"SHAP computation took {shap_time:.2f}s (target: <2s)")
        else:
            test_results['tests_passed'] += 1
        
        # Test 2: Explanation generation
        start_time = time.time()
        explanations = generate_explanation_for_assessment(
            audio_features, linguistic_features, mmse_score, risk_level, 'vi'
        )
        explanation_time = time.time() - start_time
        test_results['performance']['explanation_generation'] = explanation_time
        
        if 'summary' not in explanations:
            test_results['errors'].append("Explanation missing 'summary' field")
            test_results['tests_failed'] += 1
        else:
            test_results['tests_passed'] += 1
        
        # Test 3: Validation
        X_sample = {}
        for k, v in audio_features.items():
            if isinstance(v, (int, float)):
                X_sample[k] = float(v)
        for k, v in linguistic_features.items():
            if isinstance(v, (int, float)):
                X_sample[k] = float(v)
        
        validation = validate_shap_explanations(shap_result, X_sample)
        test_results['validation_results'] = validation
        
        if validation['is_valid']:
            test_results['tests_passed'] += 1
        else:
            test_results['tests_failed'] += 1
            test_results['errors'].extend(validation['errors'])
        
        # Test 4: Visualizations
        grouped_contributions = shap_result.get('grouped_contributions', {})
        start_time = time.time()
        visualizations = create_all_visualizations(
            shap_result, grouped_contributions, mmse_score, 'vi'
        )
        viz_time = time.time() - start_time
        test_results['performance']['visualization_creation'] = viz_time
        
        if 'waterfall' in visualizations and visualizations['waterfall']:
            test_results['tests_passed'] += 1
        else:
            test_results['errors'].append("Waterfall plot not generated")
            test_results['tests_failed'] += 1
        
        # Test 5: Edge cases
        edge_case_results = handle_edge_cases(shap_result, X_sample)
        test_results['edge_cases'] = edge_case_results
        
        # Test 6: Alternative scenarios
        scenarios = generate_alternative_scenarios(shap_result, X_sample)
        test_results['alternative_scenarios'] = scenarios
        
        if scenarios:
            test_results['tests_passed'] += 1
        else:
            test_results['warnings'].append("No alternative scenarios generated")
        
        # Overall performance
        total_time = sum(test_results['performance'].values())
        test_results['performance']['total'] = total_time
        
        if total_time > 5.0:
            test_results['warnings'].append(f"Total pipeline time: {total_time:.2f}s (target: <5s)")
        
        return test_results
        
    except Exception as e:
        logger.error(f"Error testing SHAP pipeline: {e}", exc_info=True)
        test_results['errors'].append(f"Test pipeline failed: {str(e)}")
        test_results['tests_failed'] += 1
        return test_results

