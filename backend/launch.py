#!/usr/bin/env python3
"""
Launcher script for Cognitive Assessment ML with dependency checking
"""

import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['numpy', 'pandas', 'torch', 'whisper', 'librosa', 'soundfile',
                        'transformers', 'sklearn', 'xgboost', 'joblib']

    missing_packages = []
    for package in required_packages:
        try:
            if package == 'sklearn':
                import sklearn
            elif package == 'xgboost':
                import xgboost
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("=" * 60)
        print("❌ MISSING DEPENDENCIES")
        print("The following packages are required but not installed:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n🔧 INSTALLATION OPTIONS:")
        print("1. Automatic installation:")
        print("   python setup_dependencies.py")
        print("\n2. Manual installation:")
        print("   pip install -r requirements.txt")
        print("\n3. Core dependencies only:")
        print("   pip install numpy pandas scikit-learn xgboost torch transformers")
        print("\n📖 See README_SETUP.md for detailed instructions")
        print("=" * 60)
        return False
    return True

def main():
    """Launch the cognitive assessment model."""
    if not check_dependencies():
        print("\n❌ Cannot launch application due to missing dependencies.")
        print("Please install dependencies first, then run:")
        print("   python launch.py")
        sys.exit(1)

    # Import and run the main module
    print("✅ All dependencies found. Launching Cognitive Assessment ML...")
    print()

    # Import the main module (this will work now that dependencies are checked)
    import cognitive_assessment_ml

if __name__ == "__main__":
    main()
