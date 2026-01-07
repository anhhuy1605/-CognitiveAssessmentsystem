# Quick Fix Summary - 3 Bugs

## 🐛 Bug 1: Registration Words Vẫn Lộ

**Vấn đề**: "Con mèo, Chiếc xe, Cây lúa" hiển thị trong message

**Fix**: Backend `_format_question_text()` cần KHÔNG thêm words_announcement vào question text, chỉ thêm vào hidden_content metadata

## 🐛 Bug 2: Câu Hỏi Bị Ẩn Hoàn Toàn

**Vấn đề**: Repetition, comprehension questions bị ẩn hẳn

**Fix**: HiddenMessage.tsx - processText() chỉ replace specific strings, không hide toàn bộ text

## 🐛 Bug 3: Clock Drawing Whiteboard Không Popup

**Vấn đề**: Không thấy modal để vẽ

**Fix**: 
1. Check mmse-chatbot/page.tsx có dùng ChatInterface?
2. Check ChatInterface có render QuestionTypeRenderer?
3. Check QuestionTypeRenderer có render ClockDrawingModal?

---

## 📋 Files Cần Check/Sửa

1. `backend/services/mmse_chatbot_service.py` - _format_question_text()
2. `frontend/components/mmse-question-types/HiddenMessage.tsx` - processText()
3. `frontend/app/(main)/mmse-chatbot/page.tsx` - ChatInterface integration
4. `frontend/components/mmse-chatbot/ChatInterface.tsx` - QuestionTypeRenderer integration

**Xem chi tiết trong: BUG_FIX_GUIDE.md**





