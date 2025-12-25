"""
Assessment Completion Service
=============================

Handles the completion of cognitive assessments with comprehensive analysis:
- Processes all temporary questions
- Generates MMSE predictions
- Handles personal vs community modes
- Sends emails and creates reports
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from audio_pipeline_service import audio_pipeline

logger = logging.getLogger(__name__)

class AssessmentCompletionService:
    """
    Service for completing cognitive assessments and generating comprehensive reports
    """

    def __init__(self):
        self.audio_pipeline = audio_pipeline

    async def complete_assessment(self, session_id: str) -> Dict[str, Any]:
        """
        Complete assessment by processing all temporary questions and generating comprehensive report

        Args:
            session_id: Session identifier

        Returns:
            Comprehensive report with analysis, scores, and recommendations
        """
        try:
            logger.info(f"🎯 Starting assessment completion for session {session_id}")

            # Step 1: Get all temporary questions for this session
            temp_questions = await self._get_temp_questions_by_session(session_id)
            if not temp_questions:
                raise ValueError(f"No temporary questions found for session {session_id}")

            logger.info(f"📊 Found {len(temp_questions)} questions to process")

            # Step 2: Analyze each question comprehensively
            analyzed_questions = []
            for question in temp_questions:
                logger.info(f"🔬 Analyzing question {question['questionId']}")

                analysis_result = await self.audio_pipeline.analyze_question_data(question)
                analyzed_question = {
                    **question,
                    'linguisticAnalysis': analysis_result['linguistic'],
                    'audioFeatures': analysis_result['audio'],
                    'evaluation': analysis_result['evaluation'],
                    'feedback': analysis_result['feedback'],
                    'score': analysis_result['score'],
                    'processedAt': analysis_result['processedAt']
                }
                analyzed_questions.append(analyzed_question)

            # Step 3: Create comprehensive report
            comprehensive_report = {
                'sessionId': session_id,
                'questions': analyzed_questions,
                'totalScore': self._calculate_total_score(analyzed_questions),
                'mmseScore': self._predict_mmse_score(analyzed_questions),
                'cognitiveLevel': self._classify_cognitive_level(analyzed_questions),
                'timestamp': datetime.now().isoformat(),
                'summary': self._generate_summary(analyzed_questions)
            }

            logger.info(f"✅ Assessment completed - MMSE: {comprehensive_report['mmseScore']}, Level: {comprehensive_report['cognitiveLevel']}")

            # Step 4: Save to database
            await self._save_comprehensive_results(comprehensive_report)

            # Step 5: Cleanup temporary data
            await self.audio_pipeline.cleanup_temp_files(session_id)

            return comprehensive_report

        except Exception as e:
            logger.error(f"❌ Assessment completion failed: {e}")
            raise

    async def _get_temp_questions_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all temporary questions for a session"""
        # This would integrate with database
        # For now, return mock data structure
        return [
            {
                'sessionId': session_id,
                'questionId': 'O1',
                'questionContent': 'Hôm nay là ngày bao nhiêu?',
                'audioFile': f'/tmp/{session_id}_O1.wav',
                'autoTranscript': 'Hôm nay là ngày mười lăm tháng chín năm hai nghìn không trăm hai mươi tư',
                'rawAudioFeatures': {'confidence': 0.9, 'duration': 8.5}
            },
            {
                'sessionId': session_id,
                'questionId': 'R1',
                'questionContent': 'Hãy nhắc lại 3 từ: Chanh, Chìa khóa, Bóng đèn',
                'audioFile': f'/tmp/{session_id}_R1.wav',
                'autoTranscript': 'Chanh, chìa khóa, bóng đèn',
                'rawAudioFeatures': {'confidence': 0.95, 'duration': 5.2}
            }
        ]

    def _calculate_total_score(self, analyzed_questions: List[Dict[str, Any]]) -> float:
        """Calculate total assessment score"""
        if not analyzed_questions:
            return 0.0

        total_score = sum(q.get('score', 0) for q in analyzed_questions)
        return round(total_score, 2)

    def _predict_mmse_score(self, analyzed_questions: List[Dict[str, Any]]) -> int:
        """
        Predict MMSE score based on linguistic and audio analysis

        This uses a simplified model - in production, this would use trained ML models
        """
        if not analyzed_questions:
            return 15  # Default score

        # Simple scoring based on question performance
        total_questions = len(analyzed_questions)
        high_performers = sum(1 for q in analyzed_questions if q.get('score', 0) >= 7.0)
        medium_performers = sum(1 for q in analyzed_questions if 4.0 <= q.get('score', 0) < 7.0)

        # Rough MMSE estimation
        if high_performers / total_questions >= 0.8:
            return 28  # Normal cognition
        elif high_performers / total_questions >= 0.6:
            return 24  # Mild cognitive impairment
        elif medium_performers / total_questions >= 0.5:
            return 18  # Moderate impairment
        else:
            return 12  # Severe impairment

    def _classify_cognitive_level(self, analyzed_questions: List[Dict[str, Any]]) -> str:
        """Classify cognitive impairment level"""
        mmse_score = self._predict_mmse_score(analyzed_questions)

        if mmse_score >= 24:
            return 'normal'
        elif mmse_score >= 18:
            return 'mild'
        elif mmse_score >= 10:
            return 'moderate'
        else:
            return 'severe'

    def _generate_summary(self, analyzed_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate assessment summary"""
        if not analyzed_questions:
            return {}

        scores = [q.get('score', 0) for q in analyzed_questions]
        avg_score = sum(scores) / len(scores)

        # Language performance
        language_scores = []
        for q in analyzed_questions:
            linguistic = q.get('linguisticAnalysis', {})
            language_scores.append(linguistic.get('overall_language_score', 5.0))

        avg_language = sum(language_scores) / len(language_scores) if language_scores else 5.0

        # Audio quality
        audio_qualities = []
        for q in analyzed_questions:
            audio = q.get('audioFeatures', {})
            audio_qualities.append(audio.get('rms_energy', 0.1))

        avg_audio_quality = sum(audio_qualities) / len(audio_qualities) if audio_qualities else 0.1

        return {
            'totalQuestions': len(analyzed_questions),
            'averageScore': round(avg_score, 2),
            'averageLanguageScore': round(avg_language, 2),
            'averageAudioQuality': round(avg_audio_quality, 3),
            'scoreDistribution': {
                'excellent': sum(1 for s in scores if s >= 8.0),
                'good': sum(1 for s in scores if 6.0 <= s < 8.0),
                'fair': sum(1 for s in scores if 4.0 <= s < 6.0),
                'needs_improvement': sum(1 for s in scores if s < 4.0)
            }
        }

    async def _save_comprehensive_results(self, comprehensive_report: Dict[str, Any]):
        """Save comprehensive results to database"""
        # This would save to the questions and sessions tables
        logger.info(f"💾 Saving comprehensive results for session {comprehensive_report['sessionId']}")

        # Mock implementation - in production, this would use actual database operations
        print("Mock: Saving to database...")
        print(f"Session: {comprehensive_report['sessionId']}")
        print(f"Questions processed: {len(comprehensive_report['questions'])}")
        print(f"MMSE Score: {comprehensive_report['mmseScore']}")


class PersonalModeHandler:
    """
    Handles personal mode assessment completion
    """

    def __init__(self):
        self.completion_service = AssessmentCompletionService()

    async def handle_personal_mode(self, session_id: str, comprehensive_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle personal mode completion with full results and recommendations
        """
        try:
            logger.info(f"🏠 Processing personal mode for session {session_id}")

            # Update session in database
            await self._update_session_status(session_id, comprehensive_report)

            # Generate chart data
            chart_data = self._generate_chart_data(comprehensive_report)

            # Generate exercise recommendations
            exercise_recommendations = self._generate_exercise_recommendations(
                comprehensive_report['cognitiveLevel'],
                comprehensive_report['questions']
            )

            # Save to stats with full details
            await self._save_personal_stats(session_id, comprehensive_report, chart_data, exercise_recommendations)

            # Send personalized email
            await self._send_personal_email(session_id, comprehensive_report, chart_data)

            # Mark email as sent
            await self._mark_email_sent(session_id)

            return {
                'redirect': f'/results/{session_id}',
                'data': {
                    'comprehensiveReport': comprehensive_report,
                    'chartData': chart_data,
                    'exerciseRecommendations': exercise_recommendations
                }
            }

        except Exception as e:
            logger.error(f"Personal mode handling failed: {e}")
            raise

    async def _update_session_status(self, session_id: str, report: Dict[str, Any]):
        """Update session with completion status"""
        logger.info(f"📝 Updating session {session_id} status to completed")

    async def _generate_chart_data(self, comprehensive_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for personal results page"""
        questions = comprehensive_report['questions']

        return {
            'scoreProgression': [
                {'question': q['questionId'], 'score': q['score']}
                for q in questions
            ],
            'languageBreakdown': [
                {
                    'question': q['questionId'],
                    'vocabulary': q.get('linguisticAnalysis', {}).get('vocabulary_assessment', {}).get('score', 5.0),
                    'coherence': q.get('linguisticAnalysis', {}).get('coherence_evaluation', {}).get('score', 5.0),
                    'completeness': q.get('linguisticAnalysis', {}).get('semantic_completeness', {}).get('score', 5.0)
                }
                for q in questions
            ],
            'audioQuality': [
                {
                    'question': q['questionId'],
                    'energy': q.get('audioFeatures', {}).get('rms_energy', 0.1) * 100,
                    'speakingRate': q.get('audioFeatures', {}).get('speaking_rate', 2.0)
                }
                for q in questions
            ],
            'cognitiveIndicators': {
                'memory': 0.7,  # Mock values
                'attention': 0.8,
                'language': 0.6,
                'executive': 0.7
            }
        }

    async def _generate_exercise_recommendations(self, cognitive_level: str, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate personalized exercise recommendations"""
        recommendations = []

        base_recommendations = {
            'normal': [
                {'type': 'memory', 'name': 'Đọc sách hàng ngày', 'frequency': '30 phút/ngày', 'difficulty': 'Dễ'},
                {'type': 'attention', 'name': 'Giải ô chữ', 'frequency': '15 phút/ngày', 'difficulty': 'Trung bình'},
            ],
            'mild': [
                {'type': 'memory', 'name': 'Ghi nhớ danh sách mua sắm', 'frequency': '2 lần/ngày', 'difficulty': 'Dễ'},
                {'type': 'attention', 'name': 'Đếm ngược từ 100', 'frequency': '10 phút/ngày', 'difficulty': 'Trung bình'},
                {'type': 'language', 'name': 'Kể lại câu chuyện', 'frequency': '15 phút/ngày', 'difficulty': 'Trung bình'},
            ],
            'moderate': [
                {'type': 'memory', 'name': 'Nhớ tên người quen', 'frequency': 'Nhiều lần/ngày', 'difficulty': 'Dễ'},
                {'type': 'attention', 'name': 'Lặp lại chuỗi số', 'frequency': '10 phút/ngày', 'difficulty': 'Khó'},
                {'type': 'executive', 'name': 'Lập kế hoạch bữa ăn', 'frequency': 'Hàng ngày', 'difficulty': 'Trung bình'},
            ],
            'severe': [
                {'type': 'memory', 'name': 'Nhìn hình và mô tả', 'frequency': '15 phút/ngày', 'difficulty': 'Dễ'},
                {'type': 'attention', 'name': 'Đếm từ 1-10', 'frequency': 'Nhiều lần/ngày', 'difficulty': 'Dễ'},
                {'type': 'support', 'name': 'Hỗ trợ từ người thân', 'frequency': 'Hàng ngày', 'difficulty': 'N/A'},
            ]
        }

        recommendations.extend(base_recommendations.get(cognitive_level, base_recommendations['normal']))

        # Add specific recommendations based on question performance
        for question in questions:
            score = question.get('score', 5.0)
            if score < 4.0:
                if 'memory' in question['questionContent'].lower():
                    recommendations.append({
                        'type': 'memory',
                        'name': 'Luyện tập ghi nhớ từ vựng',
                        'frequency': '20 phút/ngày',
                        'difficulty': 'Dễ'
                    })
                elif 'attention' in question['questionContent'].lower():
                    recommendations.append({
                        'type': 'attention',
                        'name': 'Bài tập tập trung',
                        'frequency': '15 phút/ngày',
                        'difficulty': 'Trung bình'
                    })

        return recommendations

    async def _save_personal_stats(self, session_id: str, report: Dict[str, Any], chart_data: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        """Save personal mode stats with full details"""
        logger.info(f"📊 Saving personal stats for session {session_id}")

    async def _send_personal_email(self, session_id: str, report: Dict[str, Any], chart_data: Dict[str, Any]):
        """Send personalized email with results and charts"""
        logger.info(f"📧 Sending personal email for session {session_id}")

    async def _mark_email_sent(self, session_id: str):
        """Mark email as sent in database"""
        logger.info(f"✅ Marked email as sent for session {session_id}")


class CommunityModeHandler:
    """
    Handles community mode assessment completion
    """

    def __init__(self):
        self.completion_service = AssessmentCompletionService()

    async def handle_community_mode(self, session_id: str, comprehensive_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle community mode completion with direct email sending
        """
        try:
            logger.info(f"🌍 Processing community mode for session {session_id}")

            # Update session status
            await self._update_session_status(session_id, comprehensive_report)

            # Save minimal stats (no charts or detailed recommendations)
            await self._save_community_stats(session_id, comprehensive_report)

            # Send direct email with results
            await self._send_community_email(session_id, comprehensive_report)

            # Mark email as sent
            await self._mark_email_sent(session_id)

            return {
                'redirect': '/community/thank-you',
                'message': 'Kết quả đã được gửi đến email của bạn'
            }

        except Exception as e:
            logger.error(f"Community mode handling failed: {e}")
            raise

    async def _update_session_status(self, session_id: str, report: Dict[str, Any]):
        """Update session status for community mode"""
        logger.info(f"📝 Updating community session {session_id}")

    async def _save_community_stats(self, session_id: str, report: Dict[str, Any]):
        """Save minimal community stats"""
        logger.info(f"📊 Saving community stats for session {session_id}")

    async def _send_community_email(self, session_id: str, report: Dict[str, Any]):
        """Send direct email with community results"""
        logger.info(f"📧 Sending community email for session {session_id}")

    async def _mark_email_sent(self, session_id: str):
        """Mark community email as sent"""
        logger.info(f"✅ Marked community email as sent for session {session_id}")


# Global instances
assessment_completion = AssessmentCompletionService()
personal_handler = PersonalModeHandler()
community_handler = CommunityModeHandler()
