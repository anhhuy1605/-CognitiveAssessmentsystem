# Fixes To Apply - Step by Step

## 🎯 Mục Tiêu

1. ✅ Hidden content được TTS đọc nhưng không hiển thị trên UI
2. ✅ Registration words không lộ trong message
3. ✅ Clock drawing modal popup đúng cách
4. ✅ Tất cả components được tích hợp thực sự

---

## 📋 FIX 1: Backend - _format_question_text()

### File: `backend/services/mmse_chatbot_service.py`
### Method: `_format_question_text()` - Line ~730

**Tìm và thay thế toàn bộ method:**

```python
def _format_question_text(self, question_data: dict, session_id: str) -> str:
    """Format question text with pronoun replacement and proper structure
    ✅ FIX: words_announcement KHÔNG được thêm vào text, chỉ thêm vào hidden_content metadata
    """
    pronoun = self.get_pronoun(session_id, False)
    pronoun_cap = self.get_pronoun(session_id, True)
    
    message_parts = []
    
    # 1. Instruction (if exists)
    if 'instruction' in question_data and question_data['instruction']:
        instruction = question_data['instruction']
        instruction = instruction.replace("{pronoun}", pronoun)
        instruction = instruction.replace("{Pronoun}", pronoun_cap)
        message_parts.append(instruction)
    
    # 2. ✅ FIX: words_announcement KHÔNG được thêm vào text
    # Words sẽ được announce bằng TTS và thêm vào hidden_content metadata
    # KHÔNG thêm vào message_parts để không hiển thị trên UI
    
    # 3. Main question
    if 'question' in question_data:
        question_text = question_data['question']
        question_text = question_text.replace("{pronoun}", pronoun)
        question_text = question_text.replace("{Pronoun}", pronoun_cap)
        message_parts.append(question_text)
    
    # 4. Instruction after (for registration)
    question_id = question_data.get('question_id', '')
    if question_id == 'reg_01':
        if 'instruction_after' in question_data:
            after_text = question_data['instruction_after']
            after_text = after_text.replace("{pronoun}", pronoun)
            after_text = after_text.replace("{Pronoun}", pronoun_cap)
            message_parts.append(after_text)
    
    # Join with double newline for clear separation
    return "\n\n".join(part for part in message_parts if part)
```

---

## 📋 FIX 2: Backend - get_current_question()

### File: `backend/services/mmse_chatbot_service.py`
### Method: `get_current_question()` - Line ~790

**Tìm phần return và sửa metadata:**

```python
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
    
    return question_text, metadata  # ✅ Return question_text (without hidden content) for UI
```

---

## 📋 FIX 3: Frontend - HiddenMessage.tsx

### File: `frontend/components/mmse-question-types/HiddenMessage.tsx`

**Sửa processText function:**

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
        const regex = new RegExp(`\\b${escaped}\\b`, 'gi');
        processed = processed.replace(regex, placeholder);
    });
    
    return processed; // ✅ Always return text (may have placeholders)
};
```

---

## 📋 FIX 4: Frontend - ChatInterface.tsx

### File: `frontend/components/mmse-chatbot/ChatInterface.tsx`

**1. Thêm ttsText vào ChatMessage interface:**

```typescript
export interface ChatMessage {
  // ... existing fields ...
  ttsText?: string;  // ✅ FIX: Full text for TTS (includes hidden content)
}
```

**2. Sửa message rendering để dùng ttsText cho TTS:**

```typescript
// Auto-speak when message arrives (use ttsText)
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

**3. Đảm bảo QuestionTypeRenderer được render:**

```typescript
{message.type === "bot" && message.questionId && message.questionCategory && 
 requiresSpecialInterface(message.questionId, message.questionCategory) && (
    <div className="mt-4 pt-4 border-t">
        <QuestionTypeRenderer
            questionId={message.questionId}
            questionCategory={message.questionCategory}
            displayMode={message.displayMode}
            hiddenContent={message.hiddenContent}
            currentTranscript={currentTranscript}
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

## 📋 FIX 5: Frontend - mmse-chatbot/page.tsx

### File: `frontend/app/(main)/mmse-chatbot/page.tsx`

**1. Đảm bảo import ChatInterface:**

```typescript
import ChatInterface from '@/components/mmse-chatbot/ChatInterface';
```

**2. Sửa addBotMessage để dùng ttsText:**

```typescript
const addBotMessage = (session: any, message: string, metadata?: any) => {
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
    
    setSession(prev => {
        if (!prev) return prev;
        return {
            ...prev,
            messages: [...prev.messages, botMessage]
        };
    });
    
    // ✅ FIX: Use ttsText for TTS, not content
    if (voiceEnabled) {
        speakText(botMessage.ttsText || botMessage.content, botMessage.hiddenContent);
    }
};
```

**3. Đảm bảo return statement dùng ChatInterface:**

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

## ✅ Verification

Sau khi apply fixes:

1. **Registration Words**: 
   - Words không hiển thị trong UI
   - Words vẫn được TTS đọc

2. **Hidden Content**:
   - Question text vẫn hiển thị
   - Chỉ answers bị hide
   - TTS đọc cả hidden content

3. **Clock Drawing**:
   - Modal popup khi đến clock drawing question
   - Có thể vẽ và submit





