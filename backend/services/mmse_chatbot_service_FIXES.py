# -*- coding: utf-8 -*-
"""
FIXES for mmse_chatbot_service.py
==================================

Apply these fixes to fix registration words exposure and hidden content handling
"""

# ============================================
# FIX 1: _format_question_text() - Line ~730
# ============================================
# Replace the entire _format_question_text method with this:

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


# ============================================
# FIX 2: get_current_question() - Ensure hidden_content in metadata
# ============================================
# In get_current_question method, ensure hidden_content is set correctly:

def get_current_question(self, session_id: str) -> Tuple[str, Dict]:
    """
    Get current question text and metadata
    ✅ FIX: hidden_content được set từ JSON và TTS sẽ đọc cả hidden content
    """
    state = self.get_session(session_id)
    if not state:
        return "Lỗi", {}
    
    domain = state.current_domain
    index = state.current_question_index
    
    questions = self._get_domain_questions(domain.value)
    if not questions or index >= len(questions):
        return "Hoàn thành", {}
    
    question_data = questions[index]
    question_id = question_data.get('question_id', '')
    
    # Format question text (KHÔNG include words_announcement)
    question_text = self._format_question_text(question_data, session_id)
    
    # ✅ FIX: Build full text for TTS (includes hidden content)
    tts_text = question_text
    
    # Add words_announcement to TTS text if exists (for registration)
    if question_id == 'reg_01' and 'words_announcement' in question_data:
        words_text = question_data['words_announcement']
        words_text = words_text.replace("**", "")
        words_text = words_text.replace("{pronoun}", self.get_pronoun(session_id, False))
        words_text = words_text.replace("{Pronoun}", self.get_pronoun(session_id, True))
        # Insert words_announcement into TTS text (after instruction, before question)
        parts = question_text.split('\n\n')
        if len(parts) >= 2:
            tts_text = f"{parts[0]}\n\n{words_text}\n\n{parts[1]}"
        else:
            tts_text = f"{question_text}\n\n{words_text}"
    
    # Add other hidden content to TTS text
    if 'hidden_content' in question_data:
        for hidden in question_data['hidden_content']:
            clean_hidden = hidden.replace("**", "")
            # Add to TTS text if not already present
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
        words_text = question_data['words_announcement']
        words_text = words_text.replace("**", "")
        if 'hidden_content' not in metadata:
            metadata['hidden_content'] = []
        # Extract words from words_announcement
        if 'words_to_recall' in question_data:
            metadata['hidden_content'].extend(question_data['words_to_recall'])
    
    # Add clock drawing target time if applicable
    if question_id == 'visual_clock_drawing':
        metadata['target_time'] = state.clock_drawing_target_time
    
    return question_text, metadata  # ✅ Return question_text (without hidden content) for UI


# ============================================
# FIX 3: submit_answer() - Ensure hidden_content preserved
# ============================================
# In submit_answer, when returning next question, ensure hidden_content is passed

# In the part where you call get_current_question():
# next_question, metadata = self.get_current_question(session_id)
# metadata['hidden_content'] = metadata.get('hidden_content', [])  # ✅ Ensure it's passed

