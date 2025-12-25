"""
Debug script to check audio features extraction
"""

import os
import sys
import json

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

def debug_audio_features():
    """Debug audio features extraction to see if it's using real data or defaults"""

    try:
        from app import extract_audio_features

        print("🔍 Debugging Audio Features Extraction...")

        # Test with a sample audio file if available
        test_audio_path = "test_audio.wav"  # Replace with actual audio file

        if os.path.exists(test_audio_path):
            print(f"📁 Using existing audio file: {test_audio_path}")
        else:
            print("⚠️ No test audio file found, creating mock test...")

            # Create a mock audio file for testing
            import numpy as np
            import wave
            import struct

            # Generate simple sine wave
            sample_rate = 16000
            duration = 3  # seconds
            frequency = 440  # A4 note
            samples = np.arange(int(duration * sample_rate)) / sample_rate
            waveform = np.sin(2 * np.pi * frequency * samples)

            # Add some silence in middle to simulate 2 utterances
            mid_point = len(waveform) // 2
            waveform[mid_point:mid_point + sample_rate//2] = 0  # 0.5s silence

            # Convert to 16-bit PCM
            waveform_int = np.int16(waveform * 32767)

            # Write WAV file
            with wave.open(test_audio_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(waveform_int.tobytes())

            print(f"🎵 Created test audio file: {test_audio_path}")

        # Extract features
        print("🔧 Extracting audio features...")
        features = extract_audio_features(test_audio_path)

        print("\n✅ Audio Features:")
        for key, value in features.items():
            if isinstance(value, list):
                print(f"   {key}: [{len(value)} items]")
            else:
                print(f"   {key}: {value}")

        # Check if using default values
        default_features = {
            'duration': 10.0,
            'pitch_mean': 200.0,
            'pitch_std': 50.0,
            'tempo': 120.0,
            'silence_mean': 0.5,
            'speech_rate': 2.0,
            'number_utterances': 5,  # This should be different if real extraction works
            'mfcc_mean': [0.0] * 13,
            'spectral_centroid_mean': 1000.0,
            'spectral_rolloff_mean': 2000.0
        }

        print("\n🔍 Checking if using default values...")
        using_defaults = True
        for key in default_features:
            if features.get(key) != default_features[key]:
                using_defaults = False
                print(f"   ❌ {key}: {features.get(key)} (real) ≠ {default_features[key]} (default)")
            else:
                print(f"   ✅ {key}: {features.get(key)} (matches default)")

        if using_defaults:
            print("❌ BACKEND IS USING DEFAULT VALUES!")
        else:
            print("✅ BACKEND IS USING REAL AUDIO FEATURES!")

        # Clean up
        if os.path.exists(test_audio_path):
            os.remove(test_audio_path)
            print(f"🗑️ Cleaned up test file: {test_audio_path}")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_audio_features()
