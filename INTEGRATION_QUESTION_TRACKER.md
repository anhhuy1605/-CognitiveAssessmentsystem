# Question Tracker Integration - Complete Guide

## 🎯 Mục Tiêu

Tạo hệ thống track câu hỏi đang tiến hành để các TSX components (special interfaces) hiện lên đúng nơi đúng lúc.

## 📋 Files Đã Tạo

### 1. Hook: `frontend/hooks/useQuestionTracker.ts`
- Hook để track current question state
- Methods: setCurrentQuestion, isQuestionActive, clearCurrentQuestion
- Auto-sync với messages

### 2. Provider: `frontend/components/mmse-question-types/QuestionTrackerProvider.tsx`
- Context provider cho question tracker
- Auto-sync với messages array
- Provides tracker context to children

### 3. Renderer: `frontend/components/mmse-question-types/QuestionRenderer.tsx`
- Smart renderer chỉ render khi question active
- Sử dụng tracker context để check
- Only renders special interfaces when needed

### 4. Enhanced Interface: `frontend/components/mmse-chatbot/ChatInterfaceWithTracker.tsx`
- Enhanced ChatInterface với question tracker
- Automatically tracks questions from messages
- Renders special interfaces only for active question

## 🔧 Integration Steps

### Step 1: Update mmse-chatbot/page.tsx

**Tìm import ChatInterface:**
```typescript
import ChatInterface from '@/components/mmse-chatbot/ChatInterface';
```

**Thay bằng:**
```typescript
import ChatInterfaceWithTracker from '@/components/mmse-chatbot/ChatInterfaceWithTracker';
```

**Tìm phần sử dụng ChatInterface:**
```typescript
<ChatInterface
  messages={session.messages}
  ...
/>
```

**Thay bằng:**
```typescript
<ChatInterfaceWithTracker
  messages={session.messages}
  ...
/>
```

### Step 2: Update addBotMessage to set question state

**Trong addBotMessage, sau khi add message:**

```typescript
const addBotMessage = (session: any, message: string, metadata?: any) => {
    const botMessage: Message = {
        id: `bot_${Date.now()}`,
        type: "bot",
        content: message,
        timestamp: new Date(),
        hiddenContent: metadata?.hidden_content || metadata?.hiddenContent,
        isRevealed: false,
        domain: metadata?.domain,
        questionId: metadata?.question_id,
        questionCategory: metadata?.question_category || metadata?.category,
        displayMode: metadata?.display_mode,
        ttsText: metadata?.tts_text || message
    };
    
    setSession(prev => {
        if (!prev) return prev;
        return {
            ...prev,
            messages: [...prev.messages, botMessage]
        };
    });
    
    // ✅ Question tracker will auto-sync with messages
    // No need to manually set, tracker syncs automatically
};
```

### Step 3: (Optional) Manual question tracking

**Nếu cần manual control, sử dụng hook:**

```typescript
import { useQuestionTracker } from '@/hooks/useQuestionTracker';

// In component
const { setCurrentQuestion, isQuestionActive } = useQuestionTracker();

// When question arrives
useEffect(() => {
    const lastMessage = session.messages[session.messages.length - 1];
    if (lastMessage?.questionId && lastMessage.type === 'bot') {
        setCurrentQuestion({
            questionId: lastMessage.questionId,
            questionCategory: lastMessage.questionCategory || '',
            domain: lastMessage.domain || '',
            index: session.messages.length - 1,
            isActive: true,
            metadata: {
                displayMode: lastMessage.displayMode,
                hiddenContent: lastMessage.hiddenContent,
            }
        });
    }
}, [session.messages, setCurrentQuestion]);
```

## ✅ How It Works

### 1. Message Flow
```
Backend sends question
  → Frontend receives in handleUserInput
    → addBotMessage adds to session.messages
      → ChatInterfaceWithTracker receives messages
        → QuestionTrackerProvider syncs with messages
          → Current question detected automatically
            → QuestionRenderer checks if active
              → Renders special interface if active
```

### 2. Question Tracking
- Tracker automatically syncs with messages array
- Last bot message with questionId becomes current question
- Previous questions are marked inactive
- Question history is maintained

### 3. Rendering Logic
- QuestionRenderer only renders if question is active
- Special interfaces only show for active question
- Previous questions' interfaces are automatically hidden

## 🚀 Benefits

1. **Automatic Tracking**: No manual state management needed
2. **Precise Rendering**: Interfaces only render when question is active
3. **Clean State**: Previous questions are automatically cleaned up
4. **Type Safe**: Full TypeScript support
5. **Easy Integration**: Just replace ChatInterface with ChatInterfaceWithTracker

## ✅ Verification

Sau khi integrate:

1. **Test Serial 7s**:
   - Complete đến Serial 7s question
   - ✅ Check: Serial7sInterface chỉ render khi question active
   - ✅ Check: Interface disappears khi move to next question

2. **Test Clock Drawing**:
   - Complete đến clock question
   - ✅ Check: ClockDrawingModal chỉ render khi question active

3. **Test Word Recall**:
   - Complete registration
   - Wait for recall question
   - ✅ Check: WordRecallInterface chỉ render khi recall question active

4. **Test Multiple Questions**:
   - Complete multiple special questions
   - ✅ Check: Only current question's interface renders
   - ✅ Check: Previous interfaces are hidden

## 📝 Notes

- Tracker syncs automatically with messages
- No need to manually track question state
- Previous questions are preserved in history
- Current question is always the last bot message with questionId

