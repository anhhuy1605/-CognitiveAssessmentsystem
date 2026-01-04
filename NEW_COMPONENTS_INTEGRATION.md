# Hướng Dẫn Tích Hợp Components Mới - MMSE Chatbot

## ✅ ĐÃ TẠO

1. **`HiddenMessage.tsx`** - Component để ẩn content nhạy cảm
2. **`ClockDrawingWhiteboard.tsx`** - Whiteboard cho clock drawing test

## 🔧 CẦN TÍCH HỢP

### 1. Update QuestionTypeRenderer để thêm ClockDrawingWhiteboard

**File**: `frontend/components/mmse-question-types/QuestionTypeRenderer.tsx`

**Thêm import:**
```typescript
import ClockDrawingWhiteboard from './ClockDrawingWhiteboard';
```

**Thêm case cho clock drawing:**
```typescript
// Clock Drawing (Visual)
if (normalizedId.includes('clock') || normalizedId.includes('visual_clock')) {
  return (
    <ClockDrawingWhiteboard
      targetTime={metadata?.target_time || "11:10"}
      onSubmit={(imageData) => {
        // Submit clock drawing image to backend
        onComplete?.({ imageData, questionId });
      }}
      onCancel={() => {
        // Handle cancel
      }}
      elderlyFriendly={true}
      canvasSize={400}
    />
  );
}
```

### 2. Update Main Page để dùng HiddenMessage Component

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

**Thêm import:**
```typescript
import HiddenMessage from "@/components/mmse-question-types/HiddenMessage";
```

**Thay thế `renderContentWithHiddenWords` bằng HiddenMessage:**

**TÌM (dòng ~1829-1835):**
```typescript
<p className="whitespace-pre-wrap">
  {renderContentWithHiddenWords(
    message.content, 
    message.hiddenContent, 
    message.isRevealed
  )}
</p>
```

**THAY THẾ BẰNG:**
```typescript
<HiddenMessage
  visibleText={message.content}
  hiddenContent={message.hiddenContent}
  isRevealed={message.isRevealed}
  textSize="lg"
  elderlyFriendly={true}
/>
```

### 3. Update Backend để trả về hiddenContent Metadata

**File**: `backend/services/mmse_chatbot_service.py`

**Trong `get_current_question()` method, thêm hiddenContent vào metadata:**

```python
# For registration - hide words
if domain == TestDomain.REGISTRATION:
    words = question.get("words", [])
    metadata["hidden_content"] = words  # ✅ ADD: For frontend to hide

# For recall - hide words (should not be shown)
if domain == TestDomain.RECALL:
    # Don't include words in metadata - they should never be shown
    pass

# For repetition - hide the sentence
if actual_question_id == "lang_repetition":
    correct_answer = question.get("correct_answer", "")
    if correct_answer:
        metadata["hidden_content"] = [correct_answer]  # ✅ ADD

# For comprehension - hide the sentence
if actual_question_id == "lang_comprehension_listening":
    # Extract sentence from question (if present)
    # Or add to hidden_content metadata
    pass

# For 3-step command - hide the steps
if actual_question_id == "lang_comprehension_3step":
    # Steps are in question text with **, should be hidden
    # Extract steps and add to hidden_content
    pass
```

### 4. Update addBotMessage để nhận hiddenContent

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

**Tìm function `addBotMessage` và đảm bảo nó nhận hiddenContent:**

```typescript
const addBotMessage = (
  session: Session, 
  content: string, 
  options?: {
    domain?: string;
    questionId?: string;
    questionCategory?: string;
    displayMode?: string;
    hiddenContent?: string[];  // ✅ ADD
    score?: {...};
  }
) => {
  // ... existing code ...
  
  const newMessage: Message = {
    // ... existing fields ...
    hiddenContent: options?.hiddenContent || [],  // ✅ ADD
    isRevealed: false,  // ✅ ADD
  };
  
  // ... rest of function ...
};
```

### 5. Update Backend API để trả về hiddenContent

**File**: `backend/services/mmse_chatbot_api.py`

**Trong `submit_answer()` endpoint, thêm hiddenContent vào response:**

```python
# After getting message and metadata from chatbot_service
if metadata.get('hidden_content'):
    response_data['hidden_content'] = metadata['hidden_content']
```

**Trong `get_questions()` endpoint, thêm hiddenContent vào question data:**

```python
# For each question, include hidden_content if applicable
question_data = {
    # ... existing fields ...
    'hidden_content': question.get('hidden_content', []),  # ✅ ADD
}
```

## 📝 JSON UPDATES CẦN THIẾT

### Thêm hidden_content field vào các questions cần ẩn:

1. **lang_repetition**:
```json
"hidden_content": ["Không có nếu, và, hoặc nhưng gì cả"]
```

2. **lang_comprehension_3step**:
```json
"hidden_content": ["Nói 'Tôi hiểu rồi'", "Đếm từ 1 đến 3", "Nói 'Xong rồi'"]
```

3. **lang_comprehension_listening**:
```json
"hidden_content": ["Con ong chăm chỉ bay qua vườn hoa"]
```

4. **visual_clock_drawing**:
```json
"hidden_content": ["11 giờ 10 phút"]  // If target time should be hidden
```

## ✅ VERIFICATION CHECKLIST

- [ ] HiddenMessage component được import và sử dụng
- [ ] ClockDrawingWhiteboard được tích hợp vào QuestionTypeRenderer
- [ ] Backend trả về hiddenContent trong metadata
- [ ] Frontend nhận và xử lý hiddenContent đúng
- [ ] JSON có hidden_content fields cho các questions cần ẩn
- [ ] Clock drawing có thể submit image
- [ ] UI mượt mà, không crash
- [ ] Thân thiện với người già (text lớn, controls dễ dùng)

## 🎨 UI/UX REQUIREMENTS

- ✅ Text size lớn (lg/xl) cho người già
- ✅ Buttons lớn, dễ click
- ✅ Colors contrast cao
- ✅ Simple, clean design
- ✅ No complex animations
- ✅ Clear instructions
- ✅ Error handling graceful

## 🚀 NEXT STEPS

1. Test HiddenMessage với các messages có hiddenContent
2. Test ClockDrawingWhiteboard với canvas drawing
3. Test integration với backend API
4. Verify không có conflicts với existing endpoints
5. Test với người dùng thật (nếu có thể)





