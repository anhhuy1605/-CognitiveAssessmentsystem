# Backend Changes - Hidden Flags và TTS Text

## ✅ Đã tạo file patch

File `backend/services/mmse_chatbot_service_HIDDEN_FLAGS_PATCH.py` chứa code cần thay đổi.

## 📝 Hướng dẫn áp dụng

### Bước 1: Thêm helper method

1. Mở file `backend/services/mmse_chatbot_service.py`
2. Tìm method `_replace_greeting` (khoảng dòng 2029)
3. Thêm method `_build_question_text_with_hidden_flags` TRƯỚC method `_replace_greeting`
4. Copy code từ file patch (Method 1)

### Bước 2: Cập nhật get_current_question()

1. Tìm section xử lý registration và instruction (khoảng dòng 395-432)
2. Thay thế toàn bộ section đó bằng code mới từ patch (Method 2)
3. Code mới chỉ có 3 dòng:
   ```python
   # ✅ NEW: Use helper method to build display and TTS text with hidden flags
   actual_question_id = question.get("question_id", f"{domain.value}_{index}")
   question_text, tts_text = self._build_question_text_with_hidden_flags(question, question_text, state)
   ```

### Bước 3: Cập nhật metadata

1. Tìm section metadata (khoảng dòng 438-458)
2. Thay thế bằng code mới từ patch (Method 3)
3. Đảm bảo thêm các field:
   - `hidden_display`
   - `hidden_audio`
   - `tts_text`

## 🧪 Test sau khi áp dụng

1. **Test registration question**:
   - Display text KHÔNG chứa "Con mèo, Chiếc xe, Cây lúa"
   - TTS text CHỨA đầy đủ "Ba từ đó là: Con mèo, Chiếc xe, Cây lúa"
   - Metadata có `tts_text` field

2. **Test repetition question**:
   - Instruction "Chỉ được nghe MỘT LẦN thôi nhé" KHÔNG hiển thị
   - Sentence to repeat được đọc trong TTS

3. **Test bee question**:
   - Sentence "Con ong đang làm tổ trên cây" KHÔNG hiển thị
   - Sentence được đọc trong TTS
   - Chỉ câu hỏi "Ông cho biết con ong đang làm gì?" hiển thị

## 📋 Checklist

- [ ] Đã thêm helper method `_build_question_text_with_hidden_flags`
- [ ] Đã cập nhật `get_current_question()` để sử dụng helper method
- [ ] Đã thêm `hidden_display`, `hidden_audio`, `tts_text` vào metadata
- [ ] Đã test với registration question
- [ ] Đã test với repetition question
- [ ] Đã test với bee question
- [ ] Đã verify backward compatibility (câu hỏi cũ không có flag vẫn hoạt động)

## 🔍 Debug

Nếu có lỗi, kiểm tra:
1. Import `Tuple` từ `typing` (nếu chưa có)
2. Method `_build_question_text_with_hidden_flags` được định nghĩa đúng
3. Variable `tts_text` được khai báo trước khi dùng trong metadata
4. Logging để xem giá trị của `question_text` và `tts_text`

## 📝 Notes

- Code hỗ trợ cả format cũ (`words_announcement_hidden`) và format mới (`hidden_display`, `hidden_audio`)
- Backward compatible: câu hỏi không có flag sẽ hoạt động bình thường
- TTS text có thể khác với display text nếu có content bị ẩn

