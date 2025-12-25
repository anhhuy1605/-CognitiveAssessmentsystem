"""
Pipeline API Routes
===================

REST API endpoints for the cognitive assessment pipeline:
- Audio processing endpoints
- Assessment completion
- Results retrieval
- Mode-specific handling
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging
from typing import Dict, Any
import json
from datetime import datetime

from audio_pipeline_service import audio_pipeline
from assessment_completion_service import (
    assessment_completion,
    personal_handler,
    community_handler
)

logger = logging.getLogger(__name__)

# Create blueprint
pipeline_bp = Blueprint('pipeline', __name__)

@pipeline_bp.route('/api/audio/process', methods=['POST'])
def process_audio_recording():
    """
    Process audio recording for a question

    Expected form data:
    - audio: WebM audio blob
    - questionId: Question identifier
    - sessionId: Session identifier
    """
    try:
        logger.info("🎵 Audio processing request received")

        # Validate request
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400

        audio_file = request.files['audio']
        question_id = request.form.get('questionId')
        session_id = request.form.get('sessionId')

        if not question_id or not session_id:
            return jsonify({
                'success': False,
                'error': 'questionId and sessionId are required'
            }), 400

        # Convert audio blob to bytes
        audio_bytes = audio_file.read()

        # Process audio asynchronously
        async def process_async():
            return await audio_pipeline.process_audio_recording(
                audio_bytes, question_id, session_id
            )

        # Run async function
        result = asyncio.run(process_async())

        if result['success']:
            logger.info(f"✅ Audio processed successfully for {question_id}")
            return jsonify(result), 200
        else:
            logger.error(f"❌ Audio processing failed: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Audio processing endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pipeline_bp.route('/api/assessment/complete', methods=['POST'])
def complete_assessment():
    """
    Complete assessment and generate comprehensive report

    Expected JSON body:
    {
        "sessionId": "session_123",
        "mode": "personal" | "community"
    }
    """
    try:
        logger.info("🎯 Assessment completion request received")

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON body required'
            }), 400

        session_id = data.get('sessionId')
        mode = data.get('mode', 'personal')

        if not session_id:
            return jsonify({
                'success': False,
                'error': 'sessionId is required'
            }), 400

        if mode not in ['personal', 'community']:
            return jsonify({
                'success': False,
                'error': 'Invalid mode. Must be "personal" or "community"'
            }), 400

        # For testing, create a mock comprehensive report
        # In production, this would call the actual completion service
        comprehensive_report = {
            'sessionId': session_id,
            'questions': [
                {
                    'questionId': 'TEST_Q1',
                    'score': 7.5,
                    'evaluation': 'Trả lời khá tốt',
                    'feedback': 'Tiếp tục phát huy',
                    'linguisticAnalysis': {'overall_language_score': 7.5},
                    'audioFeatures': {'speaking_rate': 2.0}
                }
            ],
            'totalScore': 7.5,
            'mmseScore': 24,
            'cognitiveLevel': 'mild',
            'timestamp': '2025-09-18T22:15:00.000Z',
            'summary': {
                'totalQuestions': 1,
                'averageScore': 7.5,
                'averageLanguageScore': 7.5,
                'averageAudioQuality': 0.8
            }
        }

        # Handle mode-specific processing
        if mode == 'personal':
            result = {
                'redirect': f'/results/{session_id}',
                'data': {
                    'comprehensiveReport': comprehensive_report,
                    'chartData': {
                        'scoreProgression': [{'question': 'TEST_Q1', 'score': 7.5}],
                        'languageBreakdown': [{'question': 'TEST_Q1', 'vocabulary': 7.0, 'coherence': 7.5, 'completeness': 8.0}],
                        'audioQuality': [{'question': 'TEST_Q1', 'energy': 80, 'speakingRate': 2.0}],
                        'cognitiveIndicators': {'memory': 0.7, 'attention': 0.8, 'language': 0.75, 'executive': 0.7}
                    },
                    'exerciseRecommendations': [
                        {'type': 'memory', 'name': 'Ghi nhớ danh sách mua sắm', 'frequency': '2 lần/ngày', 'difficulty': 'Dễ'}
                    ]
                }
            }
        else:  # community
            result = {
                'redirect': '/community/thank-you',
                'message': 'Kết quả đã được gửi đến email của bạn'
            }

        logger.info(f"✅ Assessment completed for session {session_id} in {mode} mode")
        return jsonify({
            'success': True,
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"Assessment completion error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pipeline_bp.route('/api/results/<session_id>', methods=['GET'])
def get_assessment_results(session_id: str):
    """
    Get assessment results for personal mode

    Returns comprehensive report, chart data, and recommendations
    """
    try:
        logger.info(f"📊 Results request for session {session_id}")

        # In production, this would fetch from database
        # For now, return mock data structure
        mock_results = {
            'sessionId': session_id,
            'comprehensiveReport': {
                'totalScore': 18.5,
                'mmseScore': 24,
                'cognitiveLevel': 'mild',
                'questions': [
                    {
                        'questionId': 'O1',
                        'score': 7.5,
                        'evaluation': 'Trả lời khá tốt',
                        'feedback': 'Cố gắng cụ thể hơn về thời gian'
                    }
                ]
            },
            'chartData': {
                'scoreProgression': [{'question': 'O1', 'score': 7.5}],
                'languageBreakdown': [{'question': 'O1', 'vocabulary': 6.0}],
                'audioQuality': [{'question': 'O1', 'energy': 75}]
            },
            'exerciseRecommendations': [
                {
                    'type': 'memory',
                    'name': 'Ghi nhớ danh sách mua sắm',
                    'frequency': '2 lần/ngày',
                    'difficulty': 'Dễ'
                }
            ]
        }

        return jsonify({
            'success': True,
            'data': mock_results
        }), 200

    except Exception as e:
        logger.error(f"Results retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pipeline_bp.route('/api/stats/user/<user_id>', methods=['GET'])
def get_user_stats(user_id: str):
    """
    Get user statistics and assessment history
    """
    try:
        logger.info(f"📈 Stats request for user {user_id}")

        # Mock user stats
        mock_stats = {
            'userId': user_id,
            'totalAssessments': 3,
            'averageScore': 22.5,
            'lastAssessment': '2024-09-18T10:30:00Z',
            'cognitiveTrend': 'stable',
            'assessments': [
                {
                    'sessionId': 'session_001',
                    'date': '2024-09-15',
                    'score': 24,
                    'level': 'normal'
                },
                {
                    'sessionId': 'session_002',
                    'date': '2024-09-10',
                    'score': 23,
                    'level': 'mild'
                }
            ]
        }

        return jsonify({
            'success': True,
            'data': mock_stats
        }), 200

    except Exception as e:
        logger.error(f"User stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pipeline_bp.route('/api/stats/session/<session_id>', methods=['GET'])
def get_session_stats(session_id: str):
    """
    Get detailed statistics for a specific session
    """
    try:
        logger.info(f"📊 Session stats request for {session_id}")

        # Mock session stats
        mock_session_stats = {
            'sessionId': session_id,
            'mode': 'personal',
            'startTime': '2024-09-18T10:00:00Z',
            'endTime': '2024-09-18T10:45:00Z',
            'duration': 2700,  # seconds
            'totalQuestions': 10,
            'completedQuestions': 10,
            'averageScore': 7.2,
            'mmseScore': 24,
            'cognitiveLevel': 'mild',
            'questionBreakdown': {
                'orientation': {'score': 8.0, 'questions': 3},
                'memory': {'score': 6.5, 'questions': 2},
                'attention': {'score': 7.8, 'questions': 3},
                'language': {'score': 7.0, 'questions': 2}
            },
            'improvement': '+1.2 từ lần trước'
        }

        return jsonify({
            'success': True,
            'data': mock_session_stats
        }), 200

    except Exception as e:
        logger.error(f"Session stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pipeline_bp.route('/api/email/send', methods=['POST'])
def send_assessment_email():
    """
    Send assessment results via email

    Expected JSON body:
    {
        "type": "personal" | "community",
        "data": {...assessment data...},
        "recipient": "email@example.com"
    }
    """
    try:
        logger.info("📧 Email sending request received")

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON body required'
            }), 400

        email_type = data.get('type')
        email_data = data.get('data', {})
        recipient = data.get('recipient')

        if not email_type or not recipient:
            return jsonify({
                'success': False,
                'error': 'type and recipient are required'
            }), 400

        if email_type not in ['personal', 'community']:
            return jsonify({
                'success': False,
                'error': 'Invalid email type'
            }), 400

        # Send email asynchronously
        async def send_email_async():
            if email_type == 'personal':
                # Send detailed personal email with charts
                return await _send_personal_email_async(email_data, recipient)
            else:
                # Send simple community email
                return await _send_community_email_async(email_data, recipient)

        result = asyncio.run(send_email_async())

        if result['success']:
            logger.info(f"✅ Email sent successfully to {recipient}")
            return jsonify({
                'success': True,
                'message': 'Email sent successfully'
            }), 200
        else:
            logger.error(f"❌ Email sending failed: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Email sending endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

async def _send_personal_email_async(email_data: Dict[str, Any], recipient: str) -> Dict[str, Any]:
    """Send detailed personal email"""
    try:
        # In production, this would use actual email service
        logger.info(f"Sending personal email to {recipient} with detailed results")

        # Mock email sending
        await asyncio.sleep(0.1)  # Simulate email sending

        return {
            'success': True,
            'message': f'Personal email sent to {recipient}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def _send_community_email_async(email_data: Dict[str, Any], recipient: str) -> Dict[str, Any]:
    """Send simple community email"""
    try:
        # In production, this would use actual email service
        logger.info(f"Sending community email to {recipient} with basic results")

        # Mock email sending
        await asyncio.sleep(0.1)  # Simulate email sending

        return {
            'success': True,
            'message': f'Community email sent to {recipient}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@pipeline_bp.route('/api/health/pipeline', methods=['GET'])
def pipeline_health_check():
    """
    Health check for the assessment pipeline
    """
    try:
        # Check various components
        checks = {
            'audio_pipeline': True,  # Would check actual audio pipeline health
            'assessment_completion': True,
            'personal_mode': True,
            'community_mode': True,
            'database': True,  # Would check database connectivity
            'email_service': True  # Would check email service
        }

        all_healthy = all(checks.values())

        return jsonify({
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'version': '1.0.0'
        }), 200 if all_healthy else 503

    except Exception as e:
        logger.error(f"Pipeline health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Error handlers
@pipeline_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'details': str(error)
    }), 400

@pipeline_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@pipeline_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
