#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMSE Chatbot Test với Database Storage
======================================
Test toàn bộ chatbot và lưu kết quả vào database
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

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_chatbot_db_{int(time.time())}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import service
try:
    from services.mmse_chatbot_service import MMSEChatbotService
except ImportError as e:
    logger.error(f"Failed to import service: {e}")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILES = [
    os.path.join(SCRIPT_DIR, "test_audio_gemini.wav"),
    os.path.join(SCRIPT_DIR, "normal_speech_1756874142.wav"),
    os.path.join(SCRIPT_DIR, "fresh_test_1756873289.wav"),
]

# Test answers
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

def find_audio_file(index: int = 0) -> Optional[str]:
    """Find an available audio file"""
    existing_files = [f for f in AUDIO_FILES if os.path.exists(f)]
    if not existing_files:
        script_audio = list(Path(SCRIPT_DIR).glob("*.wav"))
        if script_audio:
            return str(script_audio[0])
        return None
    return existing_files[index % len(existing_files)]

def get_question_answer(question_id: str, domain: str) -> str:
    """Get test answer for a question"""
    if domain in TEST_ANSWERS and question_id in TEST_ANSWERS[domain]:
        return TEST_ANSWERS[domain][question_id]
    
    # Generic fallbacks
    if "time" in question_id or "ngày" in question_id.lower():
        return "thứ hai"
    if "tháng" in question_id.lower():
        return "1"
    if "năm" in question_id.lower():
        return "2025"
    if "quốc gia" in question_id.lower():
        return "Việt Nam"
    if "tỉnh" in question_id.lower() or "thành phố" in question_id.lower():
        return "Đà Nẵng"
    if "quận" in question_id.lower() or "huyện" in question_id.lower():
        return "Hải Châu"
    
    return "có"

