# Bug Fix Checklist - Frontend Integration Issues

## 🐛 Bugs Được Báo Cáo

### 1. Registration Words Vẫn Lộ
**Mô tả**: Words "Con mèo, Chiếc xe, Cây lúa" vẫn hiển thị trong chatbot messages

**Nguyên nhân có thể**:
- Backend vẫn include words_announcement trong question text
- Frontend không filter/hide words properly
- HiddenMessage component không được sử dụng

### 2. Câu Hỏi Bị Ẩn Hoàn Toàn
**Mô tả**: Một số câu hỏi như repetition, comprehension bị ẩn hẳn

**Nguyên nhân có thể**:
- HiddenMessage đang hide toàn bộ text thay vì chỉ hide specific content
- Question text bị replace với placeholder

### 3. Clock Drawing Whiteboard Không Popup
**Mô tả**: Không thấy whiteboard để vẽ đồng hồ

**Nguyên nhân có thể**:
- ClockDrawingModal chưa được tích hợp vào chatbot page
- QuestionTypeRenderer không render ClockDrawingModal
- ChatInterface không pass props correctly

## ✅ Files Cần Kiểm Tra

1. **frontend/app/(main)/mmse-chatbot/page.tsx**
   - [ ] Có sử dụng ChatInterface?
   - [ ] Có sử dụng QuestionTypeRenderer?
   - [ ] Có pass hiddenContent correctly?

2. **frontend/components/mmse-chatbot/ChatInterface.tsx**
   - [ ] Có import và sử dụng HiddenMessage?
   - [ ] Có handle hiddenContent từ messages?
   - [ ] Có render QuestionTypeRenderer?

3. **frontend/components/mmse-question-types/QuestionTypeRenderer.tsx**
   - [ ] Có import ClockDrawingModal?
   - [ ] Có render ClockDrawingModal cho clock drawing questions?
   - [ ] Có pass props correctly?

4. **backend/services/mmse_chatbot_service.py**
   - [ ] _format_question_text có filter words_announcement?
   - [ ] Có set hidden_content trong metadata?
   - [ ] Có exclude words từ question text?

## 🔧 Fixes Cần Thiết

### Fix 1: Registration Words
- Backend: Đảm bảo words_announcement KHÔNG được include trong question text được gửi
- Frontend: Sử dụng HiddenMessage để hide words

### Fix 2: Hidden Content
- HiddenMessage: Chỉ hide specific strings, không hide toàn bộ
- Question text: Phải luôn hiển thị, chỉ hide answers

### Fix 3: Clock Drawing Modal
- QuestionTypeRenderer: Đảm bảo ClockDrawingModal được render
- ChatInterface: Pass clock drawing props correctly
- Chatbot page: Sử dụng QuestionTypeRenderer

## 📋 Action Items

1. ✅ Check if files exist
2. ⏳ Check integration in chatbot page
3. ⏳ Fix HiddenMessage logic
4. ⏳ Fix ClockDrawingModal integration
5. ⏳ Test all fixes

