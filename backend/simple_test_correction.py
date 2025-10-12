#!/usr/bin/env python3
"""
Simple test for correction
"""

import re

def test_simple_correction():
    """Test simple correction"""
    
    text = "toi hai muoi nam tuoi"
    print(f"Input: {text}")
    
    # Step 1: Common corrections
    common_corrections = {
        'toi': 'tôi',
        'nam': 'năm',
        'tuoi': 'tuổi'
    }
    
    corrected = text
    for wrong, correct in common_corrections.items():
        corrected = re.sub(r'\b' + wrong + r'\b', correct, corrected, flags=re.IGNORECASE)
        print(f"After '{wrong}' → '{correct}': {corrected}")
    
    # Step 2: Handle "mươi"
    corrected = re.sub(r'\bmuoi\b', 'mươi', corrected, flags=re.IGNORECASE)
    print(f"After 'muoi' → 'mươi': {corrected}")
    
    # Step 3: Handle compound numbers
    compound_numbers = {
        'hai mươi lăm': 'hai mươi lăm',
        'hai mươi': 'hai mươi',
        'ba mươi': 'ba mươi',
        'bốn mươi': 'bốn mươi',
        'năm mươi': 'năm mươi'
    }
    for word, correct_word in compound_numbers.items():
        if word in corrected:
            corrected = re.sub(r'\b' + word + r'\b', correct_word, corrected, flags=re.IGNORECASE)
            print(f"After '{word}' → '{correct_word}': {corrected}")
    
    # Step 4: Handle single numbers
    single_numbers = {
        'một': 'một', 'hai': 'hai', 'ba': 'ba', 'bốn': 'bốn', 'năm': 'năm',
        'sáu': 'sáu', 'bảy': 'bảy', 'tám': 'tám', 'chín': 'chín', 'mười': 'mười'
    }
    for word, correct_word in single_numbers.items():
        if word in corrected:
            corrected = re.sub(r'\b' + word + r'\b', correct_word, corrected, flags=re.IGNORECASE)
            print(f"After '{word}' → '{correct_word}': {corrected}")
    
    print(f"Final: {corrected}")
    print(f"Expected: tôi hai mươi năm tuổi")
    
    if corrected.lower() == "tôi hai mươi năm tuổi":
        print("✅ Success!")
    else:
        print("❌ Failed!")

if __name__ == "__main__":
    test_simple_correction()
