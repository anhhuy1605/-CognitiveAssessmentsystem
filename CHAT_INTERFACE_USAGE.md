# Cách Sử Dụng ChatInterface Component Mới

## ✅ ĐÃ TẠO

**File**: `frontend/components/mmse-chatbot/ChatInterface.tsx`

Component chat interface mới, đẹp, chuyên nghiệp, thân thiện người già.

## 🎨 FEATURES

- ✅ **HiddenMessage integration** - Tự động ẩn content nhạy cảm
- ✅ **QuestionTypeRenderer support** - Hỗ trợ special interfaces
- ✅ **Elderly-friendly** - Text lớn, buttons lớn, dễ sử dụng
- ✅ **Smooth animations** - Framer Motion animations
- ✅ **Audio support** - Recording, upload, playback
- ✅ **Voice TTS toggle** - Bật/tắt giọng nói
- ✅ **Score display** - Hiển thị điểm số với badge
- ✅ **Action buttons** - Hỗ trợ action buttons
- ✅ **Responsive** - Hoạt động tốt trên mobile và desktop

## 📝 CÁCH SỬ DỤNG

### 1. Import Component

```typescript
import ChatInterface, { ChatMessage } from '@/components/mmse-chatbot/ChatInterface';
```

### 2. Sử dụng trong Page

```typescript
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [inputText, setInputText] = useState('');
const [isRecording, setIsRecording] = useState(false);
const [isProcessing, setIsProcessing] = useState(false);

// Add message helper
const addMessage = (type: 'bot' | 'user' | 'system', content: string, options?: {
  hiddenContent?: string[];
  questionId?: string;
  questionCategory?: string;
  score?: {...};
}) => {
  const newMessage: ChatMessage = {
    id: `msg_${Date.now()}`,
    type,
    content,
    timestamp: new Date(),
    hiddenContent: options?.hiddenContent,
    isRevealed: false,
    questionId: options?.questionId,
    questionCategory: options?.questionCategory,
    score: options?.score,
  };
  setMessages(prev => [...prev, newMessage]);
};

// Handle send
const handleSend = (text: string, audioBlob?: Blob) => {
  // Add user message
  addMessage('user', text);
  
  // Submit to backend
  // ... your API call ...
  
  // Add bot response
  addMessage('bot', response.message, {
    hiddenContent: response.metadata?.hidden_content,
    questionId: response.metadata?.question_id,
    questionCategory: response.metadata?.category,
  });
};

// Render
<ChatInterface
  messages={messages}
  inputText={inputText}
  onInputChange={setInputText}
  onSendMessage={handleSend}
  isRecording={isRecording}
  onStartRecording={() => setIsRecording(true)}
  onStopRecording={() => setIsRecording(false)}
  isProcessing={isProcessing}
  currentTranscript={currentTranscript}
  activeQuestionId={activeQuestionId}
  elderlyFriendly={true}
  apiBaseUrl={API_BASE_URL}
/>
```

## 🔧 TÍCH HỢP VÀO PAGE HIỆN TẠI

### Option 1: Thay thế toàn bộ chat area

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

**TÌM**: Phần render messages (dòng ~1800-1950)

**THAY THẾ**: Toàn bộ messages area và input area bằng:

```typescript
<ChatInterface
  messages={session.messages.map(msg => ({
    ...msg,
    timestamp: new Date(msg.timestamp)
  }))}
  inputText={inputText}
  onInputChange={setInputText}
  onSendMessage={handleUserInput}
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

### Option 2: Giữ nguyên structure, chỉ thay message rendering

Giữ nguyên layout, chỉ thay phần render messages bằng ChatInterface component.

## ✅ VERIFICATION

Sau khi tích hợp:
- [ ] Messages hiển thị đẹp
- [ ] Hidden content được ẩn đúng
- [ ] Special interfaces hoạt động
- [ ] Recording hoạt động
- [ ] File upload hoạt động
- [ ] Voice TTS hoạt động
- [ ] Không crash
- [ ] UI mượt mà
- [ ] Thân thiện người già

