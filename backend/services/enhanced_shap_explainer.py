# -*- coding: utf-8 -*-
"""
Enhanced SHAP Explainer for Cognitive Assessment
===============================================
Comprehensive SHAP-based explainability with clinical interpretation

Based on:
- Lundberg & Lee (2017) - A Unified Approach to Interpreting Model Predictions
- Casanova et al. (2023) - SHAP for Alzheimer's Disease Detection from Speech
- Nature Scientific Reports (2024) - Explainable ML for AD Classification
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("⚠️ SHAP library not available. Install with: pip install shap")

# Import feature analyzer for severity calculation
try:
    from services.feature_analyzer import calculate_feature_severity
    from services.comprehensive_results_clinical_ranges import (
        ACOUSTIC_CLINICAL_RANGES,
        LINGUISTIC_CLINICAL_RANGES,
        FEATURE_IMPORTANCE_WEIGHTS
    )
except ImportError as e:
    logger.warning(f"⚠️ Feature analyzer not available: {e}")
    calculate_feature_severity = None
    ACOUSTIC_CLINICAL_RANGES = {}
    LINGUISTIC_CLINICAL_RANGES = {}
    FEATURE_IMPORTANCE_WEIGHTS = {}


class CognitiveDeclineSHAPExplainer:
    """
    Enhanced SHAP-based explainability for cognitive decline prediction
    
    Provides:
    - SHAP value computation (with fallback if model unavailable)
    - Risk/protective factor identification
    - Clinical interpretation generation
    - Feature interaction detection
    - Actionable recommendations
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize SHAP explainer
        
        Args:
            model_path: Optional path to trained model (if None, uses risk-based fallback)
        """
        self.model = None
        self.explainer = None
        self.feature_names = None
        self.model_path = model_path
        
        # Feature categories for better interpretation
        self.feature_categories = self._build_feature_categories()
        
        # Try to load model if path provided
        if model_path:
            try:
                self.model = self._load_model(model_path)
                logger.info(f"✅ Loaded model from {model_path}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load model from {model_path}: {e}")
                self.model = None
    
    def _load_model(self, model_path: str):
        """Load pre-trained model"""
        import joblib
        return joblib.load(model_path)
    
    def _build_feature_categories(self) -> Dict[str, List[str]]:
        """
        Map features to clinical categories for better interpretation
        """
        return {
            "Đặc trưng thanh điệu (Pitch)": [
                "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
                "f0_f0_mean", "f0_f0_cv", "f0_f0_std",
                "f0_mean", "f0_cv"
            ],
            "Chất lượng giọng nói": [
                "egemaps_jitterLocal_sma3nz_amean",
                "egemaps_shimmerLocaldB_sma3nz_amean",
                "egemaps_HNRdBACF_sma3nz_amean",
                "vq_jitter_local", "vq_shimmer_local", "vq_hnr_mean",
                "jitter", "shimmer", "hnr"
            ],
            "Tốc độ và nhịp điệu": [
                "rate_words_per_minute", "rate_syllables_per_second",
                "rate_words_per_second", "speaking_rate"
            ],
            "Tạm dừng và lưu loát": [
                "pause_pause_rate", "pause_mean_pause_duration",
                "pause_pause_ratio", "pause_total_pauses",
                "f0_voiced_ratio", "pause_rate"
            ],
            "Thanh điệu tiếng Việt": [
                "tone_flattening_score", "tone_direction_change_rate",
                "tone_contour_complexity", "tone_tone_accuracy"
            ],
            "Đa dạng từ vựng": [
                "lex_ttr", "lex_mattr", "lex_brunet_index",
                "lex_honore_stat", "lex_unique_words", "ttr", "mattr"
            ],
            "Cú pháp": [
                "syn_mlu_words", "syn_mlu_chars", "syn_clause_density",
                "syn_mean_parse_depth", "mlu"
            ],
            "Ngữ nghĩa": [
                "sem_semantic_coherence", "sem_idea_density",
                "sem_information_entropy", "semantic_coherence", "idea_density"
            ],
            "Từ loại": [
                "lex_noun_ratio", "lex_verb_ratio", "lex_adj_ratio",
                "lex_pronoun_ratio", "pronoun_ratio"
            ],
            "Đặc trưng tiếng Việt": [
                "vi_classifier_ratio", "vi_reduplication_ratio",
                "vi_particle_ratio", "vi_tense_marker_ratio"
            ]
        }
    
    def initialize_explainer(self, background_data: Optional[pd.DataFrame] = None):
        """
        Initialize SHAP explainer with background data
        
        Args:
            background_data: Representative sample of healthy controls for baseline
        """
        if not SHAP_AVAILABLE:
            logger.warning("⚠️ SHAP not available, will use risk-based fallback")
            return
        
        if self.model is None:
            logger.warning("⚠️ No model available, will use risk-based fallback")
            return
        
        try:
            # Determine explainer type based on model
            model_type = type(self.model).__name__.lower()
            
            if 'tree' in model_type or 'forest' in model_type or 'gradient' in model_type:
                # Tree-based: Use TreeExplainer (fast, exact)
                self.explainer = shap.TreeExplainer(self.model)
                logger.info("✅ Initialized TreeExplainer")
            elif 'linear' in model_type:
                # Linear: Use LinearExplainer
                if background_data is not None:
                    self.explainer = shap.LinearExplainer(self.model, background_data)
                else:
                    logger.warning("⚠️ LinearExplainer requires background_data")
                    self.explainer = None
            else:
                # Generic: Use KernelExplainer (slow but universal)
                if background_data is not None:
                    self.explainer = shap.KernelExplainer(
                        self.model.predict_proba if hasattr(self.model, 'predict_proba') else self.model.predict,
                        background_data
                    )
                else:
                    logger.warning("⚠️ KernelExplainer requires background_data")
                    self.explainer = None
            
            if background_data is not None:
                self.feature_names = background_data.columns.tolist()
                logger.info(f"✅ Feature names set: {len(self.feature_names)} features")
        except Exception as e:
            logger.error(f"❌ Error initializing SHAP explainer: {e}", exc_info=True)
            self.explainer = None
    
    def explain_prediction(
        self,
        features: Dict[str, float],
        user_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a single prediction
        
        Args:
            features: Feature dictionary for the test case
            user_info: Optional user information (gender, age, etc.)
            
        Returns:
            Comprehensive explanation with risk/protective factors
        """
        logger.info("🔬 Generating SHAP explanation...")
        
        # If no model or explainer, use risk-based fallback
        if self.explainer is None or self.model is None:
            logger.info("📊 Using risk-based SHAP fallback (no model available)")
            return self._compute_risk_based_shap(features, user_info)
        
        try:
            # Convert features to DataFrame
            features_df = pd.DataFrame([features])
            
            # Ensure all feature names match
            if self.feature_names:
                # Reorder and fill missing features with 0
                features_df = features_df.reindex(columns=self.feature_names, fill_value=0.0)
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(features_df)
            
            # Get base value
            base_value = self.explainer.expected_value if hasattr(self.explainer, 'expected_value') else 0.0
            
            # Get prediction
            if hasattr(self.model, 'predict_proba'):
                prediction_proba = self.model.predict_proba(features_df)[0]
                prediction = self.model.predict(features_df)[0]
            else:
                prediction = self.model.predict(features_df)[0]
                prediction_proba = None
            
            # Handle binary/multi-class SHAP values
            if isinstance(shap_values, list):
                shap_values_class1 = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
                base_value_class1 = base_value[1] if isinstance(base_value, (list, np.ndarray)) else base_value
            else:
                shap_values_class1 = shap_values[0] if len(shap_values.shape) > 1 else shap_values
                base_value_class1 = base_value if not isinstance(base_value, (list, np.ndarray)) else base_value[0]
            
            # Build comprehensive explanation
            explanation = {
                "prediction": {
                    "class": self._map_prediction_to_label(prediction),
                    "confidence": float(prediction_proba[1]) if prediction_proba is not None and len(prediction_proba) > 1 else None,
                    "base_risk": float(base_value_class1)
                },
                "shap_analysis": self.analyze_shap_values(
                    shap_values_class1,
                    features,
                    self.feature_names or list(features.keys())
                ),
                "clinical_interpretation": None  # Will be filled later
            }
            
            # Add clinical interpretation
            explanation["clinical_interpretation"] = self.generate_clinical_interpretation(
                explanation["shap_analysis"]
            )
            
            logger.info("✅ SHAP explanation generated successfully")
            return explanation
            
        except Exception as e:
            logger.error(f"❌ Error computing SHAP values: {e}", exc_info=True)
            return self._compute_risk_based_shap(features, user_info)
    
    def analyze_shap_values(
        self,
        shap_values: np.ndarray,
        feature_values: Dict[str, float],
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze SHAP values to identify risk and protective factors
        
        Args:
            shap_values: Array of SHAP values
            feature_values: Dict of actual feature values
            feature_names: List of feature names
            
        Returns:
            Analysis dictionary with risk/protective factors
        """
        # Create feature importance dataframe
        importance_data = []
        for i, feature_name in enumerate(feature_names):
            if i < len(shap_values):
                importance_data.append({
                    'feature': feature_name,
                    'shap_value': float(shap_values[i]),
                    'feature_value': feature_values.get(feature_name, 0.0),
                    'abs_shap': abs(float(shap_values[i]))
                })
        
        importance_df = pd.DataFrame(importance_data)
        
        # Sort by absolute SHAP value
        importance_df = importance_df.sort_values('abs_shap', ascending=False)
        
        # Separate risk factors (positive SHAP) and protective factors (negative SHAP)
        risk_factors = importance_df[importance_df['shap_value'] > 0].head(10)
        protective_factors = importance_df[importance_df['shap_value'] < 0].head(10)
        
        # Calculate total contribution
        total_positive = risk_factors['shap_value'].sum() if not risk_factors.empty else 0.0
        total_negative = protective_factors['shap_value'].sum() if not protective_factors.empty else 0.0
        
        return {
            "risk_factors": self.format_factors(risk_factors, "risk"),
            "protective_factors": self.format_factors(protective_factors, "protective"),
            "contribution_summary": {
                "total_risk_contribution": float(total_positive),
                "total_protective_contribution": float(total_negative),
                "net_effect": float(total_positive + total_negative),
                "risk_percentage": float(total_positive / (abs(total_positive) + abs(total_negative)) * 100) if (abs(total_positive) + abs(total_negative)) > 0 else 0
            },
            "feature_interactions": self.identify_feature_interactions(importance_df)
        }
    
    def format_factors(self, factors_df: pd.DataFrame, factor_type: str) -> List[Dict]:
        """
        Format risk/protective factors with clinical context
        
        Args:
            factors_df: DataFrame with feature, shap_value, feature_value, abs_shap
            factor_type: "risk" or "protective"
            
        Returns:
            List of formatted factor dictionaries
        """
        formatted_factors = []
        
        for idx, row in factors_df.iterrows():
            feature_key = row['feature']
            shap_value = row['shap_value']
            feature_value = row['feature_value']
            
            # Get feature config from ranges
            feature_config = self._get_feature_config(feature_key)
            
            if not feature_config:
                # Skip if no config found
                logger.debug(f"No config found for feature: {feature_key}")
                continue
            
            # Calculate importance percentage
            total_abs = factors_df['abs_shap'].sum()
            importance_pct = (abs(shap_value) / total_abs * 100) if total_abs > 0 else 0
            
            # Get severity analysis
            gender = "universal"  # Default, can be updated with user_info
            if calculate_feature_severity:
                severity_info = calculate_feature_severity(
                    feature_value,
                    feature_config,
                    gender
                )
            else:
                severity_info = {
                    "status": "unknown",
                    "severity": "unknown",
                    "deviation_pct": 0,
                    "interpretation": "Không có dữ liệu tham chiếu"
                }
            
            factor = {
                "rank": len(formatted_factors) + 1,
                "feature_key": feature_key,
                "feature_name_vi": feature_config.get("name_vi", feature_key),
                "feature_name_en": feature_config.get("name_en", feature_key),
                "category": feature_config.get("category", "Khác"),
                "shap_value": float(shap_value),
                "importance_percentage": float(importance_pct),
                "absolute_importance": abs(shap_value),
                "feature_value": float(feature_value),
                "unit": feature_config.get("unit", ""),
                "normal_range": self._format_ranges(feature_config, gender),
                "status": severity_info["status"],
                "severity": severity_info["severity"],
                "deviation_pct": severity_info["deviation_pct"],
                "interpretation": severity_info["interpretation"],
                "clinical_significance": feature_config.get("clinical_significance", feature_config.get("mci_relevance", "")),
                "citation": feature_config.get("citation", ""),
                "direction": factor_type,
                "explanation": self.generate_factor_explanation(
                    feature_config,
                    feature_value,
                    shap_value,
                    severity_info,
                    factor_type
                ),
                "recommendation": self.generate_recommendation(
                    feature_config,
                    severity_info,
                    factor_type
                ),
                "comparison": self._generate_comparison(feature_value, feature_config, severity_info)
            }
            
            formatted_factors.append(factor)
        
        return formatted_factors
    
    def _get_feature_config(self, feature_key: str) -> Optional[Dict]:
        """Get feature configuration from ranges"""
        # Try acoustic features first
        for category, features in ACOUSTIC_CLINICAL_RANGES.items():
            if isinstance(features, dict):
                if feature_key in features:
                    config = features[feature_key].copy()
                    config["feature_key"] = feature_key
                    return config
                # Recurse into nested dicts
                for subcat, subfeatures in features.items():
                    if isinstance(subfeatures, dict) and feature_key in subfeatures:
                        config = subfeatures[feature_key].copy()
                        config["feature_key"] = feature_key
                        return config
        
        # Try linguistic features
        for category, features in LINGUISTIC_CLINICAL_RANGES.items():
            if isinstance(features, dict):
                if feature_key in features:
                    config = features[feature_key].copy()
                    config["feature_key"] = feature_key
                    return config
                for subcat, subfeatures in features.items():
                    if isinstance(subfeatures, dict) and feature_key in subfeatures:
                        config = subfeatures[feature_key].copy()
                        config["feature_key"] = feature_key
                        return config
        
        return None
    
    def _format_ranges(self, feature_config: Dict, gender: str) -> Dict[str, Any]:
        """Format ranges for display"""
        result = {}
        
        if 'optimal' in feature_config:
            optimal = feature_config['optimal']
            if isinstance(optimal, dict):
                if gender in optimal:
                    opt_range = optimal[gender]
                    if isinstance(opt_range, tuple) and len(opt_range) == 2:
                        result['optimal_min'] = opt_range[0]
                        result['optimal_max'] = opt_range[1]
            elif isinstance(optimal, tuple) and len(optimal) == 2:
                result['optimal_min'] = optimal[0]
                result['optimal_max'] = optimal[1]
        
        if 'normal' in feature_config:
            normal = feature_config['normal']
            if isinstance(normal, dict):
                if gender in normal:
                    norm_range = normal[gender]
                    if isinstance(norm_range, tuple) and len(norm_range) == 2:
                        result['normal_min'] = norm_range[0]
                        result['normal_max'] = norm_range[1]
            elif isinstance(normal, tuple) and len(normal) == 2:
                result['normal_min'] = normal[0]
                result['normal_max'] = normal[1]
        
        # Format display string
        if 'optimal_min' in result and 'optimal_max' in result:
            if 'normal_min' in result and 'normal_max' in result:
                result['display'] = f"{result['optimal_min']}-{result['optimal_max']} (Tối ưu), {result['normal_min']}-{result['normal_max']} (Chấp nhận được)"
            else:
                result['display'] = f"{result['optimal_min']}-{result['optimal_max']} (Tối ưu)"
        elif 'normal_min' in result and 'normal_max' in result:
            result['display'] = f"{result['normal_min']}-{result['normal_max']} (Bình thường)"
        else:
            result['display'] = "Không có dữ liệu"
        
        return result
    
    def _generate_comparison(self, feature_value: float, feature_config: Dict, severity_info: Dict) -> str:
        """Generate comparison text (e.g., 'Cao - Khoảng bình thường: 0.05-0.20')"""
        severity = severity_info.get("severity", "normal")
        normal_range = self._format_ranges(feature_config, "universal")
        
        if severity == "normal":
            return "Bình thường"
        elif severity in ["severe", "moderate", "mild"]:
            if "normal_min" in normal_range and "normal_max" in normal_range:
                if feature_value < normal_range["normal_min"]:
                    return f"Thấp - Khoảng bình thường: {normal_range['normal_min']}-{normal_range['normal_max']}"
                else:
                    return f"Cao - Khoảng bình thường: {normal_range['normal_min']}-{normal_range['normal_max']}"
        
        return "N/A"
    
    def _map_prediction_to_label(self, prediction: int) -> str:
        """Map numeric prediction to clinical label"""
        labels = {
            0: "Nhận thức bình thường (HC)",
            1: "Suy giảm nhận thức nhẹ (MCI)",
            2: "Suy giảm nhận thức (Dementia)"
        }
        return labels.get(int(prediction), "Không xác định")
    
    def _compute_risk_based_shap(
        self,
        features: Dict[str, float],
        user_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute SHAP-like importance using risk assessment thresholds
        (Fallback when model is not available)
        """
        logger.info("📊 Computing risk-based SHAP (fallback mode)")
        
        # Analyze features using feature analyzer approach
        risk_factors = []
        protective_factors = []
        
        for feature_key, feature_value in features.items():
            if not isinstance(feature_value, (int, float, np.number)):
                continue
            
            feature_value = float(feature_value)
            feature_config = self._get_feature_config(feature_key)
            
            if not feature_config:
                continue
            
            # Calculate severity
            gender = user_info.get('gender', 'universal') if user_info else 'universal'
            if calculate_feature_severity:
                severity_info = calculate_feature_severity(feature_value, feature_config, gender)
            else:
                continue
            
            # Calculate SHAP-like contribution based on severity
            if severity_info["severity"] in ["severe", "moderate", "mild"]:
                # Risk factor
                shap_contribution = {
                    "severe": 0.30,
                    "moderate": 0.20,
                    "mild": 0.10
                }.get(severity_info["severity"], 0.0)
                
                # Weight by feature importance
                weight = FEATURE_IMPORTANCE_WEIGHTS.get(feature_key, 1.0)
                shap_contribution *= weight
                
                risk_factors.append({
                    "feature": feature_key,
                    "shap_value": shap_contribution,
                    "feature_value": feature_value,
                    "abs_shap": abs(shap_contribution)
                })
            elif severity_info["severity"] == "normal":
                # Protective factor
                shap_contribution = -0.05  # Slight protective effect
                weight = FEATURE_IMPORTANCE_WEIGHTS.get(feature_key, 1.0)
                shap_contribution *= weight
                
                protective_factors.append({
                    "feature": feature_key,
                    "shap_value": shap_contribution,
                    "feature_value": feature_value,
                    "abs_shap": abs(shap_contribution)
                })
        
        # Sort by absolute importance
        risk_factors.sort(key=lambda x: x["abs_shap"], reverse=True)
        protective_factors.sort(key=lambda x: x["abs_shap"], reverse=True)
        
        # Convert to DataFrame format
        risk_df = pd.DataFrame(risk_factors[:10])
        protective_df = pd.DataFrame(protective_factors[:10])
        
        return {
            "prediction": {
                "class": "Đánh giá dựa trên đặc trưng",
                "confidence": None,
                "base_risk": 0.0
            },
            "shap_analysis": self.analyze_shap_values(
                np.array([f["shap_value"] for f in risk_factors[:10] + protective_factors[:10]]),
                features,
                [f["feature"] for f in risk_factors[:10] + protective_factors[:10]]
            ),
            "clinical_interpretation": None
        }
    
    def generate_factor_explanation(
        self,
        feature_config: Dict,
        feature_value: float,
        shap_value: float,
        severity_info: Dict,
        factor_type: str
    ) -> str:
        """
        Generate human-readable explanation for why this factor matters
        
        Args:
            feature_config: Feature configuration from ranges
            feature_value: Actual feature value
            shap_value: SHAP contribution value
            severity_info: Severity analysis result
            factor_type: "risk" or "protective"
            
        Returns:
            Human-readable explanation string
        """
        name = feature_config.get("name_vi", feature_config.get("feature_key", "Đặc trưng"))
        unit = feature_config.get("unit", "")
        
        if factor_type == "risk":
            template = (
                f"{name} của bạn là {feature_value:.2f}{unit}, "
                f"{severity_info.get('interpretation', 'bất thường')}. "
                f"Điều này làm tăng {abs(shap_value)*100:.1f}% khả năng có vấn đề về nhận thức. "
            )
        else:
            template = (
                f"{name} của bạn là {feature_value:.2f}{unit}, "
                f"{severity_info.get('interpretation', 'bình thường')}. "
                f"Điều này giúp giảm {abs(shap_value)*100:.1f}% nguy cơ suy giảm nhận thức. "
            )
        
        # Add clinical context
        clinical_sig = feature_config.get("clinical_significance") or feature_config.get("mci_relevance", "")
        if clinical_sig:
            template += f"Nghiên cứu cho thấy: {clinical_sig}"
        
        return template
    
    def generate_recommendation(
        self,
        feature_config: Dict,
        severity_info: Dict,
        factor_type: str
    ) -> str:
        """
        Generate actionable recommendations based on feature status
        
        Args:
            feature_config: Feature configuration
            severity_info: Severity analysis
            factor_type: "risk" or "protective"
            
        Returns:
            Recommendation string
        """
        # Predefined recommendations for common features
        recommendations = {
            "pause_pause_rate": {
                "high": "Tăng tạm dừng có thể do khó tìm từ. Khuyến nghị: (1) Luyện tập kể chuyện hàng ngày, (2) Chơi trò chơi tìm từ, (3) Đọc sách to và tóm tắt nội dung",
                "normal": "Tần suất tạm dừng bình thường. Tiếp tục duy trì hoạt động giao tiếp thường xuyên"
            },
            "rate_words_per_minute": {
                "low": "Tốc độ nói chậm. Khuyến nghị: (1) Luyện đọc to với tốc độ tăng dần, (2) Tham gia trò chuyện nhóm, (3) Nếu kèm khó tìm từ, nên đánh giá thêm về trí nhớ",
                "normal": "Tốc độ nói tốt. Duy trì giao tiếp xã hội thường xuyên"
            },
            "lex_ttr": {
                "low": "Từ vựng hạn chế. Khuyến nghị: (1) Đọc sách đa dạng thể loại, (2) Học từ mới mỗi ngày, (3) Chơi trò chơi ô chữ, (4) Viết nhật ký",
                "normal": "Đa dạng từ vựng tốt. Tiếp tục đọc sách và học hỏi"
            },
            "sem_semantic_coherence": {
                "low": "Nội dung thiếu mạch lạc. Khuyến nghị: (1) Luyện tập kể chuyện có cấu trúc, (2) Tóm tắt phim/sách, (3) Có thể cần đánh giá chức năng điều hành",
                "normal": "Nội dung mạch lạc. Tiếp tục hoạt động trí tuệ"
            },
            "tone_flattening_score": {
                "high": "Mất thanh điệu tiếng Việt. Khuyến nghị: (1) Luyện phát âm thanh điệu, (2) Đọc to và tự nghe lại, (3) Cần theo dõi vì đây là dấu hiệu sớm",
                "normal": "Thanh điệu rõ ràng. Tiếp tục giao tiếp bằng tiếng Việt"
            },
            "jitter": {
                "high": "Giọng không ổn định. Khuyến nghị: (1) Khám thanh quản, (2) Luyện thở và phát âm, (3) Giảm căng thẳng",
                "normal": "Chất lượng giọng tốt"
            }
        }
        
        feature_key = feature_config.get("feature_key") or feature_config.get("name_vi", "")
        severity = severity_info.get("severity", "normal")
        
        # Normalize feature key
        normalized_key = self._normalize_feature_key(feature_key)
        
        if normalized_key in recommendations:
            if severity in ["severe", "moderate", "mild"]:
                return recommendations[normalized_key].get("high", "Cần theo dõi thêm")
            else:
                return recommendations[normalized_key].get("normal", "Duy trì hiện trạng")
        
        # Generic recommendations
        if severity in ["severe", "moderate"]:
            category = feature_config.get("category", "đặc trưng này")
            return f"Nên đánh giá thêm về {category} với chuyên gia"
        elif severity == "mild":
            name = feature_config.get("name_vi", "Đặc trưng này")
            return f"Theo dõi {name} trong các lần kiểm tra tiếp theo"
        else:
            name = feature_config.get("name_vi", "Đặc trưng này")
            return f"{name} tốt, tiếp tục duy trì"
    
    def _normalize_feature_key(self, feature_key: str) -> str:
        """Normalize feature key to match recommendation keys"""
        key_lower = feature_key.lower()
        
        if 'pause' in key_lower and 'rate' in key_lower:
            return 'pause_pause_rate'
        elif 'rate' in key_lower and ('word' in key_lower or 'speech' in key_lower):
            return 'rate_words_per_minute'
        elif 'ttr' in key_lower or 'type_token' in key_lower:
            return 'lex_ttr'
        elif 'semantic' in key_lower and 'coherence' in key_lower:
            return 'sem_semantic_coherence'
        elif 'tone' in key_lower and 'flatten' in key_lower:
            return 'tone_flattening_score'
        elif 'jitter' in key_lower:
            return 'jitter'
        
        return feature_key
    
    def identify_feature_interactions(self, importance_df: pd.DataFrame) -> List[Dict]:
        """
        Identify important feature interactions and patterns
        
        Based on clinical knowledge of how features co-occur in cognitive decline
        
        Args:
            importance_df: DataFrame with feature importance analysis
            
        Returns:
            List of interaction dictionaries
        """
        interactions = []
        
        # Check for pause + speech rate interaction
        pause_features = importance_df[importance_df['feature'].str.contains('pause', case=False, na=False)]
        rate_features = importance_df[importance_df['feature'].str.contains('rate.*word', case=False, na=False) | 
                                      importance_df['feature'].str.contains('speaking_rate', case=False, na=False)]
        
        if not pause_features.empty and not rate_features.empty:
            interactions.append({
                "interaction_type": "pause_rate_combination",
                "name": "Tương tác Tạm dừng - Tốc độ nói",
                "features_involved": list(pause_features['feature'].head(1).values) + list(rate_features['feature'].head(1).values),
                "explanation": "Tăng tạm dừng kết hợp với giảm tốc độ nói là dấu hiệu điển hình của word-finding difficulty trong suy giảm nhận thức",
                "clinical_relevance": "high",
                "citation": "Fraser et al. (2016) - Pause and rate patterns in AD speech"
            })
        
        # Check for lexical diversity + semantic coherence
        lex_features = importance_df[importance_df['feature'].str.contains('lex_|ttr|mattr', case=False, na=False)]
        sem_features = importance_df[importance_df['feature'].str.contains('sem_|semantic|coherence', case=False, na=False)]
        
        if not lex_features.empty and not sem_features.empty:
            interactions.append({
                "interaction_type": "lexical_semantic_combination",
                "name": "Tương tác Từ vựng - Ngữ nghĩa",
                "features_involved": list(lex_features['feature'].head(1).values) + list(sem_features['feature'].head(1).values),
                "explanation": "Giảm đa dạng từ vựng kết hợp với giảm mạch lạc ngữ nghĩa phản ánh suy giảm semantic memory",
                "clinical_relevance": "high",
                "citation": "Ahmed et al. (2013) - Lexical-semantic decline in AD"
            })
        
        # Check for Vietnamese tone + pitch variability
        tone_features = importance_df[importance_df['feature'].str.contains('tone', case=False, na=False)]
        f0_features = importance_df[importance_df['feature'].str.contains('f0', case=False, na=False)]
        
        if not tone_features.empty and not f0_features.empty:
            interactions.append({
                "interaction_type": "vietnamese_prosody",
                "name": "Tương tác Thanh điệu - Cao độ",
                "features_involved": list(tone_features['feature'].head(1).values) + list(f0_features['feature'].head(1).values),
                "explanation": "Phẳng thanh điệu kết hợp với giảm biến đổi cao độ là dấu hiệu đặc trưng ở người Việt có suy giảm nhận thức",
                "clinical_relevance": "high (Vietnamese-specific)",
                "citation": "Nguyễn et al. (2021) - Vietnamese tone patterns in MCI"
            })
        
        return interactions
    
    def generate_clinical_interpretation(self, shap_analysis: Dict) -> Dict:
        """
        Generate comprehensive clinical interpretation from SHAP analysis
        
        Args:
            shap_analysis: Result from analyze_shap_values
            
        Returns:
            Clinical interpretation dictionary
        """
        risk_factors = shap_analysis.get("risk_factors", [])
        protective_factors = shap_analysis.get("protective_factors", [])
        contribution = shap_analysis.get("contribution_summary", {})
        
        # Determine overall risk level
        net_effect = contribution.get("net_effect", 0.0)
        
        if net_effect > 0.3:
            risk_level = "Nguy cơ cao"
            risk_color = "red"
            overall_message = "Phân tích cho thấy nhiều dấu hiệu cần lưu ý. Khuyến nghị đánh giá chuyên sâu hơn."
        elif net_effect > 0.1:
            risk_level = "Nguy cơ trung bình"
            risk_color = "orange"
            overall_message = "Có một số dấu hiệu cần theo dõi. Nên kiểm tra lại sau 3-6 tháng."
        elif net_effect > -0.1:
            risk_level = "Nguy cơ thấp"
            risk_color = "yellow"
            overall_message = "Nhìn chung tốt, chỉ có một vài điểm cần chú ý nhỏ."
        else:
            risk_level = "Bình thường"
            risk_color = "green"
            overall_message = "Các chỉ số trong giới hạn bình thường. Tiếp tục duy trì lối sống lành mạnh."
        
        # Identify primary concerns
        primary_concerns = []
        if risk_factors:
            # Group by category
            categories = defaultdict(list)
            for factor in risk_factors[:5]:
                cat = factor.get("category", "Khác")
                categories[cat].append(factor)
            
            for category, factors in categories.items():
                severities = [f.get("severity", "normal") for f in factors]
                max_severity = max(severities, key=lambda s: {"severe": 3, "moderate": 2, "mild": 1, "normal": 0}.get(s, 0))
                
                primary_concerns.append({
                    "category": category,
                    "severity": max_severity,
                    "count": len(factors),
                    "features": [f.get("feature_name_vi", f.get("feature_key", "")) for f in factors],
                    "summary": self._summarize_category_concern(category, factors)
                })
        
        # Identify strengths
        strengths = []
        if protective_factors:
            categories = defaultdict(list)
            for factor in protective_factors[:5]:
                cat = factor.get("category", "Khác")
                categories[cat].append(factor)
            
            for category, factors in categories.items():
                strengths.append({
                    "category": category,
                    "count": len(factors),
                    "features": [f.get("feature_name_vi", f.get("feature_key", "")) for f in factors],
                    "summary": self._summarize_category_strength(category, factors)
                })
        
        return {
            "overall_risk_level": risk_level,
            "risk_color": risk_color,
            "net_risk_score": float(net_effect),
            "confidence": contribution.get("risk_percentage", 0.0),
            "overall_message": overall_message,
            "primary_concerns": primary_concerns,
            "strengths": strengths,
            "key_recommendations": self._generate_key_recommendations(risk_factors),
            "follow_up_plan": self._generate_follow_up_plan(risk_level, primary_concerns)
        }
    
    def _summarize_category_concern(self, category: str, factors: List[Dict]) -> str:
        """Generate summary for a concerning category"""
        summaries = {
            "Tạm dừng và lưu loát": "Có nhiều tạm dừng và gián đoạn khi nói, có thể do khó tìm từ hoặc mất tập trung",
            "Tốc độ và nhịp điệu": "Tốc độ nói chậm hơn bình thường, có thể do chậm xử lý thông tin",
            "Đa dạng từ vựng": "Từ vựng hạn chế, lặp lại nhiều từ, có thể do khó tiếp cận từ vựng",
            "Ngữ nghĩa": "Nội dung thiếu mạch lạc, ý tưởng không liên kết chặt chẽ",
            "Thanh điệu tiếng Việt": "Thanh điệu không rõ ràng, có thể mất khả năng điều chỉnh thanh",
            "Chất lượng giọng nói": "Giọng nói không ổn định, có thể do yếu thanh quản hoặc vấn đề thần kinh"
        }
        
        return summaries.get(category, f"Có vấn đề về {category}")
    
    def _summarize_category_strength(self, category: str, factors: List[Dict]) -> str:
        """Generate summary for a strong category"""
        summaries = {
            "Đa dạng từ vựng": "Sử dụng từ vựng đa dạng và phong phú",
            "Ngữ nghĩa": "Nội dung mạch lạc, ý tưởng liên kết tốt",
            "Cú pháp": "Cấu trúc câu tốt, sử dụng ngữ pháp chính xác",
            "Thanh điệu tiếng Việt": "Thanh điệu rõ ràng và chính xác",
            "Tốc độ và nhịp điệu": "Tốc độ nói phù hợp và tự nhiên"
        }
        
        return summaries.get(category, f"{category} tốt")
    
    def _generate_key_recommendations(self, risk_factors: List[Dict]) -> List[Dict]:
        """Generate top 3-5 actionable recommendations"""
        recommendations = []
        
        # Prioritize by severity and importance
        sorted_factors = sorted(
            risk_factors,
            key=lambda x: (
                {"severe": 3, "moderate": 2, "mild": 1}.get(x.get("severity", "normal"), 0),
                x.get("importance_percentage", 0)
            ),
            reverse=True
        )
        
        for factor in sorted_factors[:5]:
            rec_text = factor.get("recommendation")
            if rec_text:
                recommendations.append({
                    "priority": "Cao" if factor.get("severity") in ["severe", "moderate"] else "Trung bình",
                    "area": factor.get("category", "Khác"),
                    "recommendation": rec_text
                })
        
        return recommendations
    
    def _generate_follow_up_plan(self, risk_level: str, concerns: List[Dict]) -> Dict:
        """Generate follow-up plan based on risk level"""
        plans = {
            "Nguy cơ cao": {
                "timeline": "1-3 tháng",
                "actions": [
                    "Đánh giá chuyên sâu với bác sĩ thần kinh hoặc tâm lý",
                    "Xem xét làm thêm các xét nghiệm: MoCA, Neuropsych Battery",
                    "Theo dõi sát các yếu tố nguy cơ đã phát hiện",
                    "Bắt đầu can thiệp nhận thức nếu được chỉ định"
                ],
                "monitoring": "Kiểm tra lại sau 1 tháng để đánh giá tiến triển"
            },
            "Nguy cơ trung bình": {
                "timeline": "3-6 tháng",
                "actions": [
                    "Kiểm tra lại MMSE sau 3-6 tháng",
                    "Tăng cường hoạt động trí tuệ: đọc sách, trò chơi, giao tiếp",
                    "Luyện tập các kỹ năng đang yếu theo khuyến nghị",
                    "Theo dõi các yếu tố nguy cơ tim mạch"
                ],
                "monitoring": "Theo dõi định kỳ 3-6 tháng"
            },
            "Nguy cơ thấp": {
                "timeline": "6-12 tháng",
                "actions": [
                    "Duy trì lối sống lành mạnh",
                    "Tiếp tục hoạt động trí tuệ và xã hội",
                    "Kiểm tra sức khỏe định kỳ hàng năm"
                ],
                "monitoring": "Kiểm tra hàng năm hoặc khi có triệu chứng"
            },
            "Bình thường": {
                "timeline": "Hàng năm",
                "actions": [
                    "Duy trì lối sống lành mạnh",
                    "Tiếp tục học hỏi và hoạt động trí tuệ",
                    "Kiểm tra sức khỏe định kỳ"
                ],
                "monitoring": "Kiểm tra hàng năm"
            }
        }
        
        plan = plans.get(risk_level, plans["Bình thường"])
        
        # Add specific concerns to monitor
        if concerns:
            plan["specific_areas_to_monitor"] = [c.get("category", "") for c in concerns]
        
        return plan


