#!/usr/bin/env python3
"""
Smoke Test cho Enhanced Multimodal Cognitive Assessment Model

Test cơ bản để đảm bảo:
- Class EnhancedMultimodalCognitiveModel được định nghĩa
- Training pipeline hoạt động với synthetic data
- Prediction và save/load model works
- Artifacts được tạo ra
"""

import os
import sys
import tempfile
import shutil
import logging
import numpy as np
import pandas as pd
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_synthetic_data(n_samples=50):
    """Create synthetic CSV data for testing"""
    np.random.seed(42)
    
    # Create synthetic dx-mmse.csv
    dx_data = {
        'participant_id': [f'P{i:03d}' for i in range(n_samples)],
        'dx': np.random.choice(['control', 'dementia'], n_samples),
        'mmse': np.random.normal(20, 5, n_samples).clip(0, 30),
        'age': np.random.normal(70, 10, n_samples).clip(50, 90),
        'gender': np.random.choice(['M', 'F'], n_samples),
        'education': np.random.normal(12, 3, n_samples).clip(6, 20)
    }
    
    # Add random features
    for i in range(20):
        dx_data[f'feature_{i}'] = np.random.randn(n_samples)
    
    dx_df = pd.DataFrame(dx_data)
    
    # Create synthetic progression.csv
    prog_data = {
        'participant_id': [f'P{i:03d}' for i in range(n_samples//2)],  # Only half have progression data
        'progression_score': np.random.randn(n_samples//2),
        'follow_up_months': np.random.randint(6, 36, n_samples//2)
    }
    prog_df = pd.DataFrame(prog_data)
    
    return dx_df, prog_df

def test_class_definition():
    """Test 1: Verify class is defined and importable"""
    print("🧪 Test 1: Class Definition")
    
    try:
        from cognitive_assessment_ml import EnhancedMultimodalCognitiveModel
        
        # Test initialization
        model = EnhancedMultimodalCognitiveModel(language='vi', random_state=42, debug=True)
        
        assert model.language == 'vi'
        assert model.random_state == 42
        assert model.debug == True
        assert model.is_trained == False
        
        print("✅ Class definition test passed")
        return True
        
    except Exception as e:
        print(f"❌ Class definition test failed: {e}")
        return False

def test_training_pipeline():
    """Test 2: Training pipeline with synthetic data"""
    print("\n🧪 Test 2: Training Pipeline")
    
    try:
        from cognitive_assessment_ml import EnhancedMultimodalCognitiveModel
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create synthetic data
            dx_df, prog_df = create_synthetic_data(50)
            
            dx_path = 'synthetic_dx.csv'
            prog_path = 'synthetic_prog.csv'
            
            dx_df.to_csv(dx_path, index=False)
            prog_df.to_csv(prog_path, index=False)
            
            # Initialize and train model
            model = EnhancedMultimodalCognitiveModel(language='vi', random_state=42, debug=False)
            
            results = model.train_from_adress_data(
                dx_csv=dx_path,
                progression_csv=prog_path,
                validate_data=True
            )
            
            # Verify training results
            assert model.is_trained == True
            assert 'classification' in results
            assert 'regression' in results
            assert 'data_info' in results
            
            # Check metrics structure
            clf_metrics = results['classification']
            assert 'test_scores' in clf_metrics
            assert 'f1' in clf_metrics['test_scores']
            assert 'recall' in clf_metrics['test_scores']
            assert 'roc_auc' in clf_metrics['test_scores']
            
            reg_metrics = results['regression']
            assert 'test_scores' in reg_metrics
            assert 'mse' in reg_metrics['test_scores']
            assert 'mae' in reg_metrics['test_scores']
            assert 'r2' in reg_metrics['test_scores']
            
            print("✅ Training pipeline test passed")
            print(f"   - Classification F1: {clf_metrics['test_scores']['f1']:.3f}")
            print(f"   - Regression R²: {reg_metrics['test_scores']['r2']:.3f}")
            
            return True, model
            
    except Exception as e:
        print(f"❌ Training pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_artifacts_generation(model):
    """Test 3: Artifacts generation"""
    print("\n🧪 Test 3: Artifacts Generation")
    
    try:
        # Check if artifacts directory exists
        assert os.path.exists(model.artifacts_path), f"Artifacts directory {model.artifacts_path} not found"
        
        # Check for key artifacts
        expected_artifacts = [
            'confusion_matrix.png',
            'roc_curve.png',
            'mmse_scatter.png',
            'training_results_comprehensive.json'
        ]
        
        for artifact in expected_artifacts:
            artifact_path = os.path.join(model.artifacts_path, artifact)
            assert os.path.exists(artifact_path), f"Artifact {artifact} not found"
            print(f"   ✅ Found: {artifact}")
        
        # Check reports directory
        assert os.path.exists('reports'), "Reports directory not found"
        assert os.path.exists('reports/data_validation_report.json'), "Data validation report not found"
        
        print("✅ Artifacts generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Artifacts generation test failed: {e}")
        return False

def test_save_load_model(model):
    """Test 4: Save and load model"""
    print("\n🧪 Test 4: Save/Load Model")
    
    try:
        # Save model
        model_path = "test_model_bundle"
        saved_path = model.save_model(model_path)
        
        assert os.path.exists(model_path), "Model bundle directory not created"
        assert os.path.exists(os.path.join(model_path, "model_bundle.pkl")), "Model bundle file not found"
        assert os.path.exists(os.path.join(model_path, "metadata.json")), "Metadata file not found"
        
        # Load model in new instance
        new_model = EnhancedMultimodalCognitiveModel()
        new_model.load_model(model_path)
        
        # Verify loaded model
        assert new_model.is_trained == True
        assert new_model.language == model.language
        assert len(new_model.feature_names) == len(model.feature_names)
        assert new_model.classification_pipeline is not None
        assert new_model.regression_pipeline is not None
        
        print("✅ Save/Load model test passed")
        return True, new_model
        
    except Exception as e:
        print(f"❌ Save/Load model test failed: {e}")
        return False, None

def test_prediction(model):
    """Test 5: Prediction functionality"""
    print("\n🧪 Test 5: Prediction")
    
    try:
        # Single prediction (with placeholder audio file)
        result = model.predict_from_audio("dummy_audio.wav")
        
        assert 'audio_file' in result
        assert 'predictions' in result
        assert 'diagnosis' in result['predictions']
        assert 'confidence' in result['predictions']
        assert 'mmse_predicted' in result['predictions']
        
        print(f"   ✅ Single prediction: {result['predictions']['diagnosis']} (conf: {result['predictions']['confidence']:.3f})")
        
        # Batch prediction
        batch_results = model.predict_batch(['audio1.wav', 'audio2.wav'])
        
        assert len(batch_results) == 2
        for batch_result in batch_results:
            assert 'predictions' in batch_result
        
        print(f"   ✅ Batch prediction: {len(batch_results)} results")
        
        print("✅ Prediction test passed")
        return True
        
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        return False

def test_report_generation(model):
    """Test 6: Report generation"""
    print("\n🧪 Test 6: Report Generation")
    
    try:
        # JSON report
        json_report_path = model.generate_report("test_report", "json")
        assert os.path.exists(json_report_path), "JSON report not generated"
        
        # Verify JSON content
        with open(json_report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        assert 'timestamp' in report_data
        assert 'model_info' in report_data
        assert 'performance_metrics' in report_data
        assert 'recommendations' in report_data
        
        print(f"   ✅ JSON report generated: {json_report_path}")
        
        # PDF report (if matplotlib available)
        try:
            pdf_report_path = model.generate_report("test_report", "pdf")
            print(f"   ✅ PDF report generated: {pdf_report_path}")
        except ImportError:
            print("   ⚠️ PDF report skipped (matplotlib not available)")
        
        print("✅ Report generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        return False

def test_standalone_functions():
    """Test 7: Backward compatible standalone functions"""
    print("\n🧪 Test 7: Standalone Functions")
    
    try:
        from cognitive_assessment_ml import train_from_adress_data, predict_from_audio
        
        # Create temp directory for standalone test
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create synthetic data
            dx_df, prog_df = create_synthetic_data(30)
            
            dx_path = 'standalone_dx.csv'
            prog_path = 'standalone_prog.csv'
            
            dx_df.to_csv(dx_path, index=False)
            prog_df.to_csv(prog_path, index=False)
            
            # Test standalone training
            results = train_from_adress_data(dx_path, prog_path, language='vi')
            
            assert 'classification' in results
            assert 'regression' in results
            
            # Test standalone prediction
            prediction = predict_from_audio("dummy.wav", model_path="trained_alzheimer_model")
            assert 'predictions' in prediction
            
            print("✅ Standalone functions test passed")
            return True
            
    except Exception as e:
        print(f"❌ Standalone functions test failed: {e}")
        return False

def run_all_tests():
    """Run all smoke tests"""
    print("🚀 Starting Enhanced Cognitive Assessment ML Smoke Tests")
    print("=" * 70)
    
    tests = [
        test_class_definition,
        test_training_pipeline,
    ]
    
    results = []
    model = None
    
    # Run basic tests
    for test_func in tests:
        if test_func == test_training_pipeline:
            success, model = test_func()
            results.append(success)
        else:
            success = test_func()
            results.append(success)
        
        if not success:
            print(f"\n❌ Test suite stopped due to failure in {test_func.__name__}")
            break
    
    # Run model-dependent tests if training succeeded
    if model is not None and all(results):
        dependent_tests = [
            lambda: test_artifacts_generation(model),
            lambda: test_save_load_model(model),
            lambda: test_report_generation(model),
        ]
        
        for test_func in dependent_tests:
            if test_func.__name__ == '<lambda>':
                if 'save_load' in str(test_func):
                    success, loaded_model = test_func()
                    results.append(success)
                    if success and loaded_model:
                        results.append(test_prediction(loaded_model))
                else:
                    results.append(test_func())
            else:
                results.append(test_func())
    
    # Run standalone tests
    results.append(test_standalone_functions())
    
    # Summary
    print("\n" + "=" * 70)
    print("🏁 SMOKE TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("🎉 Enhanced Cognitive Assessment ML is ready for use!")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("🔧 Please fix issues before using in production")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
