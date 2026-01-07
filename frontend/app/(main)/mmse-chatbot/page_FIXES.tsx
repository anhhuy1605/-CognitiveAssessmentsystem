// FIXES for mmse-chatbot/page.tsx
// =================================
// Ensure TTS reads hidden content but UI doesn't show it
// 
// NOTE: This is a reference/documentation file showing code patterns.
// These functions are examples and should be integrated into the main page.tsx file.

// Type definitions for reference
interface Message {
    id: string;
    type: "bot" | "user" | "system";
    content: string;
    timestamp: Date;
    hiddenContent?: string[];
    isRevealed?: boolean;
    domain?: string;
    questionId?: string;
    questionCategory?: string;
    displayMode?: string;
    ttsText?: string;
}

// ✅ FIX 1: In handleUserInput or addBotMessage, ensure TTS uses full text
// Example function signature - integrate into your component with proper state
export const speakTextExample = (
    text: string, 
    hiddenContent: string[] | undefined,
    voiceEnabled: boolean,
    isRevealed: boolean
) => {
    if (!voiceEnabled) return;
    
    // ✅ FIX: Build full text for TTS (includes hidden content)
    let fullTextForTTS = text;
    
    if (hiddenContent && hiddenContent.length > 0 && !isRevealed) {
        // Add hidden content to TTS text
        hiddenContent.forEach((hidden) => {
            const cleanHidden = hidden.replace(/\*\*/g, '');
            // Only add if not already in text
            if (!fullTextForTTS.includes(cleanHidden)) {
                fullTextForTTS += `\n\n${cleanHidden}`;
            }
        });
    }
    
    // Use fullTextForTTS for TTS, not the processed text
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(fullTextForTTS);
        utterance.lang = 'vi-VN';
        speechSynthesis.speak(utterance);
    }
};

// ✅ FIX 2: When adding bot message, use tts_text from metadata if available
// Example function signature - integrate into your component with proper state setters
export const addBotMessageExample = (
    session: any, 
    message: string, 
    metadata: any,
    setSession: (updater: (prev: any) => any) => void,
    voiceEnabled: boolean,
    speakText: (text: string, hiddenContent?: string[]) => void
) => {
    const botMessage: Message = {
        id: `bot_${Date.now()}`,
        type: "bot",
        content: message, // ✅ This is the visible text (without hidden content)
        timestamp: new Date(),
        hiddenContent: metadata?.hidden_content || metadata?.hiddenContent,
        isRevealed: false,
        domain: metadata?.domain,
        questionId: metadata?.question_id,
        questionCategory: metadata?.question_category || metadata?.category,
        displayMode: metadata?.display_mode,
        ttsText: metadata?.tts_text || message  // ✅ FIX: Use tts_text for TTS (includes hidden content)
    };
    
    setSession((prev: any) => {
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

// ✅ FIX 3: Ensure ChatInterface is used and passes correct props
// Example JSX - integrate into your component's return statement
/*
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
*/





