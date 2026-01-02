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

def find_mmse_audio_questions_path():
    """
    Find mmse_audio_questions_standardized.json file in multiple possible locations.
    Returns the path if found, None otherwise.
    """
    possible_paths = [
        # Path 1: backend/mmse_audio_questions_standardized.json (relative to services/)
        os.path.join(os.path.dirname(__file__), '..', 'mmse_audio_questions_standardized.json'),
        # Path 2: backend/mmse_audio_questions_standardized.json (relative to project root)
        os.path.join(os.path.dirname(__file__), '..', '..', 'mmse_audio_questions_standardized.json'),
        # Path 3: mmse_audio_questions_standardized.json in services directory
        os.path.join(os.path.dirname(__file__), 'mmse_audio_questions_standardized.json'),
        # Path 4: Absolute path in deployment
        '/app/mmse_audio_questions_standardized.json',
        # Path 5: In backend directory in deployment
        '/app/backend/mmse_audio_questions_standardized.json',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.debug(f"✅ Found mmse_audio_questions_standardized.json at: {path}")
            return path
    
    logger.warning(f"⚠️ mmse_audio_questions_standardized.json not found. Tried paths: {possible_paths}")
    return None

def init_services():
    """Initialize services lazily"""
    global chatbot_service, transcriber
    
    try:
        if chatbot_service is None and MMSEChatbotService:
            try:
                chatbot_service = MMSEChatbotService()
                logger.info("✅ MMSEChatbotService initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize MMSEChatbotService: {e}", exc_info=True)
                chatbot_service = None
        
        if transcriber is None and VietnameseTranscriber:
            try:
                transcriber = VietnameseTranscriber()
                logger.info("✅ VietnameseTranscriber initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize VietnameseTranscriber: {e}")
                # Transcriber is optional for chatbot, so just log warning
                transcriber = None
    except Exception as e:
        logger.error(f"❌ Error in init_services: {e}", exc_info=True)


# ============================================
# API ENDPOINTS
# ============================================

@mmse_chatbot_bp.route('/questions', methods=['GET'])
def get_questions():
    """Get MMSE questions for chatbot"""
    try:
        # Load questions from JSON file
        questions_path = find_mmse_audio_questions_path()
        
        if not questions_path:
            error_msg = "Questions file not found. Please ensure mmse_audio_questions_standardized.json exists in backend/ directory."
            logger.error(f"❌ {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404
        
        with open(questions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract domains from the JSON structure
        mmse_data = data.get('mmse_vietnamese_chatbot', {})
        domains = mmse_data.get('domains', [])
        
        logger.info(f"✅ Loaded {len(domains)} domains from {questions_path}")
        
        return jsonify({
            'success': True,
            'domains': domains,
            'metadata': mmse_data.get('metadata', {}),
            'greeting_variable': mmse_data.get('greeting_variable', '{greeting}')
        })
            
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
        logger.info(f"📨 Received session creation request from {request.remote_addr}")
        logger.info(f"📨 Request headers: {dict(request.headers)}")
        
        # Initialize services (non-blocking, has fallback)
        try:
            init_services()
        except Exception as init_error:
            logger.warning(f"⚠️ Service initialization had issues (continuing anyway): {init_error}")
        
        data = request.get_json()
        if not data:
            logger.error("❌ No JSON data in request")
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        logger.info(f"📋 Received data: {list(data.keys())}")
        
        user_info = data.get('user_info', {})
        session_id = data.get('session_id')
        
        if not session_id:
            session_id = f"mmse_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        logger.info(f"🆔 Creating session: {session_id}")
        
        if chatbot_service:
            try:
                # Create session using the service
                state = chatbot_service.create_session(session_id, user_info)
                
                # Generate greeting
                greeting = _generate_greeting(user_info)
                chatbot_service.set_greeting(session_id, greeting)
                
                logger.info(f"✅ Session created successfully: {session_id}")
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'greeting': greeting,
                    'message': f"Xin chào {greeting}! Tôi là trợ lý đánh giá sức khỏe nhận thức."
                }), 200
            except Exception as service_error:
                logger.error(f"❌ Error in chatbot_service.create_session: {service_error}", exc_info=True)
                # Fall through to fallback
        else:
            logger.warning("⚠️ chatbot_service not available, using fallback")
        
        # Fallback without service (still works)
        greeting = _generate_greeting(user_info)
        logger.info(f"✅ Session created (fallback mode): {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'greeting': greeting,
            'message': f"Xin chào {greeting}! Tôi là trợ lý đánh giá sức khỏe nhận thức.",
            'warning': 'Running in fallback mode - some features may be limited'
        }), 200
            
    except Exception as e:
        logger.error(f"❌ Error creating session: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to create session'
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
            
            # ✅ FIX: Validate audio file was saved correctly
            if not os.path.exists(audio_path):
                logger.error(f"❌ Audio file not saved: {audio_path}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to save audio file'
                }), 500
            
            file_size = os.path.getsize(audio_path)
            logger.info(f"📁 Audio file saved: {audio_path}, size: {file_size} bytes")
            
            if file_size == 0:
                logger.error(f"❌ Audio file is empty: {audio_path}")
                return jsonify({
                    'success': False,
                    'error': 'Audio file is empty'
                }), 500
            
            # ✅ FIX: Preprocess audio (webm → wav) before transcription
            processed_audio_path = audio_path
            try:
                from modules.audio_preprocessor import preprocess_audio_for_analysis
                processed_audio_path = preprocess_audio_for_analysis(audio_path)
                logger.info(f"✅ Audio preprocessed: {audio_path} → {processed_audio_path}")
            except Exception as e:
                logger.warning(f"⚠️ Audio preprocessing failed, using original: {e}")
                processed_audio_path = audio_path
            
            # Transcribe if no text answer provided
            if not answer and transcriber:
                try:
                    # ✅ FIX: Get current question context for better transcription
                    current_question = ""
                    if chatbot_service:
                        state = chatbot_service.get_session(session_id)
                        if state:
                            question_text, _ = chatbot_service.get_current_question(session_id)
                            current_question = question_text
                    
                    logger.info(f"🎤 Transcribing audio: {processed_audio_path}")
                    logger.info(f"📋 Question context: {current_question[:100] if current_question else 'None'}...")
                    
                    # ✅ FIX: Use processed audio with language and question context
                    result = transcriber.transcribe_audio_file(
                        processed_audio_path,
                        language='vi',
                        use_vietnamese_asr=True,
                        question=current_question
                    )
                    
                    logger.info(f"📊 Transcription result: success={result.get('success')}, transcript_length={len(result.get('transcript', ''))}")
                    
                    if result.get('success'):
                        answer = result.get('transcript', '').strip()
                        # ✅ FIX: Check if transcript is actually empty or just "Không có lời thoại"
                        if not answer or answer == 'Không có lời thoại':
                            logger.warning(f"⚠️ Transcription returned empty or no speech: '{answer}'")
                            # Try to get original text if available
                            original_text = result.get('original_text', '')
                            if original_text and original_text.strip():
                                answer = original_text.strip()
                                logger.info(f"✅ Using original transcript: '{answer[:100]}...'")
                            else:
                                logger.warning("⚠️ No transcript available, will use empty string")
                        else:
                            logger.info(f"✅ Transcription successful: '{answer[:100]}...'")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        logger.error(f"❌ Transcription failed: {error_msg}")
                        # Check if it's a quota/rate limit error
                        if 'quota' in str(error_msg).lower() or '429' in str(error_msg) or 'rate limit' in str(error_msg).lower():
                            logger.error(f"🚨 Gemini quota/rate limit exceeded. Error: {error_msg}")
                            # Try to use original text if available
                            original_text = result.get('original_text', '')
                            if original_text and original_text.strip():
                                answer = original_text.strip()
                                logger.info(f"✅ Using fallback original transcript: '{answer[:100]}...'")
                except Exception as e:
                    logger.error(f"❌ Transcription exception: {e}", exc_info=True)
                    # Check if it's a quota error
                    if 'quota' in str(e).lower() or '429' in str(e) or 'rate limit' in str(e).lower():
                        logger.error(f"🚨 Gemini quota/rate limit error detected: {e}")
            
            # Use processed audio path for further processing
            audio_path = processed_audio_path
        
        if chatbot_service:
            # Check if session exists, create if not
            state = chatbot_service.get_session(session_id)
            if not state:
                logger.warning(f"⚠️ Session {session_id} not found during submit_answer, creating new session (this may reset progress!)")
                # Try to get user_info from request if available
                user_info = {}
                try:
                    user_info_json = request.form.get('user_info')
                    if user_info_json:
                        import json
                        user_info = json.loads(user_info_json)
                except:
                    pass
                
                # Create session - WARNING: This will reset all progress!
                state = chatbot_service.create_session(session_id, user_info)
                logger.warning(f"⚠️ Auto-created NEW session: {session_id} (previous progress may be lost)")
            else:
                # Log current state for debugging
                logger.debug(f"📊 Session {session_id} state: domain={state.current_domain.value}, index={state.current_question_index}, total_score={state.total_score}")
            
            # Submit to service
            try:
                message, metadata = chatbot_service.submit_answer(
                    session_id=session_id,
                    answer=answer,
                    audio_file=audio_path,
                    confidence=0.9
                )
                # ✅ FIX: Ensure metadata is always a dict
                if not isinstance(metadata, dict):
                    metadata = {}
            except Exception as submit_error:
                logger.error(f"❌ Error in submit_answer: {submit_error}", exc_info=True)
                # Return graceful error response
                message = "Xin lỗi, có lỗi xảy ra khi xử lý câu trả lời. Vui lòng thử lại."
                metadata = {}
            
            # ✅ REAL-TIME: Return comprehensive response with score updates
            response_data = {
                'success': True,
                'status': 'success',
                'message': message,
                'metadata': metadata or {},  # ✅ FIX: Ensure metadata is always a dict
                'transcript': answer
            }
            
            # Add score update if available
            if metadata.get('score_update'):
                response_data['score'] = metadata['score_update']
            
            # Add progress info
            if metadata.get('progress'):
                response_data['progress'] = metadata['progress']
            
            # Add test completion status
            if metadata.get('test_complete') or metadata.get('completed'):
                response_data['test_complete'] = True
                if metadata.get('final_score'):
                    response_data['final_score'] = metadata['final_score']
                elif metadata.get('total_score') is not None:
                    # Fallback: construct final_score from total_score
                    response_data['final_score'] = {
                        'total': metadata.get('total_score', 0),
                        'max': 35,  # v2.1: 35 points total
                        'percentage': round((metadata.get('total_score', 0) / 35) * 100, 1)
                    }
                if metadata.get('comprehensive_results'):
                    response_data['comprehensive_results'] = metadata['comprehensive_results']
            
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
                    if state.completed_at:
                        try:
                            from services.comprehensive_results_generator import generate_comprehensive_results
                            shap_explanations = None
                            if state.mci_result:
                                shap_explanations = {
                                    'feature_contributions': {},
                                    'grouped_contributions': state.mci_result.get('risk_components', {})
                                }
                            comprehensive_results = generate_comprehensive_results(
                                session_state=state,
                                shap_explanations=shap_explanations
                            )
                            full_data['comprehensive_results'] = comprehensive_results
                            logger.info("✅ Comprehensive results included in save_results")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to generate comprehensive results in save_results: {e}")
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
    """Get comprehensive results for a specific session"""
    try:
        init_services()
        
        if not chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service not initialized'
            }), 500
        
        # Get session state
        state = chatbot_service.get_session(session_id)
        if not state:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Check if test is completed
        if not state.completed_at:
            return jsonify({
                'success': False,
                'error': 'Test not completed yet',
                'in_progress': True
            }), 400
        
        # ✅ COMPREHENSIVE RESULTS: Generate full results
        try:
            from services.comprehensive_results_generator import generate_comprehensive_results
            
            # Generate SHAP explanations
            shap_explanations = None
            if state.mci_result:
                shap_explanations = {
                    'feature_contributions': {},
                    'grouped_contributions': state.mci_result.get('risk_components', {})
                }
            
            comprehensive_results = generate_comprehensive_results(
                session_state=state,
                shap_explanations=shap_explanations
            )
            
            return jsonify({
                'success': True,
                'data': comprehensive_results,
                'session_id': session_id,
                'completed_at': state.completed_at
            })
            
        except Exception as e:
            logger.error(f"Error generating comprehensive results: {e}", exc_info=True)
            # Fallback to basic results
            return jsonify({
                'success': True,
                'data': {
                    'assessment_result': {
                        'mmse_score': state.total_score or 0,
                        'classification': getattr(state, 'classification', 'Unknown'),
                        'risk_level': state.mci_result.get('risk_level', 'on') if state.mci_result else 'on'
                    },
                    'error': 'Comprehensive results generation failed',
                    'fallback': True
                },
                'session_id': session_id
            })
            
    except Exception as e:
        logger.error(f"Error getting results: {e}", exc_info=True)
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
