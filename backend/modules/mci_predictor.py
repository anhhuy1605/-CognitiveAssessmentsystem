# -*- coding: utf-8 -*-
"""
MCI Prediction Module for Vietnamese Cognitive Assessment
Predicts MCI status and estimates MMSE score from multimodal features

Author: Cognitive Assessment System
Version: 1.0
"""

import logging
import numpy as np
import os
import pickle
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.svm import SVC, SVR
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available. ML prediction will be limited.")


@dataclass
class MCIPrediction:
    """MCI prediction result"""
    mci_probability: float            # Probability of MCI (0-1)
    mci_class: str                    # 'Normal', 'MCI', 'Dementia'
    mmse_estimate: float              # Estimated MMSE score (0-30)
    confidence: float                 # Prediction confidence (0-1)
    severity: str                     # 'Normal', 'Mild', 'Moderate', 'Severe'
    risk_factors: List[str] = field(default_factory=list)  # Identified risk factors
    recommendations: List[str] = field(default_factory=list)  # Clinical recommendations


@dataclass 
class FeatureImportance:
    """Feature importance analysis"""
    feature_name: str
    importance_score: float
    interpretation: str


class MCIPredictor:
    """
    MCI Prediction and MMSE Estimation
    
    Uses ensemble of classifiers trained on multimodal features:
    - Random Forest (good for feature interactions)
    - Gradient Boosting (high accuracy)
    - Logistic Regression (interpretable)
    - SVM (robust to outliers)
    
    MMSE Estimation:
    - Ridge Regression for continuous score
    - Calibrated to MMSE 0-30 scale
    """
    
    # MMSE severity thresholds (standard clinical cutoffs)
    MMSE_THRESHOLDS = {
        'normal': 24,       # >= 24: Normal
        'mild_mci': 18,     # 18-23: Mild Cognitive Impairment
        'moderate': 10,     # 10-17: Moderate Dementia
        'severe': 0         # < 10: Severe Dementia
    }
    
    # Feature importance rankings from literature
    TOP_PREDICTIVE_FEATURES = [
        ('sem_idea_density', 0.15, 'Mật độ ý tưởng - yếu tố dự đoán mạnh nhất'),
        ('lex_pronoun_ratio', 0.12, 'Tỷ lệ đại từ - khó tìm từ'),
        ('syn_mlu_words', 0.10, 'Độ dài trung bình câu'),
        ('tone_flattening_score', 0.10, 'Phẳng thanh điệu - đặc trưng tiếng Việt'),
        ('pause_pause_rate', 0.08, 'Tần suất ngừng nghỉ'),
        ('f0_f0_cv', 0.08, 'Biến thiên cao độ'),
        ('lex_ttr', 0.07, 'Đa dạng từ vựng'),
        ('vq_jitter_local', 0.06, 'Jitter giọng nói'),
        ('rate_words_per_minute', 0.06, 'Tốc độ nói'),
        ('sem_semantic_coherence', 0.05, 'Mạch lạc ngữ nghĩa')
    ]
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize MCI Predictor
        
        Args:
            model_path: Path to pre-trained model (optional)
        """
        self.classifier = None
        self.regressor = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        
        # Load pre-trained model if available
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._initialize_default_models()
        
        logger.info("MCIPredictor initialized")
    
    def _initialize_default_models(self):
        """Initialize default ML models"""
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, using rule-based prediction only")
            return
        
        # Ensemble classifier for MCI detection
        self.classifier = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        # Regressor for MMSE estimation
        self.regressor = Ridge(alpha=1.0)
        
        logger.info("Default models initialized (not trained)")
    
    def train(self, X: np.ndarray, y_class: np.ndarray, 
              y_mmse: Optional[np.ndarray] = None):
        """
        Train the predictor on labeled data
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y_class: Class labels (0: Normal, 1: MCI, 2: Dementia)
            y_mmse: MMSE scores (optional, for regression)
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Cannot train: sklearn not available")
            return
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train classifier
        logger.info("Training MCI classifier...")
        self.classifier.fit(X_scaled, y_class)
        
        # Cross-validation
        cv_scores = cross_val_score(self.classifier, X_scaled, y_class, cv=5)
        logger.info(f"Classifier CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        
        # Train regressor if MMSE labels provided
        if y_mmse is not None:
            logger.info("Training MMSE regressor...")
            self.regressor.fit(X_scaled, y_mmse)
            
            cv_scores_reg = cross_val_score(self.regressor, X_scaled, y_mmse, cv=5, 
                                           scoring='neg_mean_squared_error')
            rmse = np.sqrt(-cv_scores_reg.mean())
            logger.info(f"Regressor CV RMSE: {rmse:.3f}")
        
        self.is_trained = True
        logger.info("Training complete")
    
    def predict(self, features: Dict[str, float]) -> MCIPrediction:
        """
        Predict MCI status and estimate MMSE score
        
        Args:
            features: Dictionary of extracted features
        
        Returns:
            MCIPrediction: Prediction result with all details
        """
        # Convert features to array
        feature_array = self._features_to_array(features)
        
        # Use ML prediction if trained, otherwise rule-based
        if self.is_trained and SKLEARN_AVAILABLE:
            return self._ml_predict(feature_array, features)
        else:
            return self._rule_based_predict(features)
    
    def _features_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert feature dictionary to numpy array"""
        # Use consistent ordering
        feature_names = sorted(features.keys())
        values = [features.get(name, 0.0) for name in feature_names]
        return np.array(values, dtype=np.float32).reshape(1, -1)
    
    def _ml_predict(self, X: np.ndarray, features: Dict[str, float]) -> MCIPrediction:
        """ML-based prediction"""
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get class probabilities
        probs = self.classifier.predict_proba(X_scaled)[0]
        predicted_class = self.classifier.predict(X_scaled)[0]
        
        # Class mapping
        class_names = ['Normal', 'MCI', 'Dementia']
        mci_class = class_names[predicted_class]
        
        # MCI probability (probability of not being normal)
        mci_probability = 1.0 - probs[0] if len(probs) > 0 else 0.5
        
        # MMSE estimation
        mmse_estimate = self.regressor.predict(X_scaled)[0]
        mmse_estimate = np.clip(mmse_estimate, 0, 30)  # Clamp to valid range
        
        # Confidence based on probability margin
        confidence = max(probs) - min(probs) if len(probs) > 1 else 0.5
        
        # Severity classification
        severity = self._classify_severity(mmse_estimate)
        
        # Risk factors
        risk_factors = self._identify_risk_factors(features)
        
        # Recommendations
        recommendations = self._generate_recommendations(mmse_estimate, risk_factors)
        
        return MCIPrediction(
            mci_probability=float(mci_probability),
            mci_class=mci_class,
            mmse_estimate=float(mmse_estimate),
            confidence=float(confidence),
            severity=severity,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _rule_based_predict(self, features: Dict[str, float]) -> MCIPrediction:
        """
        Rule-based prediction when ML model not available
        
        Uses clinical heuristics based on literature:
        - Idea density < 3.5 suggests cognitive decline
        - High pronoun ratio (> 0.15) suggests word-finding difficulty
        - Low TTR (< 0.4) suggests limited vocabulary
        - High pause rate (> 0.3) suggests processing difficulty
        - High tone flattening (> 0.4) suggests motor/cognitive decline
        """
        # Calculate risk score based on features
        risk_score = 0.0
        max_score = 10.0
        
        # Feature-based risk assessment
        risk_factors = []
        
        # 1. Idea density (strongest predictor)
        idea_density = features.get('sem_idea_density', 5.0)
        if idea_density < 3.0:
            risk_score += 2.0
            risk_factors.append("Mật độ ý tưởng thấp (dự đoán mạnh nhất cho suy giảm nhận thức)")
        elif idea_density < 4.0:
            risk_score += 1.0
            risk_factors.append("Mật độ ý tưởng dưới trung bình")
        
        # 2. Pronoun ratio
        pronoun_ratio = features.get('lex_pronoun_ratio', 0.1)
        if pronoun_ratio > 0.20:
            risk_score += 1.5
            risk_factors.append("Sử dụng đại từ cao - có thể khó tìm từ")
        elif pronoun_ratio > 0.15:
            risk_score += 0.5
            risk_factors.append("Sử dụng đại từ hơi cao")
        
        # 3. TTR (lexical diversity)
        ttr = features.get('lex_ttr', 0.5)
        if ttr < 0.3:
            risk_score += 1.5
            risk_factors.append("Đa dạng từ vựng thấp")
        elif ttr < 0.4:
            risk_score += 0.5
        
        # 4. MLU (sentence length)
        mlu = features.get('syn_mlu_words', 10.0)
        if mlu < 5:
            risk_score += 1.0
            risk_factors.append("Câu rất ngắn - có thể giảm xử lý ngôn ngữ")
        elif mlu < 7:
            risk_score += 0.5
        
        # 5. Pause rate
        pause_rate = features.get('pause_pause_rate', 0.1)
        if pause_rate > 0.4:
            risk_score += 1.0
            risk_factors.append("Tần suất ngừng nghỉ cao - có thể khó tìm từ")
        elif pause_rate > 0.25:
            risk_score += 0.5
        
        # 6. Vietnamese tone flattening (novel biomarker)
        tone_flat = features.get('tone_flattening_score', 0.2)
        if tone_flat > 0.5:
            risk_score += 1.5
            risk_factors.append("Phẳng thanh điệu cao - biomarker tiềm năng cho MCI tiếng Việt")
        elif tone_flat > 0.35:
            risk_score += 0.75
            risk_factors.append("Có dấu hiệu phẳng thanh điệu")
        
        # 7. Voice quality
        jitter = features.get('vq_jitter_local', 0.01)
        if jitter > 0.025:
            risk_score += 0.5
            risk_factors.append("Tăng bất ổn định giọng nói")
        
        # 8. Speaking rate
        wpm = features.get('rate_words_per_minute', 100)
        if wpm < 50:
            risk_score += 1.0
            risk_factors.append("Tốc độ nói rất chậm")
        elif wpm < 80:
            risk_score += 0.5
        
        # Calculate MCI probability (sigmoid-like mapping)
        normalized_score = risk_score / max_score
        mci_probability = 1 / (1 + np.exp(-5 * (normalized_score - 0.4)))
        
        # Estimate MMSE score
        # Linear mapping: low risk = high MMSE, high risk = low MMSE
        mmse_estimate = 30 - (normalized_score * 20)  # Range: 10-30
        mmse_estimate = np.clip(mmse_estimate, 10, 30)
        
        # Classification
        if mci_probability < 0.3:
            mci_class = 'Normal'
        elif mci_probability < 0.7:
            mci_class = 'MCI'
        else:
            mci_class = 'Dementia'
        
        # Severity
        severity = self._classify_severity(mmse_estimate)
        
        # Confidence (based on how many features had clear signals)
        confidence = min(0.5 + len(risk_factors) * 0.1, 0.85)
        
        # Recommendations
        recommendations = self._generate_recommendations(mmse_estimate, risk_factors)
        
        return MCIPrediction(
            mci_probability=float(mci_probability),
            mci_class=mci_class,
            mmse_estimate=float(mmse_estimate),
            confidence=float(confidence),
            severity=severity,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _classify_severity(self, mmse_score: float) -> str:
        """Classify severity based on MMSE score"""
        if mmse_score >= self.MMSE_THRESHOLDS['normal']:
            return 'Bình thường'
        elif mmse_score >= self.MMSE_THRESHOLDS['mild_mci']:
            return 'Suy giảm nhận thức nhẹ (MCI)'
        elif mmse_score >= self.MMSE_THRESHOLDS['moderate']:
            return 'Sa sút trí tuệ mức độ trung bình'
        else:
            return 'Sa sút trí tuệ mức độ nặng'
    
    def _identify_risk_factors(self, features: Dict[str, float]) -> List[str]:
        """Identify risk factors based on feature values"""
        risk_factors = []
        
        # Check each key feature against thresholds
        checks = [
            ('sem_idea_density', '<', 3.5, 'Mật độ ý tưởng thấp'),
            ('lex_pronoun_ratio', '>', 0.15, 'Sử dụng đại từ cao'),
            ('lex_ttr', '<', 0.35, 'Đa dạng từ vựng thấp'),
            ('syn_mlu_words', '<', 6, 'Độ dài câu ngắn'),
            ('pause_pause_rate', '>', 0.3, 'Nhiều khoảng ngừng'),
            ('tone_flattening_score', '>', 0.4, 'Phẳng thanh điệu'),
            ('vq_jitter_local', '>', 0.02, 'Giọng nói không ổn định'),
            ('rate_words_per_minute', '<', 70, 'Tốc độ nói chậm'),
        ]
        
        for feature_name, op, threshold, description in checks:
            value = features.get(feature_name, None)
            if value is not None:
                if op == '<' and value < threshold:
                    risk_factors.append(description)
                elif op == '>' and value > threshold:
                    risk_factors.append(description)
        
        return risk_factors
    
    def _generate_recommendations(self, mmse_score: float, 
                                   risk_factors: List[str]) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []
        
        if mmse_score >= 24:
            recommendations.append("Kết quả trong giới hạn bình thường")
            recommendations.append("Khuyến nghị tái đánh giá sau 6-12 tháng để theo dõi")
        elif mmse_score >= 18:
            recommendations.append("Phát hiện dấu hiệu suy giảm nhận thức nhẹ")
            recommendations.append("Khuyến nghị đánh giá chuyên sâu bởi bác sĩ chuyên khoa")
            recommendations.append("Cân nhắc chụp MRI não để loại trừ nguyên nhân khác")
            recommendations.append("Khuyến khích các hoạt động kích thích trí não")
        else:
            recommendations.append("Phát hiện suy giảm nhận thức đáng kể")
            recommendations.append("Cần đánh giá y tế khẩn cấp")
            recommendations.append("Khuyến nghị khám chuyên khoa thần kinh hoặc lão khoa")
            recommendations.append("Đánh giá khả năng sinh hoạt hàng ngày")
        
        # Specific recommendations based on risk factors
        if any('thanh điệu' in rf.lower() for rf in risk_factors):
            recommendations.append("Dấu hiệu phẳng thanh điệu - biomarker đặc trưng cho người Việt, cần theo dõi thêm")
        
        if any('tốc độ nói' in rf.lower() for rf in risk_factors):
            recommendations.append("Cân nhắc đánh giá ngôn ngữ trị liệu")
        
        return recommendations
    
    def get_feature_importance(self, features: Dict[str, float]) -> List[FeatureImportance]:
        """
        Get feature importance analysis
        
        Args:
            features: Extracted features
        
        Returns:
            List of FeatureImportance objects
        """
        importances = []
        
        # Use predefined importance if no trained model
        for feature_name, importance_score, interpretation in self.TOP_PREDICTIVE_FEATURES:
            if feature_name in features:
                importances.append(FeatureImportance(
                    feature_name=feature_name,
                    importance_score=importance_score,
                    interpretation=interpretation
                ))
        
        # If trained model available, use actual importances
        if self.is_trained and hasattr(self.classifier, 'feature_importances_'):
            # This would require feature name mapping
            pass
        
        return sorted(importances, key=lambda x: x.importance_score, reverse=True)
    
    def save_model(self, path: str):
        """Save trained model to file"""
        if not self.is_trained:
            logger.warning("Model not trained, nothing to save")
            return
        
        model_data = {
            'classifier': self.classifier,
            'regressor': self.regressor,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained model from file"""
        try:
            model_data = joblib.load(path)
            self.classifier = model_data['classifier']
            self.regressor = model_data['regressor']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._initialize_default_models()


def predict_mci(features: Dict[str, float], 
                model_path: Optional[str] = None) -> MCIPrediction:
    """
    Convenience function to predict MCI status
    
    Args:
        features: Extracted multimodal features
        model_path: Optional path to pre-trained model
    
    Returns:
        MCIPrediction: Prediction result
    """
    predictor = MCIPredictor(model_path)
    return predictor.predict(features)


def estimate_mmse(features: Dict[str, float]) -> Tuple[float, str]:
    """
    Convenience function to estimate MMSE score
    
    Args:
        features: Extracted multimodal features
    
    Returns:
        Tuple of (mmse_score, severity_label)
    """
    predictor = MCIPredictor()
    prediction = predictor.predict(features)
    return prediction.mmse_estimate, prediction.severity

