# Fix Exposed Answers & Markdown Bold Issues

## 🎯 VẤN ĐỀ

Các câu hỏi đang lộ đáp án/câu với markdown bold (**text**):

1. **lang_repetition**: "Câu này là: **Không có nếu, và, hoặc nhưng gì cả.**"
2. **lang_comprehension_3step**: "**Thứ nhất:** Nói 'Tôi hiểu rồi'"
3. **lang_comprehension_listening**: "Câu này là: **Con ong chăm chỉ bay qua vườn hoa.**"
4. **Clock drawing**: "rồi vẽ kim đồng hồ chỉ **11 giờ 10 phút**"

## 🔍 NGUYÊN NHÂN

JSON có markdown bold (**text**) trong các fields nhưng code không remove chúng trước khi hiển thị.

## ✅ GIẢI PHÁP

### 1. Tạo Helper Method để Remove Markdown

**File**: `backend/services/mmse_chatbot_service.py`

**Thêm method sau `_replace_greeting`:**

```python
def _remove_markdown(self, text: str) -> str:
    """
    Remove markdown formatting from text (especially **bold**)
    
    Args:
        text: Text that may contain markdown
        
    Returns:
        Text with markdown removed
    """
    if not text:
        return text
    
    # Remove markdown bold (**text**)
    text = text.replace("**", "")
    
    # Remove other common markdown if needed
    # text = text.replace("*", "")  # Italic
    # text = text.replace("_", "")  # Underscore
    
    return text
```

### 2. Update get_current_question() để Remove Markdown

**Tìm**: Function `get_current_question()` - nơi format question_text

**Sửa**: Sau khi replace greeting, thêm remove markdown:

```python
# After self._replace_greeting()
question_text = self._replace_greeting(
    question.get("question", question.get("chatbot_message", question.get("question_text", ""))), 
    state.greeting
)

# ✅ FIX: Remove markdown bold before displaying
question_text = self._remove_markdown(question_text)
```

### 3. Update Registration Handling

**Tìm**: Registration handling code (dòng ~392-423)

**Sửa**: Remove markdown từ tất cả message parts:

```python
if domain == TestDomain.REGISTRATION and index == 0:
    message_parts = []
    
    # 1. Instruction
    instruction = question.get("instruction", "")
    if instruction:
        instruction = self._replace_greeting(instruction, state.greeting)
        instruction = self._remove_markdown(instruction)  # ✅ ADD
        message_parts.append(instruction)
    
    # 2. Question (main question text)
    if question_text:
        question_text = self._remove_markdown(question_text)  # ✅ ADD
        message_parts.append(question_text)
    
    # 3. Words announcement
    words_announcement = question.get("words_announcement", "")
    if words_announcement:
        words_announcement = words_announcement.replace("**", "")  # Already here
        words_announcement = self._replace_greeting(words_announcement, state.greeting)
        words_announcement = self._remove_markdown(words_announcement)  # ✅ ADD (redundant but safe)
        message_parts.append(words_announcement)
    
    # 4. Instruction after
    instruction_after = question.get("instruction_after", "")
    if instruction_after:
        instruction_after = self._replace_greeting(instruction_after, state.greeting)
        instruction_after = self._remove_markdown(instruction_after)  # ✅ ADD
        message_parts.append(instruction_after)
```

### 4. Update JSON - Remove Markdown (Alternative - Better approach)

**HOẶC**: Update JSON trực tiếp để remove markdown bold:

1. **lang_repetition** (dòng 352):
   ```json
   "question": "Bây giờ {pronoun} hãy nhắc lại câu tôi đọc. Chỉ được nghe MỘT LẦN thôi nhé.\n\nCâu này là: Không có nếu, và, hoặc nhưng gì cả.\n\n{Pronoun} nhắc lại nhé!"
   ```

2. **lang_comprehension_3step** (dòng 367):
   ```json
   "question": "Bây giờ tôi sẽ yêu cầu {pronoun} làm 3 việc bằng cách NÓI.\n\nThứ nhất: Nói 'Tôi hiểu rồi'\nThứ hai: Đếm từ 1 đến 3\nThứ ba: Nói 'Xong rồi'\n\n{Pronoun} hãy làm theo thứ tự nhé. Bắt đầu!"
   ```

3. **lang_comprehension_listening** (dòng 385):
   ```json
   "question": "Tôi sẽ đọc một câu, {pronoun} lắng nghe rồi trả lời câu hỏi nhé.\n\nCâu này là: Con ong chăm chỉ bay qua vườn hoa.\n\n{Pronoun} cho biết con ong đang làm gì?"
   ```

4. **Clock drawing** - Tìm và remove ** từ target_time display

## 📝 RECOMMENDED APPROACH

**Cách 1 (Code-level)**: Thêm `_remove_markdown()` method và apply ở tất cả nơi format text
- ✅ Flexible, tự động handle
- ❌ Cần sửa nhiều chỗ

**Cách 2 (JSON-level)**: Remove markdown trực tiếp trong JSON
- ✅ Cleaner, không cần code changes
- ✅ Faster, không cần processing

**RECOMMEND**: Dùng **Cách 2** - update JSON trực tiếp vì đơn giản và hiệu quả hơn.

## ✅ VERIFICATION

Sau khi sửa, test:
- [ ] lang_repetition: Không còn **
- [ ] lang_comprehension_3step: Không còn **
- [ ] lang_comprehension_listening: Không còn **
- [ ] Clock drawing: Không còn ** ở target_time

