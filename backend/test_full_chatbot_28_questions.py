#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full MMSE Chatbot Test - 28 Questions với Audio Files
=====================================================
Test toàn bộ chatbot với 28 câu hỏi, sử dụng audio files có sẵn
Tự động submit answers và lấy comprehensive results
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import base64

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_full_chatbot_{int(time.time())}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_JSON_PATH = os.path.join(SCRIPT_DIR, "mmse_audio_questions_standardized.json")

# Available audio files (will cycle through them)
AUDIO_FILES = [
    os.path.join(SCRIPT_DIR, "test_audio_gemini.wav"),
    os.path.join(SCRIPT_DIR, "normal_speech_1756874142.wav"),
    os.path.join(SCRIPT_DIR, "fresh_test_1756873289.wav"),
]

# Test answers for each question type (fallback if audio fails)
TEST_ANSWERS = {
    "orientation": {
        "ori_time_01": "thứ hai",
        "ori_time_02": "3",
        "ori_time_03": "1",
        "ori_time_04": "2025",
        "ori_time_05": "sáng",
        "ori_place_01": "Việt Nam",
        "ori_place_02": "Đà Nẵng",
        "ori_place_03": "Hải Châu",
        "ori_place_04": "miền trung",
        "ori_place_05": "bệnh viện",
    },
    "registration": {
        "reg_01": "Con mèo, Chiếc xe, Cây lúa"
    },
    "attention_calculation": {
        "attn_serial_sub": "93"
    },
    "recall": {
        "recall_01": "Con mèo, Chiếc xe, Cây lúa"
    },
    "language": {
        "lang_naming_01": "đồng hồ",
        "lang_naming_02": "bút",
        "lang_repetition": "Có vất vả mới thanh nhàn, không dưng ai dễ cầm tàn che cho",
        "lang_comprehension_3step": "Tôi hiểu rồi. Một, hai, ba. Xong rồi.",
        "lang_comprehension_listening": "làm tổ",
        "lang_sentence_production": "Hôm nay trời nắng đẹp"
    },
    "visuospatial": {
        "visual_clock_drawing": "đã vẽ"
    }
}

