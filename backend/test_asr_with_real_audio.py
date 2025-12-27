"""Test ASR với audio có giọng nói thực"""
import os
import sys
from vietnamese_transcriber import RealTimeVietnameseTranscriber, TranscriptionConfig

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("🧪 Testing Gemini ASR với audio có giọng nói")
print("=" * 60)

# Check API keys
gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
print(f"Gemini API key: {'✅ SET' if gemini_key else '❌ NOT SET'}")
if gemini_key:
    print(f"Key: {gemini_key[:10]}...{gemini_key[-5:]}")
print()

# Check for existing audio files
audio_files = [
    "fresh_test_1756873289.wav",
    "normal_speech_1756874142.wav",
]

found_audio = None
for audio_file in audio_files:
    if os.path.exists(audio_file):
        found_audio = audio_file
        break

if not found_audio:
    print("❌ Không tìm thấy audio file có giọng nói")
    print()
    print("📝 Để test ASR, bạn cần:")
    print("1. Ghi âm một đoạn giọng nói (VD: 'Xin chào, tôi tên là...')")
    print("2. Lưu file .wav")
    print("3. Chạy lại script này với tên file:")
    print()
    print("   python test_asr_with_real_audio.py path/to/your/audio.wav")
    print()
    print("Hoặc test với backend đang chạy:")
    print("   python app.py")
    print("   Sau đó dùng frontend để record và test")
    sys.exit(0)

print(f"✅ Tìm thấy audio file: {found_audio}")
print(f"🎵 Testing transcription...")
print()

# Create transcriber
config = TranscriptionConfig()
transcriber = RealTimeVietnameseTranscriber(config)

# Transcribe
result = transcriber.transcribe_audio_file(found_audio, language='vi')

print("📊 Transcription Result:")
print(f"  Success: {result.get('success')}")
print(f"  Transcript: '{result.get('transcript')}'")
print(f"  Confidence: {result.get('confidence', 0):.2f}")
print(f"  Model: {result.get('model')}")
print(f"  Processing time: {result.get('processing_time', 0):.2f}s")
print(f"  Original text: '{result.get('original_text', '')}'")
print(f"  Improved text: '{result.get('improved_text', '')}'")
print()

if result.get('error'):
    print(f"  ❌ Error: {result['error']}")
    sys.exit(1)

if result.get('success'):
    print("✅ ASR test PASSED!")
    print()
    print("🎯 Kết luận:")
    print("  - Gemini API key hoạt động tốt")
    print("  - ASR transcription thành công")
    print("  - Hệ thống đã sẵn sàng!")
else:
    print(f"❌ ASR test FAILED: {result.get('error')}")

