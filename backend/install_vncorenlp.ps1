# Setup VnCoreNLP for Vietnamese NLP
Write-Host "Setting up VnCoreNLP..." -ForegroundColor Green

# Create directory
$vnCoreNLPDir = "D:\CognitiveAssessmentsystem\backend\VnCoreNLP"
New-Item -ItemType Directory -Path $vnCoreNLPDir -Force -ErrorAction SilentlyContinue

# Download JAR
$jarUrl = "https://github.com/vncorenlp/VnCoreNLP/raw/master/VnCoreNLP-1.2.jar"
$jarPath = Join-Path $vnCoreNLPDir "VnCoreNLP-1.2.jar"

if (-not (Test-Path $jarPath)) {
    Write-Host "Downloading VnCoreNLP JAR..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $jarUrl -OutFile $jarPath -UseBasicParsing
    Write-Host "Downloaded VnCoreNLP JAR" -ForegroundColor Green
}

# Download models
$modelsUrl = "https://github.com/vncorenlp/VnCoreNLP/raw/master/models.zip"
$modelsZip = Join-Path $vnCoreNLPDir "models.zip"
$modelsDir = Join-Path $vnCoreNLPDir "models"

if (-not (Test-Path $modelsDir)) {
    Write-Host "Downloading models..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $modelsUrl -OutFile $modelsZip -UseBasicParsing
    Expand-Archive -Path $modelsZip -DestinationPath $vnCoreNLPDir -Force
    Remove-Item $modelsZip -Force
    Write-Host "Extracted models" -ForegroundColor Green
}

# Check Java
Write-Host "Checking Java..." -ForegroundColor Cyan
java -version

# Install Python package
Write-Host "Installing vncorenlp package..." -ForegroundColor Cyan
& "D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1"
pip install vncorenlp

Write-Host "VnCoreNLP setup complete!" -ForegroundColor Green

