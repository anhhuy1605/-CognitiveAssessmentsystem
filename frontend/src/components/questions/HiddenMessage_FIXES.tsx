// FIXES for HiddenMessage.tsx
// ============================
// Ensure hidden content is hidden visually but available for TTS

// ✅ FIX: processText should only replace specific strings, not hide entire text
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

// ✅ IMPORTANT: This component only handles VISUAL hiding
// TTS should use the original text with hidden content included
// The parent component (ChatInterface) should pass full text to TTS

