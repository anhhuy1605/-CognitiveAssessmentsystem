# -*- coding: utf-8 -*-
"""
Simple test for acoustic analyzer with parselmouth
"""

import os
import sys
import tempfile
import wave
import struct
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing AcousticAnalyzer with parselmouth...")

try:
    from modules.acoustic_analyzer import AcousticAnalyzer
    print("SUCCESS: AcousticAnalyzer imported")
except ImportError as e:
    print(f"ERROR: Cannot import AcousticAnalyzer: {e}")
    sys.exit(1)

# Test basic import
try:
    import parselmouth
    print("SUCCESS: parselmouth imported")
except ImportError:
    print("ERROR: parselmouth not available")

# Test voice quality (which uses parselmouth)
try:
    analyzer = AcousticAnalyzer()

    # Create a simple WAV file for testing
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name

        # Create 1 second of 440Hz sine wave
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0

        # Generate samples
        samples = []
        for i in range(int(sample_rate * duration)):
            sample = int(32767 * np.sin(2 * np.pi * frequency * i / sample_rate))
            samples.append(struct.pack('<h', sample))

        # Write WAV file
        with wave.open(tmp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(samples))

        print(f"Created test WAV file: {tmp_path}")

        # Test voice quality extraction
        result = analyzer.extract_voice_quality(tmp_path)
        if result:
            print("SUCCESS: Voice quality extraction works")
            print(f"  Jitter: {result.get('jitter_local', 'N/A')}")
            print(f"  Shimmer: {result.get('shimmer_local', 'N/A')}")
            print(f"  HNR: {result.get('hnr_mean', 'N/A')}")
        else:
            print("ERROR: Voice quality extraction failed")

        # Test F0 contour extraction
        f0_result = analyzer.extract_f0_contour(tmp_path)
        if f0_result and f0_result.get('f0_values') is not None:
            print("SUCCESS: F0 contour extraction works")
            print(f"  F0 Mean: {f0_result.get('f0_mean', 'N/A'):.2f}")
            print(f"  F0 CV: {f0_result.get('f0_cv', 'N/A'):.3f}")
        else:
            print("ERROR: F0 contour extraction failed")

        # Clean up
        os.unlink(tmp_path)
        print(f"Cleaned up test file: {tmp_path}")

except Exception as e:
    print(f"ERROR testing acoustic features: {e}")
    import traceback
    traceback.print_exc()

print("AcousticAnalyzer test complete.")
