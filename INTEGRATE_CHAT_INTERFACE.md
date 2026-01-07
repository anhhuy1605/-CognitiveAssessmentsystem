# Hướng Dẫn Tích Hợp ChatInterface Component

## ✅ ĐÃ TẠO

**File**: `frontend/components/mmse-chatbot/ChatInterface.tsx`

Component chat interface mới, đẹp, chuyên nghiệp với:
- HiddenMessage integration
- QuestionTypeRenderer support
- Elderly-friendly design
- Smooth animations
- Audio recording/upload/playback

## 🔧 TÍCH HỢP VÀO PAGE

### Option 1: Thay Thế Toàn Bộ Chat Area (RECOMMENDED)

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

**TÌM** (dòng ~1796-2054):
- Phần `{/* Messages */}` (dòng 1796)
- Phần `{/* Input Area */}` (dòng 1956)

**THAY THẾ BẰNG**:

```typescript
<ChatInterface
  messages={session.messages.map(msg => ({
    ...msg,
    timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
  }))}
  inputText={inputText}
  onInputChange={setInputText}
  onSendMessage={(text, audioBlob) => handleUserInput(text, audioBlob)}
  isRecording={isRecording}
  onStartRecording={startRecording}
  onStopRecording={stopRecording}
  isProcessing={isProcessing}
  voiceEnabled={voiceEnabled}
  onToggleVoice={() => setVoiceEnabled(!voiceEnabled)}
  currentTranscript={currentTranscript}
  activeQuestionId={activeQuestionId}
  elderlyFriendly={true}
  apiBaseUrl={API_BASE_URL}
/>
```

### Option 2: Giữ Layout, Chỉ Thay Message Rendering

Giữ nguyên header và sidebar, chỉ thay phần messages area.

## 📝 CẦN UPDATE

1. **Import ChatInterface** (đã thêm)
2. **Convert messages format** - Đảm bảo timestamp là Date object
3. **Remove old message rendering code** - Xóa code cũ từ dòng 1796-2054
4. **Update handleUserInput** - Đảm bảo tương thích với ChatInterface callbacks

## ✅ VERIFICATION

Sau khi tích hợp:
- [ ] Messages hiển thị đẹp
- [ ] Hidden content được ẩn
- [ ] Special interfaces hoạt động
- [ ] Recording hoạt động
- [ ] File upload hoạt động
- [ ] Voice TTS hoạt động
- [ ] Không crash
- [ ] UI mượt mà





