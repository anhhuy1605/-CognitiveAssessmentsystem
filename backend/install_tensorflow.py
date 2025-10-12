#!/usr/bin/env python3
"""
Install TensorFlow for Speech-Based MMSE Support

This script installs TensorFlow to enable advanced speech analysis features
that provide additional cognitive assessment insights.
"""

import subprocess
import sys

def install_tensorflow():
    """Install TensorFlow CPU version"""
    print("🔧 Installing TensorFlow for enhanced speech analysis...")
    print("This will enable speech-based MMSE support for better cognitive assessment")

    try:
        # Install TensorFlow CPU version (lighter than GPU version)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tensorflow-cpu"])

        # Verify installation
        import tensorflow as tf
        print(f"✅ TensorFlow {tf.__version__} installed successfully!")
        print("🎉 Speech-based MMSE support is now available")
        print("\n📋 Next steps:")
        print("1. Restart the backend server")
        print("2. The warning will disappear and speech-based MMSE will be active")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install TensorFlow: {e}")
        return False
    except ImportError as e:
        print(f"❌ TensorFlow installation verification failed: {e}")
        return False

if __name__ == "__main__":
    success = install_tensorflow()
    sys.exit(0 if success else 1)
