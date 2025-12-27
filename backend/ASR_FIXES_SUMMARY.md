# 🔧 Tóm tắt các lỗi ASR đã sửa và hướng dẫn sử dụng

## ❌ Các lỗi đã được sửa

### 1. Lỗi `used_gpt not defined` (dòng 814)

**Nguyên nhân:**
- Biến `used_gpt` được sử dụng trong return statement nhưng không được định nghĩa
- Code: `'model': transcription_model + (' + gpt-4o' if used_gpt else '')`

**Cách sửa:**
```python
# Thêm dòng này sau khi set gpt4o_processing_time = 0
used_gpt = False  # Gemini doesn't use GPT-4o
```

**File:** `vietnamese_transcriber.py` dòng 713

---

### 2. Lỗi Exception Handler sai (dòng 825-827)

**Nguyên nhân:**
- Exception được đặt tên là `openai_error` nhưng đang dùng Gemini API
- Message lỗi: "OpenAI transcription failed" không đúng

**Cách sửa:**
```python
# Trước:
except Exception as openai_error:
    logger.error(f"❌ OpenAI transcription failed: {openai_error}")
    return self._error_result(f"OpenAI transcription failed: {openai_error}")

# Sau:
except Exception as gemini_error:
    logger.error(f"❌ Gemini transcription failed: {gemini_error}")
    return self._error_result(f"Gemini transcription failed: {gemini_error}")
```

**File:** `vietnamese_transcriber.py` dòng 825-827

---

## ✅ Kiến trúc hệ thống hiện tại

```
┌────────────────────────────────────────────────────────────┐
│                      AUDIO INPUT                           │
│                  (Recording/File)                          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   GEMINI API (ASR)                         │
│  - Model: gemini-2.5-flash                                 │
│  - Chuyển giọng nói thành text                            │
│  - KHÔNG dùng GPT-4o để improve transcript                │
│  - Vietnamese language model                               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   TRANSCRIPT (TEXT)                        │
│  - Raw transcript từ Gemini                                │
│  - Được correct bởi Vietnamese Language Model              │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   GPT-4O API (EVALUATION)                  │
│  - Model: gpt-4o                                           │
│  - Prompt: mmse_evaluation_system_prompt.txt               │
│  - Chấm điểm MMSE                                         │
│  - Đánh giá nhận thức                                     │
│  - Tạo feedback chi tiết                                   │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   MMSE SCORE + FEEDBACK                    │
│  - Điểm /30                                                │
│  - Phân loại: Normal/MCI/Moderate/Severe                  │
│  - Khuyến nghị                                             │
└────────────────────────────────────────────────────────────┘
```

## 🔑 Cấu hình API Keys

### Gemini API (cho ASR)

```powershell
# Lấy key từ: https://aistudio.google.com/app/apikey

# Set cho session hiện tại
$env:GEMINI_API_KEY="AIza..."

# Hoặc dùng script tự động
.\set_gemini_key.ps1

# Hoặc thêm vào .env
echo "GEMINI_API_KEY=AIza..." >> .env
```

### OpenAI API (cho MMSE Evaluation)

```powershell
# Lấy key từ: https://platform.openai.com/api-keys

# Set cho session hiện tại
$env:OPENAI_API_KEY="sk-..."

# Hoặc thêm vào .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

## 📝 File cấu hình quan trọng

### 1. `mmse_evaluation_system_prompt.txt`

**Mục đích:** System prompt cho GPT-4o để chấm điểm MMSE

**Nội dung chính:**
- Hướng dẫn chấm điểm chi tiết cho từng phần MMSE
- Quy tắc điều chỉnh theo tuổi, trình độ học vấn
- Xử lý đặc biệt cho tiếng Việt (thanh điệu, phương ngữ)
- Output format: JSON với section_scores, interpretation, clinical_notes

**Cách GPT-4o sử dụng:**
```python
# Trong app.py
gpt_response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},  # ← mmse_evaluation_system_prompt.txt
        {"role": "user", "content": f"Transcript: {transcript}\nQuestion: {question}"}
    ]
)
```

### 2. `vietnamese_transcriber.py`

**Mục đích:** ASR với Gemini

**Các function quan trọng:**
- `transcribe_audio_file()`: Main transcription function
- `_apply_comprehensive_vietnamese_corrections()`: Correct Vietnamese specific issues
- `_improve_with_gpt4o()`: **DEPRECATED** - không còn dùng nữa

**Cách hoạt động:**
1. Nhận audio file
2. Upload lên Gemini API
3. Gemini trả về raw transcript
4. Apply Vietnamese language model corrections
5. Return corrected transcript

## 🧪 Test ASR

### Test đơn giản

```powershell
cd D:\CognitiveAssessmentsystem\backend
& D:\CognitiveAssessmentsystem\.venv\Scripts\Activate.ps1

