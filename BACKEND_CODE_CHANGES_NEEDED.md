# Backend Code Changes Cần Thực Hiện Thủ Công

## ⚠️ LƯU Ý

Do tool limitations, các thay đổi sau cần được thực hiện **THỦ CÔNG** trong file `backend/services/mmse_chatbot_service.py`.

## ✅ CHANGE 1: Registration Handling (Dòng 392-408)

### TÌM:
```python
        # ✅ v2.1_CORRECTED: Handle instruction fields (instruction_part1, instruction_part2)
        # For registration domain, combine instruction_part1 and instruction_part2
        if domain == TestDomain.REGISTRATION and index == 0:
            instruction_part1 = question.get("instruction_part1", "")
            instruction_part2 = question.get("instruction_part2", "")
            if instruction_part1:
                instruction_part1 = self._replace_greeting(instruction_part1, state.greeting)
                question_text = f"{instruction_part1}\n\n{question_text}"
            if instruction_part2:
                instruction_part2 = self._replace_greeting(instruction_part2, state.greeting)
                question_text = f"{question_text}\n\n{instruction_part2}"
        elif index == 0:
```

### THAY THẾ BẰNG:
```python
        # ✅ FIX: Handle instruction field (new structure)
        # For registration domain, handle instruction + words_announcement + question + instruction_after
        actual_question_id = question.get("question_id", f"{domain.value}_{index}")
        if domain == TestDomain.REGISTRATION and index == 0:
            message_parts = []
            
            # 1. Instruction
            instruction = question.get("instruction", "")
            if instruction:
                instruction = self._replace_greeting(instruction, state.greeting)
                message_parts.append(instruction)
            
            # 2. Question (main question text)
            if question_text:
                message_parts.append(question_text)
            
            # 3. Words announcement (for registration)
            words_announcement = question.get("words_announcement", "")
            if words_announcement:
                # Remove markdown bold if present (safety check)
                words_announcement = words_announcement.replace("**", "")
                words_announcement = self._replace_greeting(words_announcement, state.greeting)
                message_parts.append(words_announcement)
            
            # 4. Instruction after (for registration)
            instruction_after = question.get("instruction_after", "")
            if instruction_after:
                instruction_after = self._replace_greeting(instruction_after, state.greeting)
                message_parts.append(instruction_after)
            
            # Join with double newline for clear separation
            question_text = "\n\n".join(part for part in message_parts if part)
        elif index == 0:
```

---

## ✅ CHANGE 2: Fix actual_question_id Definition (Dòng 410-411)

### TÌM:
```python
        # ✅ FIX: Get actual question_id from JSON
        actual_question_id = question.get("question_id", f"{domain.value}_{index}")
```

### THAY THẾ BẰNG:
```python
        # ✅ FIX: Get actual question_id from JSON (already defined above for registration)
        if domain != TestDomain.REGISTRATION or index != 0:
            actual_question_id = question.get("question_id", f"{domain.value}_{index}")
```

---

## ✅ CHANGE 3: Serial 7s Auto-Stop Logic (Dòng 565-582)

### TÌM:
```python
                    # Check if we have 5 answers (auto-stop)
                    if len(state.serial_7s_answers) >= 5:
                        state.serial_7s_stopped = True
                        logger.info(f"✅ Serial 7s completed: {state.serial_7s_answers}")
                        # Move to next domain after this
                        state.current_question_index += 1
                        return self._advance_to_next_domain(session_id)
                    else:
                        # Continue asking for next number
                        next_expected = state.serial_7s_current_value
                        pronoun = self.get_pronoun(session_id, False)
                        next_question = f"Tiếp tục nhé {pronoun}! Lấy {user_value} trừ 7 bằng bao nhiêu?"
                        metadata['serial_7s'] = {
                            'answers_so_far': state.serial_7s_answers,
                            'next_expected': next_expected,
                            'remaining': 5 - len(state.serial_7s_answers)
                        }
                        return next_question, metadata
```

