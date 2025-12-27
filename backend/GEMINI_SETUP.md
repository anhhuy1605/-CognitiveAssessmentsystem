# 🔑 Gemini API Setup Guide

## Vấn đề
Transcription bằng Gemini không hoạt động vì thiếu API key.

## Giải pháp

### 1. Lấy Gemini API Key

1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập bằng Google account
3. Tạo API key mới
4. Copy API key

### 2. Set Environment Variable

Chạy một trong các lệnh sau trong PowerShell:

```powershell
# Cách 1: Set GEMINI_API_KEY
$env:GEMINI_API_KEY = "your_actual_api_key_here"

# Cách 2: Set GOOGLE_API_KEY (cũng được hỗ trợ)
$env:GOOGLE_API_KEY = "your_actual_api_key_here"
```

### 3. Test Setup

```powershell
# Chạy test script
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
python test_gemini_transcription.py
```

### 4. Khởi động lại Backend

Sau khi set API key thành công, khởi động lại backend:

```powershell
# Dừng backend hiện tại (Ctrl+C)
# Rồi chạy lại
python run.py
```

## Xác minh

Khi test thành công, bạn sẽ thấy:
```
✅ API key found (length: 39)
✅ Created test audio: C:\Users\...\tmp.wav
🎵 Testing transcription...
📊 Result:
  Success: True
  Transcript: '(nội dung được trích xuất)'
  Confidence: 0.8
  Model: gemini-only
✅ Gemini transcription is working!
```

## Lưu ý

- API key sẽ bị reset khi đóng PowerShell
- Để persistent, tạo file `.env` trong thư mục `backend/`:
  ```
  GEMINI_API_KEY=your_actual_api_key_here
  ```
- Không commit file `.env` vào Git (đã có trong `.gitignore`)
