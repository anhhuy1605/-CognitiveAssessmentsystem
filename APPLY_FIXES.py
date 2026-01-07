#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-apply fixes for frontend integration issues
"""

import os
import re
from pathlib import Path

def apply_backend_fix():
    """Fix backend _format_question_text"""
    file_path = Path("backend/services/mmse_chatbot_service.py")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find _format_question_text method
    pattern = r'def _format_question_text\(self, question_data: dict, session_id: str\) -> str:.*?return "\n\n"\.join\(part for part in message_parts if part\)'
    
    new_method = '''def _format_question_text(self, question_data: dict, session_id: str) -> str:
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
    return "\\n\\n".join(part for part in message_parts if part)'''
    
    # Try to replace
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_method, content, flags=re.DOTALL)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed: {file_path}")
        return True
    else:
        print(f"⚠️ Pattern not found in {file_path}")
        return False

def check_integration():
    """Check if all components are integrated"""
    checks = {
        'ChatInterface in page.tsx': False,
        'QuestionTypeRenderer in ChatInterface': False,
        'ClockDrawingModal in QuestionTypeRenderer': False,
        'HiddenMessage in ChatInterface': False,
    }
    
    # Check page.tsx
    page_path = Path("frontend/app/(main)/mmse-chatbot/page.tsx")
    if page_path.exists():
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
            checks['ChatInterface in page.tsx'] = 'ChatInterface' in content and 'import' in content
    
    # Check ChatInterface
    chat_path = Path("frontend/components/mmse-chatbot/ChatInterface.tsx")
    if chat_path.exists():
        with open(chat_path, 'r', encoding='utf-8') as f:
            content = f.read()
            checks['QuestionTypeRenderer in ChatInterface'] = 'QuestionTypeRenderer' in content
            checks['HiddenMessage in ChatInterface'] = 'HiddenMessage' in content
    
    # Check QuestionTypeRenderer
    qtr_path = Path("frontend/components/mmse-question-types/QuestionTypeRenderer.tsx")
    if qtr_path.exists():
        with open(qtr_path, 'r', encoding='utf-8') as f:
            content = f.read()
            checks['ClockDrawingModal in QuestionTypeRenderer'] = 'ClockDrawingModal' in content
    
    print("\n📋 Integration Status:")
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check}")
    
    return all(checks.values())

if __name__ == "__main__":
    print("🔧 Applying fixes...")
    apply_backend_fix()
    check_integration()





