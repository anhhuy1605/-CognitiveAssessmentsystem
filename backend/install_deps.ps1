# PowerShell script to install dependencies
# Run once to download all packages

Write-Host "Installing Vietnamese Cognitive Assessment Backend Dependencies" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check pip
try {
    $pipVersion = python -m pip --version 2>&1
    Write-Host "pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "pip not found. Please install pip first." -ForegroundColor Red
    exit 1
}

Write-Host "`nInstalling core packages..." -ForegroundColor Blue
$corePackages = @(
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
)

foreach ($package in $corePackages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    python -m pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$package installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to install $package" -ForegroundColor Red
    }
}

Write-Host "`nInstalling PyTorch (CPU version)..." -ForegroundColor Blue
$torchPackages = @("torch", "torchaudio")
foreach ($package in $torchPackages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    python -m pip install $package --index-url https://download.pytorch.org/whl/cpu --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$package installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to install $package" -ForegroundColor Red
    }
}

Write-Host "`nInstalling ML/Audio packages..." -ForegroundColor Blue
$mlPackages = @(
    "transformers>=4.30.0",
    "noisereduce>=3.0.0",
    "webrtcvad>=2.0.10"
)
foreach ($package in $mlPackages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    python -m pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$package installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to install $package" -ForegroundColor Red
    }
}

Write-Host "`nInstallation completed!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart your terminal/PowerShell" -ForegroundColor White
Write-Host "2. Run: cd backend; python run.py" -ForegroundColor White
Write-Host "3. Backend will start without downloading packages" -ForegroundColor White

Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
