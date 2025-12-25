#!/usr/bin/env python3
"""Check package availability"""

import sys
print(f"Python version: {sys.version}")

packages_to_check = ['tensorflow', 'torch', 'librosa', 'soundfile', 'sklearn', 'scipy', 'pandas', 'numpy']

for package in packages_to_check:
    try:
        __import__(package)
        print(f"✅ {package}: installed")
    except ImportError:
        print(f"❌ {package}: not installed")

# Check specific TensorFlow version if available
try:
    import tensorflow as tf
    print(f"📦 TensorFlow version: {tf.__version__}")
except ImportError:
    print("⚠️ TensorFlow not available")

print("\nNote: TensorFlow warning is non-critical - the app runs without speech-based MMSE support")
