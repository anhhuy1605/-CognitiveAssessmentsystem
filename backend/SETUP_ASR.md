# Hướng dẫn cài đặt ASR với Gemini

## 🔑 Bước 1: Lấy Gemini API Key

1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập bằng tài khoản Google
3. Click "Create API Key"
4. Copy API key

## 🔧 Bước 2: Cài đặt API Key

### Cách 1: Set biến môi trường (PowerShell)

```powershell
# Temporary (chỉ trong session hiện tại)
$env:GEMINI_API_KEY="YOUR_API_KEY_HERE"

# Hoặc thêm vào file .env
echo "GEMINI_API_KEY=YOUR_API_KEY_HERE" >> .env
```

### Cách 2: Dùng script tự động

```powershell
cd D:\CognitiveAssessmentsystem\backend
.\set_gemini_key.ps1
```

### Cách 3: Thêm vào file `.env`

Tạo/sửa file `backend/.env`:

```bash
GEMINI_API_KEY=YOUR_API_KEY_HERE
GOOGLE_API_KEY=YOUR_API_KEY_HERE  # Alternative name
```

## 📦 Bước 3: Cài đặt VnCoreNLP (cho linguistic analysis)

### Tự động (khuyến nghị):

```powershell
cd D:\CognitiveAssessmentsystem\backend
powershell -ExecutionPolicy Bypass -File install_vncorenlp.ps1
```

### Thủ công:

1. **Download VnCoreNLP:**
   ```powershell
   mkdir VnCoreNLP
   cd VnCoreNLP
   # Download JAR
   Invoke-WebRequest -Uri "https://github.com/vncorenlp/VnCoreNLP/raw/master/VnCoreNLP-1.2.jar" -OutFile "VnCoreNLP-1.2.jar"
   # Download models
   Invoke-WebRequest -Uri "https://github.com/vncorenlp/VnCoreNLP/raw/master/models.zip" -OutFile "models.zip"
   Expand-Archive models.zip -DestinationPath .
   ```

2. **Cài đặt Java** (nếu chưa có):
   - Download từ: https://www.oracle.com/java/technologies/downloads/
   - Chọn Java JDK 8 hoặc mới hơn
   - Kiểm tra: `java -version`

3. **Cài đặt Python package:**
   ```powershell
   & D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
   pip install vncorenlp
   ```

## ✅ Bước 4: Test ASR

```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
python test_asr_simple.py
```

Kết quả mong đợi:
```
✅ ASR test PASSED
Transcript: '...'
```

## 🎯 Kiến trúc hệ thống

```
┌─────────────────┐
│  Audio Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini API     │ ◄─── Transcription (ASR)
│  (Speech-to-    │      - Vietnamese language model
│   Text)         │      - High accuracy
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Transcript     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GPT-4o API     │ ◄─── MMSE Evaluation (Scoring)
│  (Cognitive     │      - Use mmse_evaluation_system_prompt.txt
│   Assessment)   │      - Score responses
│                 │      - Generate feedback
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MMSE Score     │
│  + Feedback     │
└─────────────────┘
```

## 🔍 Troubleshooting

### Lỗi: "Gemini API key not configured"

```powershell
# Check biến môi trường
echo $env:GEMINI_API_KEY

# Set lại
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
```

### Lỗi: "Quota exceeded"

- Gemini API có giới hạn 15 requests/phút (free tier)
- Đợi 1-2 phút rồi thử lại
- Hoặc nâng cấp lên paid tier

### Lỗi: "Java not found"

```powershell
# Install Java
winget install Oracle.JavaRuntimeEnvironment

# Or download from: https://www.oracle.com/java/technologies/downloads/
```

### Lỗi: "No speech detected"

- Kiểm tra audio file có giọng nói không
- Gemini chỉ transcribe được audio có lời nói, không transcribe được âm thanh khác (beep, music, etc.)

## 📚 Tài liệu tham khảo

- Gemini API: https://ai.google.dev/docs
- VnCoreNLP: https://github.com/vncorenlp/VnCoreNLP
- MMSE Standard: https://en.wikipedia.org/wiki/Mini%E2%80%93Mental_State_Examination

