# -*- coding: utf-8 -*-
"""
Test MCI API Endpoints
Test the newly integrated MCI endpoints
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_mci_status():
    """Test MCI status endpoint"""
    print("="*60)
    print("TESTING MCI STATUS ENDPOINT")
    print("="*60)

    try:
        response = requests.get("http://localhost:5001/api/mci/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: MCI Status Response:")
            print(f"   Available: {data.get('available', False)}")
            print(f"   Components: {json.dumps(data.get('components', {}), indent=4)}")
            return True
        else:
            print(f"FAIL: Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Connection error: {e}")
        return False

def test_mci_linguistic():
    """Test MCI linguistic analysis"""
    print("\n" + "="*60)
    print("TESTING MCI LINGUISTIC ANALYSIS")
    print("="*60)

    payload = {
        "transcript": "Xin chào, tôi tên là Nguyễn Văn A. Hôm nay trời đẹp quá. Tôi rất vui được nói chuyện với bạn.",
        "task_type": "spontaneous_speech"
    }

    try:
        response = requests.post(
            "http://localhost:5001/api/mci/linguistic",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Linguistic Analysis Response:")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Features extracted: {data.get('feature_count', 0)}")
            print(f"   Word count: {data.get('word_count', 0)}")

            # Show key features
            key_features = data.get('key_features', {})
            print("   Key Features:")
            for key, value in key_features.items():
                if isinstance(value, float):
                    print(".3f")
                else:
                    print(f"     {key}: {value}")

            return True
        else:
            print(f"FAIL: Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Connection error: {e}")
        return False

def test_mci_predict():
    """Test MCI prediction from features"""
    print("\n" + "="*60)
    print("TESTING MCI PREDICTION")
    print("="*60)

    # Sample features representing MCI patient
    features = {
        'sem_idea_density': 2.8,        # Low idea density (MCI indicator)
        'lex_ttr': 0.42,               # Low vocabulary diversity
        'lex_pronoun_ratio': 0.18,     # High pronoun usage
        'syn_mlu_words': 6.2,          # Short utterances
        'pause_pause_rate': 0.25,      # High pause rate
        'f0_f0_cv': 18.5,              # Low F0 variability (tone flattening)
        'vq_jitter_local': 0.012,      # Increased jitter
        'tone_flattening_score': 0.45  # High tone flattening
    }

    payload = {"features": features}

    try:
        response = requests.post(
            "http://localhost:5001/api/mci/predict",
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: MCI Prediction Response:")
            print(f"   Success: {data.get('success', False)}")
            print(".1%")
            print(f"   MCI Class: {data.get('mci_class', 'Unknown')}")
            print(".1f")
            print(f"   Severity: {data.get('severity', 'Unknown')}")
            print(".1%")

            # Show risk factors
            risk_factors = data.get('risk_factors', [])
            if risk_factors:
                print(f"   Risk Factors ({len(risk_factors)}):")
                for rf in risk_factors:
                    print(f"     - {rf}")

            return True
        else:
            print(f"FAIL: Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Connection error: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint to verify MCI integration"""
    print("\n" + "="*60)
    print("TESTING HEALTH ENDPOINT (with MCI status)")
    print("="*60)

    try:
        response = requests.get("http://localhost:5001/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Health Response:")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Model loaded: {data.get('model_loaded', False)}")

            # Check MCI service
            mci_service = data.get('mci_service', {})
            print(f"   MCI Service Available: {mci_service.get('available', False)}")

            if mci_service.get('available', False):
                components = mci_service.get('components', {})
                print("   MCI Components:")
                for comp, available in components.items():
                    status = "YES" if available else "NO"
                    print(f"     {status} {comp}: {available}")

            return True
        else:
            print(f"FAIL: Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Connection error: {e}")
        return False

def main():
    """Run all API tests"""
    print("TESTING MCI API Endpoints")
    print("="*60)
    print("Testing MCI screening API endpoints...")
    print("Make sure the backend server is running on localhost:5001")
    print()

    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("MCI Status", test_mci_status),
        ("Linguistic Analysis", test_mci_linguistic),
        ("MCI Prediction", test_mci_predict)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"FAIL {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: ALL API TESTS PASSED! MCI endpoints are working correctly.")
    elif passed >= total - 1:
        print("WARNING: MOST TESTS PASSED. Some optional endpoints may need attention.")
    else:
        print("ERROR: SOME TESTS FAILED. Check server logs and endpoint implementations.")

    print("\n" + "="*60)
    print("API Endpoints:")
    print("   GET  /api/health           - Health check with MCI status")
    print("   GET  /api/mci/status       - MCI module availability")
    print("   POST /api/mci/linguistic   - Linguistic feature extraction")
    print("   POST /api/mci/predict      - MCI prediction from features")
    print("   POST /api/mci/analyze      - Full MCI analysis (audio + transcript)")
    print("="*60)

if __name__ == "__main__":
    main()
