"""
Models Package for Cognitive Assessment System
==============================================

This package contains all machine learning models and pipelines for the
Cognitive Assessment System, including:

- Classification models for dementia detection
- Regression models for MMSE prediction (improved v3.0)
- Speech-based models for acoustic analysis
- Validation and evaluation utilities

Updated: September 2025
Version: 3.0 (Improved Regression Models)
"""

# Core models (always available)
from .classification import AdvancedClassificationValidator
from .regression_v3 import RegressionV3Pipeline
from .regression import AdvancedRegressionPipeline

# Optional models (may require additional dependencies)
try:
    from .speech_based_mmse import SpeechBasedMMSESupport
    _speech_available = True
except ImportError:
    _speech_available = False
    SpeechBasedMMSESupport = None

__all__ = [
    'AdvancedClassificationValidator',
    'RegressionV3Pipeline',
    'AdvancedRegressionPipeline',
]

if _speech_available:
    __all__.append('SpeechBasedMMSESupport')

__version__ = "3.0.0"
__updated__ = "2025-09-14"