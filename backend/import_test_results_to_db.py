"""
Import Test Results to Database
================================
Import MMSE chatbot test results from JSON file to database
"""
import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')
TEST_RESULTS_FILE = "test_results_test_session_1766891790.json"

def load_test_results(file_path: str) -> Dict[str, Any]:
    """Load test results from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_final_score(results: List[Dict]) -> int:
    """Calculate final MMSE score from results"""
    total_score = 0
    for result in results:
        response = result.get('response', {})
        score_info = response.get('score') or response.get('metadata', {}).get('score_update', {})
        if score_info:
            points_earned = score_info.get('points_earned', 0)
            total_score += points_earned
    return total_score

def aggregate_domain_scores(results: List[Dict]) -> Dict[str, int]:
    """Aggregate scores by domain"""
    domain_scores = {}
    for result in results:
        domain = result.get('domain', 'Unknown')
        response = result.get('response', {})
        score_info = response.get('score') or response.get('metadata', {}).get('score_update', {})
        if score_info:
            points_earned = score_info.get('points_earned', 0)
            if domain not in domain_scores:
                domain_scores[domain] = 0
            domain_scores[domain] += points_earned
    return domain_scores

def extract_question_results(results: List[Dict]) -> List[Dict]:
    """Extract per-question results"""
    question_results = []
    for result in results:
        question_id = result.get('question_id', '')
        domain = result.get('domain', '')
        answer = result.get('answer', '')
        response = result.get('response', {})
        
        score_info = response.get('score') or response.get('metadata', {}).get('score_update', {})
        transcript = response.get('transcript', answer)
        
        question_result = {
            'questionId': question_id,  # Use questionId for frontend compatibility
            'question_id': question_id,  # Keep both for compatibility
            'questionText': response.get('message', ''),  # Use questionText for frontend
            'question_text': response.get('message', ''),  # Keep both
            'domain': domain,
            'category': domain,  # Add category alias
            'user_answer': answer,
            'userAnswer': answer,  # Add camelCase version
            'transcript': transcript,
            'transcription': transcript,  # Add alias
            'response': transcript,  # Add alias
            'points_earned': score_info.get('points_earned', 0),
            'points_possible': score_info.get('points_possible', 1),
            'is_correct': score_info.get('is_correct', False),
            'feedback': score_info.get('feedback', ''),
            'status': 'completed',
            'processedAt': datetime.now().isoformat(),
            'createdAt': datetime.now().isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        question_results.append(question_result)
    
    return question_results

def format_for_database(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format test results for database storage"""
    session_id = test_data.get('session_id', '')
    user_info = test_data.get('user_info', {})
    results = test_data.get('results', [])
    
    # Calculate final score
    final_score = calculate_final_score(results)
    
    # Aggregate domain scores
    domain_scores = aggregate_domain_scores(results)
    
    # Extract question results
    question_results = extract_question_results(results)
    
    # Format for database
    db_data = {
        'sessionId': session_id,
        'userInfo': {
            'name': user_info.get('name', 'Test User'),
            'age': user_info.get('age', ''),
            'gender': user_info.get('gender', ''),
            'education_years': user_info.get('education_years', ''),
            'city': user_info.get('city', ''),
            'district': user_info.get('district', '')
        },
        'totalScore': final_score,
        'maxScore': 30,
        'domainScores': domain_scores,
        'questionResults': question_results,
        'completedAt': datetime.now().isoformat(),
        'assessmentType': 'mmse_chatbot',
        'status': 'completed',
        'summary': {
            'total_questions': len(results),
            'answered_questions': len([r for r in results if r.get('response', {}).get('success')]),
            'completion_rate': 100.0 if results else 0.0
        }
    }
    
    return db_data

