# -*- coding: utf-8 -*-
"""
Demo script for MCI Screening Modules
Shows how to use the MCI screening system with sample data
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def demo_linguistic_analysis():
    """Demo linguistic analysis with Vietnamese transcript"""
    print("="*60)
    print("📝 DEMO: LINGUISTIC ANALYSIS")
    print("="*60)

    from modules import VietnameseLinguisticAnalyzer

    # Sample transcripts for different cognitive states
    transcripts = {
        "Normal": "Xin chào, tôi tên là Nguyễn Văn A. Hôm nay trời đẹp quá. Tôi rất vui được nói chuyện với bạn. Thời tiết Hà Nội thường rất mát mẻ vào buổi sáng.",
        "Mild MCI": "Tôi... tên tôi là... à... Trần Văn B. Tôi sống ở... ừm... Hà Nội. Thời tiết... thường... đẹp.",
        "Moderate MCI": "Tôi... quên rồi... tên gì nhỉ... sống ở đâu... ừm..."
    }

    analyzer = VietnameseLinguisticAnalyzer(use_phobert=False)  # Skip PhoBERT for demo

    for category, transcript in transcripts.items():
        print(f"\n🔍 {category} Transcript:")
        print(f"   \"{transcript}\"")
        print("   Analysis:")

        features = analyzer.extract_all_features(transcript, task_type='spontaneous_speech')

        # Key indicators
        print(".3f")
        print(".3f")
        print(".2f")
        print(".3f")

        # MCI risk assessment
        risk_score = 0
        if features.get('sem_idea_density', 5) < 3.5: risk_score += 1
        if features.get('lex_pronoun_ratio', 0) > 0.15: risk_score += 1
        if features.get('lex_ttr', 0.5) < 0.4: risk_score += 1

        risk_level = "Low" if risk_score == 0 else "Medium" if risk_score == 1 else "High"
        print(f"   MCI Risk: {risk_level}")

def demo_mci_prediction():
    """Demo MCI prediction with sample features"""
    print("\n" + "="*60)
    print("🧠 DEMO: MCI PREDICTION")
    print("="*60)

    from modules import MCIPredictor

    # Sample feature sets representing different patients
    patients = {
        "Healthy Elderly": {
            'sem_idea_density': 4.8,
            'lex_ttr': 0.68,
            'lex_pronoun_ratio': 0.06,
            'syn_mlu_words': 12.5,
            'pause_pause_rate': 0.08,
            'f0_f0_cv': 28.0,
            'vq_jitter_local': 0.005,
            'tone_flattening_score': 0.15
        },
        "MCI Patient": {
            'sem_idea_density': 2.8,
            'lex_ttr': 0.42,
            'lex_pronoun_ratio': 0.18,
            'syn_mlu_words': 6.2,
            'pause_pause_rate': 0.25,
            'f0_f0_cv': 18.5,
            'vq_jitter_local': 0.012,
            'tone_flattening_score': 0.45
        }
    }

    predictor = MCIPredictor()

    for patient_type, features in patients.items():
        print(f"\n🔍 {patient_type}:")
        prediction = predictor.predict(features)

        print(".1%")
        print(f"   MCI Class: {prediction.mci_class}")
        print(".1f")
        print(f"   Severity: {prediction.severity}")
        print(".1%")

        if prediction.risk_factors:
            print("   Risk Factors:")
            for rf in prediction.risk_factors[:2]:  # Show first 2
                print(f"     • {rf}")

def demo_integration_service():
    """Demo full integration service"""
    print("\n" + "="*60)
    print("🚀 DEMO: INTEGRATION SERVICE")
    print("="*60)

    from modules import MCIScreeningService

    service = MCIScreeningService(use_phobert=False)

    # Test with transcript only (no audio file needed)
    transcript = "Tôi thấy trong tranh có một người mẹ đang rửa bát. Có hai đứa trẻ đang chơi đùa. Bé trai đứng trên ghế lấy bánh mì."

    print("🔍 Analyzing transcript:")
    print(f"   \"{transcript}\"")
    print("   (Picture description task)")

    result = service.analyze(
        transcript=transcript,
        task_type='picture_description'
    )

    print("
✅ Analysis Results:"    print(".1%")
    print(".1f")
    print(f"   Severity: {result.severity}")
    print(".1%")
    print(f"   Processing time: {result.processing_time:.2f}s")
    print(f"   Linguistic features: {result.linguistic_feature_count}")
    print(f"   Acoustic features: {result.acoustic_feature_count}")

    if result.recommendations:
        print("   Recommendations:")
        for rec in result.recommendations[:2]:
            print(f"     • {rec}")

def demo_convenience_function():
    """Demo convenience function"""
    print("\n" + "="*60)
    print("🔧 DEMO: CONVENIENCE FUNCTION")
    print("="*60)

    from modules import analyze_for_mci

    # Quick analysis with transcript
    result = analyze_for_mci(
        transcript="Xin chào, tôi tên là Nguyễn Văn A. Hôm nay là ngày đẹp trời. Tôi thích đi dạo trong công viên.",
        task_type="spontaneous_speech"
    )

    print("🔍 Quick Analysis Result:")
    print(f"   Success: {result['success']}")
    print(".1%")
    print(".1f")
    print(f"   Severity: {result['severity']}")
    print(f"   Processing time: {result['processing_time']:.2f}s")

def main():
    """Run all demos"""
    print("🧪 MCI Screening Modules - Demo")
    print("="*60)
    print("This demo shows how to use the MCI screening system")
    print("with Vietnamese language transcripts.\n")

    try:
        demo_linguistic_analysis()
        demo_mci_prediction()
        demo_integration_service()
        demo_convenience_function()

        print("\n" + "="*60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nTo use with real audio files:")
        print("1. Install full dependencies: pip install -r requirements_modules.txt")
        print("2. Use: service.analyze(audio_path='audio.wav', transcript='text')")
        print("3. For API: Start server and use /api/mci/analyze endpoint")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements_modules.txt")
        print("2. Run test script: python test_mci_modules.py")

if __name__ == "__main__":
    main()
