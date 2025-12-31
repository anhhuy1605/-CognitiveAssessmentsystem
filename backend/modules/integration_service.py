# -*- coding: utf-8 -*-
"""
Integration Service for Vietnamese MCI Screening
Combines all analysis modules into a unified pipeline

Author: Cognitive Assessment System
Version: 1.0

This service provides the main entry point for:
1. Audio analysis (acoustic features)
2. Transcript analysis (linguistic features)
3. Multimodal fusion
4. MCI prediction and MMSE estimation
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import time

logger = logging.getLogger(__name__)

# Import modules - if import succeeds, module will be used (not None)
# If import fails, raise error (no graceful fallback - system requires these modules)
from .acoustic_analyzer import AcousticAnalyzer
from .linguistic_analyzer import VietnameseLinguisticAnalyzer
from .multimodal_fusion import MultimodalFusion, FusionConfig
from .mci_predictor import MCIPredictor, MCIPrediction


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    success: bool
    acoustic_features: Dict[str, Any]
    linguistic_features: Dict[str, Any]
    fused_features: Dict[str, Any]
    mci_prediction: Optional[Dict[str, Any]]
    mmse_estimate: float
    severity: str
    confidence: float
    risk_factors: list
    recommendations: list
    feature_summary: Dict[str, Any]
    processing_time: float
    errors: list


class MCIScreeningService:
    """
    Main service class for MCI screening
    
    Combines:
    - Acoustic analysis (eGeMAPS + Vietnamese tone features)
    - Linguistic analysis (Vietnamese NLP)
    - Multimodal fusion
    - MCI prediction and MMSE estimation
    
    Usage:
        service = MCIScreeningService()
        result = service.analyze(audio_path="audio.wav", transcript="Xin chào...")
    """
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 use_phobert: bool = True):
        """
        Initialize MCI Screening Service
        
        Args:
            model_path: Path to pre-trained prediction model (optional)
                       If None, will auto-detect newest model
            use_phobert: Whether to use PhoBERT for semantic analysis
        """
        self.errors = []
        
        # Auto-detect newest model if not provided
        if model_path is None:
            model_path = self._find_newest_model()
            if model_path:
                logger.info(f"✅ Auto-detected newest model: {model_path}")
        
        # Initialize acoustic analyzer - if import succeeded, must use it
        try:
            self.acoustic_analyzer = AcousticAnalyzer()
            logger.info("✅ AcousticAnalyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AcousticAnalyzer: {e}")
            self.errors.append(f"AcousticAnalyzer: {e}")
            raise  # If import succeeded but init failed, raise error
        
        # Initialize linguistic analyzer - if import succeeded, must use it
        try:
            self.linguistic_analyzer = VietnameseLinguisticAnalyzer(
                use_phobert=use_phobert
            )
            logger.info("✅ LinguisticAnalyzer initialized (underthesea + PhoBERT)")
        except Exception as e:
            logger.error(f"Failed to initialize LinguisticAnalyzer: {e}")
            self.errors.append(f"LinguisticAnalyzer: {e}")
            raise  # If import succeeded but init failed, raise error
        
        # Initialize multimodal fusion - if import succeeded, must use it
        try:
            config = FusionConfig(
                acoustic_weight=0.5,
                linguistic_weight=0.5,
                fusion_method='early',
                normalize=True
            )
            self.fusion = MultimodalFusion(config)
            logger.info("✅ MultimodalFusion initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MultimodalFusion: {e}")
            self.errors.append(f"MultimodalFusion: {e}")
            raise  # If import succeeded but init failed, raise error
        
        # Initialize predictor with auto-detected newest model - if import succeeded, must use it
        try:
            # Auto-detect newest model if not provided
            if model_path is None:
                model_path = self._find_newest_model()
                if model_path:
                    logger.info(f"✅ Auto-detected newest model: {model_path}")
            
            self.predictor = MCIPredictor(model_path)
            logger.info("✅ MCIPredictor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MCIPredictor: {e}")
            self.errors.append(f"MCIPredictor: {e}")
            raise  # If import succeeded but init failed, raise error
        
        logger.info(f"MCIScreeningService initialized (errors: {len(self.errors)})")
    
    def _find_newest_model(self) -> Optional[str]:
        """
        Find the newest model file automatically.
        Priority order:
        1. models/best_model.pkl (newest, 2025-12-16)
        2. model_bundle/model_new_clean/model.pkl (2025-12-11)
        3. model_bundle/model_new/model.pkl (2025-12-11)
        4. models/mci_fusion_model.pkl (if exists)
        """
        from pathlib import Path
        import os
        
        # Get project root (assuming this file is in backend/modules/)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        
        # Priority 1: models/best_model.pkl (newest)
        newest_model = project_root / "models" / "best_model.pkl"
        if newest_model.exists():
            logger.info(f"✅ Found newest model: {newest_model}")
            return str(newest_model)
        
        # Priority 2: model_bundle/model_new_clean/model.pkl
        clean_model = project_root / "model_bundle" / "model_new_clean" / "model.pkl"
        if clean_model.exists():
            logger.info(f"✅ Found clean model: {clean_model}")
            return str(clean_model)
        
        # Priority 3: model_bundle/model_new/model.pkl
        new_model = project_root / "model_bundle" / "model_new" / "model.pkl"
        if new_model.exists():
            logger.info(f"✅ Found new model: {new_model}")
            return str(new_model)
        
        # Priority 4: models/mci_fusion_model.pkl
        fusion_model = project_root / "models" / "mci_fusion_model.pkl"
        if fusion_model.exists():
            logger.info(f"✅ Found fusion model: {fusion_model}")
            return str(fusion_model)
        
        logger.warning("⚠️ No model found, will use default untrained models")
        return None
    
    def _find_newest_model(self) -> Optional[str]:
        """
        Find the newest model file automatically.
        Priority order:
        1. models/best_model.pkl (newest, 2025-12-16)
        2. model_bundle/model_new_clean/model.pkl (2025-12-11)
        3. model_bundle/model_new/model.pkl (2025-12-11)
        4. models/mci_fusion_model.pkl (if exists)
        """
        from pathlib import Path
        import os
        
        # Get project root (assuming this file is in backend/modules/)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        
        # Priority 1: models/best_model.pkl (newest)
        newest_model = project_root / "models" / "best_model.pkl"
        if newest_model.exists():
            return str(newest_model)
        
        # Priority 2: model_bundle/model_new_clean/model.pkl
        clean_model = project_root / "model_bundle" / "model_new_clean" / "model.pkl"
        if clean_model.exists():
            return str(clean_model)
        
        # Priority 3: model_bundle/model_new/model.pkl
        new_model = project_root / "model_bundle" / "model_new" / "model.pkl"
        if new_model.exists():
            return str(new_model)
        
        # Priority 4: models/mci_fusion_model.pkl
        fusion_model = project_root / "models" / "mci_fusion_model.pkl"
        if fusion_model.exists():
            return str(fusion_model)
        
        logger.warning("⚠️ No model found, will use default untrained models")
        return None
    
    def analyze(self, 
                audio_path: Optional[str] = None,
                transcript: Optional[str] = None,
                task_type: Optional[str] = None,
                user_info: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Main analysis function: Perform complete MCI screening
        
        Args:
            audio_path: Path to audio file (WAV, 16kHz recommended)
            transcript: Text transcript of the speech
            task_type: Type of cognitive task ('verbal_fluency', 'picture_description', 
                       'spontaneous_speech', 'qa')
            user_info: Optional user information (age, gender, education)
        
        Returns:
            AnalysisResult: Complete analysis result
        """
        start_time = time.time()
        errors = []
        
        # Initialize empty results
        acoustic_features = {}
        linguistic_features = {}
        fused_features = {}
        mci_prediction = None
        feature_summary = {}
        
        # Default values
        mmse_estimate = 25.0  # Assume normal if no prediction
        severity = "Không xác định"
        confidence = 0.0
        risk_factors = []
        recommendations = []
        
        # Step 1: Acoustic Analysis (if audio provided)
        if audio_path and self.acoustic_analyzer:
            logger.info(f"🎤 Analyzing audio: {audio_path}")
            try:
                acoustic_features = self.acoustic_analyzer.extract_all_features(
                    audio_path, 
                    transcript=transcript
                )
                logger.info(f"✅ Extracted {len(acoustic_features)} acoustic features")
            except Exception as e:
                logger.error(f"Acoustic analysis failed: {e}")
                errors.append(f"Acoustic: {e}")
        elif audio_path:
            logger.warning("Audio provided but AcousticAnalyzer not available")
            errors.append("AcousticAnalyzer not available")
        
        # Step 2: Linguistic Analysis (if transcript provided)
        if transcript and self.linguistic_analyzer:
            logger.info(f"📝 Analyzing transcript ({len(transcript)} chars)")
            try:
                linguistic_features = self.linguistic_analyzer.extract_all_features(
                    transcript,
                    task_type=task_type
                )
                logger.info(f"✅ Extracted {len(linguistic_features)} linguistic features")
            except Exception as e:
                logger.error(f"Linguistic analysis failed: {e}")
                errors.append(f"Linguistic: {e}")
        elif transcript:
            logger.warning("Transcript provided but LinguisticAnalyzer not available")
            errors.append("LinguisticAnalyzer not available")
        
        # Step 3: Multimodal Fusion
        if self.fusion and (acoustic_features or linguistic_features):
            logger.info("🔗 Performing multimodal fusion")
            try:
                fused_features = self.fusion.fuse_features(
                    acoustic_features or {},
                    linguistic_features or {}
                )
                
                # Create feature summary
                feature_summary = self.fusion.create_feature_summary(
                    acoustic_features or {},
                    linguistic_features or {}
                )
                
                logger.info("✅ Fusion complete")
            except Exception as e:
                logger.error(f"Fusion failed: {e}")
                errors.append(f"Fusion: {e}")
        
        # Step 4: MCI Prediction
        if self.predictor and (acoustic_features or linguistic_features):
            logger.info("🧠 Predicting MCI status")
            try:
                # Combine all features for prediction
                all_features = {}
                all_features.update(acoustic_features)
                all_features.update(linguistic_features)
                
                prediction = self.predictor.predict(all_features)
                
                mci_prediction = {
                    'mci_probability': prediction.mci_probability,
                    'mci_class': prediction.mci_class,
                    'mmse_estimate': prediction.mmse_estimate,
                    'confidence': prediction.confidence,
                    'severity': prediction.severity
                }
                
                mmse_estimate = prediction.mmse_estimate
                severity = prediction.severity
                confidence = prediction.confidence
                risk_factors = prediction.risk_factors
                recommendations = prediction.recommendations
                
                logger.info(f"✅ Prediction: {prediction.mci_class}, MMSE ≈ {mmse_estimate:.1f}")
                
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                errors.append(f"Prediction: {e}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"⏱️ Total processing time: {processing_time:.2f}s")
        
        # Determine success
        success = len(errors) == 0 and (acoustic_features or linguistic_features)
        
        return AnalysisResult(
            success=success,
            acoustic_features=acoustic_features,
            linguistic_features=linguistic_features,
            fused_features=fused_features,
            mci_prediction=mci_prediction,
            mmse_estimate=mmse_estimate,
            severity=severity,
            confidence=confidence,
            risk_factors=risk_factors,
            recommendations=recommendations,
            feature_summary=feature_summary,
            processing_time=processing_time,
            errors=errors
        )
    
    def analyze_audio_only(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze audio file only
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            dict: Acoustic features
        """
        if not self.acoustic_analyzer:
            return {'error': 'AcousticAnalyzer not available'}
        
        try:
            return self.acoustic_analyzer.extract_all_features(audio_path)
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_transcript_only(self, transcript: str, 
                                 task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze transcript only
        
        Args:
            transcript: Text transcript
            task_type: Optional task type
        
        Returns:
            dict: Linguistic features
        """
        if not self.linguistic_analyzer:
            return {'error': 'LinguisticAnalyzer not available'}
        
        try:
            return self.linguistic_analyzer.extract_all_features(transcript, task_type)
        except Exception as e:
            return {'error': str(e)}
    
    def get_prediction_only(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Get MCI prediction from pre-extracted features
        
        Args:
            features: Pre-extracted features
        
        Returns:
            dict: Prediction result
        """
        if not self.predictor:
            return {'error': 'MCIPredictor not available'}
        
        try:
            prediction = self.predictor.predict(features)
            return asdict(prediction) if hasattr(prediction, '__dict__') else {
                'mci_probability': prediction.mci_probability,
                'mci_class': prediction.mci_class,
                'mmse_estimate': prediction.mmse_estimate,
                'confidence': prediction.confidence,
                'severity': prediction.severity,
                'risk_factors': prediction.risk_factors,
                'recommendations': prediction.recommendations
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service status
        
        Returns:
            dict: Status of each component
        """
        return {
            'acoustic_analyzer': self.acoustic_analyzer is not None,
            'linguistic_analyzer': self.linguistic_analyzer is not None,
            'multimodal_fusion': self.fusion is not None,
            'mci_predictor': self.predictor is not None,
            'initialization_errors': self.errors,
            'is_ready': (self.acoustic_analyzer is not None or 
                        self.linguistic_analyzer is not None)
        }


# Singleton instance for easy access
_service_instance: Optional[MCIScreeningService] = None


def get_mci_service() -> MCIScreeningService:
    """
    Get or create singleton MCIScreeningService instance
    
    Returns:
        MCIScreeningService: The service instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = MCIScreeningService()
    return _service_instance


def analyze_for_mci(audio_path: Optional[str] = None,
                    transcript: Optional[str] = None,
                    task_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for MCI analysis
    
    Args:
        audio_path: Path to audio file
        transcript: Text transcript
        task_type: Type of cognitive task
    
    Returns:
        dict: Analysis result with convenient access to key metrics
    """
    service = get_mci_service()
    result = service.analyze(audio_path, transcript, task_type)
    
    # Extract MCI probability from prediction
    mci_prob = 0.0
    mci_class = "Unknown"
    if result.mci_prediction:
        mci_prob = result.mci_prediction.get('mci_probability', 0.0)
        mci_class = result.mci_prediction.get('mci_class', 'Unknown')
    
    # Convert to dict with convenient access fields
    return {
        'success': result.success,
        # Convenient access to key metrics
        'mci_probability': mci_prob,
        'mci_class': mci_class,
        'mmse_estimate': result.mmse_estimate,
        'severity': result.severity,
        'confidence': result.confidence,
        # Feature counts
        'acoustic_feature_count': len(result.acoustic_features) if result.acoustic_features else 0,
        'linguistic_feature_count': len(result.linguistic_features) if result.linguistic_features else 0,
        # Full data
        'acoustic_features': result.acoustic_features,
        'linguistic_features': result.linguistic_features,
        'fused_features': result.fused_features,
        'mci_prediction': result.mci_prediction,
        'risk_factors': result.risk_factors,
        'recommendations': result.recommendations,
        'feature_summary': result.feature_summary,
        'processing_time': result.processing_time,
        'errors': result.errors
    }

