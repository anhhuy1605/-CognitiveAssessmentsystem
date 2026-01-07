# Complete Fix & Test Guide - Tất Cả Trong Một

## 🎯 3 Bugs Cần Fix

1. **Registration Words Lộ** → Fix backend _format_question_text (✅ ĐÃ ĐÚNG)
2. **Hidden Content - TTS Phải Đọc** → Fix backend get_current_question + frontend TTS
3. **Clock Drawing Modal Không Popup** → Fix ChatInterface integration

---

## 📋 FIX 1: Backend - get_current_question() - Thêm tts_text

### File: `backend/services/mmse_chatbot_service.py`
### Method: `get_current_question()` 
### Tìm: Phần return statement (sau khi format question_text)

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

**THAY THẾ bằng:**
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

## 📋 FIX 2: Frontend - ChatInterface.tsx

### File: `frontend/components/mmse-chatbot/ChatInterface.tsx`

**2.1. Thêm ttsText vào interface:**

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

**Thêm dòng:**
```typescript
  ttsText?: string;  // ✅ FIX: Full text for TTS (includes hidden content)
```

**2.2. Sửa auto-speak useEffect:**

**Tìm useEffect cho auto-speak, thay bằng:**
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

**2.3. Đảm bảo QuestionTypeRenderer render ClockDrawing:**

**Tìm phần render QuestionTypeRenderer, đảm bảo có đầy đủ:**
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

## 📋 FIX 3: Frontend - page.tsx

### File: `frontend/app/(main)/mmse-chatbot/page.tsx`

**3.1. Sửa addBotMessage:**

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
        ttsText: metadata?.tts_text || message  // ✅ FIX: Use tts_text for TTS
    };
```

**3.2. Sửa speakText call:**

**Tìm:**
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

**3.3. Đảm bảo return dùng ChatInterface:**

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

## 📋 FIX 4: HiddenMessage.tsx

### File: `frontend/components/mmse-question-types/HiddenMessage.tsx`

**Tìm processText function, thay bằng:**
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

## 🚀 TEST SHORTCUTS

### Test 1: Registration Words (Không Lộ, TTS Đọc)
```
URL: http://localhost:3000/mmse-chatbot
Steps:
1. Start test
2. Complete registration question
3. ✅ CHECK: Message KHÔNG có "Con mèo, Chiếc xe, Cây lúa"
4. ✅ CHECK: Bật voice → TTS vẫn đọc words
```

### Test 2: Hidden Content (TTS Đọc, UI Hide)
```
URL: http://localhost:3000/mmse-chatbot
Steps:
1. Complete repetition question
2. ✅ CHECK: Question text hiển thị: "Bây giờ bạn hãy nhắc lại..."
3. ✅ CHECK: Answer bị [HIDDEN] trong UI
4. ✅ CHECK: Bật voice → TTS đọc cả answer
```

### Test 3: Clock Drawing Modal
```
URL: http://localhost:3000/mmse-chatbot
Steps:
1. Complete test đến clock drawing question
2. ✅ CHECK: Button "Mở bảng vẽ đồng hồ" xuất hiện
3. Click button
4. ✅ CHECK: Modal popup với whiteboard
5. ✅ CHECK: Vẽ được trên canvas
6. ✅ CHECK: Submit button hoạt động
```

### Test 4: Comprehensive Results
```
URL: http://localhost:3000/results/comprehensive?sessionId=<session_id>
Steps:
1. Complete full test
2. Navigate to comprehensive results
3. ✅ CHECK: Page loads với đầy đủ data
4. ✅ CHECK: SHAP explanations hiển thị
5. ✅ CHECK: Citations hiển thị
6. ✅ CHECK: PDF export works
```

---

## ✅ Verification Checklist

Sau khi apply tất cả fixes:

- [ ] Backend: get_current_question() có tts_text trong metadata
- [ ] Frontend: ChatInterface có ttsText trong ChatMessage interface
- [ ] Frontend: Auto-speak dùng ttsText
- [ ] Frontend: page.tsx addBotMessage có ttsText
- [ ] Frontend: page.tsx return dùng ChatInterface
- [ ] Frontend: ChatInterface render QuestionTypeRenderer
- [ ] Frontend: HiddenMessage processText chỉ replace specific strings
- [ ] Test: Registration words không lộ
- [ ] Test: TTS đọc hidden content
- [ ] Test: Clock drawing modal popup

---

## 📝 Quick Reference

**Files to edit:**
1. `backend/services/mmse_chatbot_service.py` - get_current_question()
2. `frontend/components/mmse-chatbot/ChatInterface.tsx` - ttsText + QuestionTypeRenderer
3. `frontend/app/(main)/mmse-chatbot/page.tsx` - addBotMessage + ChatInterface
4. `frontend/components/mmse-question-types/HiddenMessage.tsx` - processText

**Test URLs:**
- Chatbot: `/mmse-chatbot`
- Comprehensive: `/results/comprehensive?sessionId=<id>`
- Menu: `/menu`





