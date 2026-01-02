# Bug Fix Guide - Frontend Integration Issues

## 🐛 Các Bugs Cần Fix

### Bug 1: Registration Words Vẫn Lộ
**Mô tả**: "Con mèo, Chiếc xe, Cây lúa" vẫn hiển thị trong chatbot

### Bug 2: Câu Hỏi Bị Ẩn Hoàn Toàn  
**Mô tả**: Một số câu hỏi (repetition, comprehension) bị ẩn hẳn

### Bug 3: Clock Drawing Whiteboard Không Popup
**Mô tả**: Không thấy whiteboard để vẽ đồng hồ

---

## ✅ Status Check

Từ kiểm tra:
- ✅ ChatInterface.tsx có HiddenMessage import
- ✅ QuestionTypeRenderer.tsx có ClockDrawingModal
- ⚠️ mmse-chatbot/page.tsx có mention ChatInterface nhưng chưa rõ có import/use không

---

## 🔧 Fix 1: Registration Words - Backend

### File: `backend/services/mmse_chatbot_service.py`
### Method: `_format_question_text()`

**Vấn đề**: words_announcement được include trong question text

**Fix**: Đảm bảo words_announcement KHÔNG được thêm vào question text được trả về, chỉ thêm vào hidden_content

**Code cần check**:
```python
def _format_question_text(self, question_data: dict, session_id: str) -> str:
    # ... existing code ...
    
    # ✅ FIX: Đảm bảo words_announcement KHÔNG được thêm vào text
    # Chỉ thêm instruction, question, instruction_after
    # words_announcement sẽ được thêm vào hidden_content trong metadata
    
    if question_id == 'reg_01':
        # KHÔNG thêm words_announcement vào message_parts
        # words sẽ được announce bằng TTS và thêm vào hidden_content
        pass
```

---

## 🔧 Fix 2: Hidden Content Logic - HiddenMessage Component

### File: `frontend/components/mmse-question-types/HiddenMessage.tsx`

**Vấn đề**: processText có thể đang hide toàn bộ text thay vì chỉ hide specific strings

**Fix**: Đảm bảo processText chỉ replace specific hidden strings với placeholder, không hide toàn bộ text

**Code cần check/sửa**:
```typescript
const processText = (text: string): string => {
    if (!hiddenContent || hiddenContent.length === 0 || localRevealed) {
        return text; // ✅ Return original text nếu không có hidden content
    }
    
    let processed = text;
    hiddenContent.forEach((hidden) => {
        const cleanHidden = hidden.replace(/\*\*/g, '');
        // ✅ Chỉ replace exact matches, không replace toàn bộ
        const regex = new RegExp(cleanHidden.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        processed = processed.replace(regex, placeholder);
    });
    
    return processed; // ✅ Luôn return text (có thể đã được replace)
};
```

**Lưu ý**: 
- Nếu question text không chứa hidden strings, text sẽ hiển thị bình thường
- Chỉ những strings trong hiddenContent mới được replace

---

## 🔧 Fix 3: Clock Drawing Modal - Page Integration

### File: `frontend/app/(main)/mmse-chatbot/page.tsx`

**Vấn đề**: ClockDrawingModal có thể chưa được render vì page không dùng QuestionTypeRenderer đúng cách

**Fix**: Đảm bảo:
1. Page sử dụng ChatInterface component
2. ChatInterface pass props đúng cho QuestionTypeRenderer
3. QuestionTypeRenderer render ClockDrawingModal cho clock drawing questions

**Check**:
1. Page có import và sử dụng ChatInterface?
2. ChatInterface có render QuestionTypeRenderer?
3. QuestionTypeRenderer có check clock drawing question ID?

---

## 📋 Action Plan

### Step 1: Check mmse-chatbot/page.tsx
```bash
# Check xem page có dùng ChatInterface không
grep -n "ChatInterface\|QuestionTypeRenderer" frontend/app/(main)/mmse-chatbot/page.tsx
```

### Step 2: Fix Backend _format_question_text
- Đảm bảo words_announcement KHÔNG được thêm vào question text
- Chỉ thêm vào hidden_content metadata

### Step 3: Fix HiddenMessage processText
- Đảm bảo chỉ replace specific strings
- Không hide toàn bộ text

### Step 4: Verify ClockDrawingModal
- Check QuestionTypeRenderer có render ClockDrawingModal
- Check ChatInterface có pass props correctly
- Check page có use ChatInterface

---

## 🔍 Files Cần Check/Edit

1. **backend/services/mmse_chatbot_service.py**
   - Method: `_format_question_text()` - Line ~730
   - Method: `get_current_question()` - Check metadata hidden_content

2. **frontend/components/mmse-question-types/HiddenMessage.tsx**
   - Function: `processText()` - Check logic

3. **frontend/app/(main)/mmse-chatbot/page.tsx**
   - Check ChatInterface usage
   - Check QuestionTypeRenderer integration

4. **frontend/components/mmse-chatbot/ChatInterface.tsx**
   - Check QuestionTypeRenderer rendering
   - Check props passing

---

## ✅ Verification Steps

Sau khi fix:

1. **Registration Words**:
   - Complete registration question
   - Verify words KHÔNG hiển thị trong chatbot message
   - Verify words chỉ được announce bằng TTS

2. **Hidden Content**:
   - Complete repetition/comprehension questions
   - Verify question text vẫn hiển thị
   - Verify chỉ answers bị hide

3. **Clock Drawing**:
   - Reach clock drawing question
   - Verify modal popup appears
   - Verify can draw và submit

---

## 📝 Notes

- Tất cả fixes cần test thoroughly
- Backend và Frontend cần sync về hidden_content
- QuestionTypeRenderer cần đúng question ID matching

