# 🚀 HƯỚNG DẪN NHANH - BẮT ĐẦU NGAY

## ✅ Trạng thái hiện tại
- ✅ OpenAI API key: Đã có
- ✅ Java: Đã cài (version 24.0.2)
- ❌ Gemini API key: **CHƯA CÓ** ← CẦN LÀM NGAY
- ⚠️ VnCoreNLP: Chưa cài (optional)

---

## 📝 BƯỚC 1: Lấy Gemini API Key (BẮT BUỘC)

### 1.1. Truy cập trang Gemini AI Studio
Mở trình duyệt và vào: **https://aistudio.google.com/app/apikey**

### 1.2. Đăng nhập bằng tài khoản Google
- Dùng Gmail của bạn

### 1.3. Tạo API Key
- Click nút **"Create API Key"**
- Chọn project (hoặc tạo mới)
- Copy API key (dạng: `AIzaSy...`)

### 1.4. Set API Key

**Cách 1: Dùng PowerShell (NHANH NHẤT)**
```powershell
cd D:\CognitiveAssessmentsystem\backend
$env:GEMINI_API_KEY="AIzaSy_PASTE_YOUR_KEY_HERE"
```

**Cách 2: Dùng script tự động**
```powershell
cd D:\CognitiveAssessmentsystem\backend
.\set_gemini_key.ps1
# Nhập key khi được hỏi
```

**Cách 3: Tạo file .env (LƯU VĨNH VIỄN)**
```powershell
cd D:\CognitiveAssessmentsystem\backend
echo "GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE" > .env
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### 1.5. Kiểm tra
```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
python check_setup.py
```

Kết quả mong đợi: `✅ Gemini API key: AIza...`

---

## 🧪 BƯỚC 2: Test ASR với Gemini

```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
python test_asr_simple.py
```

**Kết quả mong đợi:**
```
✅ ASR test PASSED
Transcript: '...'
Confidence: 0.80
Model: gemini-2.5-flash
```

**Nếu lỗi "Quota exceeded":**
- Gemini free tier: 15 requests/phút
- Đợi 1-2 phút rồi thử lại

---

## 📦 BƯỚC 3: Cài VnCoreNLP (Optional)

VnCoreNLP dùng cho linguistic analysis nâng cao. Không bắt buộc cho ASR cơ bản.

```powershell
cd D:\CognitiveAssessmentsystem\backend
powershell -ExecutionPolicy Bypass -File install_vncorenlp.ps1
```

Quá trình này sẽ:
1. Tạo thư mục `VnCoreNLP/`
2. Download `VnCoreNLP-1.2.jar` (~50MB)
3. Download `models.zip` (~100MB)
4. Giải nén models
5. Cài package Python `vncorenlp`

**Thời gian:** ~5-10 phút (tùy tốc độ mạng)

---

## ✅ BƯỚC 4: Kiểm tra tổng thể

```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
python check_setup.py
```

**Kết quả mong đợi:**
```
✅ Gemini API key: AIza...
✅ OpenAI API key: sk-proj-...
✅ VnCoreNLP: Đã cài đặt
✅ Java: java version "24.0.2"
✅ Hệ thống đã sẵn sàng!
```

---

## 🚀 BƯỚC 5: Chạy Backend

```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
python app.py
```

Server sẽ chạy tại: **http://localhost:5001**

---

## 🔧 Troubleshooting

### Lỗi: "Gemini API key not configured"
```powershell
# Kiểm tra biến môi trường
echo $env:GEMINI_API_KEY

# Nếu null, set lại
$env:GEMINI_API_KEY="YOUR_KEY"
```

### Lỗi: "Quota exceeded"
- **Nguyên nhân:** Gemini free tier có giới hạn 15 requests/phút
- **Giải pháp:** Đợi 1-2 phút rồi thử lại

### Lỗi: "Java not found" (khi cài VnCoreNLP)
- **Nguyên nhân:** Java chưa có trong PATH
- **Giải pháp:** 
  ```powershell
  # Tìm Java
  where.exe java
  
  # Nếu không có, download tại:
  # https://www.oracle.com/java/technologies/downloads/
  ```

### Lỗi: "No speech detected"
- **Nguyên nhân:** Audio không có giọng nói hoặc chỉ có noise
- **Giải pháp:** Dùng audio file có giọng nói rõ ràng

---

## 📚 Tài liệu bổ sung

- **SETUP_ASR.md** - Hướng dẫn chi tiết về ASR
- **ASR_FIXES_SUMMARY.md** - Tổng hợp lỗi đã sửa
- **mmse_evaluation_system_prompt.txt** - System prompt cho GPT-4o

---

## 🎯 Tóm tắt các lệnh quan trọng

```powershell
# Setup
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1

# Set API key
$env:GEMINI_API_KEY="YOUR_KEY"
$env:OPENAI_API_KEY="YOUR_KEY"

# Kiểm tra
python check_setup.py

# Test ASR
python test_asr_simple.py

# Cài VnCoreNLP (optional)
powershell -ExecutionPolicy Bypass -File install_vncorenlp.ps1

# Chạy backend
python app.py
```

---

**Bắt đầu từ BƯỚC 1!** 👆

