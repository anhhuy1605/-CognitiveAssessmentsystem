# -*- coding: utf-8 -*-
"""
MCI Screening Modules for Vietnamese Cognitive Assessment

This package contains specialized modules for:
- Acoustic feature extraction (eGeMAPS + Vietnamese tone-specific)
- Linguistic analysis (Vietnamese NLP)
- Multimodal fusion
- MCI prediction and MMSE estimation
- Integration service for unified pipeline

Usage:
    from modules import MCIScreeningService, analyze_for_mci
    
    # Full pipeline
    service = MCIScreeningService()
    result = service.analyze(audio_path="audio.wav", transcript="Xin chào...")
    
    # Or use convenience function
    result = analyze_for_mci(audio_path="audio.wav", transcript="...")
"""

# Import modules - if import succeeds, module will be used (not None)
# If import fails, raise error (no graceful fallback - system requires these modules)
from .acoustic_analyzer import AcousticAnalyzer, extract_acoustic_features
from .linguistic_analyzer import VietnameseLinguisticAnalyzer, extract_linguistic_features
from .multimodal_fusion import MultimodalFusion, FusionConfig, fuse_multimodal_features
from .mci_predictor import MCIPredictor, MCIPrediction, predict_mci, estimate_mmse
from .integration_service import (
    MCIScreeningService, 
    AnalysisResult,
    get_mci_service,
    analyze_for_mci
)

__all__ = [
    # Core analyzers
    'AcousticAnalyzer',
    'VietnameseLinguisticAnalyzer', 
    'MultimodalFusion',
    'MCIPredictor',
    
    # Data classes
    'FusionConfig',
    'MCIPrediction',
    'AnalysisResult',
    
    # Integration
    'MCIScreeningService',
    'get_mci_service',
    
    # Convenience functions
    'extract_acoustic_features',
    'extract_linguistic_features',
    'fuse_multimodal_features',
    'predict_mci',
    'estimate_mmse',
    'analyze_for_mci'
]

__version__ = '1.0.0'