def load_questions() -> Dict[str, Any]:
    """Load MMSE questions from JSON"""
    try:
        with open(QUESTIONS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('mmse_vietnamese_chatbot', data)
    except Exception as e:
        logger.error(f"❌ Failed to load questions: {e}")
        return {}

def find_audio_file(index: int = 0) -> Optional[str]:
    """Find an available audio file, cycling through available files"""
    # Filter existing files
    existing_files = [f for f in AUDIO_FILES if os.path.exists(f)]
    
    if not existing_files:
        # Try to find any audio file in script directory
        script_audio = list(Path(SCRIPT_DIR).glob("*.wav"))
        if script_audio:
            logger.info(f"✅ Found audio file: {script_audio[0]}")
            return str(script_audio[0])
        logger.warning("⚠️ No audio file found")
        return None
    
    # Cycle through files
    audio_file = existing_files[index % len(existing_files)]
    logger.info(f"✅ Using audio file: {audio_file}")
    return audio_file

def check_backend_health(api_url: str) -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend is running")
            return True
    except Exception as e:
        logger.warning(f"⚠️ Backend health check failed: {e}")
    return False

def create_session(api_url: str, session_id: str, user_info: Dict) -> bool:
    """Create MMSE chatbot session"""
    try:
        response = requests.post(
            f"{api_url}/api/mmse/chatbot/session",
            json={
                "session_id": session_id,
                "user_info": user_info
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                logger.info(f"✅ Session created: {session_id}")
                return True
        logger.error(f"❌ Failed to create session: {response.status_code}")
        logger.error(f"   Response: {response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error creating session: {e}")
        return False

def submit_answer(
    api_url: str,
    session_id: str,
    answer_text: str = "",
    audio_file: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Submit answer to MMSE chatbot"""
    for attempt in range(max_retries):
        try:
            form_data = {
                "session_id": session_id,
                "answer": answer_text
            }
            
            files = {}
            if audio_file and os.path.exists(audio_file):
                try:
                    files['audio'] = (
                        os.path.basename(audio_file),
                        open(audio_file, 'rb'),
                        'audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg'
                    )
                    logger.info(f"📤 Submitting with audio: {os.path.basename(audio_file)}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to open audio file: {e}")
                    files = {}
            
            response = requests.post(
                f"{api_url}/api/mmse/chatbot/submit",
                data=form_data,
                files=files if files else None,
                timeout=180  # Long timeout for audio processing
            )
            
            if files:
                files['audio'][1].close()
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.warning(f"⚠️ Submit failed: {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {"success": False, "error": response.text}
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"❌ Error submitting answer: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "Max retries exceeded"}

def get_comprehensive_results(api_url: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive results for completed test"""
    try:
        response = requests.get(
            f"{api_url}/api/mmse/chatbot/results/{session_id}",
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data')
        logger.error(f"❌ Failed to get results: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"❌ Error getting results: {e}")
        return None

def get_question_answer(question_id: str, domain: str) -> str:
    """Get test answer for a question"""
    # Try domain-specific answers
    if domain in TEST_ANSWERS and question_id in TEST_ANSWERS[domain]:
        return TEST_ANSWERS[domain][question_id]
    
    # Generic answers
    if "time" in question_id or "ngày" in question_id.lower():
        return "thứ hai"
    if "tháng" in question_id.lower():
        return "1"
    if "năm" in question_id.lower():
        return "2025"
    if "quốc gia" in question_id.lower() or "country" in question_id.lower():
        return "Việt Nam"
    if "tỉnh" in question_id.lower() or "thành phố" in question_id.lower():
        return "Đà Nẵng"
    if "quận" in question_id.lower() or "huyện" in question_id.lower():
        return "Hải Châu"
    
    return "có"

def run_full_test():
    """Run complete MMSE chatbot test with all 28 questions"""
    session_id = f"test_full_{int(time.time())}"
    
    logger.info("=" * 80)
    logger.info("🚀 FULL MMSE CHATBOT TEST - 28 QUESTIONS")
    logger.info("=" * 80)
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check backend
    if not check_backend_health(API_BASE_URL):
        logger.error("❌ Backend not available. Please start the backend first.")
        return None
    
    # Load questions
    logger.info("\n📋 Loading questions...")
    questions_data = load_questions()
    if not questions_data:
        logger.error("❌ Failed to load questions")
        return None
    
    # User info
    user_info = {
        "name": "Test User",
        "age": "65",
        "gender": "male",
        "education_years": "12",
        "city": "Đà Nẵng",
        "district": "Hải Châu"
    }
    
    # Create session
    logger.info("\n📝 Creating session...")
    if not create_session(API_BASE_URL, session_id, user_info):
        logger.error("❌ Failed to create session")
        return None
    
    # Start test
    logger.info("\n✅ Starting test...")
    response = submit_answer(API_BASE_URL, session_id, "sẵn sàng")
    if not response.get('success'):
        logger.error(f"❌ Failed to start test: {response.get('error')}")
        return None
    
    logger.info(f"✅ Test started: {response.get('message', '')[:100]}...")
    
    # Process questions
    logger.info("\n" + "=" * 80)
    logger.info("📝 PROCESSING QUESTIONS")
    logger.info("=" * 80)
    
    question_count = 0
    audio_index = 0
    max_questions = 50  # Safety limit
    
    while question_count < max_questions:
        question_count += 1
        logger.info(f"\n--- Question {question_count} ---")
        
        # Get current question
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/mmse/chatbot/question",
                params={"session_id": session_id},
                timeout=10
            )
            if response.status_code != 200:
                logger.warning(f"⚠️ Failed to get question: {response.status_code}")
                break
            
            question_data = response.json()
            if not question_data.get('success'):
                logger.info("✅ No more questions (test may be complete)")
                break
            
            metadata = question_data.get('metadata', {})
            question_id = metadata.get('question_id', 'unknown')
            domain = metadata.get('domain', 'unknown')
            question_text = question_data.get('message', '')
            
            logger.info(f"📋 Question ID: {question_id}")
            logger.info(f"📋 Domain: {domain}")
            logger.info(f"📋 Question: {question_text[:100]}...")
            
            # Get answer
            answer = get_question_answer(question_id, domain)
            audio_file = find_audio_file(audio_index)
            audio_index += 1
            
            logger.info(f"💬 Answer: {answer}")
            if audio_file:
                logger.info(f"🎵 Audio: {os.path.basename(audio_file)}")
            
            # Submit answer
            response = submit_answer(
                API_BASE_URL,
                session_id,
                answer_text=answer,
                audio_file=audio_file
            )
            
            if not response.get('success'):
                logger.warning(f"⚠️ Failed to submit answer: {response.get('error')}")
                # Continue anyway
            
            # Check if test is complete
            if response.get('test_complete') or response.get('metadata', {}).get('test_complete'):
                logger.info("✅ Test completed!")
                break
            
            # Small delay between questions
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error processing question: {e}")
            break
    
    # Wait a bit for final processing
    logger.info("\n⏳ Waiting for final processing...")
    time.sleep(5)
    
    # Get comprehensive results
    logger.info("\n" + "=" * 80)
    logger.info("📊 GETTING COMPREHENSIVE RESULTS")
    logger.info("=" * 80)
    
    results = get_comprehensive_results(API_BASE_URL, session_id)
    
    if results:
        logger.info("✅ Comprehensive results retrieved!")
        
        # Save results to file
        results_file = f"test_results_{session_id}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"💾 Results saved to: {results_file}")
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 RESULTS SUMMARY")
        logger.info("=" * 80)
        
        assessment = results.get('assessment_result', {})
        logger.info(f"MMSE Score: {assessment.get('mmse_score', 'N/A')}/35")
        logger.info(f"Adjusted Score: {assessment.get('adjusted_score', 'N/A')}")
        logger.info(f"Risk Level: {assessment.get('risk_level', 'N/A')}")
        logger.info(f"Classification: {assessment.get('classification', 'N/A')}")
        
        feature_summary = results.get('feature_summary', {})
        logger.info(f"\nFeatures:")
        logger.info(f"  Acoustic: {feature_summary.get('acoustic_feature_count', 0)}")
        logger.info(f"  Linguistic: {feature_summary.get('linguistic_feature_count', 0)}")
        logger.info(f"  Total: {feature_summary.get('total_features', 0)}")
        
        multimodal = results.get('multimodal_analysis', {})
        logger.info(f"\nMultimodal Analysis:")
        logger.info(f"  Combined Risk: {multimodal.get('combined_risk_score', 'N/A')}")
        logger.info(f"  Risk Level: {multimodal.get('risk_level', 'N/A')}")
        
        qa_history = results.get('qa_history', [])
        logger.info(f"\nQ&A History: {len(qa_history)} pairs")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TEST COMPLETE!")
        logger.info("=" * 80)
        
        return results
    else:
        logger.error("❌ Failed to get comprehensive results")
        return None

if __name__ == "__main__":
    try:
        results = run_full_test()
        if results:
            print("\n✅ Test completed successfully!")
            print(f"📊 Check the results file for full details")
            sys.exit(0)
        else:
            print("\n❌ Test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Test error: {e}", exc_info=True)
        sys.exit(1)

