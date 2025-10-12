#!/usr/bin/env python3
"""
Debug script để kiểm tra từng phần của backend
"""

import os
import sys
import tempfile
import numpy as np
import soundfile as sf

def test_imports():
    """Test imports cơ bản"""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print("✅ Flask imported")
    except Exception as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported")
    except Exception as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    try:
        import librosa
        print("✅ Librosa imported")
    except Exception as e:
        print(f"❌ Librosa import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported")
    except Exception as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    return True

def test_audio_creation():
    """Test tạo audio file"""
    print("\n🎵 Testing audio creation...")
    
    try:
        # Tạo audio đơn giản
        duration = 2.0
        sample_rate = 16000
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)
        tone = 0.3 * np.sin(2 * np.pi * 440 * t)
        
        # Lưu file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, tone, sample_rate)
            audio_file = tmp.name
        
        print(f"✅ Audio file created: {audio_file}")
        return audio_file
        
    except Exception as e:
        print(f"❌ Audio creation failed: {e}")
        return None

def test_openai_transcription(audio_file):
    """Test OpenAI transcription"""
    print(f"\n🤖 Testing OpenAI transcription with {audio_file}...")
    
    try:
        from openai import OpenAI
        
        # Kiểm tra API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not found")
            return None
        
        client = OpenAI(api_key=api_key)
        
        # Transcribe
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="vi",
                response_format="verbose_json"
            )
        
        print(f"✅ Transcription successful: '{transcript.text}'")
        print(f"📊 Confidence: {getattr(transcript, 'confidence', 'N/A')}")
        print(f"⏱️ Duration: {getattr(transcript, 'duration', 'N/A')}")
        
        return transcript.text
        
    except Exception as e:
        print(f"❌ OpenAI transcription failed: {e}")
        return None

def test_audio_features(audio_file):
    """Test audio features extraction"""
    print(f"\n🎵 Testing audio features extraction with {audio_file}...")
    
    try:
        import librosa
        
        # Load audio
        y, sr = librosa.load(audio_file, sr=None)
        
        # Basic features
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Pitch features
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        valid_pitches = pitches[magnitudes > 0.1]
        pitch_mean = np.mean(valid_pitches) if len(valid_pitches) > 0 else 200.0
        pitch_std = np.std(valid_pitches) if len(valid_pitches) > 0 else 50.0
        
        # Energy features
        energy = librosa.feature.rms(y=y)
        energy_mean = np.mean(energy)
        energy_std = np.std(energy)
        
        features = {
            'duration': duration,
            'pitch_mean': pitch_mean,
            'pitch_std': pitch_std,
            'energy_mean': energy_mean,
            'energy_std': energy_std
        }
        
        print(f"✅ Audio features extracted: {len(features)} features")
        for key, value in features.items():
            print(f"   {key}: {value:.3f}")
        
        return features
        
    except Exception as e:
        print(f"❌ Audio features extraction failed: {e}")
        return None

def test_gpt_evaluation(transcript):
    """Test GPT evaluation"""
    print(f"\n🧠 Testing GPT evaluation with transcript: '{transcript}'...")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not found")
            return None
        
        client = OpenAI(api_key=api_key)
        
        # Simple evaluation prompt
        prompt = f"""
        Đánh giá chất lượng của transcript sau đây:
        Transcript: "{transcript}"
        
        Trả về JSON với format:
        {{
            "overall_score": 0-10,
            "clarity": 0-10,
            "completeness": 0-10,
            "comments": "nhận xét ngắn gọn"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia đánh giá chất lượng transcript."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        print(f"✅ GPT evaluation successful: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ GPT evaluation failed: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting debug test...")
    
    # Test 1: Imports
    if not test_imports():
        print("❌ Import test failed")
        return
    
    # Test 2: Audio creation
    audio_file = test_audio_creation()
    if not audio_file:
        print("❌ Audio creation failed")
        return
    
    try:
        # Test 3: OpenAI transcription
        transcript = test_openai_transcription(audio_file)
        
        # Test 4: Audio features
        features = test_audio_features(audio_file)
        
        # Test 5: GPT evaluation (if transcript exists)
        if transcript:
            gpt_result = test_gpt_evaluation(transcript)
        
        print("\n✅ All tests completed successfully!")
        
    finally:
        # Cleanup
        try:
            os.unlink(audio_file)
            print(f"🗑️ Cleaned up {audio_file}")
        except:
            pass

if __name__ == "__main__":
    main()
