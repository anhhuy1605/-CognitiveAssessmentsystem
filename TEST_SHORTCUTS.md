# Test Shortcuts - Quick Testing Guide

## 🚀 Quick Test Commands

### 1. Test Registration Words (Không Lộ)
```
1. Start chatbot
2. Navigate to: /mmse-chatbot
3. Complete registration question
4. ✅ CHECK: Words "Con mèo, Chiếc xe, Cây lúa" KHÔNG hiển thị trong message
5. ✅ CHECK: TTS vẫn đọc words (bật voice)
```

### 2. Test Hidden Content (TTS Đọc Nhưng Không Hiển Thị)
```
1. Complete repetition question
2. ✅ CHECK: Question text vẫn hiển thị: "Bây giờ bạn hãy nhắc lại câu tôi đọc..."
3. ✅ CHECK: Answer "Không có nếu, và, hoặc nhưng gì cả" KHÔNG hiển thị (bị [HIDDEN])
4. ✅ CHECK: TTS vẫn đọc cả answer (bật voice)
```

### 3. Test Clock Drawing Modal
```
1. Complete test đến clock drawing question
2. ✅ CHECK: Button "Mở bảng vẽ đồng hồ" xuất hiện
3. Click button
4. ✅ CHECK: Modal popup với whiteboard
5. ✅ CHECK: Có thể vẽ trên canvas
6. ✅ CHECK: Submit button hoạt động
```

### 4. Test Comprehensive Results
```
1. Complete full MMSE test
2. Navigate to: /results/comprehensive?sessionId=<session_id>
3. ✅ CHECK: Comprehensive results page loads
4. ✅ CHECK: SHAP explanations hiển thị
5. ✅ CHECK: Citations hiển thị
6. ✅ CHECK: PDF export works
```

## 🔗 Direct URLs

### Chatbot
```
http://localhost:3000/mmse-chatbot
```

### Comprehensive Results
```
http://localhost:3000/results/comprehensive?sessionId=<session_id>
```

### Menu (với link comprehensive)
```
http://localhost:3000/menu
```

## 📋 Test Checklist

### Backend
- [ ] Registration words không trong question text
- [ ] tts_text có hidden content
- [ ] hidden_content trong metadata

### Frontend
- [ ] HiddenMessage chỉ hide specific strings
- [ ] TTS dùng ttsText (có hidden content)
- [ ] ChatInterface render QuestionTypeRenderer
- [ ] ClockDrawingModal popup đúng

## 🎯 Expected Behavior

### Registration Question
- **UI**: "Bây giờ bạn hãy chú ý lắng nghe nhé. Tôi sẽ đọc 3 từ, bạn hãy nhớ kỹ.\n\nBạn hãy nhắc lại 3 từ vừa nghe được không?\n\nBạn hãy nhớ 3 từ này nhé..."
- **TTS**: "Bây giờ bạn hãy chú ý lắng nghe nhé. Tôi sẽ đọc 3 từ, bạn hãy nhớ kỹ.\n\nBa từ đó là: Con mèo, Chiếc xe, Cây lúa.\n\nBạn hãy nhắc lại 3 từ vừa nghe được không?..."
- **Hidden**: ["Con mèo", "Chiếc xe", "Cây lúa"]

### Repetition Question
- **UI**: "Bây giờ bạn hãy nhắc lại câu tôi đọc. Chỉ được nghe MỘT LẦN thôi nhé.\n\nBạn nhắc lại nhé!"
- **TTS**: "Bây giờ bạn hãy nhắc lại câu tôi đọc. Chỉ được nghe MỘT LẦN thôi nhé.\n\nBạn nhắc lại nhé!\n\nKhông có nếu, và, hoặc nhưng gì cả"
- **Hidden**: ["Không có nếu, và, hoặc nhưng gì cả"]

### Clock Drawing Question
- **UI**: Question text + Button "Mở bảng vẽ đồng hồ"
- **Action**: Click button → Modal popup
- **Modal**: Whiteboard với canvas, tools, submit button





