#!/usr/bin/env python3
"""
Complete Pipeline Test Script
=============================

Tests the entire cognitive assessment pipeline from audio processing to completion
"""

import requests
import time
import json
import os
from pathlib import Path

def test_pipeline_health():
    """Test pipeline health check"""
    print("🔍 Testing Pipeline Health...")
    try:
        response = requests.get('http://localhost:5001/api/health/pipeline')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pipeline Health: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def create_test_audio():
    """Create a simple test audio file"""
    print("🎵 Creating test audio file...")
    try:
        import numpy as np
        import soundfile as sf

        # Generate a simple 3-second sine wave
        sample_rate = 16000
        duration = 3
        frequency = 440  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(frequency * 2 * np.pi * t)

        test_audio_path = Path("test_audio.wav")
        # Use soundfile for better compatibility
        sf.write(test_audio_path, audio, sample_rate, subtype='PCM_16')

        print(f"✅ Test audio created: {test_audio_path}")
        return test_audio_path

    except Exception as e:
        print(f"❌ Failed to create test audio: {e}")
        return None

def test_audio_processing():
    """Test audio processing pipeline"""
    print("🎤 Testing Audio Processing...")

    # Create test audio
    audio_path = create_test_audio()
    if not audio_path or not audio_path.exists():
        print("❌ Test audio not available")
        return False

    try:
        # Prepare form data
        with open(audio_path, 'rb') as f:
            files = {
                'audio': ('test_audio.wav', f, 'audio/wav')
            }
            data = {
                'questionId': 'TEST_Q1',
                'sessionId': 'test_session_pipeline'
            }

            response = requests.post(
                'http://localhost:5001/api/audio/process',
                files=files,
                data=data
            )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Audio processing successful")
            print(f"   Transcript: {result.get('transcript', 'N/A')[:50]}...")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Temp ID: {result.get('tempId', 'N/A')}")
            return True
        else:
            print(f"❌ Audio processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        return False
    finally:
        # Cleanup
        if audio_path and audio_path.exists():
            audio_path.unlink()

def test_assessment_completion():
    """Test assessment completion"""
    print("🎯 Testing Assessment Completion...")

    try:
        payload = {
            'sessionId': 'test_session_pipeline',
            'mode': 'personal'
        }

        response = requests.post(
            'http://localhost:5001/api/assessment/complete',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Assessment completion successful")
            print(f"   Mode: {payload['mode']}")
            print(f"   Redirect: {result.get('result', {}).get('redirect', 'N/A')}")
            return True
        else:
            print(f"❌ Assessment completion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Assessment completion error: {e}")
        return False

def test_results_retrieval():
    """Test results retrieval"""
    print("📊 Testing Results Retrieval...")

    try:
        response = requests.get('http://localhost:5001/api/results/test_session_pipeline')

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                data = result.get('data', {})
                report = data.get('comprehensiveReport', {})
                print(f"✅ Results retrieval successful")
                print(f"   MMSE Score: {report.get('mmseScore', 'N/A')}")
                print(f"   Cognitive Level: {report.get('cognitiveLevel', 'N/A')}")
                print(f"   Total Questions: {report.get('questions', []).__len__()}")
                return True
            else:
                print(f"❌ Results retrieval API error: {result.get('error')}")
                return False
        else:
            print(f"❌ Results retrieval failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Results retrieval error: {e}")
        return False

def test_stats_api():
    """Test stats API"""
    print("📈 Testing Stats API...")

    try:
        # Test session stats
        response = requests.get('http://localhost:5001/api/stats/session/test_session_pipeline')

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                data = result.get('data', {})
                print(f"✅ Session stats retrieval successful")
                print(f"   Session ID: {data.get('sessionId', 'N/A')}")
                print(f"   Mode: {data.get('mode', 'N/A')}")
                print(f"   Total Questions: {data.get('totalQuestions', 'N/A')}")
                return True
            else:
                print(f"❌ Session stats API error: {result.get('error')}")
                return False
        else:
            print(f"❌ Session stats failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Stats API error: {e}")
        return False

def main():
    """Run complete pipeline test"""
    print("=" * 60)
    print("🧠 COGNITIVE ASSESSMENT PIPELINE - COMPLETE TEST")
    print("=" * 60)

    tests = [
        ("Pipeline Health", test_pipeline_health),
        ("Audio Processing", test_audio_processing),
        ("Assessment Completion", test_assessment_completion),
        ("Results Retrieval", test_results_retrieval),
        ("Stats API", test_stats_api),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'-'*20} {test_name} {'-'*20}")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Pipeline is fully operational!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
