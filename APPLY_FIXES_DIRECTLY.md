# Apply Fixes Directly - Code Snippets

## 🎯 Tất Cả Code Cần Copy-Paste

---

## ✅ FIX 1: Backend - _format_question_text (ĐÃ ĐÚNG!)

**Status**: ✅ words_announcement KHÔNG có trong _format_question_text
**Action**: Không cần sửa, đã đúng!

---

## ✅ FIX 2: Backend - get_current_question() - Thêm tts_text

### File: `backend/services/mmse_chatbot_service.py`
### Method: `get_current_question()` - Tìm phần return

**Tìm đoạn này:**
```python
    question_text = self._format_question_text(question_data, session_id)
    
    # Build metadata
    metadata = {
        'domain': domain.value,
        'question_id': question_id,
        ...
    }
    
    return question_text, metadata
```

**Thay thế bằng:**
```python
    question_text = self._format_question_text(question_data, session_id)
    
    # ✅ FIX: Build full text for TTS (includes hidden content)
    tts_text = question_text
    
    # Add words_announcement to TTS text if exists (for registration)
    if question_id == 'reg_01' and 'words_announcement' in question_data:
        words_text = question_data['words_announcement']
        words_text = words_text.replace("**", "")
        words_text = words_text.replace("{pronoun}", self.get_pronoun(session_id, False))
        words_text = words_text.replace("{Pronoun}", self.get_pronoun(session_id, True))
        # Insert words_announcement into TTS text
        parts = question_text.split('\n\n')
        if len(parts) >= 2:
            tts_text = f"{parts[0]}\n\n{words_text}\n\n{parts[1]}"
        else:
            tts_text = f"{question_text}\n\n{words_text}"
    
    # Add other hidden content to TTS text
    if 'hidden_content' in question_data:
        for hidden in question_data['hidden_content']:
            clean_hidden = hidden.replace("**", "")
            if clean_hidden not in tts_text:
                tts_text += f"\n\n{clean_hidden}"
    
    # Build metadata
    metadata = {
        'domain': domain.value,
        'question_id': question_id,
        'question_category': question_data.get('category', ''),
        'display_mode': question_data.get('display_mode', ''),
        'tts_text': tts_text,  # ✅ FIX: Full text for TTS (includes hidden content)
        'hidden_content': question_data.get('hidden_content', [])  # ✅ FIX: Hidden content for UI
    }
    
    # Add words_announcement to hidden_content if exists
    if question_id == 'reg_01' and 'words_announcement' in question_data:
        if 'words_to_recall' in question_data:
            if 'hidden_content' not in metadata:
                metadata['hidden_content'] = []
            metadata['hidden_content'].extend(question_data['words_to_recall'])
    
    # Add clock drawing target time if applicable
    if question_id == 'visual_clock_drawing':
        metadata['target_time'] = state.clock_drawing_target_time
    
    return question_text, metadata  # ✅ Return question_text (without hidden content) for UI
```

---

## ✅ FIX 3: Frontend - ChatInterface.tsx - Thêm ttsText và ClockDrawing

### File: `frontend/components/mmse-chatbot/ChatInterface.tsx`

**1. Thêm ttsText vào interface:**

**Tìm:**
```typescript
export interface ChatMessage {
  id: string;
  type: "bot" | "user" | "system";
  content: string;
  timestamp: Date;
  hiddenContent?: string[];
  ...
}
```

**Thêm:**
```typescript
  ttsText?: string;  // ✅ FIX: Full text for TTS (includes hidden content)
```

**2. Sửa auto-speak useEffect:**

**Tìm:**
```typescript
useEffect(() => {
    if (messages.length > 0 && voiceEnabled) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage.type === 'bot') {
            // speak text
        }
    }
}, [messages, voiceEnabled]);
```

**Thay bằng:**
```typescript
// ✅ FIX: Auto-speak when message arrives (use ttsText)
useEffect(() => {
    if (messages.length > 0 && voiceEnabled) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage.type === 'bot' && lastMessage.ttsText) {
            const utterance = new SpeechSynthesisUtterance(lastMessage.ttsText);
            utterance.lang = 'vi-VN';
            speechSynthesis.speak(utterance);
        }
    }
}, [messages, voiceEnabled]);
```

**3. Đảm bảo QuestionTypeRenderer render ClockDrawing:**

**Tìm phần render QuestionTypeRenderer, đảm bảo có:**
```typescript
{message.type === "bot" && message.questionId && message.questionCategory && 
 requiresSpecialInterface(message.questionId, message.questionCategory) && (
    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <QuestionTypeRenderer
            questionId={message.questionId}
            questionCategory={message.questionCategory}
            displayMode={message.displayMode}
            hiddenContent={message.hiddenContent}
            currentTranscript={message.questionId === activeQuestionId ? currentTranscript : undefined}
            isRecording={isRecording && message.questionId === activeQuestionId}
            onStop={() => {
                if (isRecording && onStopRecording) {
                    onStopRecording();
                }
                const finalAnswer = currentTranscript?.trim() || "Đã hoàn thành";
                if (finalAnswer) {
                    onSendMessage(finalAnswer);
                }
            }}
            onTimeUp={() => {
                if (isRecording && onStopRecording) {
                    onStopRecording();
                }
                const finalAnswer = currentTranscript?.trim() || "Đã kể xong";
                if (finalAnswer) {
                    onSendMessage(finalAnswer);
                }
            }}
            onAnswer={(answer) => {
                console.log("Special interface answer:", answer);
            }}
            onComplete={(result) => {
                console.log("Special interface complete:", result);
                // Handle clock drawing submission
                if (result.imageData) {
                    onSendMessage("", undefined, { imageData: result.imageData, questionId: message.questionId });
                }
            }}
            targetTime={clockDrawingTargetTime}
        />
    </div>
)}
```