# Đảm bảo API key đã set
$env:GEMINI_API_KEY="YOUR_KEY"

# Run test
python test_asr_simple.py
```

**Kết quả mong đợi:**
```
✅ ASR test PASSED
Transcript: '...'
Confidence: 0.80
Model: gemini-2.5-flash
```

### Test với audio thực tế

```powershell
# Tạo audio test với giọng nói tiếng Việt
# (Bạn cần ghi âm hoặc dùng file có sẵn)

python -c "
from vietnamese_transcriber import RealTimeVietnameseTranscriber, TranscriptionConfig
config = TranscriptionConfig()
transcriber = RealTimeVietnameseTranscriber(config)
result = transcriber.transcribe_audio_file('path/to/your/audio.wav', language='vi')
print(f'Transcript: {result[\"transcript\"]}')
"
```

## 🔧 Troubleshooting

### Vấn đề 1: "Gemini API key not configured"

**Nguyên nhân:** Chưa set API key

**Cách sửa:**
```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
# Hoặc chạy: .\set_gemini_key.ps1
```

### Vấn đề 2: "No speech content detected"

**Nguyên nhân:** 
- Audio không có giọng nói
- Audio là âm thanh khác (beep, music, noise)
- Gemini không nhận diện được

**Cách sửa:**
- Kiểm tra audio file có giọng nói rõ ràng
- Tăng volume
- Giảm noise trong audio

### Vấn đề 3: "Quota exceeded"

**Nguyên nhân:** Gemini free tier có giới hạn

**Giới hạn:**
- 15 requests/phút
- 1,500 requests/ngày

**Cách sửa:**
- Đợi 1-2 phút
- Nâng cấp lên paid tier
- Hoặc dùng nhiều API keys (rotate)

### Vấn đề 4: Transcript không chính xác

**Nguyên nhân:**
- Audio chất lượng kém
- Có nhiều noise
- Phương ngữ khác biệt

**Cách sửa:**
- Cải thiện chất lượng audio
- Nói rõ ràng, từ tốn
- Update prompt cho Gemini với context cụ thể hơn

## 📚 Tài liệu liên quan

- **SETUP_ASR.md**: Hướng dẫn cài đặt chi tiết
- **mmse_evaluation_system_prompt.txt**: System prompt cho GPT-4o
- **test_asr_simple.py**: Script test ASR cơ bản
- **set_gemini_key.ps1**: Script set API key nhanh

## 🎯 Next Steps

1. **Cài đặt API keys:**
   ```powershell
   .\set_gemini_key.ps1
   ```

2. **Test ASR:**
   ```powershell
   python test_asr_simple.py
   ```

3. **Test MMSE Evaluation:**
   ```powershell
   python test_mmse_evaluation.py
   ```

4. **Cài đặt VnCoreNLP (optional):**
   ```powershell
   powershell -ExecutionPolicy Bypass -File install_vncorenlp.ps1
   ```

5. **Run backend:**
   ```powershell
   python app.py
   ```

6. **Test full flow:**
   - Mở frontend
   - Record audio
   - Check transcript
   - Check MMSE score

---

**Tác giả:** AI Assistant  
**Ngày:** 2025-12-27  
**Version:** 1.0