def save_to_database(api_url: str, session_id: str, comprehensive_results: Dict, state) -> bool:
    """Save results to database via API"""
    try:
        # Prepare payload
        payload = {
            "sessionId": session_id,
            "userId": "test_user_db",
            "userInfo": state.user_info if hasattr(state, 'user_info') else {},
            "startedAt": state.started_at if hasattr(state, 'started_at') else datetime.now().isoformat(),
            "completedAt": state.completed_at if hasattr(state, 'completed_at') else datetime.now().isoformat(),
            "totalScore": state.total_score if state.total_score else 0,
            "domainScores": state.domain_scores if hasattr(state, 'domain_scores') else {},
            "comprehensiveResults": comprehensive_results,
            "mciResult": state.mci_result if hasattr(state, 'mci_result') and state.mci_result else None,
            "acousticFeatures": getattr(state, 'final_acoustic_features', {}),
            "linguisticFeatures": getattr(state, 'final_linguistic_features', {}),
            "qaHistory": getattr(state, 'qa_pairs', []),
            "questionFeatures": getattr(state, 'question_features', {}),
            "assessmentType": "mmse_chatbot"
        }
        
        # Save via chatbot API endpoint
        logger.info(f"📤 Saving to database via chatbot API...")
        response = requests.post(
            f"{api_url}/api/mmse/chatbot/results",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Results saved to database via chatbot API!")
                logger.info(f"   Session ID: {session_id}")
                logger.info(f"   File: {result.get('file', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Save failed: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ Save failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error saving to database: {e}", exc_info=True)
        return False

def run_full_test_with_database():
    """Run complete test and save to database"""
    session_id = f"test_db_{int(time.time())}"
    api_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
    
    logger.info("=" * 80)
    logger.info("FULL MMSE CHATBOT TEST WITH DATABASE STORAGE")
    logger.info("=" * 80)
    logger.info(f"Session ID: {session_id}")
    logger.info(f"API URL: {api_url}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Initialize service
    logger.info("\nInitializing service...")
    try:
        service = MMSEChatbotService()
        logger.info("Service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        return None
    
    # User info
    user_info = {
        "name": "Test User DB",
        "age": 65,  # ✅ FIX: Use int instead of string
        "gender": "male",
        "education_years": 12,  # ✅ FIX: Use int instead of string
        "city": "Đà Nẵng",
        "district": "Hải Châu"
    }
    
    # Create session
    logger.info("\nCreating session...")
    try:
        state = service.create_session(session_id, user_info)
        service.set_greeting(session_id, "Ông")
        logger.info("Session created")
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return None
    
    # Start test
    logger.info("\nStarting test...")
    message, metadata = service.submit_answer(session_id, "sẵn sàng")
    logger.info(f"Test started: {message[:100]}...")
    
    # Process questions
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING QUESTIONS")
    logger.info("=" * 80)
    
    question_count = 0
    audio_index = 0
    max_questions = 50
    
    while question_count < max_questions:
        question_count += 1
        logger.info(f"\n--- Question {question_count} ---")
        
        # Get current question
        try:
            question_text, metadata = service.get_current_question(session_id)
            if not question_text or "hoàn thành" in question_text.lower():
                logger.info("Test completed!")
                break
            
            question_id = metadata.get('question_id', 'unknown')
            domain = metadata.get('domain', 'unknown')
            
            logger.info(f"Question ID: {question_id}")
            logger.info(f"Domain: {domain}")
            logger.info(f"Question: {question_text[:100]}...")
            
            # Get answer
            answer = get_question_answer(question_id, domain)
            audio_file = find_audio_file(audio_index)
            audio_index += 1
            
            logger.info(f"Answer: {answer}")
            if audio_file:
                logger.info(f"Audio: {os.path.basename(audio_file)}")
            
            # Submit answer
            message, response_metadata = service.submit_answer(
                session_id,
                answer=answer,
                audio_file=audio_file if audio_file else None
            )
            
            logger.info(f"Response: {message[:100]}...")
            
            # Check if complete
            if response_metadata.get('test_complete') or response_metadata.get('completed'):
                logger.info("Test completed!")
                break
            
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            break
    
    # Wait for processing
    logger.info("\nWaiting for final processing...")
    time.sleep(3)
    
    # Get comprehensive results
    logger.info("\n" + "=" * 80)
    logger.info("GETTING COMPREHENSIVE RESULTS")
    logger.info("=" * 80)
    
    try:
        from services.comprehensive_results_generator import generate_comprehensive_results
        
        state = service.get_session(session_id)
        if not state:
            logger.error("Session not found")
            return None
        
        # Generate comprehensive results
        shap_explanations = None
        if state.mci_result:
            shap_explanations = {
                'feature_contributions': {},
                'grouped_contributions': state.mci_result.get('risk_components', {})
            }
        
        results = generate_comprehensive_results(
            session_state=state,
            shap_explanations=shap_explanations
        )
        
        logger.info("Comprehensive results generated!")
        
        # Save results to JSON file
        results_file = f"test_results_{session_id}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Results saved to: {results_file}")
        
        # ✅ SAVE TO DATABASE
        logger.info("\n" + "=" * 80)
        logger.info("SAVING TO DATABASE")
        logger.info("=" * 80)
        
        db_saved = save_to_database(api_url, session_id, results, state)
        
        if db_saved:
            logger.info("✅ Results saved to database successfully!")
        else:
            logger.warning("⚠️ Failed to save to database, but results are in JSON file")
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS SUMMARY")
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
        
        question_features = results.get('question_features', {})
        logger.info(f"Per-question features: {len(question_features)} questions")
        
        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETE!")
        logger.info("=" * 80)
        
        return {
            'session_id': session_id,
            'results': results,
            'db_saved': db_saved,
            'results_file': results_file
        }
        
    except Exception as e:
        logger.error(f"Failed to get results: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    try:
        result = run_full_test_with_database()
        if result:
        print("\nTest completed successfully!")
        print(f"Session ID: {result['session_id']}")
        print(f"Results file: {result['results_file']}")
        print(f"Database saved: {result['db_saved']}")
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

