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

# Import with graceful fallback for missing dependencies
try:
    from .acoustic_analyzer import AcousticAnalyzer, extract_acoustic_features
except ImportError:
    AcousticAnalyzer = None
    extract_acoustic_features = None

try:
    from .linguistic_analyzer import VietnameseLinguisticAnalyzer, extract_linguistic_features
except ImportError:
    VietnameseLinguisticAnalyzer = None
    extract_linguistic_features = None

try:
    from .multimodal_fusion import MultimodalFusion, FusionConfig, fuse_multimodal_features
except ImportError:
    MultimodalFusion = None
    FusionConfig = None
    fuse_multimodal_features = None

try:
    from .mci_predictor import MCIPredictor, MCIPrediction, predict_mci, estimate_mmse
except ImportError:
    MCIPredictor = None
    MCIPrediction = None
    predict_mci = None
    estimate_mmse = None

try:
    from .integration_service import (
        MCIScreeningService, 
        AnalysisResult,
        get_mci_service,
        analyze_for_mci
    )
except ImportError:
    MCIScreeningService = None
    AnalysisResult = None
    get_mci_service = None
    analyze_for_mci = None

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

