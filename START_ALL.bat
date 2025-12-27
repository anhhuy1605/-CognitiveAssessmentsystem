@echo off
echo ============================================
echo Starting Cognitive Assessment System
echo ============================================

REM Start Backend
echo Starting Backend (Flask)...
start "Backend" cmd /k "cd /d D:\CognitiveAssessmentsystem\backend && D:\CognitiveAssessmentsystem\.venv\Scripts\activate.bat && set PYTHONIOENCODING=utf-8 && python app.py"

REM Wait a bit
timeout /t 5 /nobreak

REM Start Frontend
echo Starting Frontend (Next.js)...
start "Frontend" cmd /k "cd /d D:\CognitiveAssessmentsystem\frontend && npm run dev"

echo ============================================
echo Both servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo MMSE Chatbot: http://localhost:3000/mmse-chatbot
echo ============================================
pause

