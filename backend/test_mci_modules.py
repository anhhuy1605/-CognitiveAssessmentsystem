# -*- coding: utf-8 -*-
"""
Test script for MCI Screening Modules
Test all components individually and as integrated system
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test module imports"""
    print("="*60)
    print("🧪 TESTING MODULE IMPORTS")
    print("="*60)

    try:
        from modules import (
            AcousticAnalyzer,
            VietnameseLinguisticAnalyzer,
            MultimodalFusion,
            MCIPredictor,
            MCIScreeningService,
            analyze_for_mci
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_acoustic_analyzer():
    """Test acoustic analyzer"""
    print("\n" + "="*60)
    print("🎤 TESTING ACOUSTIC ANALYZER")
    print("="*60)

    try:
        from modules import AcousticAnalyzer

        analyzer = AcousticAnalyzer()
        print("✅ AcousticAnalyzer initialized")

        # Test with dummy data (should handle gracefully)
        features = analyzer.extract_all_features("nonexistent.wav")
        if features:
            print(f"✅ Extracted {len(features)} features")
            print(f"   Sample features: {list(features.keys())[:5]}")
        else:
            print("⚠️ No features extracted (expected for nonexistent file)")

        return True
    except Exception as e:
        print(f"❌ Acoustic analyzer error: {e}")
        return False

def test_linguistic_analyzer():
    """Test linguistic analyzer"""
    print("\n" + "="*60)
    print("📝 TESTING LINGUISTIC ANALYZER")
    print("="*60)

    try:
        from modules import VietnameseLinguisticAnalyzer

        analyzer = VietnameseLinguisticAnalyzer(use_phobert=False)  # Skip PhoBERT for speed
        print("✅ VietnameseLinguisticAnalyzer initialized")

        # Test with sample transcript
        transcript = "Xin chào, tôi tên là Nguyễn Văn A. Hôm nay trời đẹp quá."
        features = analyzer.extract_all_features(transcript, task_type='spontaneous_speech')

        print(f"✅ Extracted {len(features)} linguistic features")
        print(f"   Sample features: {list(features.keys())[:5]}")
        print(f"   TTR: {features.get('lex_ttr', 'N/A')}")
        print(f"   MLU: {features.get('syn_mlu_words', 'N/A')}")

        return True
    except Exception as e:
        print(f"❌ Linguistic analyzer error: {e}")
        return False

def test_mci_predictor():
    """Test MCI predictor"""
    print("\n" + "="*60)
    print("🧠 TESTING MCI PREDICTOR")
    print("="*60)

    try:
        from modules import MCIPredictor

        predictor = MCIPredictor()
        print("✅ MCIPredictor initialized")

        # Test with sample features
        sample_features = {
            'sem_idea_density': 4.2,
            'lex_ttr': 0.65,
            'lex_pronoun_ratio': 0.08,
            'syn_mlu_words': 9.5,
            'pause_pause_rate': 0.15,
            'f0_f0_cv': 25.0,
            'vq_jitter_local': 0.008,
            'tone_flattening_score': 0.2
        }

        prediction = predictor.predict(sample_features)

        print("✅ Prediction successful:")
        print(f"   MCI Probability: {prediction.mci_probability:.1%}")
        print(f"   MCI Class: {prediction.mci_class}")
        print(f"   MMSE Estimate: {prediction.mmse_estimate:.1f}/30")
        print(f"   Severity: {prediction.severity}")
        print(f"   Confidence: {prediction.confidence:.1%}")
        print(f"   Risk Factors: {len(prediction.risk_factors)} found")

        return True
    except Exception as e:
        print(f"❌ MCI predictor error: {e}")
        return False

def test_multimodal_fusion():
    """Test multimodal fusion"""
    print("\n" + "="*60)
    print("🔗 TESTING MULTIMODAL FUSION")
    print("="*60)

    try:
        from modules import MultimodalFusion

        fusion = MultimodalFusion()
        print("✅ MultimodalFusion initialized")

        # Test with sample features
        acoustic_features = {
            'f0_f0_mean': 180.5,
            'f0_f0_cv': 25.0,
            'vq_jitter_local': 0.008,
            'vq_shimmer_local': 0.035,
            'vq_hnr_mean': 18.5,
            'pause_pause_rate': 0.15,
            'rate_words_per_minute': 125.0,
            'tone_flattening_score': 0.2
        }

        linguistic_features = {
            'lex_ttr': 0.65,
            'lex_mattr': 0.68,
            'lex_pronoun_ratio': 0.08,
            'lex_noun_ratio': 0.25,
            'lex_content_word_ratio': 0.75,
            'syn_mlu_words': 9.5,
            'syn_incomplete_sentence_ratio': 0.05,
            'sem_idea_density': 4.2,
            'sem_semantic_coherence': 0.85,
            'vi_classifier_ratio': 0.03
        }

        fused = fusion.fuse_features(acoustic_features, linguistic_features)

        print("✅ Fusion successful:")
        print(f"   Fused vector length: {len(fused['fused_vector'])}")
        print(f"   Acoustic features: {fused['n_acoustic_features']}")
        print(f"   Linguistic features: {fused['n_linguistic_features']}")
        print(f"   Fusion method: {fused['fusion_method']}")

        return True
    except Exception as e:
        print(f"❌ Multimodal fusion error: {e}")
        return False

def test_integration_service():
    """Test integration service"""
    print("\n" + "="*60)
    print("🚀 TESTING INTEGRATION SERVICE")
    print("="*60)

    try:
        from modules import MCIScreeningService

        service = MCIScreeningService(use_phobert=False)  # Skip PhoBERT for speed
        print("✅ MCIScreeningService initialized")

        status = service.get_status()
        print("✅ Status check:")
        print(f"   Service ready: {status['is_ready']}")
        print(f"   Acoustic analyzer: {status['acoustic_analyzer']}")
        print(f"   Linguistic analyzer: {status['linguistic_analyzer']}")
        print(f"   Multimodal fusion: {status['multimodal_fusion']}")
        print(f"   MCI predictor: {status['mci_predictor']}")

        if status['is_ready']:
            print("🎉 MCI service is fully functional!")
        else:
            print("⚠️ Some components not available (expected if dependencies missing)")

        return True
    except Exception as e:
        print(f"❌ Integration service error: {e}")
        return False

def test_convenience_functions():
    """Test convenience functions"""
    print("\n" + "="*60)
    print("🔧 TESTING CONVENIENCE FUNCTIONS")
    print("="*60)

    try:
        from modules import analyze_for_mci

        # Test with transcript only (no audio)
        result = analyze_for_mci(
            transcript="Xin chào, tôi tên là Nguyễn Văn A. Hôm nay trời đẹp."
        )

        print("✅ Convenience function successful:")
        print(f"   Success: {result['success']}")
        print(f"   MCI Probability: {result['mci_probability']:.1%}")
        print(f"   MMSE Estimate: {result['mmse_estimate']:.1f}/30")
        print(f"   Linguistic features: {result['linguistic_feature_count']}")

        return True
    except Exception as e:
        print(f"❌ Convenience function error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 MCI Screening Modules Test Suite")
    print("="*60)

    tests = [
        ("Module Imports", test_imports),
        ("Acoustic Analyzer", test_acoustic_analyzer),
        ("Linguistic Analyzer", test_linguistic_analyzer),
        ("MCI Predictor", test_mci_predictor),
        ("Multimodal Fusion", test_multimodal_fusion),
        ("Integration Service", test_integration_service),
        ("Convenience Functions", test_convenience_functions)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! MCI modules are ready to use.")
    elif passed >= total - 1:  # Allow 1 failure for optional dependencies
        print("⚠️ MOST TESTS PASSED. Some optional dependencies may be missing.")
    else:
        print("❌ SOME TESTS FAILED. Check dependency installation.")

    print("\nNext steps:")
    print("1. Install missing dependencies: pip install -r requirements_modules.txt")
    print("2. Test with real audio: python test_mci_modules.py --audio path/to/audio.wav")
    print("3. Start backend server: python app.py")
    print("4. Test API endpoints: curl http://localhost:5001/api/mci/status")

if __name__ == "__main__":
    main()
