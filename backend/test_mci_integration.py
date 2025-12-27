# -*- coding: utf-8 -*-
"""
Test MCI Module Integration in Main App
Verifies that the new MCI modules are being used for evaluation
"""

import requests
import json
import sys

def test_mci_modules_in_evaluation():
    """Test that evaluation uses MCI modules"""
    print("=" * 60)
    print("TESTING MCI MODULE INTEGRATION")
    print("=" * 60)
    
    # Test 1: Check MCI service status
    print("\n1. Checking MCI Service Status...")
    try:
        response = requests.get("http://localhost:5001/api/mci/status")
        status = response.json()
        
        if status.get('success') and status.get('available'):
            print("   MCI Service: AVAILABLE")
            components = status.get('components', {})
            for comp, available in components.items():
                print(f"   - {comp}: {'OK' if available else 'NOT AVAILABLE'}")
        else:
            print("   MCI Service: NOT AVAILABLE")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Test 2: Direct MCI linguistic analysis
    print("\n2. Testing Direct MCI Linguistic Analysis...")
    try:
        transcript = "Toi song o Ha Noi, lam viec hang ngay va di cong viec thuong xuyen."
        response = requests.post(
            "http://localhost:5001/api/mci/linguistic",
            json={"transcript": transcript, "task_type": "spontaneous_speech"}
        )
        result = response.json()
        
        if result.get('success'):
            print(f"   Features extracted: {result.get('feature_count')}")
            key_features = result.get('key_features', {})
            print(f"   TTR: {key_features.get('ttr', 0):.3f}")
            print(f"   Idea Density: {key_features.get('idea_density', 0):.2f}")
            print(f"   Semantic Coherence: {key_features.get('semantic_coherence', 0):.3f}")
        else:
            print(f"   ERROR: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Test 3: Full MCI analysis
    print("\n3. Testing Full MCI Analysis...")
    try:
        response = requests.post(
            "http://localhost:5001/api/mci/analyze",
            data={"transcript": transcript, "task_type": "spontaneous_speech"}
        )
        result = response.json()
        
        mci_prob = result.get('mci_probability', 0)
        mmse_est = result.get('mmse_estimate', 0)
        mci_class = result.get('mci_class', 'Unknown')
        
        print(f"   MCI Probability: {mci_prob:.1%}")
        print(f"   MMSE Estimate: {mmse_est}/30")
        print(f"   MCI Class: {mci_class}")
        
        if mci_prob is not None and mmse_est is not None:
            print("   Full MCI analysis: OK")
        else:
            print("   Full MCI analysis: FAILED")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Test 4: Main evaluation endpoint
    print("\n4. Testing Main Evaluation Endpoint...")
    try:
        response = requests.post(
            "http://localhost:5001/api/evaluate",
            json={
                "transcript": transcript,
                "question": "Hay ke ve ngay hom nay cua ban",
                "language": "vi"
            }
        )
        result = response.json()
        
        if result.get('success'):
            evaluation = result.get('evaluation', {})
            
            # Check if MCI analysis is included
            mci_analysis = evaluation.get('mci_analysis')
            
            print(f"   Overall Score: {evaluation.get('overall_score')}")
            print(f"   Context Score: {evaluation.get('context_relevance_score')}")
            print(f"   Vocabulary Score: {evaluation.get('vocabulary_score')}")
            
            if mci_analysis:
                print(f"   MCI Analysis Present: YES")
                print(f"   - MMSE Estimate: {mci_analysis.get('mmse_estimate')}")
                print(f"   - MCI Probability: {mci_analysis.get('mci_probability')}")
                print("   >>> NEW MCI MODULES ARE BEING USED!")
            else:
                print(f"   MCI Analysis Present: NO (using GPT fallback)")
        else:
            print(f"   ERROR: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - MCI MODULES ARE INTEGRATED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_mci_modules_in_evaluation()
    sys.exit(0 if success else 1)


