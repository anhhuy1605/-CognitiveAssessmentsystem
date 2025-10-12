# Install TensorFlow for speech-based MMSE support (optional)
# This script installs TensorFlow and enables advanced speech analysis features

Write-Host "🔧 Installing TensorFlow for enhanced speech analysis..." -ForegroundColor Yellow
Write-Host "This will enable speech-based MMSE support for better cognitive assessment" -ForegroundColor Cyan

# Install TensorFlow CPU version (lighter than GPU version)
pip install tensorflow-cpu

# Verify installation
python -c "
try:
    import tensorflow as tf
    print(f'✅ TensorFlow {tf.__version__} installed successfully!')
    print('🎉 Speech-based MMSE support is now available')
except ImportError as e:
    print(f'❌ TensorFlow installation failed: {e}')
    exit(1)
"

Write-Host "`n📋 TensorFlow installation complete!" -ForegroundColor Green
Write-Host "Restart the backend server to enable speech-based MMSE support" -ForegroundColor Cyan
