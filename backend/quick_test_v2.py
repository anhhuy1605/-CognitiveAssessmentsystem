#!/usr/bin/env python3
"""
Quick Test for Clinical ML Models v2
Unified 2-tier architecture testing
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock heavy dependencies for quick testing
from unittest.mock import MagicMock
sys.modules['torch'] = MagicMock()
sys.modules['librosa'] = MagicMock()
sys.modules['transformers'] = MagicMock()

# Import unified clinical model
from clinical_ml_models import TierOneScreeningModel, TierTwoEnsembleModel

class EnhancedMultimodalCognitiveModel:
    """Wrapper for backward compatibility"""
    def __init__(self, language='vi', random_state=42, debug=False):
        self.tier1 = TierOneScreeningModel()
        self.tier2 = TierTwoEnsembleModel()

def test_v2():
    print("🚀 Testing Clinical ML Models (Unified 2-tier architecture)...")

    # Generate sample data for testing
    import numpy as np
    np.random.seed(42)
    n_samples = 100
    n_features = 20

    X = np.random.randn(n_samples, n_features)
    y_class = np.random.choice([0, 1, 2], n_samples, p=[0.6, 0.3, 0.1])
    y_mmse = np.random.normal(25, 5, n_samples).clip(0, 30)

    print(f"Sample data generated: {X.shape[0]} samples, {X.shape[1]} features")

    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_class_train, y_class_test, y_mmse_train, y_mmse_test = train_test_split(
        X, y_class, y_mmse, test_size=0.2, random_state=42
    )

    print(f"Train: {X_train.shape[0]} samples, Test: {X_test.shape[0]} samples")

    # Test Tier 2 ensemble model
    from clinical_ml_models import TierTwoEnsembleModel
    model = TierTwoEnsembleModel()

    print("Training clinical ML model (Tier 2)...")
    model.fit(X_train, y_class_train, y_mmse_train)

    # Evaluate
    predictions = model.predict(X_test)
    y_pred = predictions['mmse_predictions']

    from sklearn.metrics import mean_absolute_error, r2_score
    mae = mean_absolute_error(y_mmse_test, y_pred)
    r2 = r2_score(y_mmse_test, y_pred)

    print(".3f")
    print(".3f")

    # Test clinical validation
    from clinical_ml_models import ClinicalValidationFramework
    cvf = ClinicalValidationFramework()
    print("Clinical validation framework initialized")

    return model

if __name__ == "__main__":
    test_v2()
    print("✅ Clinical ML models test completed!")