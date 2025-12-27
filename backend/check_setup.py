"""Kiểm tra setup của hệ thống"""
import os
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("🔍 Kiểm tra cấu hình hệ thống")
print("=" * 60)

# Check Gemini API key
gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if gemini_key:
    print(f"✅ Gemini API key: {gemini_key[:10]}...{gemini_key[-5:]}")
else:
    print("❌ Gemini API key: CHƯA CÓ")
    print("\n📝 Để set Gemini API key:")
    print("   Cách 1: Chạy script tự động")
    print("      cd D:\\CognitiveAssessmentsystem\\backend")
    print("      .\\set_gemini_key.ps1")
    print("\n   Cách 2: Set thủ công")
    print("      $env:GEMINI_API_KEY=\"YOUR_KEY_HERE\"")
    print("\n   Lấy key tại: https://aistudio.google.com/app/apikey")

print()

# Check OpenAI API key
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"✅ OpenAI API key: {openai_key[:10]}...{openai_key[-5:]}")
else:
    print("⚠️ OpenAI API key: CHƯA CÓ (cần cho MMSE evaluation)")
    print("\n📝 Để set OpenAI API key:")
    print("      $env:OPENAI_API_KEY=\"YOUR_KEY_HERE\"")
    print("\n   Lấy key tại: https://platform.openai.com/api-keys")

print()

# Check VnCoreNLP
vncorenlp_jar = "D:\\CognitiveAssessmentsystem\\backend\\VnCoreNLP\\VnCoreNLP-1.2.jar"
if os.path.exists(vncorenlp_jar):
    print(f"✅ VnCoreNLP: Đã cài đặt")
else:
    print("⚠️ VnCoreNLP: Chưa cài (optional, cho linguistic analysis)")
    print("   Chạy: powershell -ExecutionPolicy Bypass -File install_vncorenlp.ps1")

print()

# Check Java
try:
    import subprocess
    result = subprocess.run(['java', '-version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version_line = result.stderr.split('\n')[0] if result.stderr else ""
        print(f"✅ Java: {version_line}")
    else:
        print("⚠️ Java: Không tìm thấy (cần cho VnCoreNLP)")
except Exception as e:
    print("⚠️ Java: Không tìm thấy (cần cho VnCoreNLP)")

print()

# Summary
print("=" * 60)
if gemini_key and openai_key:
    print("✅ Hệ thống đã sẵn sàng!")
    print("   Chạy test: python test_asr_simple.py")
elif gemini_key:
    print("⚠️ Cần thêm OpenAI API key cho MMSE evaluation")
    print("   ASR vẫn hoạt động bình thường")
else:
    print("❌ Cần setup Gemini API key trước")
    print("   Chạy: .\\set_gemini_key.ps1")

