@echo off
echo Starting Vietnamese Cognitive Assessment Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "models" mkdir models
if not exist "tudien" mkdir tudien
if not exist "storage" mkdir storage

REM Start the server
echo Starting server...
python run.py

pause
