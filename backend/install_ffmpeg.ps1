# Install FFmpeg for Windows
Write-Host "🚀 Installing FFmpeg for audio conversion..." -ForegroundColor Green

# Create ffmpeg directory
$ffmpegDir = "C:\ffmpeg"
if (!(Test-Path $ffmpegDir)) {
    New-Item -ItemType Directory -Path $ffmpegDir -Force
}

# Download FFmpeg (Windows build)
$ffmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$zipFile = "$ffmpegDir\ffmpeg.zip"

Write-Host "📥 Downloading FFmpeg..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipFile -UseBasicParsing
    Write-Host "✅ Download completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Extract FFmpeg
Write-Host "📦 Extracting FFmpeg..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipFile -DestinationPath $ffmpegDir -Force
    
    # Find the extracted folder and move ffmpeg.exe to root
    $extractedFolder = Get-ChildItem -Path $ffmpegDir -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1
    if ($extractedFolder) {
        $ffmpegExe = Join-Path $extractedFolder.FullName "bin\ffmpeg.exe"
        if (Test-Path $ffmpegExe) {
            Copy-Item $ffmpegExe -Destination "$ffmpegDir\ffmpeg.exe" -Force
            Write-Host "✅ FFmpeg extracted successfully" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Extraction failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Add to PATH (for current session)
$env:PATH += ";$ffmpegDir"

# Add to system PATH permanently (requires admin rights)
Write-Host "🔧 Adding FFmpeg to system PATH..." -ForegroundColor Yellow
try {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$ffmpegDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$ffmpegDir", "Machine")
        Write-Host "✅ FFmpeg added to system PATH (restart terminal to use)" -ForegroundColor Green
    } else {
        Write-Host "✅ FFmpeg already in system PATH" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Could not add to system PATH (run as administrator for permanent PATH)" -ForegroundColor Yellow
    Write-Host "💡 FFmpeg available for current session only" -ForegroundColor Cyan
}

# Test FFmpeg
Write-Host "🧪 Testing FFmpeg installation..." -ForegroundColor Yellow
try {
    $ffmpegPath = if (Test-Path "$ffmpegDir\ffmpeg.exe") { "$ffmpegDir\ffmpeg.exe" } else { "ffmpeg" }
    $version = & $ffmpegPath -version 2>$null | Select-Object -First 1
    if ($version) {
        Write-Host "✅ FFmpeg working: $($version.Split(' ')[2])" -ForegroundColor Green
        Write-Host "🎉 Installation completed successfully!" -ForegroundColor Green
        Write-Host "💡 Restart your terminal or IDE to use FFmpeg globally" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ FFmpeg test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Cleanup
Remove-Item $zipFile -Force -ErrorAction SilentlyContinue
Write-Host "🧹 Cleanup completed" -ForegroundColor Green
