# -*- coding: utf-8 -*-
"""
Test Script for SHAP Explainability Module
==========================================

Tests the complete SHAP pipeline with sample data.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR
sys.path.insert(0, str(PROJECT_ROOT))

# Sample feature data (simulating assessment results)
SAMPLE_AUDIO_FEATURES = {
    'f0_mean': 150.5,
    'f0_std': 25.3,
    'f0_range': 80.2,
    'vq_jitter_local': 1.2,
    'vq_shimmer_local': 3.5,
    'vq_hnr_mean': 15.8,
    'pause_duration_mean': 0.6,
    'pause_ratio': 0.35,
    'rate_syllables_per_sec': 4.2,
    'egemaps_mfcc_1': 0.15,
    'egemaps_mfcc_2': -0.08,
    'egemaps_spectral_centroid': 1200.5
}

SAMPLE_LINGUISTIC_FEATURES = {
    'lex_ttr': 0.65,
    'lex_mattr': 0.62,
    'lex_pronoun_ratio': 0.12,
    'lex_repetition_rate': 0.03,
    'lex_filler_word_ratio': 0.05,
    'syn_mlu': 10.5,
    'syn_avg_sentence_length': 11.2,
    'sem_coherence': 0.75,
    'sem_idea_density': 0.58
}

def test_shap_computation():
    """Test SHAP value computation"""
    print("\n" + "="*60)
    print("TEST 1: SHAP Value Computation")
    print("="*60)
    
    try:
        from modules.shap_explainer import compute_shap_for_assessment
        
        shap_result = compute_shap_for_assessment(
            audio_features=SAMPLE_AUDIO_FEATURES,
            linguistic_features=SAMPLE_LINGUISTIC_FEATURES,
            mmse_score=22
        )
        
        print("✅ SHAP computation successful")
        print(f"   Base value: {shap_result.get('base_value', 0):.2f}")
        print(f"   Prediction: {shap_result.get('prediction', 0):.2f}")
        print(f"   Features analyzed: {len(shap_result.get('feature_contributions', {}))}")
        
        # Show top 5 features
        feature_importance = shap_result.get('feature_importance', {})
        print("\n   Top 5 contributing features:")
        for i, (feat, imp) in enumerate(list(feature_importance.items())[:5], 1):
            contrib = shap_result['feature_contributions'].get(feat, 0)
            print(f"   {i}. {feat[:40]:40s} | Contribution: {contrib:+.3f} | Importance: {imp:.3f}")
        
        return shap_result
        
    except Exception as e:
        print(f"❌ SHAP computation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_explanation_generation(shap_result):
    """Test explanation generation"""
    print("\n" + "="*60)
    print("TEST 2: Explanation Generation")
    print("="*60)
    
    try:
        from modules.explanation_generator import generate_explanation_for_assessment
        
        explanation = generate_explanation_for_assessment(
            audio_features=SAMPLE_AUDIO_FEATURES,
            linguistic_features=SAMPLE_LINGUISTIC_FEATURES,
            mmse_score=22,
            risk_level='mild',
            language='vi'
        )
        
        print("✅ Explanation generation successful")
        print(f"\n   Summary: {explanation.get('summary', '')[:100]}...")
        print(f"   Risk Level: {explanation.get('risk_level', 'unknown')}")
        print(f"   Positive factors: {len(explanation.get('positive_factors', []))}")
        print(f"   Negative factors: {len(explanation.get('negative_factors', []))}")
        print(f"   Recommendations: {len(explanation.get('recommendations', []))}")
        
        # Show top negative factor
        negative_factors = explanation.get('negative_factors', [])
        if negative_factors:
            top_factor = negative_factors[0]
            print(f"\n   Top concern: {top_factor.get('feature_display_name', '')}")
            print(f"   Interpretation: {top_factor.get('interpretation', '')[:80]}...")
        
        return explanation
        
    except Exception as e:
        print(f"❌ Explanation generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_visualizations(shap_result):
    """Test visualization creation"""
    print("\n" + "="*60)
    print("TEST 3: Visualization Creation")
    print("="*60)
    
    try:
        from modules.shap_visualizations import create_all_visualizations
        
        grouped_contributions = shap_result.get('grouped_contributions', {})
        visualizations = create_all_visualizations(
            shap_result=shap_result,
            grouped_contributions=grouped_contributions,
            mmse_score=22,
            language='vi'
        )
        
        print("✅ Visualization creation successful")
        print(f"   Waterfall plot: {'✅' if visualizations.get('waterfall') else '❌'}")
        print(f"   Importance bar: {'✅' if visualizations.get('importance_bar') else '❌'}")
        print(f"   Radar chart: {'✅' if visualizations.get('radar_chart') else '❌'}")
        print(f"   Risk gauge: {'✅' if visualizations.get('risk_gauge') else '❌'}")
        
        return visualizations
        
    except Exception as e:
        print(f"❌ Visualization creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_report_generation(shap_result, explanation, visualizations):
    """Test report generation"""
    print("\n" + "="*60)
    print("TEST 4: Report Generation")
    print("="*60)
    
    try:
        from modules.report_generator import generate_complete_report
        
        # Create output directory
        output_dir = PROJECT_ROOT / 'test_reports'
        output_dir.mkdir(exist_ok=True)
        
        report_package = generate_complete_report(
            audio_features=SAMPLE_AUDIO_FEATURES,
            linguistic_features=SAMPLE_LINGUISTIC_FEATURES,
            mmse_score=22,
            risk_level='mild',
            language='vi',
            output_dir=str(output_dir)
        )
        
        print("✅ Report generation successful")
        print(f"   PDF size: {len(report_package.get('pdf', b''))} bytes")
        print(f"   HTML size: {len(report_package.get('html', ''))} characters")
        print(f"   Summary card: {'✅' if report_package.get('summary_card') else '❌'}")
        print(f"   Reports saved to: {output_dir}")
        
        return report_package
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_validation(shap_result):
    """Test validation"""
    print("\n" + "="*60)
    print("TEST 5: Validation")
    print("="*60)
    
    try:
        from modules.shap_validation import (
            validate_shap_explanations,
            handle_edge_cases,
            generate_alternative_scenarios
        )
        
        # Combine features for X_sample
        X_sample = {}
        X_sample.update(SAMPLE_AUDIO_FEATURES)
        X_sample.update(SAMPLE_LINGUISTIC_FEATURES)
        
        # Validate SHAP values
        validation = validate_shap_explanations(
            shap_result=shap_result,
            X_sample=X_sample,
            tolerance=0.01
        )
        
        print("✅ Validation successful")
        print(f"   Is valid: {'✅' if validation['is_valid'] else '❌'}")
        if validation['errors']:
            print(f"   Errors: {len(validation['errors'])}")
            for error in validation['errors'][:3]:
                print(f"     - {error}")
        if validation['warnings']:
            print(f"   Warnings: {len(validation['warnings'])}")
            for warning in validation['warnings'][:3]:
                print(f"     - {warning}")
        
        # Handle edge cases
        edge_cases = handle_edge_cases(
            shap_result=shap_result,
            X_sample=X_sample,
            audio_metadata={'duration': 25, 'quality': 'good'}
        )
        
        if edge_cases['edge_cases']:
            print(f"\n   Edge cases detected: {edge_cases['edge_cases']}")
        else:
            print("\n   ✅ No edge cases detected")
        
        # Alternative scenarios
        scenarios = generate_alternative_scenarios(shap_result, X_sample, top_k=3)
        print(f"\n   Alternative scenarios: {len(scenarios)}")
        for i, scenario in enumerate(scenarios[:2], 1):
            print(f"   {i}. {scenario.get('interpretation', '')[:60]}...")
        
        return validation
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_pipeline():
    """Test complete pipeline"""
    print("\n" + "="*60)
    print("TEST 6: Full Pipeline Test")
    print("="*60)
    
    try:
        from modules.shap_validation import test_shap_pipeline
        
        results = test_shap_pipeline(
            audio_features=SAMPLE_AUDIO_FEATURES,
            linguistic_features=SAMPLE_LINGUISTIC_FEATURES,
            mmse_score=22,
            risk_level='mild'
        )
        
        print("✅ Full pipeline test completed")
        print(f"   Tests passed: {results.get('tests_passed', 0)}")
        print(f"   Tests failed: {results.get('tests_failed', 0)}")
        print(f"   Performance:")
        for key, value in results.get('performance', {}).items():
            print(f"     - {key}: {value:.2f}s")
        
        if results.get('errors'):
            print(f"\n   Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"     - {error}")
        
        return results
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SHAP EXPLAINABILITY MODULE - TEST SUITE")
    print("="*60)
    
    # Test 1: SHAP computation
    shap_result = test_shap_computation()
    if not shap_result:
        print("\n❌ Cannot continue without SHAP results")
        return
    
    # Test 2: Explanation generation
    explanation = test_explanation_generation(shap_result)
    
    # Test 3: Visualizations
    visualizations = test_visualizations(shap_result)
    
    # Test 4: Report generation
    if explanation and visualizations:
        test_report_generation(shap_result, explanation, visualizations)
    
    # Test 5: Validation
    test_validation(shap_result)
    
    # Test 6: Full pipeline
    test_full_pipeline()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print("\n✅ All tests completed. Check output above for results.")


if __name__ == '__main__':
    main()

