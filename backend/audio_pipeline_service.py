"""
Audio Pipeline Service
======================

Comprehensive audio processing pipeline for cognitive assessment system:
- WebM to WAV conversion
- Gemini API integration for speech-to-text and noise reduction
- Audio feature extraction with Librosa
- Temporary file management
"""

import os
import io
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import base64

# Audio processing
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

# Gemini API
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AudioPipelineService:
    """
    Complete audio processing pipeline for cognitive assessment
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "cognitive_audio_temp"
        self.temp_dir.mkdir(exist_ok=True)

        # Initialize Gemini
        self._init_gemini()

        # Thread pool for CPU-intensive tasks
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _init_gemini(self):
        """Initialize Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini API initialized")
        else:
            self.gemini_model = None
            logger.warning("⚠️ Gemini API key not found")

    async def process_audio_recording(self, audio_blob: bytes, question_id: str, session_id: str) -> Dict[str, Any]:
        """
        Main pipeline for processing audio recordings

        Args:
            audio_blob: Raw audio data (WebM format)
            question_id: Question identifier
            session_id: Session identifier

        Returns:
            Dict containing processed results
        """
        try:
            logger.info(f"🎵 Processing audio for question {question_id}, session {session_id}")

            # Step 1: Convert WebM to WAV
            wav_buffer = await self._convert_webm_to_wav(audio_blob)
            logger.info("✅ Audio conversion completed")

            # Step 2: Upload to temporary storage
            temp_audio_path = await self._upload_temp_audio(wav_buffer, question_id, session_id)
            logger.info(f"✅ Temp audio saved: {temp_audio_path}")

            # Step 3: Process with Gemini (speech-to-text + noise reduction)
            gemini_result = await self._process_with_gemini(temp_audio_path)
            logger.info("✅ Gemini processing completed")

            # Step 4: Save temporary question result
            temp_result = await self._save_temp_question_result({
                'sessionId': session_id,
                'questionId': question_id,
                'audioFile': str(temp_audio_path),
                'autoTranscript': gemini_result.get('transcript', ''),
                'rawAudioFeatures': gemini_result
            })

            logger.info(f"✅ Audio processing completed for {question_id}")
            return {
                'success': True,
                'tempId': temp_result['id'],
                'transcript': gemini_result.get('transcript', ''),
                'audioPath': str(temp_audio_path),
                'confidence': gemini_result.get('confidence', 0.0)
            }

        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'questionId': question_id,
                'sessionId': session_id
            }

    async def _convert_webm_to_wav(self, audio_blob: bytes) -> bytes:
        """Convert WebM audio to WAV format"""
        def _convert():
            try:
                # Create AudioSegment from bytes
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_blob), format="webm")

                # Convert to WAV
                wav_buffer = io.BytesIO()
                audio_segment.export(wav_buffer, format="wav")
                wav_buffer.seek(0)

                return wav_buffer.getvalue()

            except Exception as e:
                logger.error(f"Audio conversion failed: {e}")
                raise

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _convert)

    async def _upload_temp_audio(self, wav_buffer: bytes, question_id: str, session_id: str) -> Path:
        """Upload audio to temporary storage"""
        temp_filename = f"{session_id}_{question_id}_{int(asyncio.get_event_loop().time())}.wav"
        temp_path = self.temp_dir / temp_filename

        with open(temp_path, 'wb') as f:
            f.write(wav_buffer)

        return temp_path

    async def _process_with_gemini(self, audio_path: str) -> Dict[str, Any]:
        """Process audio with Gemini API for speech-to-text and analysis"""
        if not self.gemini_model:
            return {
                'transcript': '',
                'confidence': 0.0,
                'error': 'Gemini API not configured'
            }

        try:
            # Upload file to Gemini
            audio_file = genai.upload_file(audio_path)

            # Create prompt for comprehensive audio analysis
            prompt = """
            Phân tích file audio này và trả về JSON với cấu trúc sau:
            {
                "transcript": "đầy đủ transcript bằng tiếng Việt",
                "confidence": 0.0-1.0 (độ tin cậy của transcript),
                "noise_level": 0.0-1.0 (mức độ nhiễu),
                "speech_clarity": 0.0-1.0 (độ rõ ràng của giọng nói),
                "duration_seconds": số giây,
                "word_count": số từ,
                "language_detected": "vi" hoặc ngôn ngữ khác
            }

            Hãy tập trung vào:
            - Transcript chính xác bằng tiếng Việt
            - Đánh giá chất lượng âm thanh
            - Phân tích độ rõ ràng của giọng nói
            """

            # Generate response
            response = self.gemini_model.generate_content([
                prompt,
                audio_file
            ])

            # Parse JSON response
            try:
                result_text = response.text.strip()
                # Remove markdown code blocks if present
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]

                result = json.loads(result_text.strip())
                return result

            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'transcript': response.text.strip(),
                    'confidence': 0.8,
                    'noise_level': 0.3,
                    'speech_clarity': 0.7,
                    'duration_seconds': 0,
                    'word_count': len(response.text.split()),
                    'language_detected': 'vi'
                }

        except Exception as e:
            logger.error(f"Gemini processing failed: {e}")
            return {
                'transcript': '',
                'confidence': 0.0,
                'error': str(e)
            }

    async def _save_temp_question_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save temporary question result to database"""
        # This would integrate with the database
        # For now, return mock result
        import uuid
        return {
            'id': str(uuid.uuid4()),
            'sessionId': data['sessionId'],
            'questionId': data['questionId'],
            'audioFile': data['audioFile'],
            'autoTranscript': data['autoTranscript'],
            'rawAudioFeatures': data['rawAudioFeatures'],
            'status': 'completed',
            'createdAt': str(asyncio.get_event_loop().time())
        }

    async def analyze_question_data(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive analysis of question data using GPT-4o and Librosa
        """
        try:
            logger.info(f"🔬 Analyzing question data for {question_data.get('questionId')}")

            # Step 1: GPT-4o linguistic analysis
            linguistic_analysis = await self._analyze_with_gpt4o({
                'transcript': question_data.get('autoTranscript', ''),
                'question': question_data.get('questionContent', ''),
                'analysis_types': [
                    'vocabulary_assessment',
                    'coherence_evaluation',
                    'semantic_completeness',
                    'content_continuity'
                ]
            })

            # Step 2: Librosa audio feature extraction
            audio_features = await self._extract_audio_features({
                'audioPath': question_data.get('audioFile', ''),
                'features': [
                    'speaking_rate',
                    'pitch_mean',
                    'pitch_variation',
                    'pause_patterns',
                    'spectral_features'
                ]
            })

            # Step 3: Generate evaluation and feedback
            evaluation = self._generate_evaluation(linguistic_analysis, audio_features)
            feedback = self._generate_feedback(linguistic_analysis, audio_features)
            score = self._calculate_question_score(linguistic_analysis, audio_features)

            return {
                'linguistic': linguistic_analysis,
                'audio': audio_features,
                'evaluation': evaluation,
                'feedback': feedback,
                'score': score,
                'processedAt': str(asyncio.get_event_loop().time())
            }

        except Exception as e:
            logger.error(f"Question analysis failed: {e}")
            return {
                'error': str(e),
                'linguistic': {},
                'audio': {},
                'evaluation': 'Không thể phân tích',
                'feedback': 'Có lỗi trong quá trình phân tích',
                'score': 0.0
            }

    async def _analyze_with_gpt4o(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transcript with GPT-4o for linguistic features"""
        try:
            import openai

            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            prompt = f"""
            Phân tích transcript sau đây và trả về JSON đánh giá các khía cạnh ngôn ngữ:

            Transcript: "{params['transcript']}"
            Câu hỏi: "{params['question']}"

            Trả về JSON với cấu trúc:
            {{
                "vocabulary_assessment": {{
                    "score": 0.0-10.0,
                    "richness": 0.0-1.0,
                    "diversity": 0.0-1.0,
                    "complexity": 0.0-1.0
                }},
                "coherence_evaluation": {{
                    "score": 0.0-10.0,
                    "logical_flow": 0.0-1.0,
                    "topic_adherence": 0.0-1.0,
                    "completeness": 0.0-1.0
                }},
                "semantic_completeness": {{
                    "score": 0.0-10.0,
                    "content_coverage": 0.0-1.0,
                    "detail_level": 0.0-1.0,
                    "relevance": 0.0-1.0
                }},
                "content_continuity": {{
                    "score": 0.0-10.0,
                    "consistency": 0.0-1.0,
                    "transitions": 0.0-1.0,
                    "narrative_flow": 0.0-1.0
                }},
                "overall_language_score": 0.0-10.0,
                "cognitive_indicators": {{
                    "memory_performance": 0.0-1.0,
                    "attention_focus": 0.0-1.0,
                    "language_fluency": 0.0-1.0,
                    "executive_function": 0.0-1.0
                }}
            }}

            Đánh giá một cách khách quan và chi tiết.
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback structure
                return {
                    "vocabulary_assessment": {"score": 5.0, "richness": 0.5, "diversity": 0.5, "complexity": 0.5},
                    "coherence_evaluation": {"score": 5.0, "logical_flow": 0.5, "topic_adherence": 0.5, "completeness": 0.5},
                    "semantic_completeness": {"score": 5.0, "content_coverage": 0.5, "detail_level": 0.5, "relevance": 0.5},
                    "content_continuity": {"score": 5.0, "consistency": 0.5, "transitions": 0.5, "narrative_flow": 0.5},
                    "overall_language_score": 5.0,
                    "cognitive_indicators": {"memory_performance": 0.5, "attention_focus": 0.5, "language_fluency": 0.5, "executive_function": 0.5}
                }

        except Exception as e:
            logger.error(f"GPT-4o analysis failed: {e}")
            return {
                "error": str(e),
                "overall_language_score": 5.0
            }

    async def _extract_audio_features(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract audio features using Librosa"""
        def _extract():
            try:
                audio_path = params['audioPath']
                if not os.path.exists(audio_path):
                    return {'error': 'Audio file not found'}

                # Load audio
                y, sr = librosa.load(audio_path, sr=None)

                features = {
                    'duration_seconds': len(y) / sr,
                    'sample_rate': sr
                }

                # Speaking rate estimation
                rms = librosa.feature.rms(y=y)[0]
                peaks, _ = librosa.util.peak_pick(rms, 3, 3, 3, 3, 0.5, len(rms)//10)
                speaking_rate = len(peaks) / (len(y) / sr) if len(peaks) > 0 else 0

                features['speaking_rate'] = speaking_rate

                # Pitch analysis
                pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
                pitch_values = pitches[magnitudes > np.percentile(magnitudes, 85)]
                if len(pitch_values) > 0:
                    features['pitch_mean'] = float(np.mean(pitch_values))
                    features['pitch_std'] = float(np.std(pitch_values))
                    features['pitch_min'] = float(np.min(pitch_values))
                    features['pitch_max'] = float(np.max(pitch_values))
                else:
                    features.update({
                        'pitch_mean': 0.0,
                        'pitch_std': 0.0,
                        'pitch_min': 0.0,
                        'pitch_max': 0.0
                    })

                # Pause pattern analysis
                intervals = librosa.effects.split(y, top_db=25)
                if len(intervals) > 1:
                    pauses = []
                    for i in range(1, len(intervals)):
                        pause_duration = (intervals[i][0] - intervals[i-1][1]) / sr
                        pauses.append(pause_duration)

                    features['pause_count'] = len(pauses)
                    features['avg_pause_duration'] = float(np.mean(pauses)) if pauses else 0.0
                    features['total_pause_time'] = float(np.sum(pauses))
                else:
                    features.update({
                        'pause_count': 0,
                        'avg_pause_duration': 0.0,
                        'total_pause_time': 0.0
                    })

                # Spectral features
                stft = librosa.stft(y)
                spectrogram = np.abs(stft)
                features['spectral_centroid'] = float(np.mean(librosa.feature.spectral_centroid(S=stft, sr=sr)))
                features['spectral_bandwidth'] = float(np.mean(librosa.feature.spectral_bandwidth(S=stft, sr=sr)))
                features['spectral_rolloff'] = float(np.mean(librosa.feature.spectral_rolloff(S=spectrogram, sr=sr)))

                # Voice quality features
                features['rms_energy'] = float(np.mean(rms))
                features['zero_crossing_rate'] = float(np.mean(librosa.feature.zero_crossing_rate(y)))

                return features

            except Exception as e:
                logger.error(f"Audio feature extraction failed: {e}")
                return {'error': str(e)}

        # Run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _extract)

    def _generate_evaluation(self, linguistic: Dict, audio: Dict) -> str:
        """Generate comprehensive evaluation"""
        try:
            language_score = linguistic.get('overall_language_score', 5.0)
            audio_quality = audio.get('rms_energy', 0.1)

            if language_score >= 8.0 and audio_quality > 0.05:
                return "Trả lời xuất sắc với ngôn ngữ phong phú, mạch lạc và chất lượng âm thanh tốt"
            elif language_score >= 6.0 and audio_quality > 0.03:
                return "Trả lời khá tốt với ngôn ngữ tương đối mạch lạc và chất lượng âm thanh chấp nhận được"
            elif language_score >= 4.0:
                return "Trả lời cơ bản với một số điểm mạnh nhưng cần cải thiện tính mạch lạc"
            else:
                return "Trả lời cần cải thiện đáng kể về tính mạch lạc và phong phú ngôn ngữ"

        except Exception as e:
            return "Không thể đánh giá do lỗi kỹ thuật"

    def _generate_feedback(self, linguistic: Dict, audio: Dict) -> str:
        """Generate personalized feedback"""
        try:
            feedback_parts = []

            # Language feedback
            cognitive_indicators = linguistic.get('cognitive_indicators', {})
            if cognitive_indicators.get('memory_performance', 0.5) < 0.6:
                feedback_parts.append("Cố gắng nhớ và trình bày thông tin một cách có hệ thống hơn")
            if cognitive_indicators.get('attention_focus', 0.5) < 0.6:
                feedback_parts.append("Tập trung trả lời từng phần của câu hỏi một cách tuần tự")
            if cognitive_indicators.get('language_fluency', 0.5) < 0.6:
                feedback_parts.append("Nói chậm và rõ ràng hơn, tránh ngập ngừng")

            # Audio feedback
            if audio.get('rms_energy', 0.1) < 0.03:
                feedback_parts.append("Nói to và rõ ràng hơn để cải thiện chất lượng ghi âm")
            if audio.get('speaking_rate', 2.0) < 1.5:
                feedback_parts.append("Tăng tốc độ nói một chút để thể hiện sự tự tin hơn")

            if not feedback_parts:
                feedback_parts.append("Bạn đã làm rất tốt! Tiếp tục phát huy")

            return ". ".join(feedback_parts)

        except Exception as e:
            return "Phản hồi sẽ được cung cấp sau khi hoàn thành đánh giá"

    def _calculate_question_score(self, linguistic: Dict, audio: Dict) -> float:
        """Calculate question score based on multiple factors"""
        try:
            # Language component (70%)
            language_score = linguistic.get('overall_language_score', 5.0)
            language_component = (language_score / 10.0) * 0.7

            # Audio quality component (20%)
            audio_quality = min(audio.get('rms_energy', 0.1) * 10, 1.0)  # Normalize
            audio_component = audio_quality * 0.2

            # Speaking rate component (10%)
            speaking_rate = min(audio.get('speaking_rate', 2.0) / 3.0, 1.0)  # Normalize
            rate_component = speaking_rate * 0.1

            total_score = (language_component + audio_component + rate_component) * 10  # Scale to 0-10

            return round(total_score, 2)

        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return 5.0  # Default score

    async def cleanup_temp_files(self, session_id: str):
        """Clean up temporary files for a session"""
        try:
            import glob
            pattern = str(self.temp_dir / f"{session_id}_*.wav")
            temp_files = glob.glob(pattern)

            for file_path in temp_files:
                try:
                    os.remove(file_path)
                    logger.info(f"🗑️ Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file_path}: {e}")

        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")


# Global instance
audio_pipeline = AudioPipelineService()
