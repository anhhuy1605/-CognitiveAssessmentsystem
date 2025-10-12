#!/usr/bin/env python3
"""
Test script cho improved pipeline với anti-overfitting measures
"""

import os
import sys
import tempfile
import subprocess
import logging
import numpy as np
import pandas as pd

# Install dependencies
print("📦 Installing dependencies...")
try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--quiet",
        "numpy", "pandas", "scikit-learn", "imbalanced-learn", 
        "xgboost", "matplotlib", "joblib"
    ])
except Exception as e:
    print(f"⚠️ Dependency installation failed: {e}")

# Stub heavy dependencies
print("🔧 Setting up stubs...")
from unittest.mock import MagicMock

sys.modules['whisper'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.optim'] = MagicMock()
sys.modules['torch.utils'] = MagicMock()
sys.modules['torch.utils.data'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['librosa'] = MagicMock()
sys.modules['soundfile'] = MagicMock()
sys.modules['webrtcvad'] = MagicMock()
sys.modules['transformers'] = MagicMock()

# Stub NLP
underthesea_mock = MagicMock()
underthesea_mock.word_tokenize = lambda x: x.split()
underthesea_mock.pos_tag = lambda x: [(w, 'N') for w in x.split()]
underthesea_mock.sentiment = lambda x: 'positive'
underthesea_mock.dependency_parse = lambda x: []
sys.modules['underthesea'] = underthesea_mock

jieba_mock = MagicMock()
jieba_mock.lcut = lambda x: x.split()
sys.modules['jieba'] = jieba_mock

# Import our module
try:
    # Import unified clinical model
    from clinical_ml_models import TierOneScreeningModel, TierTwoEnsembleModel

    class EnhancedMultimodalCognitiveModel:
        """Wrapper for backward compatibility"""
        def __init__(self, language='vi', random_state=42, debug=False):
            self.tier1 = TierOneScreeningModel()
            self.tier2 = TierTwoEnsembleModel()
    print("✅ Enhanced model imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def create_realistic_synthetic_data(n_samples=200):
    """Create more realistic synthetic data to test overfitting"""
    np.random.seed(42)
    
    # Create features with some correlation structure
    n_features = 25
    
    # Generate correlated features
    base_features = np.random.randn(n_samples, 5)
    
    # Add noise features
    noise_features = np.random.randn(n_samples, n_features - 5) * 0.5
    
    # Combine features
    X = np.hstack([base_features, noise_features])
    
    # Create realistic target based on some features + noise
    # Classification: based on first 3 features with some noise
    decision_score = (0.5 * X[:, 0] + 0.3 * X[:, 1] - 0.2 * X[:, 2] + 
                     np.random.normal(0, 0.3, n_samples))
    y_class = (decision_score > 0).astype(int)
    
    # Add some label noise to make it more realistic
    flip_indices = np.random.choice(n_samples, size=int(0.05 * n_samples), replace=False)
    y_class[flip_indices] = 1 - y_class[flip_indices]
    
    # MMSE: based on classification + some additional features + noise
    mmse_base = 25 - 8 * y_class  # Dementia patients have lower MMSE
    mmse_adjustment = 0.2 * X[:, 3] - 0.1 * X[:, 4]
    mmse_noise = np.random.normal(0, 2, n_samples)
    y_mmse = np.clip(mmse_base + mmse_adjustment + mmse_noise, 0, 30)
    
    # Create DataFrame
    feature_names = [f'feature_{i}' for i in range(n_features)]
    data = {
        'participant_id': [f'P{i:04d}' for i in range(n_samples)],
        'dx': y_class,
        'mmse': y_mmse,
        'age': np.random.normal(70, 10, n_samples).clip(50, 90),
        'gender': np.random.choice(['M', 'F'], n_samples),
        'education': np.random.normal(12, 3, n_samples).clip(6, 20)
    }
    
    # Add features
    for i, fname in enumerate(feature_names):
        data[fname] = X[:, i]
    
    df = pd.DataFrame(data)
    
    print(f"Created realistic synthetic data: {n_samples} samples")
    print(f"Class distribution: {pd.Series(y_class).value_counts().to_dict()}")
    print(f"MMSE stats: mean={np.mean(y_mmse):.1f}, std={np.std(y_mmse):.1f}")
    
    return df

def test_improved_pipeline():
    """Test the improved pipeline"""
    print("\n🧪 Testing Improved Pipeline...")
    
    # Create realistic synthetic data
    df = create_realistic_synthetic_data(200)
    df.to_csv('realistic_test_data.csv', index=False)
    
    # Initialize model
    model = EnhancedMultimodalCognitiveModel(
        language='vi', 
        random_state=42, 
        debug=False  # Reduce verbosity
    )
    
    print("\n🚀 Training with improved pipeline...")
    
    # Train model
    results = model.train_from_adress_data(
        dx_csv='realistic_test_data.csv',
        validate_data=True
    )
    
    print("\n📊 TRAINING RESULTS:")
    print("="*50)
    
    # Classification results
    clf_results = results['classification']
    print(f"🎯 CLASSIFICATION:")
    print(f"   Best Algorithm: {clf_results['best_algorithm']}")
    print(f"   CV F1: {clf_results['cv_scores']['f1_mean']:.3f} ± {clf_results['cv_scores']['f1_std']:.3f}")
    print(f"   Test Accuracy: {clf_results['test_scores']['accuracy']:.3f}")
    print(f"   Test F1: {clf_results['test_scores']['f1']:.3f}")
    print(f"   Test Precision: {clf_results['test_scores']['precision']:.3f}")
    print(f"   Test Recall: {clf_results['test_scores']['recall']:.3f}")
    print(f"   Test ROC-AUC: {clf_results['test_scores']['roc_auc']:.3f}")
    
    # Algorithm comparison
    print(f"\n   Algorithm Comparison:")
    for alg, metrics in clf_results['algorithm_comparison'].items():
        if 'cv_f1_mean' in metrics:
            print(f"     {alg}: F1 = {metrics['cv_f1_mean']:.3f} ± {metrics['cv_f1_std']:.3f}")
    
    # Regression results
    reg_results = results['regression']
    print(f"\n📈 REGRESSION:")
    print(f"   Best Algorithm: {reg_results['best_algorithm']}")
    print(f"   CV MSE: {reg_results['cv_scores']['mse_mean']:.2f} ± {reg_results['cv_scores']['mse_std']:.2f}")
    print(f"   CV R²: {reg_results['cv_scores']['r2_mean']:.3f}")
    print(f"   Test MSE: {reg_results['test_scores']['mse']:.2f}")
    print(f"   Test MAE: {reg_results['test_scores']['mae']:.2f}")
    print(f"   Test R²: {reg_results['test_scores']['r2']:.3f}")
    print(f"   Test RMSE: {reg_results['test_scores']['rmse']:.2f}")
    
    # Algorithm comparison
    print(f"\n   Algorithm Comparison:")
    for alg, metrics in reg_results['algorithm_comparison'].items():
        if 'cv_mse_mean' in metrics:
            print(f"     {alg}: MSE = {metrics['cv_mse_mean']:.2f}, R² = {metrics['cv_r2_mean']:.3f}")
    
    # Overfitting analysis
    print(f"\n🔍 OVERFITTING ANALYSIS:")
    clf_cv_f1 = clf_results['cv_scores']['f1_mean']
    clf_test_f1 = clf_results['test_scores']['f1']
    clf_gap = clf_cv_f1 - clf_test_f1
    
    reg_cv_mse = reg_results['cv_scores']['mse_mean']
    reg_test_mse = reg_results['test_scores']['mse']
    reg_gap = abs(reg_test_mse - reg_cv_mse) / reg_cv_mse if reg_cv_mse > 0 else 0
    
    print(f"   Classification CV-Test F1 gap: {clf_gap:.3f}")
    print(f"   Regression CV-Test MSE gap: {reg_gap:.1%}")
    
    if abs(clf_gap) < 0.1:
        print("   ✅ Classification: Good generalization (low overfitting)")
    else:
        print("   ⚠️ Classification: Possible overfitting detected")
    
    if reg_gap < 0.2:  # 20% difference
        print("   ✅ Regression: Good generalization (low overfitting)")
    else:
        print("   ⚠️ Regression: Possible overfitting detected")
    
    # Test prediction
    print(f"\n🔮 Testing prediction...")
    pred_result = model.predict_from_audio('test_audio.wav')
    print(f"   Prediction: {pred_result['predictions']['diagnosis']}")
    print(f"   Confidence: {pred_result['predictions']['confidence']:.3f}")
    print(f"   MMSE Predicted: {pred_result['predictions']['mmse_predicted']:.1f}")
    
    # Test save/load
    print(f"\n💾 Testing save/load...")
    model.save_model('improved_model')
    
    new_model = EnhancedMultimodalCognitiveModel()
    new_model.load_model('improved_model')
    print(f"   ✅ Model saved and loaded successfully")
    
    # Generate report
    print(f"\n📋 Generating report...")
    report_path = model.generate_report('improved_pipeline_test', 'json')
    print(f"   Report saved: {report_path}")
    
    print("\n" + "="*50)
    print("🎉 IMPROVED PIPELINE TEST COMPLETED!")
    
    # Final assessment
    if (clf_results['test_scores']['f1'] > 0.5 and 
        clf_results['test_scores']['f1'] < 0.95 and  # Not suspiciously perfect
        reg_results['test_scores']['r2'] > 0.1 and
        abs(clf_gap) < 0.15):
        print("✅ Pipeline shows realistic performance with good generalization!")
    else:
        print("⚠️ Pipeline may still have issues - check results carefully")
    
    return results

if __name__ == "__main__":
    try:
        results = test_improved_pipeline()
        print("\n✨ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        for file in ['realistic_test_data.csv']:
            if os.path.exists(file):
                os.remove(file)
