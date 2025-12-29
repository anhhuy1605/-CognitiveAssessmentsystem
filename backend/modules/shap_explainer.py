# -*- coding: utf-8 -*-
"""
SHAP Explainability Module for Cognitive Assessment
===================================================

Computes SHAP values for feature importance in cognitive risk assessment.
Based on Lundberg & Lee (2017) SHAP framework.

Author: Cognitive Assessment System
Version: 1.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP library not available. Install with: pip install shap")

# Try to import sklearn for models
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Some features will be limited.")


class CognitiveAssessmentExplainer:
    """
    SHAP-based explainability for cognitive assessment models
    
    Computes SHAP values to explain:
    - Feature contributions to risk assessment
    - Feature interactions
    - Grouped feature importance
    
    Based on:
    - TreeSHAP for tree-based models (fast, exact)
    - KernelSHAP for ensemble models (model-agnostic)
    - LinearSHAP for linear models (fast)
    """
    
    # Feature groups for aggregation
    FEATURE_GROUPS = {
        'acoustic_prosodic': [
            'f0_mean', 'f0_std', 'f0_range', 'f0_cv',
            'f0_contour', 'pitch_variability'
        ],
        'acoustic_spectral': [
            'egemaps_mfcc_1', 'egemaps_mfcc_2', 'egemaps_mfcc_3',
            'egemaps_spectral_centroid', 'egemaps_spectral_flux'
        ],
        'acoustic_voice_quality': [
            'vq_jitter', 'vq_shimmer', 'vq_hnr',
            'vq_jitter_local', 'vq_shimmer_local'
        ],
        'acoustic_temporal': [
            'pause_duration_mean', 'pause_ratio', 'pause_count',
            'rate_syllables_per_sec', 'rate_words_per_sec'
        ],
        'acoustic_tone': [
            'tone_flattening_score', 'tone_variability',
            'tone_ngang_ratio', 'tone_sac_ratio'
        ],
        'linguistic_lexical': [
            'lex_ttr', 'lex_mattr', 'lex_brunet_index',
            'lex_word_freq_std', 'lex_avg_word_length'
        ],
        'linguistic_syntactic': [
            'syn_mlu', 'syn_avg_sentence_length',
            'syn_pos_noun_ratio', 'syn_pos_verb_ratio'
        ],
        'linguistic_semantic': [
            'sem_coherence', 'sem_idea_density',
            'sem_sentence_similarity_mean'
        ],
        'linguistic_vietnamese': [
            'vi_classifier_count', 'vi_tense_marker_count',
            'vi_aspect_marker_count'
        ],
        'linguistic_pragmatic': [
            'lex_filler_word_ratio', 'lex_repetition_rate',
            'lex_pronoun_ratio'
        ]
    }
    
    def __init__(self, 
                 models: Optional[Dict[str, Any]] = None,
                 feature_names: Optional[List[str]] = None,
                 feature_groups: Optional[Dict[str, List[str]]] = None):
        """
        Initialize SHAP explainer
        
        Args:
            models: Dict of trained models {'random_forest': model, 'xgboost': model, ...}
                    If None, will use default risk assessment logic
            feature_names: List of all feature names
            feature_groups: Dict mapping features to categories (uses default if None)
        """
        self.models = models or {}
        self.feature_names = feature_names or []
        self.feature_groups = feature_groups or self.FEATURE_GROUPS
        
        # Initialize explainers (lazy loading)
        self.explainers = {}
        self.scaler = None
        
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available. Explanations will be limited.")
    
    def compute_shap_values(self, 
                           X_sample: Dict[str, float],
                           model_name: str = 'risk_assessor',
                           background_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Compute SHAP values for a single prediction
        
        Args:
            X_sample: Dict of feature values for this patient
            model_name: Which model to explain ('risk_assessor', 'random_forest', etc.)
            background_data: Background dataset for KernelSHAP (optional)
        
        Returns:
            {
                'shap_values': np.array,  # Raw SHAP values
                'base_value': float,       # Expected model output
                'prediction': float,        # Actual prediction
                'feature_contributions': dict,  # Feature -> contribution
                'grouped_contributions': dict,  # Feature group -> contribution
                'interactions': list,      # Top feature interactions
                'feature_importance': dict  # Absolute importance ranking
            }
        """
        if not SHAP_AVAILABLE:
            # Fallback: Use simple feature deviation method
            return self._compute_simple_importance(X_sample)
        
        try:
            # Convert sample to array
            X_array = self._dict_to_array(X_sample)
            
            # Get model
            model = self.models.get(model_name)
            
            if model is None:
                # Use risk assessment logic if no model
                return self._compute_risk_based_shap(X_sample)
            
            # Choose explainer based on model type
            explainer = self._get_explainer(model, model_name, background_data)
            
            # Compute SHAP values
            shap_values = explainer.shap_values(X_array)
            base_value = explainer.expected_value if hasattr(explainer, 'expected_value') else 0.0
            
            # Get prediction
            prediction = model.predict(X_array.reshape(1, -1))[0] if hasattr(model, 'predict') else base_value
            
            # Convert to dict
            feature_contributions = {
                self.feature_names[i]: float(shap_values[i])
                for i in range(len(self.feature_names))
            }
            
            # Aggregate by groups
            grouped_contributions = self.aggregate_by_feature_groups(feature_contributions)
            
            # Detect interactions
            interactions = self.detect_feature_interactions(
                shap_values, X_sample, top_k=5
            )
            
            # Feature importance (absolute)
            feature_importance = {
                feat: abs(contrib)
                for feat, contrib in feature_contributions.items()
            }
            feature_importance = dict(sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            ))
            
            return {
                'shap_values': shap_values,
                'base_value': float(base_value),
                'prediction': float(prediction),
                'feature_contributions': feature_contributions,
                'grouped_contributions': grouped_contributions,
                'interactions': interactions,
                'feature_importance': feature_importance
            }
            
        except Exception as e:
            logger.error(f"Error computing SHAP values: {e}", exc_info=True)
            return self._compute_simple_importance(X_sample)
    
    def _get_explainer(self, model, model_name: str, background_data: Optional[pd.DataFrame] = None):
        """Get appropriate SHAP explainer for model type"""
        if model_name in self.explainers:
            return self.explainers[model_name]
        
        # Determine explainer type
        model_type = type(model).__name__.lower()
        
        if 'tree' in model_type or 'forest' in model_type or 'gradient' in model_type:
            # Tree-based: Use TreeExplainer (fast, exact)
            explainer = shap.TreeExplainer(model)
        elif 'linear' in model_type:
            # Linear: Use LinearExplainer (fast)
            explainer = shap.LinearExplainer(model, background_data)
        else:
            # Generic: Use KernelExplainer (slow but universal)
            if background_data is None:
                # Create dummy background
                background_data = pd.DataFrame([np.zeros(len(self.feature_names))])
            explainer = shap.KernelExplainer(
                model.predict,
                background_data
            )
        
        self.explainers[model_name] = explainer
        return explainer
    
    def _compute_risk_based_shap(self, X_sample: Dict[str, float]) -> Dict[str, Any]:
        """
        Compute SHAP-like importance using risk assessment thresholds
        
        When no ML model is available, use deviation from normal ranges
        to estimate feature importance.
        """
        try:
            from risk_assessment import ACOUSTIC_THRESHOLDS, LINGUISTIC_THRESHOLDS
        except ImportError:
            # Fallback if risk_assessment not available
            logger.warning("risk_assessment module not available, using simple importance")
            return self._compute_simple_importance(X_sample)
        
        feature_contributions = {}
        
        # Acoustic features
        for feature_name, value in X_sample.items():
            if feature_name.startswith('egemaps_') or feature_name.startswith('f0_') or \
               feature_name.startswith('vq_') or feature_name.startswith('pause_'):
                
                # Find threshold
                thresholds = None
                if feature_name in ACOUSTIC_THRESHOLDS:
                    thresholds = ACOUSTIC_THRESHOLDS[feature_name]
                elif any(feature_name.startswith(prefix) for prefix in ['egemaps_', 'f0_', 'vq_', 'pause_']):
                    # Try to find base feature name
                    base_name = feature_name.split('_', 1)[-1] if '_' in feature_name else feature_name
                    if base_name in ACOUSTIC_THRESHOLDS:
                        thresholds = ACOUSTIC_THRESHOLDS[base_name]
                
                if thresholds:
                    normal_range = thresholds.get('normal', (0, 1))
                    contribution = self._calculate_deviation_contribution(value, normal_range)
                    feature_contributions[feature_name] = contribution
        
        # Linguistic features
        for feature_name, value in X_sample.items():
            if feature_name.startswith('lex_') or feature_name.startswith('syn_') or \
               feature_name.startswith('sem_') or feature_name.startswith('vi_'):
                
                thresholds = None
                base_name = feature_name.split('_', 1)[-1] if '_' in feature_name else feature_name
                if base_name in LINGUISTIC_THRESHOLDS:
                    thresholds = LINGUISTIC_THRESHOLDS[base_name]
                
                if thresholds:
                    normal_range = thresholds.get('normal', (0, 1))
                    contribution = self._calculate_deviation_contribution(value, normal_range)
                    feature_contributions[feature_name] = contribution
        
        # Aggregate
        grouped_contributions = self.aggregate_by_feature_groups(feature_contributions)
        
        # Feature importance
        feature_importance = {
            feat: abs(contrib)
            for feat, contrib in feature_contributions.items()
        }
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return {
            'shap_values': np.array(list(feature_contributions.values())),
            'base_value': 0.0,
            'prediction': sum(feature_contributions.values()),
            'feature_contributions': feature_contributions,
            'grouped_contributions': grouped_contributions,
            'interactions': [],
            'feature_importance': feature_importance
        }
    
    def _calculate_deviation_contribution(self, value: float, normal_range: Tuple[float, float]) -> float:
        """
        Calculate contribution based on deviation from normal range
        
        Returns negative value if outside normal (risk), positive if in normal (protective)
        """
        low, high = normal_range
        
        if low <= value <= high:
            # Within normal: positive contribution
            return 0.1  # Small positive
        elif value < low:
            # Below normal: negative contribution
            deviation = (low - value) / low if low > 0 else abs(value)
            return -min(deviation, 2.0)  # Cap at -2.0
        else:
            # Above normal: negative contribution
            deviation = (value - high) / high if high > 0 else abs(value)
            return -min(deviation, 2.0)  # Cap at -2.0
    
    def _compute_simple_importance(self, X_sample: Dict[str, float]) -> Dict[str, Any]:
        """Fallback: Simple importance when SHAP unavailable"""
        # Use variance-based importance
        contributions = {}
        for feat, val in X_sample.items():
            # Simple heuristic: larger absolute values = more important
            contributions[feat] = val / 100.0 if abs(val) > 0 else 0.0
        
        grouped = self.aggregate_by_feature_groups(contributions)
        
        return {
            'shap_values': np.array(list(contributions.values())),
            'base_value': 0.0,
            'prediction': sum(contributions.values()),
            'feature_contributions': contributions,
            'grouped_contributions': grouped,
            'interactions': [],
            'feature_importance': dict(sorted(
                {k: abs(v) for k, v in contributions.items()}.items(),
                key=lambda x: x[1],
                reverse=True
            ))
        }
    
    def aggregate_by_feature_groups(self, shap_values: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate SHAP values by feature groups for easier interpretation
        
        Example:
        - All MFCC features -> "Voice Quality Score"
        - All pitch features -> "Speech Melody Score"
        - All pause features -> "Speech Fluency Score"
        - TTR + vocabulary -> "Vocabulary Richness Score"
        
        Returns:
            {
                'voice_quality': {
                    'contribution': 0.5,
                    'features': ['mfcc_1', 'mfcc_2', ...],
                    'count': 10
                },
                ...
            }
        """
        grouped = {}
        
        # Map feature groups to human-readable names
        group_names = {
            'acoustic_prosodic': 'Speech Melody',
            'acoustic_spectral': 'Voice Quality',
            'acoustic_voice_quality': 'Voice Stability',
            'acoustic_temporal': 'Speech Fluency',
            'acoustic_tone': 'Tone Production',
            'linguistic_lexical': 'Vocabulary Richness',
            'linguistic_syntactic': 'Grammar Complexity',
            'linguistic_semantic': 'Content Coherence',
            'linguistic_vietnamese': 'Vietnamese Language Use',
            'linguistic_pragmatic': 'Speech Patterns'
        }
        
        for group_key, feature_list in self.feature_groups.items():
            group_contrib = 0.0
            matched_features = []
            
            for feature_name, contrib in shap_values.items():
                # Check if feature belongs to this group
                if any(feat_pattern in feature_name for feat_pattern in feature_list):
                    group_contrib += contrib
                    matched_features.append(feature_name)
            
            if matched_features:
                group_name = group_names.get(group_key, group_key)
                grouped[group_name] = {
                    'contribution': group_contrib,
                    'features': matched_features,
                    'count': len(matched_features),
                    'group_key': group_key
                }
        
        return grouped
    
    def detect_feature_interactions(self, 
                                   shap_values: np.ndarray,
                                   X_sample: Dict[str, float],
                                   top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Identify important feature interactions using SHAP interaction values
        
        Clinical relevance examples:
        - Slow speaking rate + long pauses = severe fluency issues
        - Low TTR + high repetition = vocabulary problems
        - Poor coherence + low information content = semantic deficits
        
        Args:
            shap_values: SHAP values array
            X_sample: Feature values
            top_k: Number of top interactions to return
        
        Returns:
            [
                {
                    'feature_1': 'speaking_rate',
                    'feature_2': 'pause_duration',
                    'interaction_strength': -0.8,
                    'interpretation': 'Combined effect of slow speech and frequent pauses'
                },
                ...
            ]
        """
        interactions = []
        
        # Simple heuristic: Find features that are both abnormal
        abnormal_features = []
        for feat, val in X_sample.items():
            # Check if value is significantly different from 0
            if abs(val) > np.std(list(X_sample.values())) * 1.5:
                abnormal_features.append((feat, val))
        
        # Find pairs of abnormal features
        for i, (feat1, val1) in enumerate(abnormal_features):
            for feat2, val2 in abnormal_features[i+1:]:
                # Calculate interaction strength (simple heuristic)
                interaction = val1 * val2 / 100.0  # Normalize
                
                if abs(interaction) > 0.1:  # Threshold
                    interpretation = self._interpret_interaction(feat1, feat2, interaction)
                    interactions.append({
                        'feature_1': feat1,
                        'feature_2': feat2,
                        'interaction_strength': interaction,
                        'interpretation': interpretation
                    })
        
        # Sort by absolute interaction strength
        interactions.sort(key=lambda x: abs(x['interaction_strength']), reverse=True)
        
        return interactions[:top_k]
    
    def _interpret_interaction(self, feat1: str, feat2: str, strength: float) -> str:
        """Generate human-readable interpretation of feature interaction"""
        # Map feature names to descriptions
        feat_descriptions = {
            'rate_syllables_per_sec': 'tốc độ nói',
            'pause_duration_mean': 'thời gian dừng lại',
            'lex_ttr': 'sự đa dạng từ vựng',
            'lex_repetition_rate': 'tỷ lệ lặp từ',
            'sem_coherence': 'tính mạch lạc',
            'f0_std': 'biến thiên cao độ',
            'vq_jitter': 'độ rung giọng'
        }
        
        desc1 = feat_descriptions.get(feat1, feat1)
        desc2 = feat_descriptions.get(feat2, feat2)
        
        if strength < 0:
            return f"Sự kết hợp của {desc1} thấp và {desc2} cao cho thấy vấn đề về khả năng giao tiếp"
        else:
            return f"Sự kết hợp của {desc1} và {desc2} cho thấy khả năng ngôn ngữ ổn định"
    
    def _dict_to_array(self, X_sample: Dict[str, float]) -> np.ndarray:
        """Convert feature dict to numpy array"""
        if not self.feature_names:
            # Auto-detect feature names
            self.feature_names = sorted(X_sample.keys())
        
        return np.array([X_sample.get(feat, 0.0) for feat in self.feature_names])


def compute_shap_for_assessment(audio_features: Dict[str, Any],
                                linguistic_features: Dict[str, Any],
                                mmse_score: int = 0) -> Dict[str, Any]:
    """
    Convenience function to compute SHAP values from assessment results
    
    Args:
        audio_features: Acoustic features dict
        linguistic_features: Linguistic features dict
        mmse_score: MMSE score (0-30)
    
    Returns:
        SHAP explanation dict
    """
    # Combine features
    all_features = {}
    
    # Flatten audio features
    for key, value in audio_features.items():
        if key == 'f0_contour':
            # Skip raw arrays, use statistics only
            continue
        if isinstance(value, (int, float)):
            all_features[key] = float(value)
        elif isinstance(value, dict):
            # Extract numeric values from nested dicts
            for subkey, subval in value.items():
                if isinstance(subval, (int, float)):
                    all_features[f"{key}_{subkey}"] = float(subval)
    
    # Add linguistic features
    for key, value in linguistic_features.items():
        if isinstance(value, (int, float)):
            all_features[key] = float(value)
    
    # Initialize explainer
    explainer = CognitiveAssessmentExplainer(feature_names=list(all_features.keys()))
    
    # Compute SHAP values
    shap_result = explainer.compute_shap_values(all_features)
    
    return shap_result
