"""
Full Automated MMSE Chatbot Test
================================
Chạy toàn bộ test MMSE chatbot với audio files có sẵn
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_mmse_chatbot_full.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')
TEST_SESSION_ID = f"test_session_{int(time.time())}"

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'backend' else SCRIPT_DIR

# Available audio files (relative to script location)
AUDIO_FILES = [
    os.path.join(SCRIPT_DIR, "test_audio_gemini.wav"),
    os.path.join(SCRIPT_DIR, "normal_speech_1756874142.wav"),
    os.path.join(SCRIPT_DIR, "fresh_test_1756873289.wav"),
    os.path.join(PROJECT_ROOT, "frontend", "test.mp3"),
]

# Load MMSE questions
QUESTIONS_JSON_PATH = os.path.join(SCRIPT_DIR, "mmse_audio_questions_standardized.json")

def load_questions() -> Dict[str, Any]:
    """Load MMSE questions from JSON"""
    with open(QUESTIONS_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['mmse_vietnamese_chatbot']

def get_all_questions(questions_data: Dict) -> List[Dict]:
    """Extract all questions from all domains"""
    all_questions = []
    for domain in questions_data.get('domains', []):
        for question in domain.get('questions', []):
            question['domain'] = domain.get('domain_code', '')
            question['domain_name'] = domain.get('domain_name', '')
            all_questions.append(question)
    return all_questions

def find_audio_file() -> str:
    """Find an available audio file"""
    for audio_path in AUDIO_FILES:
        if os.path.exists(audio_path):
            logger.info(f"✅ Found audio file: {audio_path}")
            return audio_path
    
    # Try to find any audio file in script directory
    script_audio = list(Path(SCRIPT_DIR).glob("*.wav"))
    if script_audio:
        logger.info(f"✅ Found audio file: {script_audio[0]}")
        return str(script_audio[0])
    
    # Try to find in project root
    project_audio = list(Path(PROJECT_ROOT).glob("**/*.wav"))
    if project_audio:
        logger.info(f"✅ Found audio file: {project_audio[0]}")
        return str(project_audio[0])
    
    logger.warning("⚠️ No audio file found, will use text-only answers")
    return None

def create_session(api_url: str, session_id: str, user_info: Dict, max_retries: int = 3) -> bool:
    """Create MMSE chatbot session with retry"""
    for attempt in range(max_retries):
        try:
            logger.info(f"📝 Creating session (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(
                f"{api_url}/api/mmse/chatbot/session",
                json={
                    "session_id": session_id,
                    "user_info": user_info
                },
                timeout=30  # Increased timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Session created: {session_id}")
                logger.info(f"   Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return True
            else:
                logger.warning(f"⚠️ Failed to create session: {response.status_code}")
                logger.warning(f"   Response: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                return False
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            logger.error(f"❌ All retries failed for session creation")
            return False
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False
    return False

def submit_answer(
    api_url: str,
    session_id: str,
    answer_text: str = "",
    audio_file: str = None,
    max_retries: int = 2
) -> Dict[str, Any]:
    """Submit answer to MMSE chatbot with retry"""
    for attempt in range(max_retries):
        try:
            form_data = {
                "session_id": session_id,
                "answer": answer_text
            }
            
            files = {}
            if audio_file and os.path.exists(audio_file):
                files['audio'] = (
                    os.path.basename(audio_file),
                    open(audio_file, 'rb'),
                    'audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg'
                )
                logger.info(f"📤 Submitting with audio: {audio_file} (attempt {attempt + 1}/{max_retries})")
            else:
                logger.info(f"📤 Submitting text only: {answer_text} (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(
                f"{api_url}/api/mmse/chatbot/submit",
                data=form_data,
                files=files if files else None,
                timeout=120  # Increased timeout for audio processing
            )
            
            if files:
                files['audio'][1].close()
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.warning(f"⚠️ Failed to submit answer: {response.status_code}")
                logger.warning(f"   Response: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {"success": False, "error": response.text}
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"❌ Error submitting answer: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "All retries failed"}

def get_current_question(api_url: str, session_id: str) -> Dict[str, Any]:
    """Get current question from session"""
    try:
        response = requests.get(
            f"{api_url}/api/mmse/chatbot/question",
            params={"session_id": session_id},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Failed to get question: {response.status_code}")
            return {"success": False}
    except Exception as e:
        logger.error(f"❌ Error getting question: {e}")
        return {"success": False}

def generate_mock_answer(question: Dict) -> str:
    """Generate a mock answer based on question type"""
    question_id = question.get('question_id', '')
    question_text = question.get('chatbot_message', '').lower()
    
    # Get current date/time for realistic answers
    now = datetime.now()
    
    # Orientation - Time
    if 'ori_time' in question_id:
        if 'thứ mấy' in question_text:
            # Get day of week in Vietnamese
            days = ['thứ hai', 'thứ ba', 'thứ tư', 'thứ năm', 'thứ sáu', 'thứ bảy', 'chủ nhật']
            return days[now.weekday()]
        elif 'ngày' in question_text and 'bao nhiêu' in question_text:
            return f"ngày {now.day}"
        elif 'tháng' in question_text:
            return f"tháng {now.month}"
        elif 'năm' in question_text:
            return f"năm {now.year}"
        elif 'buổi' in question_text:
            hour = now.hour
            if 5 <= hour < 12:
                return "sáng"
            elif 12 <= hour < 14:
                return "trưa"
            elif 14 <= hour < 18:
                return "chiều"
            else:
                return "tối"
    
    # Orientation - Place
    elif 'ori_place' in question_id:
        if 'đang ở đâu' in question_text.lower():
            return "đà nẵng"
        elif 'tỉnh' in question_text.lower() or 'thành phố' in question_text.lower():
            return "đà nẵng"
        elif 'quận' in question_text.lower() or 'huyện' in question_text.lower():
            return "quận hải châu"
    
    # Registration
    elif 'reg' in question_id:
        return "con mèo, chiếc xe, cây lúa"
    
    # Attention - Serial Subtraction
    elif 'attn_serial_sub' in question_id:
        return "93, 86, 79, 72, 65"
    
    # Recall
    elif 'recall' in question_id:
        return "con mèo, chiếc xe, cây lúa"
    
    # Language - Naming
    elif 'lang_naming' in question_id:
        if 'bút chì' in question_text.lower():
            return "bút chì"
        elif 'đồng hồ' in question_text.lower():
            return "đồng hồ"
    
    # Language - Repetition
    elif 'lang_repetition' in question_id:
        if 'không' in question_text.lower():
            return "không nếu, nhưng, hoặc"
    
    # Language - Commands
    elif 'lang_commands' in question_id:
        return "đã làm xong"
    
    # Language - Reading
    elif 'lang_reading' in question_id:
        return "đã đọc xong"
    
    # Language - Writing
    elif 'lang_writing' in question_id:
        return "đã viết xong"
    
    # Visuospatial
    elif 'visuospatial' in question_id:
        return "đã vẽ xong"
    
    # Default
    return "có"

def check_backend_health(api_url: str) -> bool:
    """Check if backend is healthy and responsive"""
    try:
        logger.info("🏥 Checking backend health...")
        response = requests.get(f"{api_url}/api/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend is healthy")
            return True
        else:
            logger.warning(f"⚠️ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to backend. Is it running?")
        logger.error("   Please start backend: cd backend && python app.py")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Health check failed: {e}")
        logger.warning("   Continuing anyway...")
        return False

def run_full_test():
    """Run complete MMSE chatbot test"""
    logger.info("=" * 80)
    logger.info("🚀 STARTING FULL MMSE CHATBOT TEST")
    logger.info("=" * 80)
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info(f"Session ID: {TEST_SESSION_ID}")
    
    # Check backend health first
    if not check_backend_health(API_BASE_URL):
        logger.error("❌ Backend health check failed. Please ensure backend is running.")
        return
    
    # Load questions
    logger.info("\n📋 Loading MMSE questions...")
    questions_data = load_questions()
    all_questions = get_all_questions(questions_data)
    logger.info(f"✅ Loaded {len(all_questions)} questions")
    
    # Find audio file
    logger.info("\n🎵 Finding audio file...")
    audio_file = find_audio_file()
    
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
    if not create_session(API_BASE_URL, TEST_SESSION_ID, user_info):
        logger.error("❌ Failed to create session. Exiting.")
        return
    
    # Get initial question
    logger.info("\n📥 Getting initial question...")
    initial_question = get_current_question(API_BASE_URL, TEST_SESSION_ID)
    if initial_question.get('success'):
        logger.info(f"✅ Initial question: {initial_question.get('message', '')[:100]}...")
    
    # Submit "ready" answer to start
    logger.info("\n✅ Submitting 'ready' to start test...")
    ready_response = submit_answer(API_BASE_URL, TEST_SESSION_ID, "sẵn sàng")
    if ready_response.get('success'):
        logger.info(f"✅ Test started: {ready_response.get('message', '')[:100]}...")
    
    # Process all questions
    logger.info("\n" + "=" * 80)
    logger.info("📝 PROCESSING QUESTIONS")
    logger.info("=" * 80)
    
    results = []
    max_questions = min(len(all_questions), 30)  # Limit to 30 questions for testing
    
    for i, question in enumerate(all_questions[:max_questions], 1):
        question_id = question.get('question_id', 'unknown')
        domain = question.get('domain_name', 'Unknown')
        question_text = question.get('chatbot_message', '')
        
        logger.info(f"\n--- Question {i}/{max_questions} ---")
        logger.info(f"Domain: {domain}")
        logger.info(f"Question ID: {question_id}")
        logger.info(f"Question: {question_text[:150]}...")
        
        # Get current question from backend
        current_q = get_current_question(API_BASE_URL, TEST_SESSION_ID)
        if current_q.get('success'):
            logger.info(f"Current question from backend: {current_q.get('message', '')[:100]}...")
        
        # Generate answer
        answer = generate_mock_answer(question)
        logger.info(f"Generated answer: {answer}")
        
        # Submit answer
        response = submit_answer(
            API_BASE_URL,
            TEST_SESSION_ID,
            answer_text=answer,
            audio_file=audio_file if i % 2 == 0 else None  # Use audio every other question
        )
        
        if response.get('success'):
            logger.info(f"✅ Answer submitted successfully")
            logger.info(f"   Response message: {response.get('message', '')[:100]}...")
            
            # Check for score update
            if 'score' in response:
                score_info = response['score']
                logger.info(f"📊 Score update: {score_info}")
            
            # Check for progress
            if 'progress' in response:
                progress = response['progress']
                logger.info(f"📈 Progress: {progress}")
            
            # Check if test complete
            if response.get('test_complete'):
                logger.info("🎉 TEST COMPLETED!")
                if 'final_score' in response:
                    logger.info(f"🏆 Final Score: {response['final_score']}")
                break
        else:
            logger.error(f"❌ Failed to submit answer: {response.get('error', 'Unknown error')}")
        
        results.append({
            "question_id": question_id,
            "domain": domain,
            "answer": answer,
            "response": response
        })
        
        # Small delay between questions
        time.sleep(1)
    
    # Get final results
    logger.info("\n" + "=" * 80)
    logger.info("📊 FINAL RESULTS")
    logger.info("=" * 80)
    
    # Try to get final results
    try:
        final_response = requests.get(
            f"{API_BASE_URL}/api/mmse/chatbot/results",
            params={"session_id": TEST_SESSION_ID},
            timeout=10
        )
        if final_response.status_code == 200:
            final_data = final_response.json()
            logger.info(f"Final Results:\n{json.dumps(final_data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        logger.warning(f"⚠️ Could not get final results: {e}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total questions processed: {len(results)}")
    logger.info(f"Successful submissions: {sum(1 for r in results if r['response'].get('success'))}")
    logger.info(f"Failed submissions: {sum(1 for r in results if not r['response'].get('success'))}")
    
    # Save results to file
    results_file = f"test_results_{TEST_SESSION_ID}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "session_id": TEST_SESSION_ID,
            "user_info": user_info,
            "results": results,
            "summary": {
                "total_questions": len(results),
                "successful": sum(1 for r in results if r['response'].get('success')),
                "failed": sum(1 for r in results if not r['response'].get('success'))
            }
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ Results saved to: {results_file}")
    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST COMPLETED")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        run_full_test()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)

