# -*- coding: utf-8 -*-
"""
Demo script for MCI Screening Modules
Shows how to use the MCI screening system with sample data
"""

import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def demo_linguistic_analysis():
    """Demo linguistic analysis with Vietnamese transcript"""
    print("="*60)
    print("[DEMO] LINGUISTIC ANALYSIS")
    print("="*60)

    from modules import VietnameseLinguisticAnalyzer

    # Sample transcripts for different cognitive states
    transcripts = {
        "Normal": "Xin chao, toi ten la Nguyen Van A. Hom nay troi dep qua. Toi rat vui duoc noi chuyen voi ban.",
        "Mild MCI": "Toi... ten toi la... a... Tran Van B. Toi song o... um... Ha Noi. Thoi tiet... thuong... dep.",
        "Moderate MCI": "Toi... quen roi... ten gi nhi... song o dau... um..."
    }

    analyzer = VietnameseLinguisticAnalyzer(use_phobert=False)  # Skip PhoBERT for demo

    for category, transcript in transcripts.items():
        print(f"\n[{category}] Transcript:")
        print(f"   \"{transcript}\"")
        print("   Analysis:")

        features = analyzer.extract_all_features(transcript, task_type='spontaneous_speech')

        # Key indicators
        ttr = features.get('lex_ttr', 0)
        mattr = features.get('lex_mattr', 0)
        idea_density = features.get('sem_idea_density', 0)
        pronoun_ratio = features.get('lex_pronoun_ratio', 0)
        
        print(f"   TTR: {ttr:.3f}")
        print(f"   MATTR: {mattr:.3f}")
        print(f"   Idea Density: {idea_density:.2f}")
        print(f"   Pronoun Ratio: {pronoun_ratio:.3f}")

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
    print("[DEMO] MCI PREDICTION")
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
        print(f"\n[{patient_type}]:")
        prediction = predictor.predict(features)

        print(f"   MCI Probability: {prediction.mci_probability:.1%}")
        print(f"   MCI Class: {prediction.mci_class}")
        print(f"   MMSE Estimate: {prediction.mmse_estimate:.1f}/30")
        print(f"   Severity: {prediction.severity}")
        print(f"   Confidence: {prediction.confidence:.1%}")

        if prediction.risk_factors:
            print("   Risk Factors:")
            for rf in prediction.risk_factors[:2]:  # Show first 2
                print(f"     - {rf}")

def demo_integration_service():
    """Demo full integration service"""
    print("\n" + "="*60)
    print("[DEMO] INTEGRATION SERVICE")
    print("="*60)

    from modules import MCIScreeningService

    service = MCIScreeningService(use_phobert=False)

    # Test with transcript only (no audio file needed)
    transcript = "Toi thay trong tranh co mot nguoi me dang rua bat. Co hai dua tre dang choi dua. Be trai dung tren ghe lay banh mi."

    print("[Analyzing transcript]:")
    print(f"   \"{transcript}\"")
    print("   (Picture description task)")

    result = service.analyze(
        transcript=transcript,
        task_type='picture_description'
    )

    # Access prediction safely
    mci_prob = 0
    if result.mci_prediction:
        mci_prob = result.mci_prediction.get('mci_probability', 0)

    print("\n[SUCCESS] Analysis Results:")
    print(f"   MCI Probability: {mci_prob:.1%}")
    print(f"   MMSE Estimate: {result.mmse_estimate:.1f}/30")
    print(f"   Severity: {result.severity}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Processing time: {result.processing_time:.2f}s")
    print(f"   Linguistic features: {len(result.linguistic_features) if result.linguistic_features else 0}")
    print(f"   Acoustic features: {len(result.acoustic_features) if result.acoustic_features else 0}")

    if result.recommendations:
        print("   Recommendations:")
        for rec in result.recommendations[:2]:
            print(f"     - {rec}")

def demo_convenience_function():
    """Demo convenience function"""
    print("\n" + "="*60)
    print("[DEMO] CONVENIENCE FUNCTION")
    print("="*60)

    from modules import analyze_for_mci

    # Quick analysis with transcript
    result = analyze_for_mci(
        transcript="Xin chao, toi ten la Nguyen Van A. Hom nay la ngay dep troi. Toi thich di dao trong cong vien.",
        task_type="spontaneous_speech"
    )

    print("[Quick Analysis Result]:")
    print(f"   Success: {result['success']}")
    print(f"   MCI Probability: {result['mci_probability']:.1%}")
    print(f"   MMSE Estimate: {result['mmse_estimate']:.1f}/30")
    print(f"   Severity: {result['severity']}")
    print(f"   Processing time: {result['processing_time']:.2f}s")

def main():
    """Run all demos"""
    print("[MCI Screening Modules - Demo]")
    print("="*60)
    print("This demo shows how to use the MCI screening system")
    print("with Vietnamese language transcripts.\n")

    try:
        demo_linguistic_analysis()
        demo_mci_prediction()
        demo_integration_service()
        demo_convenience_function()

        print("\n" + "="*60)
        print("[SUCCESS] DEMO COMPLETED!")
        print("="*60)
        print("\nTo use with real audio files:")
        print("1. Install full dependencies: pip install -r requirements_modules.txt")
        print("2. Use: service.analyze(audio_path='audio.wav', transcript='text')")
        print("3. For API: Start server and use /api/mci/analyze endpoint")

    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements_modules.txt")
        print("2. Run test script: python test_mci_modules.py")

if __name__ == "__main__":
    main()
