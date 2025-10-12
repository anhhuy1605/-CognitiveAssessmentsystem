#!/usr/bin/env python3
"""
Test script for updated system with Gemini 2.5 Flash
"""

import requests
import json

def test_gemini_system():
    print('🧪 Testing updated system with Gemini 2.5 Flash...')
    
    # Test data
    test_data = {
        'question': 'Hãy kể về gia đình của bạn',
        'transcript': 'Gia đình tôi có bố mẹ và hai anh em. Bố tôi làm công nhân, mẹ tôi là giáo viên.',
        'user_data': {
            'age': '45',
            'gender': 'Nam',
            'education': 'Đại học'
        }
    }
    
    try:
        response = requests.post('http://localhost:5001/api/evaluate', 
                               json=test_data, 
                               timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print('✅ Test successful!')
            print('📊 Full Response:')
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print('\n📊 Results:')
            eval_data = result.get("evaluation", {})
            print(f'  - Vocabulary Score: {eval_data.get("vocabulary_score", "N/A")}')
            print(f'  - Context Relevance: {eval_data.get("context_relevance_score", "N/A")}')
            print(f'  - Overall Score: {eval_data.get("overall_score", "N/A")}')
            print(f'  - Analysis: {eval_data.get("analysis", "N/A")[:100]}...')
            print(f'  - Feedback: {eval_data.get("feedback", "N/A")[:100]}...')
            
            # Test with elderly person
            print('\n🧪 Testing with elderly person...')
            test_data_elderly = {
                'question': 'Bạn có thể kể tên 3 con vật không?',
                'transcript': 'Chó, mèo, gà',
                'user_data': {
                    'age': '70',
                    'gender': 'Nữ',
                    'education': 'Tiểu học'
                }
            }
            
            response2 = requests.post('http://localhost:5001/api/evaluate', 
                                    json=test_data_elderly, 
                                    timeout=120)
            
            if response2.status_code == 200:
                result2 = response2.json()
                print('✅ Elderly test successful!')
                print('📊 Results:')
                eval_data2 = result2.get("evaluation", {})
                print(f'  - Vocabulary Score: {eval_data2.get("vocabulary_score", "N/A")}')
                print(f'  - Context Relevance: {eval_data2.get("context_relevance_score", "N/A")}')
                print(f'  - Overall Score: {eval_data2.get("overall_score", "N/A")}')
                print(f'  - Analysis: {eval_data2.get("analysis", "N/A")[:100]}...')
            else:
                print(f'❌ Elderly test failed: {response2.status_code}')
                
        else:
            print(f'❌ Test failed: {response.status_code}')
            print(f'Error: {response.text}')
            
    except Exception as e:
        print(f'❌ Test error: {e}')

if __name__ == '__main__':
    test_gemini_system()
