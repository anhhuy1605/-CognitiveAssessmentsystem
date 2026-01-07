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
                            
                            # ✅ FIX: Log feature availability before generating results
                            final_acoustic = getattr(state, 'final_acoustic_features', {})
                            final_linguistic = getattr(state, 'final_linguistic_features', {})
                            logger.info(f"📊 Generating comprehensive results with features: "
                                       f"Acoustic={len(final_acoustic)}, Linguistic={len(final_linguistic)}")
                            
                            comprehensive_results = generate_comprehensive_results(
                                session_state=state,
                                shap_explanations=shap_explanations
                            )
                            
                            # ✅ FIX: Validate features are in results
                            acoustic_count = comprehensive_results.get('feature_summary', {}).get('acoustic_feature_count', 0)
                            linguistic_count = comprehensive_results.get('feature_summary', {}).get('linguistic_feature_count', 0)
                            
                            if acoustic_count == 0:
                                logger.error("❌ NO ACOUSTIC FEATURES in comprehensive results!")
                            if linguistic_count == 0:
                                logger.error("❌ NO LINGUISTIC FEATURES in comprehensive results!")
                            
                            full_data['comprehensive_results'] = comprehensive_results
                            logger.info("✅ Comprehensive results included in save_results")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to generate comprehensive results in save_results: {e}")
                            import traceback
                            traceback.print_exc()
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
        
        # ✅ FIX: If session not in memory, try to load from saved JSON file
        if not state:
            logger.warning(f"Session {session_id} not in memory, trying to load from file...")
            try:
                results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'chatbot')
                result_file = os.path.join(results_dir, f"{session_id}.json")
                
                if os.path.exists(result_file):
                    logger.info(f"Found saved results file: {result_file}")
                    with open(result_file, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                    
                    # Try to reconstruct session state from saved data
                    # Return the saved comprehensive results directly if available
                    comprehensive_results = None
                    
                    # Check different possible structures (both camelCase and snake_case)
                    if 'comprehensiveResults' in saved_data:
                        comprehensive_results = saved_data['comprehensiveResults']
                    elif 'comprehensive_results' in saved_data:
                        comprehensive_results = saved_data['comprehensive_results']
                    elif 'data' in saved_data:
                        if isinstance(saved_data['data'], dict):
                            if 'comprehensiveResults' in saved_data['data']:
                                comprehensive_results = saved_data['data']['comprehensiveResults']
                            elif 'comprehensive_results' in saved_data['data']:
                                comprehensive_results = saved_data['data']['comprehensive_results']
                            elif 'assessment_result' in saved_data['data']:
                                # This IS the comprehensive results structure
                                comprehensive_results = saved_data['data']
                    # Also check at root level if it looks like comprehensive results structure
                    elif 'assessment_result' in saved_data:
                        comprehensive_results = saved_data
                    
                    if comprehensive_results:
                        logger.info(f"✅ Loaded comprehensive results from file for session {session_id}")
                        return jsonify({
                            'success': True,
                            'data': comprehensive_results,
                            'session_id': session_id,
                            'completed_at': saved_data.get('completedAt') or saved_data.get('completed_at') or (comprehensive_results.get('metadata', {}).get('timestamp') if isinstance(comprehensive_results, dict) else None),
                            'loaded_from_file': True
                        })
                    else:
                        logger.warning(f"Saved file exists but no comprehensive_results found. Keys: {list(saved_data.keys())}")
                        # If we have the raw data but no comprehensive_results, we can't generate it without session state
                        # Return error but suggest the file structure
                        return jsonify({
                            'success': False,
                            'error': 'Comprehensive results not found in saved file',
                            'message': f'File exists but does not contain comprehensive_results. Available keys: {list(saved_data.keys())[:10]}',
                            'file_path': result_file
                        }), 404
            except Exception as e:
                logger.warning(f"Could not load session from file: {e}")
        
        if not state:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'message': 'Session not found in memory or saved files'
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
            
            # ✅ CRITICAL: Log state before generating results
            logger.info("=" * 80)
            logger.info(f"📊 GET RESULTS for session: {session_id}")
            logger.info("=" * 80)
            
            # ✅ FIX: Check final features first
            final_acoustic = getattr(state, 'final_acoustic_features', {})
            final_linguistic = getattr(state, 'final_linguistic_features', {})
            qa_pairs = getattr(state, 'qa_pairs', [])
            question_features = getattr(state, 'question_features', {})
            
            logger.info(f"   Final acoustic features: {len(final_acoustic)} features")
            logger.info(f"   Final linguistic features: {len(final_linguistic)} features")
            logger.info(f"   Q&A pairs: {len(qa_pairs)} pairs")
            logger.info(f"   Per-question features: {len(question_features)} questions")
            logger.info(f"   Acoustic features (per question): {len(state.acoustic_features) if state.acoustic_features else 0} questions")
            logger.info(f"   Linguistic features (legacy): {len(state.linguistic_features) if state.linguistic_features else 0} features")
            logger.info(f"   MCI result: {'Yes' if state.mci_result else 'No'}")
            logger.info(f"   Domain scores: {state.domain_scores}")
            
            if not final_acoustic:
                logger.error("   ❌ NO FINAL ACOUSTIC FEATURES FOUND!")
            if not final_linguistic:
                logger.error("   ❌ NO FINAL LINGUISTIC FEATURES FOUND!")
            
            # Generate SHAP explanations
            shap_explanations = None
            if state.mci_result:
                shap_explanations = {
                    'feature_contributions': {},
                    'grouped_contributions': state.mci_result.get('risk_components', {})
                }
                logger.info(f"   SHAP input: {list(shap_explanations['grouped_contributions'].keys())}")
            
            comprehensive_results = generate_comprehensive_results(
                session_state=state,
                shap_explanations=shap_explanations
            )
            
            # ✅ CRITICAL: Ensure features are in response
            if 'multimodal_analysis' not in comprehensive_results:
                logger.warning("⚠️ multimodal_analysis missing from comprehensive_results!")
            else:
                ma = comprehensive_results['multimodal_analysis']
                if not ma.get('acoustic_features'):
                    logger.warning("⚠️ acoustic_features missing from multimodal_analysis!")
                if not ma.get('linguistic_features'):
                    logger.warning("⚠️ linguistic_features missing from multimodal_analysis!")
            
            # ✅ Aggregate acoustic features for debug info
            avg_acoustic_count = 0
            if state.acoustic_features:
                all_acoustic = {}
                for q_id, features in state.acoustic_features.items():
                    for k, v in features.items():
                        if k not in all_acoustic:
                            all_acoustic[k] = []
                        if isinstance(v, (int, float)):
                            all_acoustic[k].append(float(v))
                avg_acoustic_count = len(all_acoustic)
            
            return jsonify({
                'success': True,
                'data': comprehensive_results,
                'session_id': session_id,
                'completed_at': state.completed_at,
                '_debug': {
                    'acoustic_count': avg_acoustic_count,
                    'linguistic_count': len(state.linguistic_features) if state.linguistic_features else 0,
                    'has_mci_result': state.mci_result is not None
                }
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


@mmse_chatbot_bp.route('/sessions', methods=['GET'])
def list_completed_sessions():
    """List all completed sessions for comprehensive results page"""
    try:
        init_services()
        
        if not chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service not initialized'
            }), 500
        
        # Get all sessions from service
        # Note: This requires service to have a method to list all sessions
        # For now, we'll check if service has a sessions dict/attribute
        sessions = []
        
        try:
            # Try to access internal sessions dict if available
            if hasattr(chatbot_service, 'sessions'):
                for session_id, state in chatbot_service.sessions.items():
                    if state and state.completed_at:
                        sessions.append({
                            'sessionId': session_id,
                            'completedAt': state.completed_at.isoformat() if hasattr(state.completed_at, 'isoformat') else str(state.completed_at),
                            'totalScore': state.total_score or 0,
                            'riskLevel': state.mci_result.get('risk_level', 'on') if state.mci_result else 'on',
                            'userInfo': state.user_info if hasattr(state, 'user_info') else {}
                        })
        except Exception as e:
            logger.warning(f"Could not list sessions from service: {e}")
        
        # Sort by completed_at descending (most recent first)
        sessions.sort(key=lambda x: x.get('completedAt', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'count': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mmse_chatbot_bp.route('/test/create-full-session', methods=['POST'])
def create_test_full_session():
    """Create a test session with complete features for debugging comprehensive results"""
    try:
        init_services()
        
        if not chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service not initialized'
            }), 500
        
        logger.info("🧪 Creating test session with complete features via API...")
        
        # Import and run the test creation function
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_path))
        
        from test_comprehensive_results import create_test_session_with_features
        
        result = create_test_session_with_features(service_instance=chatbot_service)
        if not result:
            return jsonify({
                'success': False,
                'error': 'Failed to create test session'
            }), 500
        
        session_id, state = result
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Test session created with complete features',
            'summary': {
                'total_score': state.total_score,
                'acoustic_features_count': len(state.acoustic_features),
                'linguistic_features_count': len(state.linguistic_features),
                'risk_level': state.mci_result['risk_level'] if state.mci_result else None,
                'completed_at': state.completed_at
            },
            'api_endpoint': f'/api/mmse/chatbot/results/{session_id}',
            'test_files': {
                'json': f'test_comprehensive_results_{session_id}.json',
                'summary': f'test_comprehensive_summary_{session_id}.txt'
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating test session: {e}", exc_info=True)
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
