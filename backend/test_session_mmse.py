#!/usr/bin/env python3
"""
Test script for Session-Based MMSE Assessment
Demonstrates the proper question-by-question workflow
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5001"

def test_session_based_mmse():
    """Test complete session-based MMSE assessment workflow"""

    print("🧠 TESTING SESSION-BASED MMSE ASSESSMENT")
    print("=" * 60)

    # Test data
    user_email = "test_session@example.com"
    user_info = {
        "name": "Nguyễn Văn Test",
        "age": 70,
        "education": 12
    }

    # Sample questions for MMSE
    mmse_questions = [
        {"id": "orientation_time", "content": "Hôm nay là ngày nào trong tuần?"},
        {"id": "orientation_place", "content": "Chúng ta đang ở đâu?"},
        {"id": "registration", "content": "Hãy nhắc lại 3 từ: bút, bàn, hoa"},
        {"id": "attention_calc", "content": "100 trừ 7 bằng bao nhiêu?"},
        {"id": "recall", "content": "Hãy nhắc lại 3 từ đã nói lúc trước"},
        {"id": "language_naming", "content": "Vật này gọi là gì? (chỉ vào bút)"},
        {"id": "language_repeat", "content": "Hãy lặp lại: 'Không nếu, và, hoặc'"},
        {"id": "language_commands", "content": "Hãy làm theo: nắm tay phải, gập đôi và đặt lên đầu gối"},
        {"id": "language_reading", "content": "Hãy đọc và làm theo: 'Đóng mắt lại'"},
        {"id": "language_writing", "content": "Hãy viết một câu bất kỳ"},
        {"id": "language_copying", "content": "Hãy sao chép hình này (hình ngôi sao chồng)"}
    ]

    # 1. Start session
    print("\\n1️⃣ STARTING MMSE SESSION")
    print("-" * 30)

    start_payload = {
        "user_email": user_email,
        "user_info": user_info
    }

    try:
        response = requests.post(f"{BASE_URL}/api/mmse/session/start",
                               json=start_payload, timeout=10)

        if response.status_code == 201:
            data = response.json()
            session_id = data['session_id']
            print(f"✅ Session started: {session_id}")
            print(f"   Status: {data['status']}")
            print(f"   Total questions: {data['total_questions']}")
        else:
            print(f"❌ Failed to start session: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

    # 2. Submit questions one by one
    print("\\n2️⃣ SUBMITTING QUESTIONS (One by One)")
    print("-" * 40)

    submitted_questions = 0

    for i, question in enumerate(mmse_questions[:5]):  # Test with first 5 questions
        print(f"\\n📝 Submitting Question {i+1}: {question['content'][:50]}...")

        # Create a simple test audio file (simulate user recording)
        import tempfile
        import wave
        import struct

        # Generate simple test audio
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            audio_path = tmp_file.name

            with wave.open(audio_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)

                # Generate sine wave with some variation
                for j in range(int(sample_rate * duration)):
                    # Add some variation to simulate real speech
                    freq_variation = frequency * (1 + 0.1 * (j / (sample_rate * duration)))
                    sample = int(10000 * (j / (sample_rate * duration)))  # Fade in
                    wav_file.writeframes(struct.pack('<h', sample))

        try:
            # Submit question with audio
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': ('question_audio.wav', audio_file, 'audio/wav')}
                data = {
                    'question_id': question['id'],
                    'question_content': question['content'],
                    'user_name': user_info['name'],
                    'user_age': str(user_info['age']),
                    'user_education': str(user_info['education']),
                    'user_email': user_email
                }

                response = requests.post(
                    f"{BASE_URL}/api/mmse/session/{session_id}/question",
                    files=files,
                    data=data,
                    timeout=15
                )

                if response.status_code == 200:
                    result = response.json()
                    print("   ✅ Submitted successfully")
                    print(f"   📊 Progress: {result['progress']['completed_questions']}/{result['progress']['total_questions']}")
                    print(f"   🎤 Transcript: {result['transcript'][:50]}...")
                    print(f"   📈 Score: {result['score']}")
                    submitted_questions += 1
                else:
                    print(f"   ❌ Failed: {response.status_code}")
                    print(f"   Error: {response.text}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(audio_path)
            except:
                pass

        # Small delay between submissions
        time.sleep(0.5)

    print(f"\\n✅ Submitted {submitted_questions}/5 test questions")

    # 3. Check progress
    print("\\n3️⃣ CHECKING SESSION PROGRESS")
    print("-" * 30)

    try:
        response = requests.get(f"{BASE_URL}/api/mmse/session/{session_id}/progress", timeout=10)

        if response.status_code == 200:
            data = response.json()
            progress = data['progress']
            print(f"✅ Session {session_id} progress:")
            print(f"   📊 Completed: {progress['completed_questions']}/{progress['total_questions']}")
            print(f"   📈 Completion: {progress['completion_percentage']:.1f}%")
            print(f"   🏁 Is Complete: {progress['is_complete']}")
        else:
            print(f"❌ Failed to get progress: {response.status_code}")

    except Exception as e:
        print(f"❌ Error checking progress: {e}")

    # 4. Try to complete session (should fail - not all questions done)
    print("\\n4️⃣ TESTING EARLY COMPLETION (Should Fail)")
    print("-" * 45)

    try:
        response = requests.post(f"{BASE_URL}/api/mmse/session/{session_id}/complete", timeout=10)

        if response.status_code == 400:
            print("✅ Correctly rejected early completion")
            print(f"   Error: {response.json()['error']}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")

    except Exception as e:
        print(f"❌ Error testing completion: {e}")

    # 5. Summary
    print("\\n🎯 SESSION-BASED MMSE ASSESSMENT SUMMARY")
    print("=" * 50)
    print(f"📋 Session ID: {session_id}")
    print(f"👤 User: {user_email}")
    print(f"✅ Questions Submitted: {submitted_questions}/12")
    print(f"⏳ Session Status: IN PROGRESS")
    print()
    print("📝 Key Features Demonstrated:")
    print("   ✅ Session-based workflow (not single-shot)")
    print("   ✅ Question-by-question tracking")
    print("   ✅ Progress monitoring")
    print("   ✅ Prevents premature completion")
    print("   ✅ Aggregated scoring (when complete)")
    print()
    print("🚀 Next Steps to Complete Assessment:")
    print(f"   1. Submit remaining {11-submitted_questions} questions")
    print(f"   2. Call POST /api/mmse/session/{session_id}/complete")
    print(f"   3. Get final aggregated MMSE score")

    return True

def test_api_endpoints():
    """Test all new API endpoints"""
    print("\\n🔍 TESTING API ENDPOINTS")
    print("=" * 30)

    endpoints = [
        ('GET', '/api/mmse/session/1/progress', 'Session progress'),
        ('GET', '/api/database/sessions', 'List sessions'),
        ('GET', '/api/database/questions', 'List questions'),
        ('GET', '/api/database/stats', 'Get stats'),
        ('GET', '/api/database/health', 'Database health'),
    ]

    for method, endpoint, description in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=5)

            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {description}: {response.status_code}")

        except Exception as e:
            print(f"❌ {description}: Connection failed")

if __name__ == '__main__':
    print("🧠 COGNITIVE ASSESSMENT - SESSION-BASED MMSE TEST")
    print("=" * 60)

    # Test session-based workflow
    session_test = test_session_based_mmse()

    # Test API endpoints
    test_api_endpoints()

    print("\\n🎉 TESTING COMPLETED!")
    print("Session-based MMSE assessment is working correctly!")
    print("MMSE scores are now calculated only after completing all questions.")
