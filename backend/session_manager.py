#!/usr/bin/env python3
"""
Session Manager for MMSE Assessment
Manages question-by-question assessment and aggregates final MMSE score only when complete
"""

import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any

# Load environment
load_dotenv('config.env')

class MMSESessionManager:
    """Manages MMSE assessment sessions and question tracking"""

    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')

    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def create_session(self, user_email: str, user_info: Dict = None) -> str:
        """Create a new MMSE assessment session"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Create session record
            cursor.execute('''
                INSERT INTO sessions (user_id, mode, status, mmse_score)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (user_email, 'personal', 'in_progress', None))

            session_result = cursor.fetchone()
            session_id = str(session_result['id'])

            conn.commit()
            return session_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def add_question_response(self, session_id: str, question_data: Dict) -> bool:
        """Add a single question response to the session"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Validate session exists and is in progress
            cursor.execute('''
                SELECT status FROM sessions WHERE id = %s
            ''', (session_id,))

            session = cursor.fetchone()
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session['status'] != 'in_progress':
                raise ValueError(f"Session {session_id} is not in progress")

            # Insert question response
            cursor.execute('''
                INSERT INTO questions (
                    session_id, question_id, question_content, audio_file,
                    auto_transcript, manual_transcript, linguistic_analysis,
                    audio_features, evaluation, feedback, score, processed_at,
                    user_name, user_age, user_education, user_email
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                session_id,
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

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_session_progress(self, session_id: str) -> Dict:
        """Get current progress of a session"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get session info
            cursor.execute('''
                SELECT * FROM sessions WHERE id = %s
            ''', (session_id,))

            session = cursor.fetchone()
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Count completed questions
            cursor.execute('''
                SELECT COUNT(*) as completed_count FROM questions
                WHERE session_id = %s AND score IS NOT NULL
            ''', (session_id,))

            completed_result = cursor.fetchone()
            completed_questions = completed_result['completed_count']

            # Expected total questions based on questions.json (12 questions across 6 domains)
            total_questions = 12

            progress = {
                'session_id': session_id,
                'status': session['status'],
                'completed_questions': completed_questions,
                'total_questions': total_questions,
                'completion_percentage': (completed_questions / total_questions) * 100,
                'is_complete': completed_questions >= total_questions
            }

            return progress

        finally:
            cursor.close()
            conn.close()

    def complete_session_assessment(self, session_id: str) -> Dict:
        """Complete the session and calculate final MMSE score"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if session can be completed
            progress = self.get_session_progress(session_id)
            if not progress['is_complete']:
                raise ValueError(f"Session {session_id} is not complete yet")

            # Get all question scores
            cursor.execute('''
                SELECT question_id, score, auto_transcript, audio_features
                FROM questions
                WHERE session_id = %s AND score IS NOT NULL
                ORDER BY question_id
            ''', (session_id,))

            questions = cursor.fetchall()

            # Calculate total MMSE score
            total_score = sum(q['score'] for q in questions)

            # Prepare detailed results
            question_results = []
            for q in questions:
                question_results.append({
                    'question_id': q['question_id'],
                    'score': q['score'],
                    'transcript': q['auto_transcript'],
                    'audio_features': q['audio_features']
                })

            # Update session with final score
            cursor.execute('''
                UPDATE sessions
                SET status = 'completed',
                    mmse_score = %s,
                    end_time = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            ''', (total_score, session_id))

            # Create stats record
            cursor.execute('''
                INSERT INTO stats (
                    session_id, mode, summary, detailed_results, chart_data,
                    exercise_recommendations, audio_files
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                session_id,
                'personal',
                json.dumps({
                    'total_score': total_score,
                    'completion_rate': 100,
                    'cognitive_level': self._determine_cognitive_level(total_score)
                }),
                json.dumps(question_results),
                None,  # chart_data
                json.dumps(self._generate_recommendations(total_score)),  # exercise_recommendations
                json.dumps([q['audio_features'] for q in questions])  # audio_files
            ))

            conn.commit()

            return {
                'session_id': session_id,
                'status': 'completed',
                'final_mmse_score': total_score,
                'cognitive_level': self._determine_cognitive_level(total_score),
                'question_results': question_results,
                'recommendations': self._generate_recommendations(total_score)
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def _determine_cognitive_level(self, score: float) -> str:
        """Determine cognitive level based on MMSE score (0-30 scale) - Clinical Validation Standards"""
        if score >= 24:
            return "normal"  # Nhận thức bình thường (≥24 điểm) - Primary cutoff for cognitive impairment
        elif score >= 18:
            return "mild"    # Suy giảm nhận thức nhẹ (MCI) (18-23 điểm)
        elif score >= 10:
            return "moderate"  # Suy giảm nhận thức trung bình (10-17 điểm)
        else:
            return "severe"    # Suy giảm nhận thức nặng (0-9 điểm)

    def _generate_recommendations(self, score: float) -> List[str]:
        """Generate clinical recommendations based on MMSE score ranges - Clinical Validation Standards"""
        if score >= 24:  # Nhận thức bình thường (≥24 điểm) - Primary cutoff
            return [
                "Tiếp tục duy trì lối sống năng động và lành mạnh",
                "Tham gia các hoạt động trí tuệ và xã hội hàng ngày",
                "Duy trì chế độ ăn uống cân bằng và tập thể dục đều đặn",
                "Theo dõi sức khỏe định kỳ để phát hiện sớm các thay đổi"
            ]
        elif score >= 18:  # Suy giảm nhận thức nhẹ (MCI) (18-23 điểm)
            return [
                "Thực hiện các bài tập nhận thức đơn giản hàng ngày (đọc sách, giải ô chữ)",
                "Tăng cường tương tác xã hội và tham gia hoạt động cộng đồng",
                "Theo dõi sức khỏe định kỳ với bác sĩ thần kinh",
                "Tham gia các chương trình kích thích trí não và phòng ngừa suy giảm nhận thức",
                "Duy trì chế độ sống năng động và tránh các yếu tố nguy cơ"
            ]
        elif score >= 10:  # Suy giảm nhận thức trung bình (10-17 điểm)
            return [
                "Khám chuyên khoa thần kinh ngay để được chẩn đoán và điều trị",
                "Tham gia chương trình phục hồi chức năng nhận thức chuyên biệt",
                "Nhận hỗ trợ từ người chăm sóc và gia đình",
                "Theo dõi và điều trị tích cực các bệnh lý nền (tiểu đường, cao huyết áp, v.v.)",
                "Đánh giá và quản lý các triệu chứng hành vi"
            ]
        else:  # Suy giảm nhận thức nặng (0-9 điểm)
            return [
                "Khám chuyên khoa thần kinh ngay lập tức để được chăm sóc chuyên biệt",
                "Cần chăm sóc y tế toàn diện và liên tục",
                "Nhận hỗ trợ 24/7 từ người chăm sóc chuyên nghiệp",
                "Tham gia chương trình phục hồi chức năng chuyên sâu và lâu dài",
                "Đánh giá và quản lý các vấn đề an toàn và dinh dưỡng"
            ]

    def get_session_results(self, session_id: str) -> Dict:
        """Get complete session results"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get session info
            cursor.execute('SELECT * FROM sessions WHERE id = %s', (session_id,))
            session = cursor.fetchone()

            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session['status'] != 'completed':
                raise ValueError(f"Session {session_id} is not completed yet")

            # Get all questions
            cursor.execute('''
                SELECT * FROM questions
                WHERE session_id = %s
                ORDER BY question_id
            ''', (session_id,))

            questions = cursor.fetchall()

            # Get stats
            cursor.execute('SELECT * FROM stats WHERE session_id = %s', (session_id,))
            stats = cursor.fetchone()

            return {
                'session': dict(session),
                'questions': [dict(q) for q in questions],
                'stats': dict(stats) if stats else None
            }

        finally:
            cursor.close()
            conn.close()

# Global instance
_session_manager = None

def get_session_manager() -> MMSESessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = MMSESessionManager()
    return _session_manager
