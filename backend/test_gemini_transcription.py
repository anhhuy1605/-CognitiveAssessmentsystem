#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Gemini Transcription
"""
import os
import sys
import tempfile
import wave
import struct

def create_test_audio(duration=2.0, sample_rate=16000):
    """Create a simple test audio file with a beep"""
    num_samples = int(duration * sample_rate)

    # Generate a simple sine wave (beep sound)
    frequency = 440  # A4 note
    samples = []
    for i in range(num_samples):
        sample = int(32767 * 0.3 * (i / num_samples) * (1 - i / num_samples) * 0.5)  # Fade in/out
        samples.append(sample)

    # WAV file header
    wav_header = struct.pack('<4sL4s4sLHHLLHH4sL',
        b'RIFF',
        36 + len(samples) * 2,  # File size
        b'WAVE',
        b'fmt ',
        16,  # Format chunk size
        1,   # Audio format (PCM)
        1,   # Number of channels
        sample_rate,  # Sample rate
        sample_rate * 2,  # Byte rate
        2,   # Block align
        16,  # Bits per sample
        b'data',
        len(samples) * 2  # Data size
    )

    # Convert samples to bytes
    wav_data = b''.join(struct.pack('<h', sample) for sample in samples)

    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(wav_header + wav_data)
        return f.name

def test_gemini_transcription():
    """Test Gemini transcription with API key"""
    print("🧪 Testing Gemini Transcription")
    print("=" * 50)

    # Check API keys
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not gemini_key:
        print("❌ No Gemini API key found!")
        print("Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
        print("\nExample:")
        print("  export GEMINI_API_KEY='your_api_key_here'")
        print("  # or")
        print("  export GOOGLE_API_KEY='your_api_key_here'")
        return False

    print(f"✅ API key found (length: {len(gemini_key)})")
    print("🔄 Creating test audio file...")

    # Create test audio
    audio_path = create_test_audio(duration=2.0)
    print(f"✅ Created test audio: {audio_path}")

    try:
        # Test transcription
        print("🎵 Testing transcription...")
        from vietnamese_transcriber import RealTimeVietnameseTranscriber, TranscriptionConfig

        config = TranscriptionConfig()
        transcriber = RealTimeVietnameseTranscriber(config)

        result = transcriber.transcribe_audio_file(audio_path, 'vi')

        print("📊 Result:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Transcript: '{result.get('transcript', '')}'")
        print(f"  Confidence: {result.get('confidence', 0.0)}")
        print(f"  Model: {result.get('model', 'unknown')}")

        if result.get('success'):
            print("✅ Gemini transcription is working!")
            return True
        else:
            print(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(audio_path)
            print("🧹 Cleaned up test file")
        except:
            pass

if __name__ == "__main__":
    success = test_gemini_transcription()
    sys.exit(0 if success else 1)