---

## ✅ FIX 4: Frontend - page.tsx - addBotMessage và ChatInterface

### File: `frontend/app/(main)/mmse-chatbot/page.tsx`

**1. Sửa addBotMessage:**

**Tìm:**
```typescript
const addBotMessage = (session: any, message: string, metadata?: any) => {
    const botMessage: Message = {
        id: `bot_${Date.now()}`,
        type: "bot",
        content: message,
        ...
    };
```

**Thêm ttsText:**
```typescript
    const botMessage: Message = {
        id: `bot_${Date.now()}`,
        type: "bot",
        content: message, // ✅ Visible text (without hidden content)
        timestamp: new Date(),
        hiddenContent: metadata?.hidden_content || metadata?.hiddenContent,
        isRevealed: false,
        domain: metadata?.domain,
        questionId: metadata?.question_id,
        questionCategory: metadata?.question_category || metadata?.category,
        displayMode: metadata?.display_mode,
        ttsText: metadata?.tts_text || message  // ✅ FIX: Use tts_text for TTS (includes hidden content)
    };
```

**2. Sửa speakText:**

**Tìm:**
```typescript
const speakText = (text: string) => {
    if (!voiceEnabled) return;
    // ... TTS code
};
```

**Thay bằng:**
```typescript
const speakText = (text: string, hiddenContent?: string[]) => {
    if (!voiceEnabled) return;
    
    // ✅ FIX: text đã là ttsText (includes hidden content) từ metadata
    // Không cần thêm hidden content nữa
    
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'vi-VN';
        speechSynthesis.speak(utterance);
    }
};
```

**3. Sửa addBotMessage để dùng ttsText:**

**Tìm phần gọi speakText trong addBotMessage:**
```typescript
    if (voiceEnabled) {
        speakText(botMessage.content);
    }
```

**Thay bằng:**
```typescript
    // ✅ FIX: Use ttsText for TTS, not content
    if (voiceEnabled && botMessage.ttsText) {
        speakText(botMessage.ttsText);
    }
```

**4. Đảm bảo return dùng ChatInterface:**

**Tìm return statement, đảm bảo có:**
```typescript
return (
    <div className="flex flex-col h-screen">
        <ChatInterface
            messages={session.messages}
            currentTranscript={currentTranscript}
            isRecording={isRecording}
            isProcessing={isProcessing}
            voiceEnabled={voiceEnabled}
            onSendMessage={handleUserInput}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onFileUpload={handleFileUpload}
            onToggleVoice={toggleVoice}
            activeQuestionId={session.messages[session.messages.length - 1]?.questionId}
            clockDrawingTargetTime={session.messages[session.messages.length - 1]?.displayMode}
            elderlyFriendly={true}
        />
    </div>
);
```

---

## ✅ FIX 5: HiddenMessage.tsx - Chỉ Hide Specific Strings

### File: `frontend/components/mmse-question-types/HiddenMessage.tsx`

**Tìm processText function:**

**Thay bằng:**
```typescript
const processText = (text: string): string => {
    if (!hiddenContent || hiddenContent.length === 0 || localRevealed) {
        return text; // ✅ Return original text if no hidden content or revealed
    }
    
    let processed = text;
    hiddenContent.forEach((hidden) => {
        // Remove markdown bold if present
        const cleanHidden = hidden.replace(/\*\*/g, '');
        
        // ✅ FIX: Only replace exact matches, preserve rest of text
        // Use word boundaries to avoid partial matches
        const escaped = cleanHidden.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Try with word boundaries first
        let regex = new RegExp(`\\b${escaped}\\b`, 'gi');
        if (!regex.test(processed)) {
            // If no match with word boundaries, try without
            regex = new RegExp(escaped, 'gi');
        }
        processed = processed.replace(regex, placeholder);
    });
    
    return processed; // ✅ Always return text (may have placeholders)
};
```

---

## 🚀 Test Shortcuts

Sau khi apply tất cả fixes:

### Test 1: Registration Words
```
1. /mmse-chatbot
2. Complete registration
3. ✅ Check: Words không hiển thị
4. ✅ Check: TTS đọc words (bật voice)
```

### Test 2: Hidden Content
```
1. Complete repetition question
2. ✅ Check: Question hiển thị
3. ✅ Check: Answer bị [HIDDEN]
4. ✅ Check: TTS đọc cả answer
```

### Test 3: Clock Drawing
```
1. Complete đến clock question
2. ✅ Check: Button "Mở bảng vẽ đồng hồ"
3. ✅ Check: Modal popup
4. ✅ Check: Có thể vẽ và submit
```

---

## ✅ Verification

Sau khi apply:
- [ ] Backend: tts_text có hidden content
- [ ] Frontend: TTS dùng ttsText
- [ ] Frontend: UI dùng content (đã hide)
- [ ] ClockDrawingModal popup
- [ ] Registration words không lộ





