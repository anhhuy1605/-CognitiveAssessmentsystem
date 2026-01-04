# -*- coding: utf-8 -*-
"""
Comprehensive Results Robustness Test
======================================
Test comprehensive results generation với nhiều edge cases để đảm bảo không crash
"""

import sys
import os
import json
import traceback
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.mmse_chatbot_service import MMSEChatbotService, SessionState
from services.comprehensive_results_generator import generate_comprehensive_results

def test_case(name, session_state_factory, expected_success=True):
    """Run a test case"""
    print(f"\n{'='*80}")
    print(f"TEST CASE: {name}")
    print(f"{'='*80}")
    
    try:
        chatbot_service = MMSEChatbotService()
        session_id = f"test_robust_{int(datetime.now().timestamp())}"
        
        # Create session state
        state = session_state_factory(session_id, chatbot_service)
        
        # Generate comprehensive results
        results = generate_comprehensive_results(session_state=state, shap_explanations=None)
        
        # Validate structure
        required_sections = [
            'assessment_result',
            'feature_summary',
            'detailed_analysis',
            'multimodal_analysis',
            'shap_explanation',
            'recommendations',
            'citations',
            'clinical_interpretation',
            'metadata'
        ]
        
        missing_sections = [s for s in required_sections if s not in results]
        
        if missing_sections:
            print(f"  [FAIL] Missing sections: {missing_sections}")
            return False
        
        # Check that all sections are non-None
        for section in required_sections:
            if results[section] is None:
                print(f"  [FAIL] Section '{section}' is None")
                return False
        
        print(f"  [PASS] All {len(required_sections)} sections present")
        print(f"  [PASS] Metadata: session_id={results['metadata'].get('session_id')}, version={results['metadata'].get('version')}")
        
        return True
        
    except Exception as e:
        if expected_success:
            print(f"  [FAIL] Unexpected exception: {type(e).__name__}: {e}")
            traceback.print_exc()
            return False
        else:
            print(f"  [PASS] Expected exception caught: {type(e).__name__}")
            return True


def test_case_1_minimal(session_id, service):
    """Test 1: Minimal session - chỉ có MMSE score, không có features"""
    state = service.create_session(session_id, {'age': 65, 'gender': 'male'})
    state.total_score = 28
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {}
    state.acoustic_features = {}
    state.linguistic_features = {}
    state.mci_result = None
    return state


def test_case_2_no_user_info(session_id, service):
    """Test 2: Session không có user_info"""
    state = service.create_session(session_id, None)
    state.total_score = 25
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 8}
    state.acoustic_features = {}
    state.linguistic_features = {}
    state.mci_result = {'risk_level': 'on', 'combined_risk_score': 0.3}
    # Remove user_info
    state.user_info = None if hasattr(state, 'user_info') else {}
    return state


def test_case_3_invalid_user_info(session_id, service):
    """Test 3: User info với invalid types"""
    state = service.create_session(session_id, {
        'age': 'invalid',  # Should be int
        'gender': None,  # None value
        'education_years': 'twelve'  # Should be int
    })
    state.total_score = 24
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 7, 'recall': 1}
    state.acoustic_features = {'q1': {'jitter': 0.015}}
    state.linguistic_features = {'TTR': 0.55}
    state.mci_result = {'risk_level': 'nguy_co_nhe', 'combined_risk_score': 0.55}
    return state


def test_case_4_missing_domain_scores(session_id, service):
    """Test 4: Missing domain_scores"""
    state = service.create_session(session_id, {'age': 70, 'gender': 'female'})
    state.total_score = 22
    state.completed_at = datetime.now().isoformat()
    # Don't set domain_scores
    state.acoustic_features = {'q1': {'pause_rate': 0.45, 'jitter': 0.025}}
    state.linguistic_features = {'TTR': 0.42, 'idea_density': 0.38}
    state.mci_result = {'risk_level': 'nguy_co_cao', 'combined_risk_score': 0.72}
    return state


def test_case_5_invalid_feature_values(session_id, service):
    """Test 5: Feature values với invalid types (None, string, etc.)"""
    state = service.create_session(session_id, {'age': 75, 'gender': 'male'})
    state.total_score = 26
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 9, 'recall': 2}
    
    # Invalid feature values
    state.acoustic_features = {
        'q1': {
            'jitter': None,  # None value
            'shimmer': 'invalid',  # String instead of float
            'pause_rate': 0.35,  # Valid
            'hnr': float('inf'),  # Infinity
            'f0_mean': float('nan')  # NaN
        }
    }
    state.linguistic_features = {
        'TTR': None,  # None
        'MLU': 'five',  # String
        'idea_density': 0.50  # Valid
    }
    state.mci_result = {'risk_level': 'on', 'combined_risk_score': 0.4}
    return state


