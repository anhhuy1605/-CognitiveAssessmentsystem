# Script to set Gemini API key easily
Write-Host "🔑 Gemini API Key Setup" -ForegroundColor Cyan
Write-Host "=" * 60

# Prompt for API key
$apiKey = Read-Host "Nhập Gemini API key của bạn"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "❌ API key không được để trống!" -ForegroundColor Red
    exit 1
}

# Set environment variable
$env:GEMINI_API_KEY = $apiKey
Write-Host "✅ Đã set GEMINI_API_KEY cho session hiện tại" -ForegroundColor Green

# Ask to save to .env file
$save = Read-Host "Bạn có muốn lưu vào file .env? (y/n)"

if ($save -eq 'y') {
    $envFile = "D:\CognitiveAssessmentsystem\backend\.env"
    
    # Check if .env exists
    if (Test-Path $envFile) {
        # Read existing content
        $content = Get-Content $envFile -Raw
        
        # Remove existing GEMINI_API_KEY lines
        $content = $content -replace "GEMINI_API_KEY=.*`n", ""
        $content = $content -replace "GOOGLE_API_KEY=.*`n", ""
        
        # Add new key
        $content += "`nGEMINI_API_KEY=$apiKey`n"
        
        # Write back
        Set-Content -Path $envFile -Value $content.Trim()
    }
    else {
        # Create new .env file
        "GEMINI_API_KEY=$apiKey" | Out-File -FilePath $envFile -Encoding UTF8
    }
    
    Write-Host "✅ Đã lưu vào $envFile" -ForegroundColor Green
}

Write-Host "`n📝 Để sử dụng trong session mới, chạy:" -ForegroundColor Yellow
Write-Host '  $env:GEMINI_API_KEY="' + $apiKey + '"' -ForegroundColor White
Write-Host "`nHoặc thêm vào file .env:" -ForegroundColor Yellow
Write-Host "  GEMINI_API_KEY=$apiKey" -ForegroundColor White

Write-Host "`n✅ Hoàn tất!" -ForegroundColor Green
Write-Host "Chạy test_asr_simple.py để kiểm tra ASR" -ForegroundColor Cyan
