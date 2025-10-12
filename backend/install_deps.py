#!/usr/bin/env python3
"""
Script cài đặt tất cả dependencies cần thiết cho backend
Chạy một lần duy nhất để tải về tất cả packages
"""

import subprocess
import sys
import os

def install_package(package_name, index_url=None):
    """Cài đặt package với progress bar"""
    print(f"📦 Installing {package_name}...")
    
    cmd = [sys.executable, "-m", "pip", "install", package_name, "--quiet"]
    if index_url:
        cmd.extend(["--index-url", index_url])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ {package_name} installed successfully")
            return True
        else:
            print(f"❌ Failed to install {package_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout installing {package_name}")
        return False
    except Exception as e:
        print(f"❌ Error installing {package_name}: {e}")
        return False

def main():
    print("🚀 Installing Vietnamese Cognitive Assessment Backend Dependencies")
    print("=" * 60)
    
    # Core packages
    core_packages = [
        "flask>=2.3.0",
        "flask-cors>=4.0.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
        "scipy>=1.7.0",
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "openai>=1.0.0",
        "python-dotenv>=0.19.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0"
    ]
    
    # PyTorch packages (CPU version)
    torch_packages = [
        "torch",
        "torchaudio"
    ]
    
    # ML/Audio packages
    ml_packages = [
        "transformers>=4.30.0",
        "noisereduce>=3.0.0",
        "webrtcvad>=2.0.10"
    ]
    
    # Optional packages
    optional_packages = [
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "python-multipart>=0.0.6"
    ]
    
    print("\n📋 Installing core packages...")
    for package in core_packages:
        install_package(package)
    
    print("\n🔥 Installing PyTorch (CPU version)...")
    for package in torch_packages:
        install_package(package, "https://download.pytorch.org/whl/cpu")
    
    print("\n🤖 Installing ML/Audio packages...")
    for package in ml_packages:
        install_package(package)
    
    print("\n⚡ Installing optional packages...")
    for package in optional_packages:
        install_package(package)
    
    print("\n🎉 Installation completed!")
    print("\n📝 Next steps:")
    print("1. Restart your terminal/PowerShell")
    print("2. Run: cd backend && python run.py")
    print("3. Backend will start without downloading packages")

if __name__ == "__main__":
    main()
