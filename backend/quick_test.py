#!/usr/bin/env python3
"""
Quick test script for backend dual model setup
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test all critical imports."""
    print("🔧 Testing imports...")

    try:
        # Test old model
        import clinical_ml_models
        print("✅ Unified model: clinical_ml_models (2-tier architecture)")

        # Test Flask
        from flask import Flask
        print("✅ Flask available")

        # Test MMSE components
        try:
            from scoring_engine import MMSEScorer
            print("✅ MMSE v2.0: scoring_engine")
        except ImportError:
            print("⚠️  MMSE v2.0: scoring_engine not found")

        try:
            from feature_extraction import FeatureExtractor
            print("✅ MMSE v2.0: feature_extraction")
        except ImportError:
            print("⚠️  MMSE v2.0: feature_extraction not found")

        try:
            from services.mmse_assessment_service import get_mmse_service
            print("✅ MMSE v2.0: mmse_assessment_service")
        except ImportError:
            print("⚠️  MMSE v2.0: mmse_assessment_service not found")

        return True

    except ImportError as e:
        print(f"❌ Critical import failed: {e}")
        return False

def test_files():
    """Test critical files exist."""
    print("\n📁 Checking files...")

    backend_dir = Path(__file__).parent
    files_to_check = [
        "app.py",
        "cognitive_assessment_ml.py",
        "questions.json",
        "services/mmse_assessment_service.py",
        "services/scoring_engine.py",
        "services/feature_extraction.py"
    ]

    all_good = True
    for file_path in files_to_check:
        full_path = backend_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_good = False

    return all_good

def test_mmse_service():
    """Test MMSE service specifically."""
    print("\n🧠 Testing MMSE service...")

    try:
        from services.mmse_assessment_service import get_mmse_service
        service = get_mmse_service()

        # Test basic functionality
        questions = service.get_questions()
        print(f"✅ Questions loaded: {len(questions)} items")

        model_info = service.get_model_info()
        print(f"✅ Model info: {model_info}")

        return True

    except Exception as e:
        print(f"❌ MMSE service failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Backend Dual Model Quick Test")
    print("=" * 40)

    # Check files
    files_ok = test_files()

    # Check imports
    imports_ok = test_imports()

    # Check MMSE service
    mmse_ok = test_mmse_service()

    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST SUMMARY")
    print("=" * 40)
    print(f"Files:        {'✅ OK' if files_ok else '❌ FAILED'}")
    print(f"Imports:      {'✅ OK' if imports_ok else '❌ FAILED'}")
    print(f"MMSE Service: {'✅ OK' if mmse_ok else '❌ FAILED'}")

    if files_ok and imports_ok:
        print("\n🎉 READY TO START BACKEND!")
        print("Run: python start_dual_model.py")
        return True
    else:
        print("\n⚠️  SETUP ISSUES DETECTED")
        print("Please fix the issues above before starting.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
