#!/usr/bin/env python3
"""
Database API Endpoints for Cognitive Assessment System
Provides CRUD operations for sessions, questions, stats, and temp_questions tables
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment
load_dotenv('config.env')
DATABASE_URL = os.getenv('DATABASE_URL')

# Create blueprint
database_bp = Blueprint('database', __name__)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# =============================================================================
# SESSIONS API ENDPOINTS
# =============================================================================

@database_bp.route('/api/database/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions or filter by user"""
    try:
        user_id = request.args.get('user_id')
        mode = request.args.get('mode')
        status = request.args.get('status')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)

        if mode:
            query += " AND mode = %s"
            params.append(mode)

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        sessions = cursor.fetchall()

        # Convert to dict format
        result = []
        for session in sessions:
            session_dict = dict(session)
            # Convert datetime objects to ISO format
            for key, value in session_dict.items():
                if isinstance(value, datetime):
                    session_dict[key] = value.isoformat()
            result.append(session_dict)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'sessions': result,
            'count': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/sessions', methods=['POST'])
def create_session():
    """Create a new session"""
    try:
        data = request.get_json()

        required_fields = ['user_id', 'mode']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new session
        cursor.execute('''
            INSERT INTO sessions (user_id, mode, status, total_score, mmse_score, cognitive_level, email_sent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        ''', (
            data['user_id'],
            data['mode'],
            data.get('status', 'in_progress'),
            data.get('total_score'),
            data.get('mmse_score'),
            data.get('cognitive_level'),
            data.get('email_sent', 0)
        ))

        result = cursor.fetchone()
        session_id = result['id']
        created_at = result['created_at']

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'session_id': session_id,
            'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get a specific session by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sessions WHERE id = %s', (session_id,))
        session = cursor.fetchone()

        cursor.close()
        conn.close()

        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        # Convert to dict and format datetime
        session_dict = dict(session)
        for key, value in session_dict.items():
            if isinstance(value, datetime):
                session_dict[key] = value.isoformat()

        return jsonify({
            'success': True,
            'session': session_dict
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Update a session"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute('SELECT id FROM sessions WHERE id = %s', (session_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        # Build update query
        update_fields = []
        values = []

        field_mapping = {
            'user_id': 'user_id',
            'mode': 'mode',
            'status': 'status',
            'total_score': 'total_score',
            'mmse_score': 'mmse_score',
            'cognitive_level': 'cognitive_level',
            'email_sent': 'email_sent',
            'end_time': 'end_time'
        }

        for json_field, db_field in field_mapping.items():
            if json_field in data:
                update_fields.append(f"{db_field} = %s")
                values.append(data[json_field])

        if not update_fields:
            return jsonify({
                'success': False,
                'error': 'No fields to update'
            }), 400

        # Add updated_at
        update_fields.append("updated_at = NOW()")
        values.append(session_id)

        query = f"UPDATE sessions SET {', '.join(update_fields)} WHERE id = %s"

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Session updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute('SELECT id FROM sessions WHERE id = %s', (session_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        # Delete session (this will cascade to related records if foreign keys are set)
        cursor.execute('DELETE FROM sessions WHERE id = %s', (session_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Session deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# QUESTIONS API ENDPOINTS
# =============================================================================

@database_bp.route('/api/database/questions', methods=['GET'])
def get_questions():
    """Get questions with optional filtering"""
    try:
        session_id = request.args.get('session_id')
        user_email = request.args.get('user_email')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        if user_email:
            query += " AND user_email = %s"
            params.append(user_email)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        questions = cursor.fetchall()

        # Convert to dict format
        result = []
        for question in questions:
            question_dict = dict(question)
            for key, value in question_dict.items():
                if isinstance(value, datetime):
                    question_dict[key] = value.isoformat()
            result.append(question_dict)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'questions': result,
            'count': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/questions', methods=['POST'])
def create_question():
    """Create a new question"""
    try:
        data = request.get_json()

        required_fields = ['session_id', 'question_id', 'question_content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new question
        cursor.execute('''
            INSERT INTO questions (
                session_id, question_id, question_content, audio_file, auto_transcript,
                manual_transcript, linguistic_analysis, audio_features, evaluation,
                feedback, score, processed_at, user_name, user_age, user_education, user_email
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        ''', (
            data['session_id'],
            data['question_id'],
            data['question_content'],
            data.get('audio_file'),
            data.get('auto_transcript'),
            data.get('manual_transcript'),
            json.dumps(data.get('linguistic_analysis')) if data.get('linguistic_analysis') else None,
            json.dumps(data.get('audio_features')) if data.get('audio_features') else None,
            data.get('evaluation'),
            data.get('feedback'),
            data.get('score'),
            data.get('processed_at'),
            data.get('user_name'),
            data.get('user_age'),
            data.get('user_education'),
            data.get('user_email')
        ))

        result = cursor.fetchone()
        question_id = result['id']
        created_at = result['created_at']

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'question_id': question_id,
            'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/questions/<question_id>', methods=['PUT'])
def update_question(question_id):
    """Update a question"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if question exists
        cursor.execute('SELECT id FROM questions WHERE id = %s', (question_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Question not found'
            }), 404

        # Build update query
        update_fields = []
        values = []

        field_mapping = {
            'question_content': 'question_content',
            'audio_file': 'audio_file',
            'auto_transcript': 'auto_transcript',
            'manual_transcript': 'manual_transcript',
            'linguistic_analysis': 'linguistic_analysis',
            'audio_features': 'audio_features',
            'evaluation': 'evaluation',
            'feedback': 'feedback',
            'score': 'score',
            'processed_at': 'processed_at',
            'user_name': 'user_name',
            'user_age': 'user_age',
            'user_education': 'user_education',
            'user_email': 'user_email'
        }

        for json_field, db_field in field_mapping.items():
            if json_field in data:
                update_fields.append(f"{db_field} = %s")
                if json_field in ['linguistic_analysis', 'audio_features']:
                    values.append(json.dumps(data[json_field]))
                else:
                    values.append(data[json_field])

        if not update_fields:
            return jsonify({
                'success': False,
                'error': 'No fields to update'
            }), 400

        values.append(question_id)
        query = f"UPDATE questions SET {', '.join(update_fields)} WHERE id = %s"

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Question updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# STATS API ENDPOINTS
# =============================================================================

@database_bp.route('/api/database/stats', methods=['GET'])
def get_stats():
    """Get stats with optional filtering"""
    try:
        session_id = request.args.get('session_id')
        user_id = request.args.get('user_id')
        mode = request.args.get('mode')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM stats WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)

        if mode:
            query += " AND mode = %s"
            params.append(mode)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        stats_records = cursor.fetchall()

        # Convert to dict format
        result = []
        for stat in stats_records:
            stat_dict = dict(stat)
            for key, value in stat_dict.items():
                if isinstance(value, datetime):
                    stat_dict[key] = value.isoformat()
            result.append(stat_dict)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'stats': result,
            'count': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/stats', methods=['POST'])
def create_stats():
    """Create new stats record"""
    try:
        data = request.get_json()

        required_fields = ['session_id', 'mode']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new stats
        cursor.execute('''
            INSERT INTO stats (
                session_id, user_id, mode, summary, detailed_results,
                chart_data, exercise_recommendations, user_name, user_age,
                user_education, user_email, audio_files
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        ''', (
            data['session_id'],
            data.get('user_id'),
            data['mode'],
            json.dumps(data.get('summary')) if data.get('summary') else None,
            json.dumps(data.get('detailed_results')) if data.get('detailed_results') else None,
            json.dumps(data.get('chart_data')) if data.get('chart_data') else None,
            json.dumps(data.get('exercise_recommendations')) if data.get('exercise_recommendations') else None,
            data.get('user_name'),
            data.get('user_age'),
            data.get('user_education'),
            data.get('user_email'),
            json.dumps(data.get('audio_files')) if data.get('audio_files') else None
        ))

        result = cursor.fetchone()
        stats_id = result['id']
        created_at = result['created_at']

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'stats_id': stats_id,
            'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# TEMP QUESTIONS API ENDPOINTS
# =============================================================================

@database_bp.route('/api/database/temp-questions', methods=['GET'])
def get_temp_questions():
    """Get temporary questions with optional filtering"""
    try:
        session_id = request.args.get('session_id')
        status = request.args.get('status')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM temp_questions WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        if status:
            query += " AND status = %s"
            params.append(status)

        # Auto-cleanup expired records
        cleanup_query = "DELETE FROM temp_questions WHERE expires_at < NOW()"
        cursor.execute(cleanup_query)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        temp_questions = cursor.fetchall()

        # Convert to dict format
        result = []
        for temp_q in temp_questions:
            temp_q_dict = dict(temp_q)
            for key, value in temp_q_dict.items():
                if isinstance(value, datetime):
                    temp_q_dict[key] = value.isoformat()
            result.append(temp_q_dict)

        conn.commit()  # Commit cleanup
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'temp_questions': result,
            'count': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_bp.route('/api/database/temp-questions', methods=['POST'])
def create_temp_question():
    """Create a temporary question"""
    try:
        data = request.get_json()

        required_fields = ['session_id', 'question_id', 'question_content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Set default expiration (24 hours from now)
        expires_at = datetime.now() + timedelta(hours=24)

        # Insert new temp question
        cursor.execute('''
            INSERT INTO temp_questions (
                session_id, question_id, question_content, audio_file, auto_transcript,
                raw_audio_features, status, expires_at, user_name, user_age,
                user_education, user_email
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        ''', (
            data['session_id'],
            data['question_id'],
            data['question_content'],
            data.get('audio_file'),
            data.get('auto_transcript'),
            json.dumps(data.get('raw_audio_features')) if data.get('raw_audio_features') else None,
            data.get('status', 'pending'),
            expires_at,
            data.get('user_name'),
            data.get('user_age'),
            data.get('user_education'),
            data.get('user_email')
        ))

        result = cursor.fetchone()
        temp_question_id = result['id']
        created_at = result['created_at']

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'temp_question_id': temp_question_id,
            'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at,
            'expires_at': expires_at.isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# BULK OPERATIONS
# =============================================================================

@database_bp.route('/api/database/bulk/questions', methods=['POST'])
def bulk_create_questions():
    """Bulk create questions for a session"""
    try:
        data = request.get_json()

        if not data or 'questions' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing questions array'
            }), 400

        questions = data['questions']
        if not isinstance(questions, list) or len(questions) == 0:
            return jsonify({
                'success': False,
                'error': 'Questions must be a non-empty array'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        created_questions = []

        for question_data in questions:
            try:
                cursor.execute('''
                    INSERT INTO questions (
                        session_id, question_id, question_content, audio_file, auto_transcript,
                        manual_transcript, linguistic_analysis, audio_features, evaluation,
                        feedback, score, processed_at, user_name, user_age, user_education, user_email
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, question_id
                ''', (
                    question_data.get('session_id'),
                    question_data.get('question_id'),
                    question_data.get('question_content'),
                    question_data.get('audio_file'),
                    question_data.get('auto_transcript'),
                    question_data.get('manual_transcript'),
                    json.dumps(question_data.get('linguistic_analysis')) if question_data.get('linguistic_analysis') else None,
                    json.dumps(question_data.get('audio_features')) if question_data.get('audio_features') else None,
                    question_data.get('evaluation'),
                    question_data.get('feedback'),
                    question_data.get('score'),
                    question_data.get('processed_at'),
                    question_data.get('user_name'),
                    question_data.get('user_age'),
                    question_data.get('user_education'),
                    question_data.get('user_email')
                ))

                result = cursor.fetchone()
                created_questions.append({
                    'id': result['id'],
                    'question_id': result['question_id']
                })

            except Exception as e:
                print(f"Error creating question {question_data.get('question_id')}: {e}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'created_count': len(created_questions),
            'questions': created_questions
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@database_bp.route('/api/database/health', methods=['GET'])
def database_health():
    """Check database connectivity and table status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get table counts
        tables = ['users', 'sessions', 'questions', 'stats', 'temp_questions',
                 'cognitive_assessment_results', 'community_assessments',
                 'training_samples', 'user_reports']

        table_counts = {}
        total_records = 0

        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                table_counts[table] = count
                total_records += count
            except:
                table_counts[table] = 'Error'

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'tables': table_counts,
            'total_records': total_records,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@database_bp.route('/api/database/cleanup', methods=['POST'])
def cleanup_expired():
    """Clean up expired temporary data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clean up expired temp questions
        cursor.execute('DELETE FROM temp_questions WHERE expires_at < NOW()')
        deleted_count = cursor.rowcount

        # Clean up old sessions (older than 90 days, completed)
        cursor.execute('''
            DELETE FROM sessions
            WHERE status = 'completed'
            AND end_time < NOW() - INTERVAL '90 days'
        ''')
        deleted_sessions = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'cleanup': {
                'expired_temp_questions': deleted_count,
                'old_completed_sessions': deleted_sessions
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