def save_to_database(api_url: str, data: Dict[str, Any]) -> bool:
    """Save results to database via API"""
    try:
        session_id = data['sessionId']
        logger.info(f"📤 Saving results to database for session: {session_id}")
        
        # Save via MMSE chatbot results endpoint
        response = requests.post(
            f"{api_url}/api/mmse/chatbot/results",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Results saved successfully via chatbot API!")
                logger.info(f"   Session ID: {session_id}")
                logger.info(f"   Final Score: {data['totalScore']}/30")
                
                # Also save to MMSE results DB for stats page
                mmse_response = requests.post(
                    f"{api_url}/api/mmse/results/{session_id}",
                    json={
                        'totalScore': data['totalScore'],
                        'cognitiveStatus': 'Normal' if data['totalScore'] >= 24 else 'MCI' if data['totalScore'] >= 21 else 'Dementia',
                        'domainScores': data['domainScores'],
                        'completedAt': data['completedAt']
                    },
                    timeout=10
                )
                
                if mmse_response.status_code == 200:
                    logger.info(f"✅ Also saved to MMSE results DB for stats page")
                
                # Save to frontend database via Next.js API
                frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
                
                # Format questionResults as JSON string (database expects string)
                question_results_json = json.dumps(data['questionResults'], ensure_ascii=False)
                
                # Format cognitiveAnalysis as JSON string
                cognitive_analysis_json = json.dumps({
                    'totalScore': data['totalScore'],
                    'domainScores': data['domainScores'],
                    'status': 'completed',
                    'summary': data.get('summary', {})
                }, ensure_ascii=False)
                
                # Format userInfo as JSON string
                user_info_json = json.dumps(data['userInfo'], ensure_ascii=False)
                
                frontend_data = {
                    'sessionId': session_id,
                    'userId': data['userInfo'].get('name', 'test_user'),
                    'userInfo': user_info_json,  # JSON string
                    'startedAt': data['completedAt'],  # Use completedAt as startedAt if not available
                    'finalMmseScore': data['totalScore'],
                    'overallGptScore': float(data['totalScore']) * 3.33,  # Convert to percentage (out of 100)
                    'questionResults': question_results_json,  # JSON string
                    'cognitiveAnalysis': cognitive_analysis_json,  # JSON string
                    'assessmentType': 'mmse_chatbot',
                    'status': 'completed',
                    'totalQuestions': len(data['questionResults']),
                    'answeredQuestions': len(data['questionResults']),
                    'completionRate': 100.0,
                    'usageMode': 'personal'
                }
                
                logger.info(f"📤 Saving to frontend database: sessionId={session_id}, finalMmseScore={data['totalScore']}")
                logger.info(f"   Question results count: {len(data['questionResults'])}")
                
                try:
                    frontend_response = requests.post(
                        f"{frontend_url}/api/save-cognitive-assessment-results",
                        json=frontend_data,
                        timeout=10
                    )
                    if frontend_response.status_code == 200:
                        logger.info(f"✅ Also saved to frontend database for stats page")
                    else:
                        logger.warning(f"⚠️ Frontend save returned {frontend_response.status_code}: {frontend_response.text}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not save to frontend database: {e}")
                
                return True
            else:
                logger.error(f"❌ Failed to save: {result.get('error', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("📥 IMPORTING TEST RESULTS TO DATABASE")
    logger.info("=" * 80)
    
    # Check if file exists
    if not os.path.exists(TEST_RESULTS_FILE):
        logger.error(f"❌ File not found: {TEST_RESULTS_FILE}")
        logger.info("   Please provide the correct path to test results JSON file")
        return
    
    # Load test results
    logger.info(f"\n📋 Loading test results from: {TEST_RESULTS_FILE}")
    try:
        test_data = load_test_results(TEST_RESULTS_FILE)
        logger.info(f"✅ Loaded test results for session: {test_data.get('session_id', 'unknown')}")
    except Exception as e:
        logger.error(f"❌ Failed to load test results: {e}")
        return
    
    # Format for database
    logger.info("\n🔄 Formatting data for database...")
    db_data = format_for_database(test_data)
    logger.info(f"✅ Formatted data:")
    logger.info(f"   Session ID: {db_data['sessionId']}")
    logger.info(f"   Final Score: {db_data['totalScore']}/30")
    logger.info(f"   Questions: {len(db_data['questionResults'])}")
    logger.info(f"   Domains: {list(db_data['domainScores'].keys())}")
    
    # Check backend health
    logger.info(f"\n🏥 Checking backend health...")
    try:
        health_response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            logger.info("✅ Backend is healthy")
        else:
            logger.warning("⚠️ Backend health check returned non-200 status")
    except Exception as e:
        logger.error(f"❌ Cannot connect to backend: {e}")
        logger.error("   Please ensure backend is running at " + API_BASE_URL)
        return
    
    # Save to database
    logger.info(f"\n💾 Saving to database...")
    if save_to_database(API_BASE_URL, db_data):
        logger.info("\n" + "=" * 80)
        logger.info("✅ IMPORT COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Session ID: {db_data['sessionId']}")
        logger.info(f"   Final Score: {db_data['totalScore']}/30")
        logger.info(f"   Domain Scores: {db_data['domainScores']}")
        logger.info(f"\n🌐 View results at:")
        logger.info(f"   Stats: http://localhost:3000/stats")
        logger.info(f"   Results: http://localhost:3000/results/{db_data['sessionId']}")
    else:
        logger.error("\n❌ IMPORT FAILED")
        logger.error("   Please check the error messages above")

if __name__ == "__main__":
    # Allow custom file path as argument
    if len(sys.argv) > 1:
        TEST_RESULTS_FILE = sys.argv[1]
        # Handle relative paths
        if not os.path.isabs(TEST_RESULTS_FILE):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            TEST_RESULTS_FILE = os.path.join(script_dir, TEST_RESULTS_FILE)
    
    main()

