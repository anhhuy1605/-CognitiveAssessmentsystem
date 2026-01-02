# -*- coding: utf-8 -*-
"""
PATCH FILE: Backend Changes for Hidden Flags and TTS Text
==========================================================

Apply these changes to backend/services/mmse_chatbot_service.py

## Method 1: Add helper method (before _replace_greeting method, around line 2029)

Add this new method:
"""

def _build_question_text_with_hidden_flags(self, question: Dict, question_text: str, state: SessionState) -> Tuple[str, str]:
    """
    ✅ NEW: Build display text and TTS text separately based on hidden flags
    
    Args:
        question: Question data from JSON
        question_text: Base question text
        state: Session state
        
    Returns:
        Tuple of (display_text, tts_text)
    """
    display_parts = []
    tts_parts = []
    
    # Helper to check if content should be hidden
    def is_hidden_display(field_name: str, default: bool = False) -> bool:
        # Check new format first
        if f"{field_name}_hidden_display" in question:
            return question.get(f"{field_name}_hidden_display", default)
        # Check old format
        if f"{field_name}_hidden" in question:
            return question.get(f"{field_name}_hidden", default)
        # Check global hidden_display flag
        return question.get("hidden_display", default)
    
    def is_hidden_audio(field_name: str, default: bool = False) -> bool:
        # Check new format first
        if f"{field_name}_hidden_audio" in question:
            return question.get(f"{field_name}_hidden_audio", default)
        # Check old format (inverted logic: tts=True means not hidden)
        if f"{field_name}_tts" in question:
            return not question.get(f"{field_name}_tts", True)
        # Check global hidden_audio flag
        return question.get("hidden_audio", default)
    
    # 1. Instruction
    instruction = question.get("instruction", "")
    if instruction:
        instruction = self._replace_greeting(instruction, state.greeting)
        if not is_hidden_display("instruction", False):
            display_parts.append(instruction)
        if not is_hidden_audio("instruction", False):
            tts_parts.append(instruction)
    
    # 2. Main question text
    if question_text:
        if not is_hidden_display("question", False):
            display_parts.append(question_text)
        if not is_hidden_audio("question", False):
            tts_parts.append(question_text)
    
    # 3. Words announcement (for registration)
    words_announcement = question.get("words_announcement", "")
    if words_announcement:
        words_announcement = words_announcement.replace("**", "")
        words_announcement = self._replace_greeting(words_announcement, state.greeting)
        # Default: hidden from display but in TTS
        if not is_hidden_display("words_announcement", True):
            display_parts.append(words_announcement)
        if not is_hidden_audio("words_announcement", False):  # Default: read in TTS
            tts_parts.append(words_announcement)
    
    # 4. Sentence to repeat (for repetition question)
    sentence_to_repeat = question.get("sentence_to_repeat", "")
    if sentence_to_repeat:
        sentence_to_repeat = self._replace_greeting(sentence_to_repeat, state.greeting)
        if not is_hidden_display("sentence_to_repeat", False):
            display_parts.append(sentence_to_repeat)
        if not is_hidden_audio("sentence_to_repeat", False):  # Default: read in TTS
            tts_parts.append(sentence_to_repeat)
    
    # 5. Sentence to listen (for bee question)
    sentence_to_listen = question.get("sentence_to_listen", "")
    if sentence_to_listen:
        sentence_to_listen = self._replace_greeting(sentence_to_listen, state.greeting)
        # Default: hidden from display but in TTS
        if not is_hidden_display("sentence_to_listen", True):
            display_parts.append(sentence_to_listen)
        if not is_hidden_audio("sentence_to_listen", False):  # Default: read in TTS
            tts_parts.append(sentence_to_listen)
    
    # 6. Instruction after (for registration)
    instruction_after = question.get("instruction_after", "")
    if instruction_after:
        instruction_after = self._replace_greeting(instruction_after, state.greeting)
        # Default: completely hidden
        if not is_hidden_display("instruction_after", True):
            display_parts.append(instruction_after)
        if not is_hidden_audio("instruction_after", True):  # Default: don't read
            tts_parts.append(instruction_after)
    
    # Build final texts
    display_text = "\n\n".join(part for part in display_parts if part)
    
    # Check if metadata has tts_text (highest priority)
    metadata = question.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("tts_text"):
        tts_text = self._replace_greeting(metadata.get("tts_text"), state.greeting)
    elif tts_parts:
        tts_text = "\n\n".join(part for part in tts_parts if part)
    else:
        tts_text = display_text  # Fallback
    
    return display_text, tts_text


