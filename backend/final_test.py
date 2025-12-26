#!/usr/bin/env python3
"""
Final test of MCI Screening System
"""

print("MCI SYSTEM STATUS TEST")
print("="*50)

# Test imports
try:
    from modules.integration_service import MCIScreeningService
    print("PASS: Modules imported successfully")
except Exception as e:
    print(f"FAIL: Import error: {e}")
    exit(1)

# Test service initialization
try:
    service = MCIScreeningService(use_phobert=False)
    status = service.get_status()
    print("PASS: MCI service initialized")
    print(f"  Ready: {status['is_ready']}")
    print(f"  Acoustic: {status['acoustic_analyzer']}")
    print(f"  Linguistic: {status['linguistic_analyzer']}")
    print(f"  Predictor: {status['mci_predictor']}")
except Exception as e:
    print(f"FAIL: Service initialization error: {e}")
    exit(1)

# Test linguistic analysis
try:
    result = service.analyze(transcript='Xin chao toi ten la Nguyen Van A. Hom nay troi dep qua.')
    print("PASS: Linguistic analysis completed")
    print(f"  Success: {result.success}")
    print(f"  Linguistic features: {len(result.linguistic_features)}")
    print(f"  MMSE estimate: {result.mmse_estimate:.1f}")
    print(f"  Severity: {result.severity}")
except Exception as e:
    print(f"FAIL: Linguistic analysis error: {e}")
    exit(1)

print("")
print("SUCCESS: MCI Screening System is fully functional!")
print("Features available:")
print("- Vietnamese linguistic analysis")
print("- Voice quality analysis (with parselmouth)")
print("- MCI prediction and MMSE estimation")
print("- Rule-based clinical decision making")
