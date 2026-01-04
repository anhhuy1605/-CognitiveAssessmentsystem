# Tóm tắt các cải thiện MMSE Test

## ✅ Đã hoàn thành

### 1. Sửa lỗi education_years
- **File**: `backend/services/comprehensive_results_generator.py`
- **Thay đổi**: Convert `education_years` từ string sang int trước khi so sánh
- **Dòng**: ~257

### 2. Cập nhật frontend để sử dụng tts_text từ metadata
- **File**: `frontend/app/(main)/mmse-chatbot-v2/page.tsx`
- **Thay đổi**: Thêm `ttsText: data.metadata?.tts_text || messageText` vào addBotMessage
- **Dòng**: ~718

### 3. Cập nhật JSON với các flag ẩn
- **File**: `backend/mmse_audio_questions_standardized.json`
- **Thay đổi**:
  - Registration question: Thêm `words_announcement_hidden: true`, `words_announcement_tts: true`
  - Registration question: Thêm `instruction_after_hidden: true`, `instruction_after_tts: false`
  - Repetition question: Thêm `instruction_hidden: true`, `instruction_tts: false`, `sentence_to_repeat_tts: true`
  - Bee question: Thêm `sentence_to_listen_hidden: true`, `sentence_to_listen_tts: true`

## ⚠️ Cần hoàn thành

### 4. Cập nhật backend service để xử lý các flag ẩn
- **File**: `backend/services/mmse_chatbot_service.py`
- **Vị trí**: Method `get_current_question()` (~line 366-471)
- **Cần thay đổi**:
  1. Tách logic xây dựng display text và TTS text
  2. Cho registration: Không thêm `words_announcement` vào `message_parts` nếu `words_announcement_hidden: true`
  3. Cho registration: Không thêm `instruction_after` vào `message_parts` nếu `instruction_after_hidden: true`
  4. Cho repetition: Không thêm `instruction` vào display nếu `instruction_hidden: true`
  5. Cho repetition: Thêm `sentence_to_repeat` vào TTS nếu `sentence_to_repeat_tts: true`
  6. Cho bee question: Thêm `sentence_to_listen` vào TTS nếu `sentence_to_listen_tts: true`
  7. Thêm `tts_text` vào metadata

### 5. Thêm câu hỏi về con ong
- **File**: `backend/mmse_audio_questions_standardized.json`
- **Vị trí**: Domain `7_language`, question `lang_comprehension_listening`
- **Đã cập nhật**: Câu hỏi đã có, cần đảm bảo:
  - Instruction: "Tôi sẽ đọc một câu, {pronoun} lắng nghe rồi trả lời câu hỏi nhé." (visible)
  - Sentence: "Con ong đang làm tổ trên cây" (hidden, TTS reads)
  - Question: "{Pronoun} cho biết con ong đang làm gì?" (visible)
  - Correct answer: "làm tổ"

### 6. Thêm tính năng vẽ đồng hồ
- **Cần tạo**: Component `ClockDrawingCanvas.tsx`
- **Vị trí**: `frontend/src/components/questions/ClockDrawingCanvas.tsx`
- **Tính năng**:
  - Canvas vẽ tay tự do
  - Nút xóa/vẽ lại
  - Lưu hình ảnh dưới dạng base64
  - Gửi về backend khi hoàn thành

### 7. Cập nhật flow logic
- **Cần đảm bảo thứ tự**:
  1. Registration (nhớ 3 từ) - ĐẦU TEST
  2. Orientation (ngày tháng, địa điểm)
  3. Attention (làm 3 việc theo thứ tự)
  4. Bee question (con ong)
  5. Recall (nhắc lại 3 từ)
  6. Clock drawing (vẽ đồng hồ) - CUỐI TEST

## 📝 Chi tiết kỹ thuật

### Backend Changes Needed

```python
# In get_current_question() method:

# For Registration:
if domain == TestDomain.REGISTRATION and index == 0:
    message_parts = []
    tts_parts = []
    
    # Instruction (visible)
    if instruction:
        message_parts.append(instruction)
        tts_parts.append(instruction)
    
    # Question (visible)
    if question_text:
        message_parts.append(question_text)
        tts_parts.append(question_text)
    
    # Words announcement (hidden from UI, in TTS)
    words_announcement = question.get("words_announcement", "")
    if words_announcement:
        words_announcement = self._replace_greeting(words_announcement, state.greeting)
        if question.get("words_announcement_tts", True):
            tts_parts.append(words_announcement)
        # Don't add to message_parts if hidden
    
    # Instruction after (completely hidden)
    instruction_after = question.get("instruction_after", "")
    if instruction_after:
        instruction_after = self._replace_greeting(instruction_after, state.greeting)
        # Don't add to message_parts or tts_parts
    
    question_text = "\n\n".join(message_parts)
    tts_text = "\n\n".join(tts_parts)

# For other questions:
# Similar logic for instruction_hidden, sentence_to_repeat, sentence_to_listen

# Add to metadata:
metadata["tts_text"] = tts_text
```

### Frontend Changes Needed

1. **Clock Drawing Component**: Tạo component mới với HTML5 Canvas
2. **Question Flow**: Đảm bảo thứ tự đúng theo yêu cầu
3. **TTS Handling**: Đã cập nhật để sử dụng `tts_text` từ metadata

## 🔄 Next Steps

1. Hoàn thành cập nhật backend service (item 4)
2. Tạo Clock Drawing component (item 6)
3. Kiểm tra và điều chỉnh flow logic (item 7)
4. Test toàn bộ flow với các tính năng mới





