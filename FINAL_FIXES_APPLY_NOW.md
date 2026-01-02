# Final Fixes - Apply Now

## 🎯 3 Bugs Cần Fix Ngay

### Bug 1: Registration Words Lộ
**Fix**: Backend _format_question_text() không thêm words_announcement vào text

### Bug 2: Hidden Content - TTS Phải Đọc
**Fix**: 
- Backend: tts_text bao gồm hidden content
- Frontend: TTS dùng ttsText, UI dùng content (đã hide)

### Bug 3: Clock Drawing Modal Không Popup
**Fix**: Đảm bảo QuestionTypeRenderer render ClockDrawingModal

---

## 📋 Files Cần Sửa (Theo Thứ Tự)

### 1. backend/services/mmse_chatbot_service.py

**Tìm**: `def _format_question_text` (line ~730)

**Sửa**: Xóa phần thêm words_announcement vào message_parts

**Tìm**: `def get_current_question` (line ~790)

**Sửa**: Thêm tts_text vào metadata (bao gồm hidden content)

### 2. frontend/components/mmse-question-types/HiddenMessage.tsx

**Tìm**: `const processText = (text: string)`

**Sửa**: Chỉ replace specific strings, không hide toàn bộ

### 3. frontend/components/mmse-chatbot/ChatInterface.tsx

**Tìm**: `interface ChatMessage`

**Sửa**: Thêm `ttsText?: string`

**Tìm**: Auto-speak useEffect

**Sửa**: Dùng `message.ttsText` thay vì `message.content`

**Tìm**: QuestionTypeRenderer rendering

**Sửa**: Đảm bảo có render với đầy đủ props

### 4. frontend/app/(main)/mmse-chatbot/page.tsx

**Tìm**: `const addBotMessage`

**Sửa**: Thêm `ttsText: metadata?.tts_text || message`

**Tìm**: `return` statement

**Sửa**: Đảm bảo dùng ChatInterface component

---

## ✅ Test Shortcuts

Sau khi fix, test ngay:

1. **Registration**: `/mmse-chatbot` → Complete registration → Check words không lộ, TTS đọc
2. **Hidden Content**: Complete repetition → Check answer hidden, TTS đọc
3. **Clock Drawing**: Complete đến clock question → Check modal popup

**Xem chi tiết trong: TEST_SHORTCUTS.md**

