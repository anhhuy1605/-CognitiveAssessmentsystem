"""
MMSE Chatbot API - RESTful endpoints for the chatbot conversation flow
Handles session management, answer submission, and results storage
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import tempfile

# Import services
try:
    from services.mmse_chatbot_service import MMSEChatbotService
except ImportError:
    MMSEChatbotService = None

try:
    from vietnamese_transcriber import VietnameseTranscriber
except ImportError:
    VietnameseTranscriber = None

# Setup logging
logger = logging.getLogger(__name__)

# Create Blueprint
mmse_chatbot_bp = Blueprint('mmse_chatbot', __name__, url_prefix='/api/mmse/chatbot')

# Initialize services
chatbot_service = None
transcriber = None

def init_services():
    """Initialize services lazily"""
    global chatbot_service, transcriber
    
    if chatbot_service is None and MMSEChatbotService:
        try:
            chatbot_service = MMSEChatbotService()
            logger.info("✅ MMSEChatbotService initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MMSEChatbotService: {e}")
    
    if transcriber is None and VietnameseTranscriber:
        try:
            transcriber = VietnameseTranscriber()
            logger.info("✅ VietnameseTranscriber initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize VietnameseTranscriber: {e}")


# ============================================
# API ENDPOINTS
# ============================================

@mmse_chatbot_bp.route('/questions', methods=['GET'])
def get_questions():
    """Get MMSE questions for chatbot"""
    try:
        # Load questions from JSON file
        questions_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'mmse_audio_questions_standardized.json'
        )
        
        if os.path.exists(questions_path):
            with open(questions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract domains from the JSON structure
            mmse_data = data.get('mmse_vietnamese_chatbot', {})
            domains = mmse_data.get('domains', [])
            
            return jsonify({
                'success': True,
                'domains': domains,
                'metadata': mmse_data.get('metadata', {}),
                'greeting_variable': mmse_data.get('greeting_variable', '{greeting}')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Questions file not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error loading questions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mmse_chatbot_bp.route('/session', methods=['POST'])
def create_session():
    """Create a new MMSE chatbot session"""
    try:
        init_services()
        
        data = request.get_json()
        
        user_info = data.get('user_info', {})
        session_id = data.get('session_id')
        
        if not session_id:
            session_id = f"mmse_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        if chatbot_service:
            # Create session using the service
            state = chatbot_service.create_session(session_id, user_info)
            
            # Generate greeting
            greeting = _generate_greeting(user_info)
            chatbot_service.set_greeting(session_id, greeting)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'greeting': greeting,
                'message': f"Xin chào {greeting}! Tôi là trợ lý đánh giá sức khỏe nhận thức."
            })
        else:
            # Fallback without service
            greeting = _generate_greeting(user_info)
            return jsonify({
                'success': True,
                'session_id': session_id,
                'greeting': greeting,
                'message': f"Xin chào {greeting}! Tôi là trợ lý đánh giá sức khỏe nhận thức."
            })
            
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mmse_chatbot_bp.route('/submit', methods=['POST'])
def submit_answer():
    """Submit an answer and get the next question"""
    try:
        init_services()
        
        session_id = request.form.get('session_id')
        answer = request.form.get('answer', '')
        audio_file = request.files.get('audio')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID required'
            }), 400
        
        # Handle audio file
        audio_path = None
        if audio_file:
            # Save to temp file
            temp_dir = tempfile.mkdtemp()
            filename = secure_filename(audio_file.filename or 'recording.webm')
            audio_path = os.path.join(temp_dir, filename)
            audio_file.save(audio_path)
            
            # Transcribe if no text answer provided
            if not answer and transcriber:
                try:
                    result = transcriber.transcribe_audio_file(audio_path)
                    if result.get('success'):
                        answer = result.get('transcript', '')
                except Exception as e:
                    logger.warning(f"Transcription failed: {e}")
        
        if chatbot_service:
            # Check if session exists, create if not
            state = chatbot_service.get_session(session_id)
            if not state:
                logger.info(f"⚠️ Session {session_id} not found, creating new session")
                # Try to get user_info from request if available
                user_info = {}
                try:
                    user_info_json = request.form.get('user_info')
                    if user_info_json:
                        import json
                        user_info = json.loads(user_info_json)
                except:
                    pass
                
                # Create session
                state = chatbot_service.create_session(session_id, user_info)
                logger.info(f"✅ Auto-created session: {session_id}")
            
            # Submit to service
            message, metadata = chatbot_service.submit_answer(
                session_id=session_id,
                answer=answer,
                audio_file=audio_path,
                confidence=0.9
            )
            
            # ✅ REAL-TIME: Return comprehensive response with score updates
            response_data = {
                'success': True,
                'status': 'success',
                'message': message,
                'metadata': metadata,
                'transcript': answer
            }
            
            # Add score update if available
            if metadata.get('score_update'):
                response_data['score'] = metadata['score_update']
            
            # Add progress info
            if metadata.get('progress'):
                response_data['progress'] = metadata['progress']
            
            # Add test completion status
            if metadata.get('test_complete'):
                response_data['test_complete'] = True
                if metadata.get('final_score'):
                    response_data['final_score'] = metadata['final_score']
            
            return jsonify(response_data)
        else:
            # Fallback response
            return jsonify({
                'success': True,
                'message': 'Cảm ơn câu trả lời của bạn.',
                'transcript': answer
            })
            
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mmse_chatbot_bp.route('/results', methods=['POST'])
def save_results():
    """Save chatbot session results to database with full features"""
    try:
        init_services()
        data = request.get_json()
        
        session_id = data.get('sessionId')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID required'
            }), 400
        
        # Get full session state from service to include mci_result and acoustic_features
        full_data = data.copy()
        acoustic_features = {}
        linguistic_features = {}
        mmse_score = 0
        
        if chatbot_service:
            try:
                state = chatbot_service.get_session(session_id)
                if state:
                    # Add MCI result if available
                    if state.mci_result:
                        full_data['mciResult'] = state.mci_result
                    
                    # Add acoustic features if available
                    if state.acoustic_features:
                        # Aggregate acoustic features
                        all_acoustic = {}
                        for question_id, features in state.acoustic_features.items():
                            for key, value in features.items():
                                if key not in all_acoustic:
                                    all_acoustic[key] = []
                                if isinstance(value, (int, float)):
                                    all_acoustic[key].append(value)
                        
                        # Average acoustic features
                        avg_acoustic = {
                            k: float(sum(v) / len(v)) if v else 0.0 
                            for k, v in all_acoustic.items()
                        }
                        full_data['acousticFeatures'] = avg_acoustic
                        full_data['acousticFeaturesPerQuestion'] = state.acoustic_features
                        acoustic_features = avg_acoustic
                    
                    # Add linguistic features if available
                    if state.linguistic_features:
                        full_data['linguisticFeatures'] = state.linguistic_features
                        linguistic_features = state.linguistic_features
                    
                    # Add domain scores
                    if state.domain_scores:
                        full_data['domainScoresDetailed'] = state.domain_scores
                    
                    # Get MMSE score
                    if state.total_score is not None:
                        mmse_score = int(state.total_score)
                        full_data['totalScore'] = mmse_score
                    elif 'totalScore' in data:
                        mmse_score = int(data.get('totalScore', 0))
                    
                    logger.info(f"✅ Added full features to results: MCI={state.mci_result is not None}, Acoustic={len(state.acoustic_features) if state.acoustic_features else 0}")
            except Exception as e:
                logger.warning(f"⚠️ Could not get full session state: {e}")
        
        # Generate Clinical Risk Assessment if we have features
        if acoustic_features or linguistic_features:
            try:
                from risk_assessment import ClinicalRiskAssessor
                
                assessor = ClinicalRiskAssessor(
                    acoustic_features=acoustic_features,
                    linguistic_features=linguistic_features,
                    mmse_score=mmse_score
                )
                
                risk_assessment = assessor.assess_risk()
                full_data['riskAssessment'] = risk_assessment
                
                logger.info(f"✅ Generated risk assessment: risk={risk_assessment['overall_risk']}, abnormal_features={risk_assessment['abnormal_features_count']}")
            except Exception as e:
                logger.error(f"❌ Error generating risk assessment: {e}")
                import traceback
                traceback.print_exc()
        
        # Create results directory if needed
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'chatbot')
        os.makedirs(results_dir, exist_ok=True)
        
        # Save to JSON file
        result_file = os.path.join(results_dir, f"{session_id}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✅ Saved chatbot results for session: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'file': result_file,
            'data': full_data  # Return full data including features and risk assessment
        })
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mmse_chatbot_bp.route('/results/<session_id>', methods=['GET'])
def get_results(session_id: str):
    """Get results for a specific session"""
    try:
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'chatbot')
        result_file = os.path.join(results_dir, f"{session_id}.json")
        
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# HELPER FUNCTIONS
# ============================================

def _generate_greeting(user_info: Dict) -> str:
    """Generate appropriate greeting based on user info"""
    age_str = user_info.get('age', '')
    gender = user_info.get('gender', '')
    
    try:
        age = int(age_str)
    except (ValueError, TypeError):
        return 'bạn'
    
    if age >= 60:
        return 'ông' if gender == 'male' else 'bà'
    elif age >= 30:
        return 'anh' if gender == 'male' else 'chị'
    else:
        return 'anh' if gender == 'male' else 'em'


# ============================================
# REGISTER BLUEPRINT
# ============================================

def register_chatbot_api(app):
    """Register the chatbot API blueprint with the Flask app"""
    app.register_blueprint(mmse_chatbot_bp)
    logger.info("✅ MMSE Chatbot API registered")
