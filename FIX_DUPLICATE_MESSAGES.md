# Fix Duplicate Messages - Hướng Dẫn Sửa Thủ Công

## 🎯 VẤN ĐỀ

Bạn đang thấy duplicate messages:

### Registration:
```
Bây giờ Ông hãy ghi nhớ 3 từ mà tôi sắp đọc.  ← DUPLICATE (từ transition message)
Bây giờ ông hãy chú ý lắng nghe nhé...        ← Đúng (từ JSON instruction)
```

### Serial 7s:
```
Bây giờ chúng ta sẽ làm một bài tập tính toán đơn giản.  ← DUPLICATE (từ transition message)
Bây giờ chúng ta sẽ làm một bài tập tính toán đơn giản.  ← DUPLICATE (từ JSON instruction)
```

## 🔍 NGUYÊN NHÂN

File: `backend/services/mmse_chatbot_service.py`

**Dòng 772-787**: `_advance_to_next_domain()` đang thêm transition messages trước khi gọi `get_current_question()`, nhưng JSON đã có instruction fields đầy đủ rồi.

## ✅ GIẢI PHÁP

### TÌM (Dòng 772-787):
```python
        # Domain transition messages
        transition_messages = {
            TestDomain.REGISTRATION: f"Bây giờ {state.greeting} hãy ghi nhớ 3 từ mà tôi sắp đọc.",
            TestDomain.ATTENTION_CALCULATION: f"Bây giờ chúng ta sẽ làm một bài tập tính toán đơn giản.",
            TestDomain.OPEN_QUESTIONS: f"Bây giờ {state.greeting} hãy kể cho tôi nghe một số điều về cuộc sống hàng ngày.",
            TestDomain.RECALL: f"Bây giờ {state.greeting} hãy nhắc lại 3 từ mà tôi đã đọc lúc nãy.",
            TestDomain.LANGUAGE: f"Bây giờ chúng ta sẽ kiểm tra về ngôn ngữ.",
            TestDomain.VISUOSPATIAL: f"Cuối cùng, {state.greeting} hãy tưởng tượng một hình.",
        }
        
        transition = transition_messages.get(next_domain, "")
        next_question, metadata = self.get_current_question(session_id)
        
        if transition:
            return f"{transition}\n\n{next_question}", metadata
        return next_question, metadata
```

### THAY THẾ BẰNG:
```python
        # ✅ FIX: Don't add transition messages - JSON already has instruction fields
        # Transition messages cause duplicates with JSON instruction fields
        # JSON structure now includes proper instructions for each domain
        next_question, metadata = self.get_current_question(session_id)
        return next_question, metadata
```

## 📝 KẾT QUẢ SAU KHI SỬA

### Registration (không còn duplicate):
```
Bây giờ ông hãy chú ý lắng nghe nhé. Tôi sẽ đọc 3 từ, ông hãy nhớ kỹ.

Ông hãy nhắc lại 3 từ vừa nghe được không?

Ba từ đó là: Con mèo, Chiếc xe, Cây lúa.

Ông hãy nhớ 3 từ này nhé, một lát nữa tôi sẽ hỏi lại.
```

### Serial 7s (không còn duplicate):
```
Bây giờ chúng ta sẽ làm một bài tập tính toán đơn giản.

Ông hãy tính 100 trừ 7 bằng bao nhiêu? Rồi lấy kết quả vừa tính được trừ tiếp cho 7. Hãy tính trừ 5 lần như vậy.
```

## ✅ VERIFICATION

Sau khi sửa, chạy:
```bash
cd backend
python -m py_compile services/mmse_chatbot_service.py
```

Nếu không có lỗi syntax → ✅ Hoàn thành!





