#!/usr/bin/env python3
"""
Simple test script để kiểm tra backend
"""

import requests
import json
import time
import os
import tempfile
import numpy as np
import soundfile as sf

def create_simple_audio(duration=2.0, sample_rate=16000):
    """Tạo audio đơn giản để test"""
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, False)
    # Tạo tone 440Hz
    tone = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    # Tạo file tạm
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        sf.write(tmp.name, tone, sample_rate)
        return tmp.name

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_transcribe(audio_file):
    """Test transcription endpoint"""
    print(f"\n🎵 Testing transcription with {audio_file}...")
    try:
        with open(audio_file, 'rb') as f:
            files = {'audio': f}
            data = {'language': 'vi'}
            
            response = requests.post("http://localhost:5001/api/transcribe", 
                                   files=files, data=data, timeout=30)
            
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription successful")
            print(f"Transcript: '{result.get('transcript', 'N/A')}'")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
            print(f"Model: {result.get('model', 'N/A')}")
            return True
        else:
            print(f"❌ Transcription failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return False

def test_assessment(audio_file):
    """Test full assessment endpoint"""
    print(f"\n🧠 Testing full assessment with {audio_file}...")
    try:
        with open(audio_file, 'rb') as f:
            files = {'audio': f}
            data = {'language': 'vi'}
            
            response = requests.post("http://localhost:5001/auto-transcribe", 
                                   files=files, data=data, timeout=60)
            
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Assessment successful")
            
            if 'transcription' in result:
                transcript = result['transcription']
                print(f"Transcript: '{transcript.get('transcript', 'N/A')}'")
                print(f"Confidence: {transcript.get('confidence', 'N/A')}")
            
            if 'audio_features' in result:
                features = result['audio_features']
                print(f"Audio features: {len(features)} features")
            
            if 'ml_prediction' in result:
                ml_pred = result['ml_prediction']
                print(f"ML Score: {ml_pred.get('predicted_score', 'N/A')}")
                print(f"ML Confidence: {ml_pred.get('confidence', 'N/A')}")
            
            if 'final_score' in result:
                print(f"Final Score: {result['final_score']}")
            
            return True
        else:
            print(f"❌ Assessment failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Assessment error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting simple backend test...")
    
    # Test 1: Health check
    if not test_health():
        print("❌ Backend not running or not responding")
        return
    
    # Test 2: Create test audio
    audio_file = create_simple_audio(2.0)
    print(f"📁 Created test audio: {audio_file}")
    
    try:
        # Test 3: Basic transcription
        test_transcribe(audio_file)
        
        # Test 4: Full assessment
        test_assessment(audio_file)
        
    finally:
        # Cleanup
        try:
            os.unlink(audio_file)
            print(f"🗑️ Cleaned up {audio_file}")
        except:
            pass
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
