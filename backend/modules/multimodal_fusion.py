# -*- coding: utf-8 -*-
"""
Multimodal Fusion Module for Vietnamese MCI Screening
Combines acoustic and linguistic features for enhanced prediction

Author: Cognitive Assessment System
Version: 1.0
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available. Feature fusion will be limited.")


@dataclass
class FusionConfig:
    """Configuration for multimodal fusion"""
    acoustic_weight: float = 0.5      # Weight for acoustic features
    linguistic_weight: float = 0.5    # Weight for linguistic features
    fusion_method: str = 'early'      # 'early', 'late', 'hybrid'
    normalize: bool = True            # Whether to normalize features
    use_pca: bool = False             # Whether to apply PCA
    pca_components: int = 50          # Number of PCA components
    feature_selection: bool = False   # Whether to apply feature selection
    n_features: int = 100             # Number of features to select


class MultimodalFusion:
    """
    Multimodal Fusion for combining acoustic and linguistic features
    
    Fusion Strategies:
    1. Early Fusion: Concatenate features before classification
    2. Late Fusion: Combine predictions from separate models
    3. Hybrid Fusion: Combine both approaches
    
    Feature Processing:
    - Normalization (StandardScaler or MinMaxScaler)
    - Dimensionality reduction (PCA)
    - Feature selection (SelectKBest)
    """
    
    # Key features identified from literature for MCI detection
    KEY_ACOUSTIC_FEATURES = [
        # F0 features (voice pitch)
        'f0_f0_mean', 'f0_f0_std', 'f0_f0_cv', 'f0_f0_range',
        # Voice quality
        'vq_jitter_local', 'vq_shimmer_local', 'vq_hnr_mean',
        # Pause patterns
        'pause_mean_pause_duration', 'pause_pause_rate', 'pause_total_pause_time',
        # Speaking rate
        'rate_words_per_minute', 'rate_syllables_per_second',
        # Vietnamese tone features
        'tone_flattening_score', 'tone_f0_variability_index', 'tone_contour_complexity'
    ]
    
    KEY_LINGUISTIC_FEATURES = [
        # Lexical diversity
        'lex_ttr', 'lex_mattr', 'lex_brunet_index',
        # POS ratios
        'lex_pronoun_ratio', 'lex_noun_ratio', 'lex_content_word_ratio',
        # Syntactic complexity
        'syn_mlu_words', 'syn_incomplete_sentence_ratio', 'syn_clause_density',
        # Semantic features
        'sem_idea_density', 'sem_semantic_coherence', 'sem_information_entropy',
        # Vietnamese-specific
        'vi_classifier_ratio', 'vi_filler_ratio', 'vi_tense_marker_ratio'
    ]
    
    def __init__(self, config: Optional[FusionConfig] = None):
        """
        Initialize Multimodal Fusion
        
        Args:
            config: Fusion configuration (optional)
        """
        self.config = config or FusionConfig()
        
        # Initialize scalers
        self.acoustic_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.linguistic_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.combined_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
        # Initialize PCA
        self.pca = None
        if SKLEARN_AVAILABLE and self.config.use_pca:
            self.pca = PCA(n_components=self.config.pca_components)
        
        # Feature selector
        self.feature_selector = None
        
        # Track fitted state
        self.is_fitted = False
        
        logger.info(f"MultimodalFusion initialized with config: {self.config}")
    
    def extract_key_features(self, features: Dict[str, Any], 
                              feature_type: str) -> Dict[str, float]:
        """
        Extract key features for MCI detection
        
        Args:
            features: All extracted features
            feature_type: 'acoustic' or 'linguistic'
        
        Returns:
            dict: Selected key features
        """
        if feature_type == 'acoustic':
            key_list = self.KEY_ACOUSTIC_FEATURES
        elif feature_type == 'linguistic':
            key_list = self.KEY_LINGUISTIC_FEATURES
        else:
            key_list = []
        
        selected = {}
        for key in key_list:
            if key in features:
                value = features[key]
                # Ensure numeric
                if isinstance(value, (int, float)) and not np.isnan(value):
                    selected[key] = float(value)
                else:
                    selected[key] = 0.0
        
        return selected
    
    def normalize_features(self, features: np.ndarray, 
                            feature_type: str = 'combined') -> np.ndarray:
        """
        Normalize features using StandardScaler
        
        Args:
            features: Feature array (n_samples, n_features)
            feature_type: 'acoustic', 'linguistic', or 'combined'
        
        Returns:
            Normalized feature array
        """
        if not SKLEARN_AVAILABLE:
            return features
        
        if feature_type == 'acoustic':
            scaler = self.acoustic_scaler
        elif feature_type == 'linguistic':
            scaler = self.linguistic_scaler
        else:
            scaler = self.combined_scaler
        
        # Handle single sample case
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        return scaler.fit_transform(features)
    
    def early_fusion(self, acoustic_features: Dict[str, float], 
                      linguistic_features: Dict[str, float]) -> np.ndarray:
        """
        Early Fusion: Concatenate features before classification
        
        This is the simplest fusion strategy:
        1. Normalize acoustic features
        2. Normalize linguistic features
        3. Concatenate into single feature vector
        
        Args:
            acoustic_features: Extracted acoustic features
            linguistic_features: Extracted linguistic features
        
        Returns:
            Combined feature vector
        """
        # Convert to arrays
        acoustic_keys = sorted(acoustic_features.keys())
        linguistic_keys = sorted(linguistic_features.keys())
        
        acoustic_array = np.array([acoustic_features.get(k, 0.0) for k in acoustic_keys])
        linguistic_array = np.array([linguistic_features.get(k, 0.0) for k in linguistic_keys])
        
        # Handle NaN values
        acoustic_array = np.nan_to_num(acoustic_array, nan=0.0, posinf=0.0, neginf=0.0)
        linguistic_array = np.nan_to_num(linguistic_array, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalize if configured
        if self.config.normalize and SKLEARN_AVAILABLE:
            if len(acoustic_array) > 0:
                acoustic_array = self.normalize_features(
                    acoustic_array.reshape(1, -1), 'acoustic'
                ).flatten()
            if len(linguistic_array) > 0:
                linguistic_array = self.normalize_features(
                    linguistic_array.reshape(1, -1), 'linguistic'
                ).flatten()
        
        # Apply weights
        acoustic_weighted = acoustic_array * self.config.acoustic_weight
        linguistic_weighted = linguistic_array * self.config.linguistic_weight
        
        # Concatenate
        combined = np.concatenate([acoustic_weighted, linguistic_weighted])
        
        return combined
    
    def late_fusion(self, acoustic_prediction: float, 
                     linguistic_prediction: float) -> float:
        """
        Late Fusion: Combine predictions from separate models
        
        Simple weighted average of predictions.
        
        Args:
            acoustic_prediction: Prediction from acoustic model
            linguistic_prediction: Prediction from linguistic model
        
        Returns:
            Combined prediction
        """
        return (self.config.acoustic_weight * acoustic_prediction + 
                self.config.linguistic_weight * linguistic_prediction)
    
    def hybrid_fusion(self, acoustic_features: Dict[str, float],
                       linguistic_features: Dict[str, float],
                       acoustic_prediction: Optional[float] = None,
                       linguistic_prediction: Optional[float] = None) -> Tuple[np.ndarray, Optional[float]]:
        """
        Hybrid Fusion: Combine both early and late fusion
        
        1. Create early fusion feature vector
        2. If predictions available, create ensemble prediction
        
        Args:
            acoustic_features: Extracted acoustic features
            linguistic_features: Extracted linguistic features
            acoustic_prediction: Optional prediction from acoustic model
            linguistic_prediction: Optional prediction from linguistic model
        
        Returns:
            Tuple of (combined_features, ensemble_prediction)
        """
        # Early fusion component
        combined_features = self.early_fusion(acoustic_features, linguistic_features)
        
        # Late fusion component (if predictions available)
        ensemble_prediction = None
        if acoustic_prediction is not None and linguistic_prediction is not None:
            ensemble_prediction = self.late_fusion(acoustic_prediction, linguistic_prediction)
        
        return combined_features, ensemble_prediction
    
    def fuse_features(self, acoustic_features: Dict[str, Any],
                       linguistic_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main fusion function: Combine acoustic and linguistic features
        
        Args:
            acoustic_features: All acoustic features
            linguistic_features: All linguistic features
        
        Returns:
            dict: Fused feature dictionary with metadata
        """
        # Extract key features
        key_acoustic = self.extract_key_features(acoustic_features, 'acoustic')
        key_linguistic = self.extract_key_features(linguistic_features, 'linguistic')
        
        # Apply fusion based on configured method
        if self.config.fusion_method == 'early':
            fused_vector = self.early_fusion(key_acoustic, key_linguistic)
        elif self.config.fusion_method == 'hybrid':
            fused_vector, _ = self.hybrid_fusion(key_acoustic, key_linguistic)
        else:
            # Default to early fusion
            fused_vector = self.early_fusion(key_acoustic, key_linguistic)
        
        # Apply PCA if configured
        if self.pca is not None and len(fused_vector) > self.config.pca_components:
            try:
                fused_vector = self.pca.fit_transform(fused_vector.reshape(1, -1)).flatten()
            except Exception as e:
                logger.warning(f"PCA failed: {e}")
        
        # Create feature names
        acoustic_keys = sorted(key_acoustic.keys())
        linguistic_keys = sorted(key_linguistic.keys())
        feature_names = [f"a_{k}" for k in acoustic_keys] + [f"l_{k}" for k in linguistic_keys]
        
        return {
            'fused_vector': fused_vector,
            'feature_names': feature_names,
            'n_acoustic_features': len(key_acoustic),
            'n_linguistic_features': len(key_linguistic),
            'n_total_features': len(fused_vector),
            'fusion_method': self.config.fusion_method,
            'acoustic_weight': self.config.acoustic_weight,
            'linguistic_weight': self.config.linguistic_weight,
            # Also include raw key features for interpretability
            'key_acoustic_features': key_acoustic,
            'key_linguistic_features': key_linguistic
        }
    
    def compute_modality_reliability(self, acoustic_features: Dict[str, float],
                                      linguistic_features: Dict[str, float]) -> Dict[str, float]:
        """
        Compute reliability/quality scores for each modality
        
        This can be used for adaptive weighting:
        - If audio quality is low, increase linguistic weight
        - If transcript is short, increase acoustic weight
        
        Args:
            acoustic_features: Acoustic features
            linguistic_features: Linguistic features
        
        Returns:
            dict: Reliability scores for each modality
        """
        # Acoustic reliability indicators
        acoustic_reliability = 1.0
        
        # Check for missing/zero features
        acoustic_values = list(acoustic_features.values())
        acoustic_missing = sum(1 for v in acoustic_values if v == 0 or np.isnan(v)) / max(len(acoustic_values), 1)
        acoustic_reliability *= (1.0 - acoustic_missing)
        
        # Check F0 quality (indicator of voice detection)
        f0_cv = acoustic_features.get('f0_f0_cv', 0)
        if f0_cv < 5:  # Very low variability = poor quality
            acoustic_reliability *= 0.5
        
        # Linguistic reliability indicators
        linguistic_reliability = 1.0
        
        # Check total words
        total_words = linguistic_features.get('lex_total_words', 0)
        if total_words < 10:
            linguistic_reliability *= 0.3
        elif total_words < 30:
            linguistic_reliability *= 0.7
        
        # Check for missing features
        linguistic_values = list(linguistic_features.values())
        linguistic_missing = sum(1 for v in linguistic_values if v == 0 or (isinstance(v, float) and np.isnan(v))) / max(len(linguistic_values), 1)
        linguistic_reliability *= (1.0 - linguistic_missing * 0.5)
        
        return {
            'acoustic_reliability': float(acoustic_reliability),
            'linguistic_reliability': float(linguistic_reliability),
            'recommended_acoustic_weight': float(acoustic_reliability / (acoustic_reliability + linguistic_reliability + 0.001)),
            'recommended_linguistic_weight': float(linguistic_reliability / (acoustic_reliability + linguistic_reliability + 0.001))
        }
    
    def create_feature_summary(self, acoustic_features: Dict[str, Any],
                                linguistic_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a human-readable summary of extracted features
        
        Args:
            acoustic_features: All acoustic features
            linguistic_features: All linguistic features
        
        Returns:
            dict: Summary with interpretations
        """
        summary = {
            'acoustic': {},
            'linguistic': {},
            'overall': {}
        }
        
        # Acoustic summary
        summary['acoustic'] = {
            'voice_quality': {
                'jitter': acoustic_features.get('vq_jitter_local', 0),
                'shimmer': acoustic_features.get('vq_shimmer_local', 0),
                'hnr': acoustic_features.get('vq_hnr_mean', 0),
                'interpretation': self._interpret_voice_quality(acoustic_features)
            },
            'prosody': {
                'f0_mean': acoustic_features.get('f0_f0_mean', 0),
                'f0_variability': acoustic_features.get('f0_f0_cv', 0),
                'interpretation': self._interpret_prosody(acoustic_features)
            },
            'fluency': {
                'speaking_rate': acoustic_features.get('rate_words_per_minute', 0),
                'pause_rate': acoustic_features.get('pause_pause_rate', 0),
                'interpretation': self._interpret_fluency(acoustic_features)
            },
            'tone_preservation': {
                'flattening_score': acoustic_features.get('tone_flattening_score', 0),
                'interpretation': self._interpret_tone(acoustic_features)
            }
        }
        
        # Linguistic summary
        summary['linguistic'] = {
            'lexical_diversity': {
                'ttr': linguistic_features.get('lex_ttr', 0),
                'mattr': linguistic_features.get('lex_mattr', 0),
                'interpretation': self._interpret_lexical(linguistic_features)
            },
            'syntactic_complexity': {
                'mlu': linguistic_features.get('syn_mlu_words', 0),
                'incomplete_ratio': linguistic_features.get('syn_incomplete_sentence_ratio', 0),
                'interpretation': self._interpret_syntactic(linguistic_features)
            },
            'semantic_coherence': {
                'idea_density': linguistic_features.get('sem_idea_density', 0),
                'coherence': linguistic_features.get('sem_semantic_coherence', 0),
                'interpretation': self._interpret_semantic(linguistic_features)
            }
        }
        
        # Overall assessment
        reliability = self.compute_modality_reliability(acoustic_features, linguistic_features)
        summary['overall'] = {
            'modality_reliability': reliability,
            'feature_quality': 'good' if min(reliability['acoustic_reliability'], 
                                             reliability['linguistic_reliability']) > 0.5 else 'limited'
        }
        
        return summary
    
    def _interpret_voice_quality(self, features: Dict[str, Any]) -> str:
        """Interpret voice quality features"""
        jitter = features.get('vq_jitter_local', 0)
        shimmer = features.get('vq_shimmer_local', 0)
        
        if jitter > 0.02 or shimmer > 0.1:
            return "Tăng bất ổn định giọng nói - có thể liên quan đến suy giảm kiểm soát vận động"
        elif jitter > 0.01 or shimmer > 0.05:
            return "Giọng nói có dấu hiệu bất ổn nhẹ"
        else:
            return "Chất lượng giọng nói bình thường"
    
    def _interpret_prosody(self, features: Dict[str, Any]) -> str:
        """Interpret prosody features"""
        f0_cv = features.get('f0_f0_cv', 0)
        
        if f0_cv < 10:
            return "Biến thiên cao độ thấp - có thể có dấu hiệu phẳng thanh điệu"
        elif f0_cv < 20:
            return "Biến thiên cao độ trung bình"
        else:
            return "Biến thiên cao độ bình thường"
    
    def _interpret_fluency(self, features: Dict[str, Any]) -> str:
        """Interpret fluency features"""
        wpm = features.get('rate_words_per_minute', 0)
        pause_rate = features.get('pause_pause_rate', 0)
        
        if wpm < 60 or pause_rate > 0.5:
            return "Tốc độ nói chậm, nhiều khoảng ngừng - có thể khó tìm từ"
        elif wpm < 90 or pause_rate > 0.3:
            return "Tốc độ nói hơi chậm"
        else:
            return "Tốc độ nói và độ lưu loát bình thường"
    
    def _interpret_tone(self, features: Dict[str, Any]) -> str:
        """Interpret Vietnamese tone features"""
        flattening = features.get('tone_flattening_score', 0)
        
        if flattening > 0.5:
            return "Dấu hiệu phẳng thanh điệu cao - biomarker tiềm năng cho MCI ở người Việt"
        elif flattening > 0.3:
            return "Có một số dấu hiệu phẳng thanh điệu"
        else:
            return "Bảo toàn thanh điệu tốt"
    
    def _interpret_lexical(self, features: Dict[str, Any]) -> str:
        """Interpret lexical features"""
        ttr = features.get('lex_ttr', 0)
        pronoun_ratio = features.get('lex_pronoun_ratio', 0)
        
        if ttr < 0.3:
            return "Đa dạng từ vựng thấp - có thể khó tìm từ"
        elif pronoun_ratio > 0.15:
            return "Sử dụng đại từ cao - có thể thay thế danh từ cụ thể"
        elif ttr < 0.5:
            return "Đa dạng từ vựng trung bình"
        else:
            return "Đa dạng từ vựng tốt"
    
    def _interpret_syntactic(self, features: Dict[str, Any]) -> str:
        """Interpret syntactic features"""
        mlu = features.get('syn_mlu_words', 0)
        incomplete = features.get('syn_incomplete_sentence_ratio', 0)
        
        if mlu < 5 or incomplete > 0.3:
            return "Câu ngắn, nhiều câu không hoàn chỉnh - có thể suy giảm xử lý ngôn ngữ"
        elif mlu < 8:
            return "Độ phức tạp cú pháp trung bình"
        else:
            return "Độ phức tạp cú pháp bình thường"
    
    def _interpret_semantic(self, features: Dict[str, Any]) -> str:
        """Interpret semantic features"""
        idea_density = features.get('sem_idea_density', 0)
        coherence = features.get('sem_semantic_coherence', 0)
        
        if idea_density < 3:
            return "Mật độ ý tưởng thấp - đây là chỉ báo mạnh cho suy giảm nhận thức"
        elif coherence < 0.5:
            return "Mạch lạc ngữ nghĩa giảm"
        elif idea_density < 5:
            return "Mật độ ý tưởng trung bình"
        else:
            return "Nội dung ngữ nghĩa phong phú"


# Convenience function
def fuse_multimodal_features(acoustic_features: Dict[str, Any],
                              linguistic_features: Dict[str, Any],
                              config: Optional[FusionConfig] = None) -> Dict[str, Any]:
    """
    Convenience function to fuse acoustic and linguistic features
    
    Args:
        acoustic_features: Extracted acoustic features
        linguistic_features: Extracted linguistic features
        config: Optional fusion configuration
    
    Returns:
        dict: Fused features with metadata
    """
    fusion = MultimodalFusion(config)
    return fusion.fuse_features(acoustic_features, linguistic_features)