def test_case_6_empty_mci_result(session_id, service):
    """Test 6: MCI result rỗng hoặc incomplete"""
    state = service.create_session(session_id, {'age': 68, 'gender': 'female'})
    state.total_score = 27
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 10, 'language': 7}
    state.acoustic_features = {'q1': {'speaking_rate': 120.0}}
    state.linguistic_features = {'TTR': 0.65}
    state.mci_result = {}  # Empty dict
    return state


def test_case_7_missing_total_score(session_id, service):
    """Test 7: Missing total_score"""
    state = service.create_session(session_id, {'age': 72, 'gender': 'male'})
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 8}
    state.acoustic_features = {}
    state.linguistic_features = {}
    state.mci_result = None
    # Don't set total_score
    return state


def test_case_8_very_large_values(session_id, service):
    """Test 8: Very large feature values"""
    state = service.create_session(session_id, {'age': 65, 'gender': 'female'})
    state.total_score = 30
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 10}
    state.acoustic_features = {
        'q1': {
            'jitter': 1e10,  # Very large
            'pause_rate': 1000.0,  # Unrealistic but should not crash
            'speaking_rate': 1e6
        }
    }
    state.linguistic_features = {
        'TTR': 999.0,  # Unrealistic
        'MLU': 1e5
    }
    state.mci_result = {'risk_level': 'on', 'combined_risk_score': 0.2}
    return state


def test_case_9_nested_errors(session_id, service):
    """Test 9: Nested dict structures với errors"""
    state = service.create_session(session_id, {'age': 70, 'gender': 'male'})
    state.total_score = 23
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {'orientation': 7}
    
    # Nested structures that might cause issues
    state.acoustic_features = {
        'q1': {
            'jitter': 0.020,
            'nested': {'invalid': 'structure'}  # Unexpected nested structure
        },
        'q2': []  # List instead of dict
    }
    state.linguistic_features = {
        'TTR': 0.48,
        'nested_list': [1, 2, 3]  # List value
    }
    state.mci_result = {
        'risk_level': 'nguy_co_nhe',
        'risk_components': {
            'mmse': 'invalid',  # Should be float
            'acoustic': None
        }
    }
    return state


def test_case_10_full_valid(session_id, service):
    """Test 10: Full valid session - để so sánh"""
    state = service.create_session(session_id, {
        'age': 72,
        'gender': 'female',
        'education_years': 10
    })
    state.total_score = 24
    state.completed_at = datetime.now().isoformat()
    state.domain_scores = {
        'orientation': 8,
        'registration': 2,
        'attention_calculation': 3,
        'executive_function': 2,
        'recall': 1,
        'language': 6,
        'visuospatial': 2
    }
    state.acoustic_features = {
        'q1': {
            'jitter': 0.025,
            'shimmer': 0.065,
            'hnr': 11.5,
            'pause_rate': 0.45,
            'speaking_rate': 95.0,
            'f0_mean': 185.0,
            'f0_cv': 0.08
        }
    }
    state.linguistic_features = {
        'TTR': 0.42,
        'pronoun_ratio': 0.38,
        'idea_density': 0.38,
        'MLU': 5.5
    }
    state.mci_result = {
        'combined_risk_score': 0.65,
        'risk_level': 'nguy_co_nhe',
        'risk_components': {
            'mmse': 0.25,
            'acoustic': 0.22,
            'linguistic': 0.18
        }
    }
    return state


def run_all_tests():
    """Run all test cases"""
    print("="*80)
    print("COMPREHENSIVE RESULTS ROBUSTNESS TEST SUITE")
    print("="*80)
    
    test_cases = [
        ("Minimal Session (no features)", test_case_1_minimal, True),
        ("No User Info", test_case_2_no_user_info, True),
        ("Invalid User Info Types", test_case_3_invalid_user_info, True),
        ("Missing Domain Scores", test_case_4_missing_domain_scores, True),
        ("Invalid Feature Values", test_case_5_invalid_feature_values, True),
        ("Empty MCI Result", test_case_6_empty_mci_result, True),
        ("Missing Total Score", test_case_7_missing_total_score, True),
        ("Very Large Values", test_case_8_very_large_values, True),
        ("Nested Errors", test_case_9_nested_errors, True),
        ("Full Valid Session", test_case_10_full_valid, True),
    ]
    
    results = []
    for name, factory, expected_success in test_cases:
        try:
            result = test_case(name, factory, expected_success)
            results.append((name, result))
        except Exception as e:
            print(f"  [ERROR] TEST FRAMEWORK ERROR: {e}")
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! System is robust.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)

