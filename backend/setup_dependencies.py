#!/usr/bin/env python3
"""
Automatic dependency installer for Cognitive Assessment ML
"""

import subprocess
import sys
import os

def install_package(package_name, description=""):
    """Install a Python package using pip."""
    try:
        print(f"Installing {package_name}...{description}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package_name}: {e}")
        return False

def main():
    """Install all required dependencies."""
    print("Cognitive Assessment ML - Dependency Installer")
    print("=" * 50)

    # Core dependencies
    core_packages = [
        ("numpy>=1.21.0", " (numerical computing)"),
        ("pandas>=1.3.0", " (data manipulation)"),
        ("scikit-learn>=1.0.0", " (machine learning)"),
        ("xgboost>=1.5.0", " (gradient boosting)"),
        ("torch>=1.9.0", " (deep learning)"),
        ("transformers>=4.15.0", " (NLP models)"),
        ("joblib>=1.1.0", " (model serialization)"),
    ]

    # Audio processing dependencies
    audio_packages = [
        ("openai-whisper", " (speech recognition)"),
        ("librosa", " (audio processing)"),
        ("soundfile", " (audio file I/O)"),
    ]

    # Optional packages
    optional_packages = [
        ("matplotlib", " (plotting - optional)"),
    ]

    success_count = 0
    total_count = 0

    print("\nInstalling core dependencies...")
    for package, desc in core_packages:
        total_count += 1
        if install_package(package, desc):
            success_count += 1

    print("\nInstalling audio processing dependencies...")
    for package, desc in audio_packages:
        total_count += 1
        if install_package(package, desc):
            success_count += 1

    print("\nInstalling optional dependencies...")
    for package, desc in optional_packages:
        if install_package(package, desc):
            success_count += 1

    print(f"\nInstallation complete: {success_count}/{total_count} packages installed successfully")

    if success_count == total_count:
        print("\n🎉 All dependencies installed! You can now run the cognitive assessment model.")
        print("Run: python cognitive_assessment_ml.py")
    else:
        print(f"\n⚠ {total_count - success_count} packages failed to install.")
        print("You may need to install them manually or check your Python/pip setup.")

if __name__ == "__main__":
    main()
