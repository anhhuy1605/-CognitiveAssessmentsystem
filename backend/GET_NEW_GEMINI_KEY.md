# 🔑 Cách lấy Gemini API Key mới (miễn phí)

## **Quota đã hết? Tạo key mới!**

Mỗi tài khoản Google có quota riêng (20 requests/day).

### **Bước 1: Tạo tài khoản Google mới (hoặc dùng tài khoản khác)**
- Mở https://accounts.google.com/signup
- Tạo Gmail mới (miễn phí)

### **Bước 2: Lấy API Key mới**
1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập bằng tài khoản Google mới
3. Click **"Create API Key"**
4. Copy key mới

### **Bước 3: Cập nhật key**

#### **Cách 1: PowerShell (nhanh)**
```powershell
cd D:\CognitiveAssessmentsystem\backend
$env:GEMINI_API_KEY="YOUR_NEW_KEY_HERE"
```

#### **Cách 2: Cập nhật file config.env**
Mở file `backend/config.env`, dòng 32:
```
GEMINI_API_KEY=YOUR_NEW_KEY_HERE
```

### **Bước 4: Test lại**
```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
$env:GEMINI_API_KEY="YOUR_NEW_KEY"
python test_asr_simple.py
```

---

## **Hoặc: Nâng cấp lên Paid tier**

### **Gemini API Pricing**
- **Free tier**: 15-20 requests/phút, 1500 requests/ngày
- **Paid tier**: ~$0.000125/request (rất rẻ)

### **Cách nâng cấp:**
1. Truy cập: https://aistudio.google.com/app/apikey
2. Click "Enable billing"
3. Thêm credit card
4. Quota sẽ tăng ngay lập tức

---

## **Tạm thời: Dùng Whisper fallback**

Nếu không muốn tạo key mới ngay, có thể enable Whisper fallback:

```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1
$env:FORCE_WHISPER_FALLBACK="true"
python test_asr_simple.py
```

**Lưu ý:** Whisper cần OpenAI API key và tốn tiền (~$0.006/phút audio)

---

## **Kiểm tra quota hiện tại**

Xem đã dùng bao nhiêu requests:
- Truy cập: https://ai.dev/usage?tab=rate-limit
- Đăng nhập tài khoản Google
- Xem mục "generativelanguage.googleapis.com/generate_content_free_tier_requests"

---

## **Mẹo tiết kiệm quota**

1. **Cache transcript**: Lưu kết quả transcript để không cần gọi API lại
2. **Batch processing**: Gom nhiều audio lại xử lý một lúc
3. **Dùng nhiều API keys**: Rotate giữa các keys khác nhau
4. **Chuyển sang paid tier**: Rất rẻ (~$0.0001/request)