### THAY THẾ BẰNG:
```python
                    # ✅ FIX: Check if we have 5 answers (auto-stop)
                    if len(state.serial_7s_answers) >= 5:
                        state.serial_7s_stopped = True
                        logger.info(f"✅ Serial 7s COMPLETED: {state.serial_7s_answers}")
                        
                        # ✅ Calculate correct count
                        correct_count = self._count_correct_serial7s_answers(state.serial_7s_answers)
                        logger.info(f"✅ Serial 7s Score: {correct_count}/5 correct")
                        
                        # ✅ Get appropriate completion message based on score
                        pronoun = self.get_pronoun(session_id, True)
                        pronoun_lower = self.get_pronoun(session_id, False)
                        
                        if correct_count == 5:
                            completion_message = f"Xuất sắc! {pronoun} tính đúng cả 5 số!"
                        elif correct_count >= 4:
                            completion_message = f"Rất tốt! {pronoun} tính đúng {correct_count}/5 số."
                        elif correct_count >= 3:
                            completion_message = f"Được rồi! {pronoun} tính đúng {correct_count} số."
                        elif correct_count >= 2:
                            completion_message = f"Không sao {pronoun_lower}, phép tính này hơi khó."
                        else:
                            completion_message = f"Không sao {pronoun_lower}, chúng ta tiếp tục phần tiếp theo nhé."
                        
                        # ✅ Move to next question
                        state.current_question_index += 1
                        logger.info(f"➡️ Moving to next question: index {state.current_question_index}")
                        
                        # ✅ Return completion metadata so frontend knows to stop
                        metadata['serial_7s_stopped'] = True
                        metadata['serial_7s_completed'] = True
                        metadata['serial_7s_answers'] = state.serial_7s_answers
                        metadata['serial_7s_correct_count'] = correct_count
                        metadata['serial_7s_score'] = correct_count
                        metadata['move_to_next_question'] = True
                        metadata['auto_stopped'] = True
                        
                        # ✅ Return completion message, then advance to next question
                        next_question_text, next_metadata = self._advance_to_next_domain(session_id)
                        # Merge metadata
                        next_metadata.update(metadata)
                        return completion_message, next_metadata
                    else:
                        # Continue asking for next number
                        state.serial_7s_current_value = user_value  # Update current value to user's answer
                        next_value_to_subtract = state.serial_7s_current_value - 7
                        pronoun = self.get_pronoun(session_id, False)
                        
                        remaining = 5 - len(state.serial_7s_answers)
                        next_question = f"Tiếp tục nhé {pronoun}! Lấy {user_value} trừ 7 bằng bao nhiêu?"
                        
                        logger.info(f"➡️ Serial 7s: Asking for next ({remaining} remaining)")
                        
                        metadata['serial_7s'] = {
                            'answers_so_far': state.serial_7s_answers,
                            'current_value': user_value,
                            'next_expected': next_value_to_subtract,
                            'remaining': remaining,
                            'stopped': False
                        }
                        
                        return next_question, metadata
```

---

## ✅ CHANGE 4: Thêm Helper Method (Sau _extract_animals_from_text, trước _replace_greeting)

### TÌM:
```python
        return animals
    
    def _replace_greeting(self, text: str, greeting: str) -> str:
```

### THAY THẾ BẰNG:
```python
        return animals
    
    def _count_correct_serial7s_answers(self, answers: List[int]) -> int:
        """
        Count how many Serial 7s answers are objectively correct.
        Expected sequence: [93, 86, 79, 72, 65]
        
        Args:
            answers: List of user answers (integers)
            
        Returns:
            Number of correct answers
        """
        expected = [93, 86, 79, 72, 65]
        correct_count = 0
        
        for i, answer in enumerate(answers):
            if i < len(expected) and answer == expected[i]:
                correct_count += 1
                logger.debug(f"✓ Serial 7s Answer {i+1}: {answer} is correct (expected {expected[i]})")
            elif i < len(expected):
                logger.debug(f"✗ Serial 7s Answer {i+1}: {answer} is incorrect (expected {expected[i]})")
        
        logger.info(f"✅ Serial 7s correct count: {correct_count}/{len(answers)}")
        return correct_count
    
    def _replace_greeting(self, text: str, greeting: str) -> str:
```

---

## ✅ VERIFICATION

Sau khi sửa, chạy:

```bash
cd backend
python -m py_compile services/mmse_chatbot_service.py
```

Nếu không có lỗi syntax, code đã đúng!

