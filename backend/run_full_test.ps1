# Run Full MMSE Chatbot Test
# ============================

Write-Host "🚀 Starting Full MMSE Chatbot Test..." -ForegroundColor Green
Write-Host ""

# Check if backend is running
Write-Host "📡 Checking backend connection..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-WebRequest -Uri "http://localhost:5001/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend is not running. Please start backend first:" -ForegroundColor Red
    Write-Host "   cd backend" -ForegroundColor Yellow
    Write-Host "   python app.py" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment if exists
if (Test-Path "..\.venv\Scripts\Activate.ps1") {
    Write-Host "🐍 Activating virtual environment..." -ForegroundColor Yellow
    & "..\.venv\Scripts\Activate.ps1"
}

# Set API URL
$env:API_BASE_URL = "http://localhost:5001"

# Run test
Write-Host ""
Write-Host "🧪 Running full test..." -ForegroundColor Cyan
Write-Host ""

python test_mmse_chatbot_full_automated.py

Write-Host ""
Write-Host "✅ Test completed! Check test_mmse_chatbot_full.log for details." -ForegroundColor Green

