"""Test ASR với Gemini đơn giản"""
import os
import sys
from vietnamese_transcriber import RealTimeVietnameseTranscriber, TranscriptionConfig
import wave
import numpy as np

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("🧪 Testing Gemini ASR")
print("=" * 60)

# Check API keys
gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
print(f"Gemini API key: {'✅ SET' if gemini_key else '❌ NOT SET'}")
print(f"Key preview: {gemini_key[:10]}..." if gemini_key else "")
print()

# Create test audio file (500Hz tone, 2 seconds)
def create_test_audio(filename, duration=2, sample_rate=16000):
    """Create a simple test audio file"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 500  # Hz
    audio = np.sin(2 * np.pi * frequency * t) * 0.3  # Lower amplitude
    audio = (audio * 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    
    print(f"✅ Created test audio: {filename}")
    return filename

# Test transcription
print("🔧 Creating test audio...")
test_audio = create_test_audio("test_audio_gemini.wav")

print(f"🎵 Testing transcription with Gemini...")
config = TranscriptionConfig()
transcriber = RealTimeVietnameseTranscriber(config)

result = transcriber.transcribe_audio_file(test_audio, language='vi')

print("\n📊 Transcription Result:")
print(f"  Success: {result.get('success')}")
print(f"  Transcript: '{result.get('transcript')}'")
print(f"  Confidence: {result.get('confidence', 0):.2f}")
print(f"  Model: {result.get('model')}")
print(f"  Processing time: {result.get('processing_time', 0):.2f}s")
print(f"  Original text: '{result.get('original_text', '')}'")

if result.get('error'):
    print(f"  ❌ Error: {result['error']}")

# Cleanup
os.remove(test_audio)
print(f"\n🧹 Cleaned up test file")

if result.get('success'):
    print("\n✅ ASR test PASSED")
else:
    print(f"\n❌ ASR test FAILED: {result.get('error')}")

