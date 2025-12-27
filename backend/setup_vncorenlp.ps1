# Setup VnCoreNLP for Vietnamese NLP
# PowerShell script for Windows

Write-Host "🚀 Setting up VnCoreNLP..." -ForegroundColor Green

# Create VnCoreNLP directory
$vnCoreNLPDir = "D:\CognitiveAssessmentsystem\backend\VnCoreNLP"
if (-not (Test-Path $vnCoreNLPDir)) {
    New-Item -ItemType Directory -Path $vnCoreNLPDir -Force
    Write-Host "✅ Created directory: $vnCoreNLPDir" -ForegroundColor Green
} else {
    Write-Host "📁 Directory already exists: $vnCoreNLPDir" -ForegroundColor Yellow
}

# Download VnCoreNLP JAR file
$jarUrl = "https://github.com/vncorenlp/VnCoreNLP/raw/master/VnCoreNLP-1.2.jar"
$jarPath = Join-Path $vnCoreNLPDir "VnCoreNLP-1.2.jar"

if (-not (Test-Path $jarPath)) {
    Write-Host "📥 Downloading VnCoreNLP-1.2.jar..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $jarUrl -OutFile $jarPath -UseBasicParsing
        Write-Host "✅ Downloaded VnCoreNLP-1.2.jar" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to download VnCoreNLP JAR: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ VnCoreNLP-1.2.jar already exists" -ForegroundColor Yellow
}

# Download models
$modelsUrl = "https://github.com/vncorenlp/VnCoreNLP/raw/master/models.zip"
$modelsZip = Join-Path $vnCoreNLPDir "models.zip"
$modelsDir = Join-Path $vnCoreNLPDir "models"

if (-not (Test-Path $modelsDir)) {
    Write-Host "📥 Downloading VnCoreNLP models..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $modelsUrl -OutFile $modelsZip -UseBasicParsing
        Write-Host "✅ Downloaded models.zip" -ForegroundColor Green
        
        Write-Host "📦 Extracting models..." -ForegroundColor Cyan
        Expand-Archive -Path $modelsZip -DestinationPath $vnCoreNLPDir -Force
        Remove-Item $modelsZip -Force
        Write-Host "✅ Extracted models" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to download/extract models: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Models directory already exists" -ForegroundColor Yellow
}

# Check Java installation
Write-Host "☕ Checking Java installation..." -ForegroundColor Cyan
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "✅ Java is installed: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Java not found. Please install Java JDK 8 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.oracle.com/java/technologies/downloads/" -ForegroundColor Yellow
}

# Install vncorenlp Python package
Write-Host "🐍 Installing vncorenlp Python package..." -ForegroundColor Cyan
& "D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1"
pip install vncorenlp

Write-Host ""
Write-Host "✅ VnCoreNLP setup complete!" -ForegroundColor Green
Write-Host "📁 Location: $vnCoreNLPDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 To use VnCoreNLP in Python:" -ForegroundColor Yellow
Write-Host "from vncorenlp import VnCoreNLP" -ForegroundColor White
Write-Host "annotator = VnCoreNLP('$vnCoreNLPDir/VnCoreNLP-1.2.jar', annotators='wseg,pos,ner', max_heap_size='-Xmx2g')" -ForegroundColor White

