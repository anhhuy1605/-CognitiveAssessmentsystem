# Import Test Results to Database
# ================================

param(
    [string]$ResultsFile = "test_results_test_session_1766891790.json"
)

Write-Host "📥 Importing Test Results to Database..." -ForegroundColor Green
Write-Host ""

# Check if file exists
if (-not (Test-Path $ResultsFile)) {
    Write-Host "❌ File not found: $ResultsFile" -ForegroundColor Red
    Write-Host "   Usage: .\import_test_results.ps1 [path_to_results.json]" -ForegroundColor Yellow
    exit 1
}

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

# Set environment variables
$env:API_BASE_URL = "http://localhost:5001"
$env:FRONTEND_URL = "http://localhost:3000"

# Run import script
Write-Host ""
Write-Host "🔄 Running import script..." -ForegroundColor Cyan
Write-Host ""

python import_test_results_to_db.py $ResultsFile

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Import completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 View results at:" -ForegroundColor Cyan
    Write-Host "   Stats: http://localhost:3000/stats" -ForegroundColor Yellow
    Write-Host "   Results: http://localhost:3000/results/[sessionId]" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Import failed. Check the error messages above." -ForegroundColor Red
    exit 1
}

