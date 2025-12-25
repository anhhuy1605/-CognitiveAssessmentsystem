"""
Vietnamese Cognitive Assessment Backend Package
"""

__version__ = "2.0.0"
__author__ = "Vietnamese AI Team"
__description__ = "Advanced Vietnamese Cognitive Assessment API with ML and Speech Recognition"

from .app import app, cognitive_model, openai_client, VietnameseTranscriber

__all__ = ['app', 'cognitive_model', 'openai_client', 'VietnameseTranscriber']
