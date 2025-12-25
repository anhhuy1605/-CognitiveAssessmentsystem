# install.bat - Installation script for Windows
@echo off

echo 🚀 Installing Vietnamese Speech Transcriber...

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✅ Python version: %python_version%

:: Create virtual environment
echo 📦 Creating virtual environment...
python -m venv vietnamese_transcriber_env
call vietnamese_transcriber_env\Scripts\activate.bat

:: Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

:: Install PyTorch
echo 🔥 Installing PyTorch...
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    echo 🎮 NVIDIA GPU detected, installing CUDA version...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    echo 💻 Installing CPU version...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
)

:: Install requirements
echo 📚 Installing requirements...
pip install -r requirements.txt

:: Create directories
echo 🇻🇳 Setting up Vietnamese resources...
mkdir tudien 2>nul
mkdir models 2>nul

:: Test installation
echo 🧪 Testing installation...
python -c "from vietnamese_transcriber import RealTimeVietnameseTranscriber; print('✅ Installation successful!')"

echo 🎉 Installation complete!
echo 📖 Usage:
echo   vietnamese_transcriber_env\Scripts\activate.bat
echo   python vietnamese_transcriber.py --mode test --file your_audio.wav
pause