"""
## Method 2: Replace get_current_question() method (around line 366-471)

REPLACE this section:
"""

# OLD CODE (lines ~395-432):
#         # ✅ v2.1_CORRECTED: Handle instruction fields (instruction_part1, instruction_part2)
#         # For registration domain, combine instruction_part1 and instruction_part2
#         actual_question_id = question.get("question_id", f"{domain.value}_{index}")
#         if domain == TestDomain.REGISTRATION and index == 0:
#             message_parts = []
#             
#             # 1. Instruction
#             instruction = question.get("instruction", "")
#             if instruction:
#                 instruction = self._replace_greeting(instruction, state.greeting)
#                 message_parts.append(instruction)
#             
#             # 2. Question (main question text)
#             if question_text:
#                 message_parts.append(question_text)
#             
#             # 3. Words announcement (for registration)
#             words_announcement = question.get("words_announcement", "")
#             if words_announcement:
#                 # Remove markdown bold if present (safety check)
#                 words_announcement = words_announcement.replace("**", "")
#                 words_announcement = self._replace_greeting(words_announcement, state.greeting)
#                 message_parts.append(words_announcement)
#             
#             # 4. Instruction after (for registration)
#             instruction_after = question.get("instruction_after", "")
#             if instruction_after:
#                 instruction_after = self._replace_greeting(instruction_after, state.greeting)
#                 message_parts.append(instruction_after)
#             
#             # Join with double newline for clear separation
#             question_text = "\n\n".join(part for part in message_parts if part)
#         elif index == 0:
#             # For other domains, use single instruction field
#             instruction = question.get("instruction", "")
#             if instruction and instruction not in question_text:
#                 instruction = self._replace_greeting(instruction, state.greeting)
#                 question_text = f"{instruction}\n\n{question_text}"

# NEW CODE:
        # ✅ NEW: Use helper method to build display and TTS text with hidden flags
        actual_question_id = question.get("question_id", f"{domain.value}_{index}")
        question_text, tts_text = self._build_question_text_with_hidden_flags(question, question_text, state)


"""
## Method 3: Update metadata section (around line 438-458)

REPLACE this section:
"""

# OLD CODE (lines ~438-458):
#         metadata = {
#             "domain": domain.value,
#             "question_index": index,
#             "total_questions": len(questions),
#             "question_id": actual_question_id,  # ✅ Use actual question_id from JSON
#             "points": question.get("points", 1),
#             "category": question.get("question_category", ""),
#             "completed": False
#         }
#         
#         # ✅ v2.1_CORRECTED: Special handling for Registration
#         if domain == TestDomain.REGISTRATION:
#             # v2.1 uses "words" field instead of "word_list"
#             registration_words = question.get("words", question.get("word_list", state.registration_words))
#             metadata["words"] = registration_words
#             # Store words for recall later
#             if "words" in question:
#                 state.registration_words = registration_words
#             metadata["instruction_after"] = self._replace_greeting(
#                 question.get("instruction_after", ""), state.greeting
#             )

# NEW CODE:
        # ✅ NEW: Extract hidden flags from question (support both old and new formats)
        hidden_display = question.get("hidden_display", False)
        hidden_audio = question.get("hidden_audio", False)
        
        # For backward compatibility, check old format flags
        if not hidden_display:
            if question.get("words_announcement_hidden", False) or question.get("instruction_after_hidden", False):
                hidden_display = True
        
        metadata = {
            "domain": domain.value,
            "question_index": index,
            "total_questions": len(questions),
            "question_id": actual_question_id,  # ✅ Use actual question_id from JSON
            "points": question.get("points", 1),
            "category": question.get("question_category", ""),
            "completed": False,
            "hidden_display": hidden_display,  # ✅ NEW: Flag for hidden display
            "hidden_audio": hidden_audio,  # ✅ NEW: Flag for hidden audio
            "tts_text": tts_text  # ✅ NEW: TTS text (may differ from display text)
        }
        
        # ✅ v2.1_CORRECTED: Special handling for Registration
        if domain == TestDomain.REGISTRATION:
            # v2.1 uses "words" field instead of "word_list"
            registration_words = question.get("words", question.get("word_list", state.registration_words))
            metadata["words"] = registration_words
            # Store words for recall later
            if "words" in question:
                state.registration_words = registration_words

