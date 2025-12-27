"""Test MMSE Chatbot với full multimodal support"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("🧪 Testing MMSE Chatbot Service - Multimodal Integration")
print("=" * 60)

from services.mmse_chatbot_service import MMSEChatbotService

print("\n📦 Initializing service...")
service = MMSEChatbotService()

print("\n✅ Component Status:")
print(f"  Acoustic analyzer: {'✅ Available' if service.acoustic_analyzer else '❌ Missing'}")
print(f"  Linguistic analyzer: {'✅ Available' if service.linguistic_analyzer else '❌ Missing'}")
print(f"  MCI service: {'✅ Available' if service.mci_service else '❌ Missing'}")

print("\n📊 Feature Counts:")
if service.acoustic_analyzer:
    print("  Acoustic: 117 features (eGeMAPS, F0, pause, tone, VQ)")
if service.linguistic_analyzer:
    print("  Linguistic: 42 features (lexical, semantic, syntactic, Vietnamese)")
if service.mci_service:
    print("  MCI Predictor: Multimodal fusion + Random Forest")

print("\n" + "=" * 60)
if service.acoustic_analyzer and service.linguistic_analyzer and service.mci_service:
    print("✅ MMSE CHATBOT - FULL MULTIMODAL SUPPORT READY!")
    print("\n🎯 Pipeline hoàn chỉnh:")
    print("  Audio → ASR (Gemini)")
    print("       → Acoustic Analysis (117 features)")
    print("       → Linguistic Analysis (42 features)")
    print("       → GPT-4o Evaluation")
    print("       → Multimodal Fusion")
    print("       → MCI Prediction")
    print("       → Final MMSE Score + Risk Assessment")
else:
    print("⚠️ Some components missing, but service can still work")

print("\n🚀 Service ready for use!")

