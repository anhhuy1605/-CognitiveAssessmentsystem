"""
MMSE Assessment Service v2.0
Service tích hợp model MMSE mới với pipeline scoring engine, feature extraction.
"""

import os
import sys
import logging
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib

# Add release_v1 to path
RELEASE_V1_PATH = Path(__file__).parent.parent.parent / "release_v1"
sys.path.insert(0, str(RELEASE_V1_PATH))

# Import our new MMSE components
try:
    from scoring_engine import MMSEScorer
    from feature_extraction import FeatureExtractor
    from encryption import AudioEncryption
except ImportError as e:
    logging.error(f"Failed to import MMSE components: {e}")
    MMSEScorer = None
    FeatureExtractor = None
    AudioEncryption = None

logger = logging.getLogger(__name__)


class MMSEAssessmentService:
    """Service for MMSE assessment using new v2.0 model."""
    
    def __init__(self, model_dir: str = None):
        """Initialize MMSE service with trained model."""
        self.model_dir = Path(model_dir or RELEASE_V1_PATH)
        self.model = None
        self.metadata = None
        self.scaler = None
        self.feature_names = []
        self.weights = {}
        
        # Initialize components
        self.scorer = None
        self.feature_extractor = None
        self.encryptor = None
        
        # Load model if available
        self._load_model()
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize scoring and feature extraction components."""
        try:
            if MMSEScorer:
                # Initialize with sentence transformer if available
                try:
                    from sentence_transformers import SentenceTransformer
                    sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                    self.scorer = MMSEScorer(sbert_model)
                    logger.info("MMSE scorer initialized with sentence transformer")
                except Exception:
                    self.scorer = MMSEScorer()
                    logger.info("MMSE scorer initialized without sentence transformer")
            
            if FeatureExtractor:
                self.feature_extractor = FeatureExtractor()
                
                # Load training distributions if available
                distributions_path = self.model_dir / "training_distributions.json"
                if distributions_path.exists():
                    with open(distributions_path, 'r') as f:
                        self.feature_extractor.training_distributions = json.load(f)
                    logger.info("Loaded training distributions for feature normalization")
            
            if AudioEncryption:
                self.encryptor = AudioEncryption()
                
            logger.info("MMSE components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MMSE components: {e}")
    
    def _load_model(self):
        """Load trained MMSE model and metadata."""
        try:
            # Load model
            model_path = self.model_dir / "model_MMSE_v1.pkl"
            if model_path.exists():
                self.model = joblib.load(model_path)
                logger.info(f"Loaded MMSE model from {model_path}")
            
            # Load metadata
            metadata_path = self.model_dir / "model_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                
                # Extract key information
                self.weights = self.metadata.get('weights', {})
                self.feature_names = self.metadata.get('feature_list', [])
                
                # Load scaler if available
                if 'scalers' in self.metadata:
                    from sklearn.preprocessing import StandardScaler
                    self.scaler = StandardScaler()
                    self.scaler.mean_ = np.array(self.metadata['scalers']['feature_means'])
                    self.scaler.scale_ = np.array(self.metadata['scalers']['feature_stds'])
                
                logger.info("Loaded MMSE model metadata and weights")
            
        except Exception as e:
            logger.error(f"Failed to load MMSE model: {e}")
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper."""
        try:
            import whisper
            import os

            # Log audio file info
            file_size = os.path.getsize(audio_path)
            logger.info(f"🎵 Transcribing file: {audio_path}")
            logger.info(f"📊 File size: {file_size} bytes")

            if file_size < 1024:
                logger.warning(f"⚠️ Audio file too small: {file_size} bytes")
                return {
                    'transcript': '',
                    'asr_confidence': 0.0,
                    'segments': [],
                    'language': 'vi',
                    'error': 'Audio file too small'
                }

            # Load Whisper model
            model = whisper.load_model("large-v2")

            # Clear any cached results
            if hasattr(model, 'cache'):
                model.cache.clear()
            
            # Check audio duration
            import librosa
            try:
                audio, sr = librosa.load(audio_path, sr=None, duration=1.0)  # Load first second
                duration = len(audio) / sr
                logger.info(f"⏱️ Audio duration: {duration:.2f}s")

                if duration < 0.5:
                    logger.warning(f"⚠️ Audio too short: {duration:.2f}s")
                    return {
                        'transcript': '',
                        'asr_confidence': 0.0,
                        'segments': [],
                        'language': 'vi',
                        'error': f'Audio too short ({duration:.2f}s)'
                    }
            except Exception as e:
                logger.warning(f"⚠️ Could not check audio duration: {e}")

            # Transcribe
            logger.info("🎤 Starting transcription...")
            result = model.transcribe(audio_path, language='vi', word_timestamps=True)

            # Log transcription result
            raw_transcript = result['text'].strip()
            logger.info(f"📝 Raw transcript: '{raw_transcript}'")

            # Extract confidence scores
            word_confidences = []
            if 'segments' in result:
                for segment in result['segments']:
                    if 'words' in segment:
                        word_confidences.extend([w.get('probability', 0.5) for w in segment['words']])

            avg_confidence = np.mean(word_confidences) if word_confidences else 0.5
            logger.info(f"🎯 ASR confidence: {avg_confidence:.3f}")
            logger.info(f"📊 Number of segments: {len(result.get('segments', []))}")
            logger.info(f"🌐 Detected language: {result.get('language', 'unknown')}")

            # Validate transcript
            if not raw_transcript or len(raw_transcript.strip()) < 3:
                logger.warning("⚠️ Transcript too short or empty")
                return {
                    'transcript': '',
                    'asr_confidence': 0.0,
                    'segments': [],
                    'language': 'vi',
                    'error': 'Empty or too short transcript'
                }

            return {
                'transcript': raw_transcript,
                'asr_confidence': avg_confidence,
                'segments': result.get('segments', []),
                'language': result.get('language', 'vi')
            }
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                'transcript': '',
                'asr_confidence': 0.0,
                'segments': [],
                'language': 'vi',
                'error': str(e)
            }
    
    def assess_session(self, audio_path: str, session_id: str = None,
                      patient_info: Dict = None) -> Dict[str, Any]:
        """Complete MMSE assessment from audio file."""
        try:
            session_id = session_id or f"session_{int(pd.Timestamp.now().timestamp())}"
            start_time = pd.Timestamp.now()
            logger.info("=" * 80)
            logger.info(f"🎯 BẮT ĐẦU ĐÁNH GIÁ MMSE CHO SESSION: {session_id}")
            logger.info("=" * 80)
            logger.info(f"📁 Audio path: {audio_path}")
            logger.info(f"👤 Patient info: {patient_info or 'Không có'}")
            logger.info(f"⏰ Start time: {start_time}")

            # Step 1: Transcribe audio
            logger.info("🎤 BƯỚC 1: TRANSCRIBE AUDIO")
            logger.info(f"Transcribing audio for session {session_id}")
            transcribe_start = pd.Timestamp.now()
            transcription_result = self.transcribe_audio(audio_path)
            
            if 'error' in transcription_result:
                logger.error(f"❌ TRANSCRIPTION FAILED: {transcription_result['error']}")
                return {
                    'session_id': session_id,
                    'status': 'error',
                    'error': f"Transcription failed: {transcription_result['error']}"
                }

            # Log transcription results
            transcribe_end = pd.Timestamp.now()
            transcribe_duration = (transcribe_end - transcribe_start).total_seconds()
            logger.info(f"✅ Transcription completed in {transcribe_duration:.2f}s")
            logger.info(f"📝 Transcript: {transcription_result['transcript'][:200]}{'...' if len(transcription_result['transcript']) > 200 else ''}")

            # Step 2: Score MMSE items
            logger.info("📊 BƯỚC 2: SCORING MMSE ITEMS")
            logger.info(f"Scoring MMSE items for session {session_id}")
            scoring_start = pd.Timestamp.now()
            session_data = {
                'session_id': session_id,
                'transcript': transcription_result['transcript'],
                'asr_confidence': transcription_result['asr_confidence']
            }
            
            if not self.scorer:
                logger.error("❌ MMSE scorer not available")
                return {
                    'session_id': session_id,
                    'status': 'error',
                    'error': 'MMSE scorer not available'
                }

            score_result = self.scorer.score_session(session_data)

            # Log scoring results
            scoring_end = pd.Timestamp.now()
            scoring_duration = (scoring_end - scoring_start).total_seconds()
            logger.info(f"✅ Scoring completed in {scoring_duration:.2f}s")
            logger.info(f"📈 Raw MMSE score (M_raw): {score_result['M_raw']}")
            logger.info(f"📈 Language scalar (L_scalar): {score_result['L_scalar']:.3f}")
            logger.info(f"📈 Acoustic scalar (A_scalar): {score_result['A_scalar']:.3f}")

            # Log per-item scores
            logger.info("📋 Per-item scores:")
            for item_id, score in score_result['per_item_scores'].items():
                logger.info(f"  {item_id}: {score}")
            
            # Step 3: Extract features
            logger.info("🔍 BƯỚC 3: FEATURE EXTRACTION")
            logger.info(f"Extracting features for session {session_id}")
            feature_start = pd.Timestamp.now()
            if not self.feature_extractor:
                logger.error("❌ Feature extractor not available")
                return {
                    'session_id': session_id,
                    'status': 'error',
                    'error': 'Feature extractor not available'
                }

            features = self.feature_extractor.extract_all_features(
                session_data, audio_path, score_result['per_item_scores']
            )

            # Log feature extraction results
            feature_end = pd.Timestamp.now()
            feature_duration = (feature_end - feature_start).total_seconds()
            logger.info(f"✅ Feature extraction completed in {feature_duration:.2f}s")

            # Log linguistic features
            logger.info("🗣️ Linguistic features:")
            logger.info(f"  TTR: {features.get('TTR', 0):.3f}")
            logger.info(f"  Idea density: {features.get('idea_density', 0):.3f}")
            logger.info(f"  Fluency (F_flu): {features.get('F_flu', 0):.3f}")
            logger.info(f"  Word count: {features.get('word_count', 0)}")

            # Log acoustic features
            logger.info("🎵 Acoustic features:")
            logger.info(f"  Speech rate: {features.get('speech_rate_wpm', 0):.1f} WPM")
            logger.info(f"  Pause rate: {(features.get('pause_rate', 0) * 100):.1f}%")
            logger.info(f"  F0 variability: {features.get('f0_variability', 0):.1f} Hz")
            logger.info(f"  F0 mean: {features.get('f0_mean', 0):.1f} Hz")
            
            # Update scalars in score result
            score_result['L_scalar'] = features['L_scalar']
            score_result['A_scalar'] = features['A_scalar']
            
            # Step 4: Predict final MMSE score
            logger.info("🧮 BƯỚC 4: TÍNH ĐIỂM CUỐI CÙNG")
            logger.info(f"Computing final MMSE score for session {session_id}")
            final_score_start = pd.Timestamp.now()

            if self.weights:
                logger.info("⚖️ Using NNLS weights for final score calculation:")
                logger.info(f"  w_M (manual score): {self.weights['w_M']:.4f}")
                logger.info(f"  w_L (linguistic): {self.weights['w_L']:.4f}")
                logger.info(f"  w_A (acoustic): {self.weights['w_A']:.4f}")

                # Use NNLS weights
                final_score = (
                    self.weights['w_M'] * score_result['M_raw'] +
                    self.weights['w_L'] * score_result['L_scalar'] * 30.0 +
                    self.weights['w_A'] * score_result['A_scalar'] * 30.0
                )
                final_score = np.clip(final_score, 0, 30)
                score_result['Score_total_raw'] = final_score
                score_result['Score_total_rounded'] = round(final_score)

                logger.info(f"📊 Final score calculation:")
                logger.info(f"  Manual score contribution: {self.weights['w_M']:.4f} × {score_result['M_raw']} = {self.weights['w_M'] * score_result['M_raw']:.2f}")
                logger.info(f"  Linguistic contribution: {self.weights['w_L']:.4f} × {score_result['L_scalar']:.3f} × 30 = {self.weights['w_L'] * score_result['L_scalar'] * 30:.2f}")
                logger.info(f"  Acoustic contribution: {self.weights['w_A']:.4f} × {score_result['A_scalar']:.3f} × 30 = {self.weights['w_A'] * score_result['A_scalar'] * 30:.2f}")
                logger.info(f"  Final score (raw): {final_score:.2f}")
                logger.info(f"  Final score (rounded): {round(final_score)}/30")
            else:
                logger.warning("⚠️ No weights available, using raw score only")
                score_result['Score_total_raw'] = score_result['M_raw']
                score_result['Score_total_rounded'] = round(score_result['M_raw'])
            
            # Step 5: ML model prediction (if available)
            logger.info("🤖 BƯỚC 5: ML MODEL PREDICTION")
            ml_prediction = None
            if self.model and self.feature_names:
                try:
                    logger.info(f"🧠 ML model available, predicting with {len(self.feature_names)} features")

                    # Prepare features for ML model
                    feature_vector = []
                    for feature_name in self.feature_names:
                        if feature_name in features:
                            feature_vector.append(features[feature_name])
                        elif feature_name in score_result:
                            feature_vector.append(score_result[feature_name])
                        else:
                            feature_vector.append(0.0)  # Default value

                    feature_vector = np.array(feature_vector).reshape(1, -1)
                    logger.info(f"📊 Feature vector shape: {feature_vector.shape}")

                    # Scale features if scaler available
                    if self.scaler is not None:
                        feature_vector = self.scaler.transform(feature_vector)
                        logger.info("📏 Features scaled with StandardScaler")

                    # Predict
                    ml_prediction = self.model.predict(feature_vector)[0]
                    ml_prediction = np.clip(ml_prediction, 0, 30)

                    logger.info(f"🎯 ML model prediction: {ml_prediction:.2f}/30")

                except Exception as e:
                    logger.error(f"❌ ML model prediction failed: {e}")
            else:
                logger.info("⚠️ ML model not available, skipping ML prediction")
            
            # Step 6: Classification (cognitive impairment)
            logger.info("🔬 BƯỚC 6: CLASSIFICATION")
            logger.info("Classifying cognitive status...")
            cognitive_status = self._classify_cognitive_status(
                score_result['Score_total_rounded'] if 'Score_total_rounded' in score_result else score_result['M_raw'],
                ml_prediction
            )

            logger.info(f"🏥 Cognitive status: {cognitive_status['status']}")
            logger.info(f"📊 Primary score: {cognitive_status['primary_score']:.1f}")
            if cognitive_status['secondary_score']:
                logger.info(f"📊 Secondary score: {cognitive_status['secondary_score']:.1f}")
            logger.info(f"🎯 Confidence: {cognitive_status['confidence']:.1%}")
            logger.info(f"📝 Description: {cognitive_status['description']}")
            logger.info(f"📋 Risk level: {cognitive_status['risk_level']}")

            # Log recommendations
            if cognitive_status['recommendations']:
                logger.info("💡 Recommendations:")
                for i, rec in enumerate(cognitive_status['recommendations'], 1):
                    logger.info(f"  {i}. {rec}")
            
            # Compile final result
            result = {
                'session_id': session_id,
                'status': 'success',
                'timestamp': pd.Timestamp.now().isoformat(),

                # Core MMSE scores
                'mmse_scores': {
                    'M_raw': score_result['M_raw'],
                    'L_scalar': score_result['L_scalar'],
                    'A_scalar': score_result['A_scalar'],
                    'final_score': score_result.get('Score_total_rounded', score_result['M_raw']),
                    'ml_prediction': ml_prediction
                },

                # Per-item scores
                'item_scores': score_result['per_item_scores'],
                'item_confidences': score_result.get('item_confidences', {}),

                # Features
                'features': {
                    'linguistic': {
                        'TTR': features.get('TTR', 0),
                        'idea_density': features.get('idea_density', 0),
                        'F_flu': features.get('F_flu', 0),
                        'word_count': features.get('word_count', 0)
                    },
                    'acoustic': {
                        'speech_rate_wpm': features.get('speech_rate_wpm', 0),
                        'pause_rate': features.get('pause_rate', 0),
                        'f0_variability': features.get('f0_variability', 0),
                        'f0_mean': features.get('f0_mean', 0)
                    }
                },

                # ASR info
                'transcription': {
                    'text': transcription_result['transcript'],
                    'confidence': transcription_result['asr_confidence'],
                    'language': transcription_result['language']
                },

                # Clinical assessment
                'cognitive_status': cognitive_status,

                # Patient info (if provided)
                'patient_info': patient_info or {}
            }

            # Calculate total duration and log final summary
            end_time = pd.Timestamp.now()
            total_duration = (end_time - start_time).total_seconds()

            logger.info("=" * 80)
            logger.info("🎉 KẾT QUẢ CUỐI CÙNG")
            logger.info("=" * 80)
            logger.info(f"📊 ĐIỂM MMSE CUỐI CÙNG: {result['mmse_scores']['final_score']}/30")
            if ml_prediction is not None:
                logger.info(f"🤖 Dự đoán ML: {ml_prediction:.1f}/30")
            logger.info(f"🏥 Trạng thái nhận thức: {cognitive_status['status']}")
            logger.info(f"⚠️ Mức độ nguy cơ: {cognitive_status['risk_level']}")
            logger.info(f"⏱️ Tổng thời gian xử lý: {total_duration:.2f}s")
            logger.info(f"📝 Transcript: {transcription_result['transcript'][:100]}{'...' if len(transcription_result['transcript']) > 100 else ''}")
            logger.info("=" * 80)

            logger.info(f"MMSE assessment completed for session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"MMSE assessment failed for session {session_id}: {e}")
            return {
                'session_id': session_id or 'unknown',
                'status': 'error',
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _classify_cognitive_status(self, mmse_score: float, ml_prediction: float = None) -> Dict[str, Any]:
        """Classify cognitive status based on MMSE score."""
        
        # Use ML prediction if available and reliable
        if ml_prediction is not None:
            primary_score = ml_prediction
            secondary_score = mmse_score
        else:
            primary_score = mmse_score
            secondary_score = None
        
        # Standard MMSE cutoffs
        if primary_score >= 27:
            status = "normal"
            risk_level = "low"
            description = "Nhận thức bình thường"
        elif primary_score >= 24:
            status = "mild_impairment"
            risk_level = "moderate"
            description = "Suy giảm nhận thức nhẹ"
        elif primary_score >= 18:
            status = "moderate_impairment"
            risk_level = "high"
            description = "Suy giảm nhận thức vừa"
        else:
            status = "severe_impairment"
            risk_level = "very_high"
            description = "Suy giảm nhận thức nặng"
        
        # Calculate confidence based on score agreement
        confidence = 0.8  # Default confidence
        if secondary_score is not None:
            score_diff = abs(primary_score - secondary_score)
            if score_diff <= 2:
                confidence = 0.9
            elif score_diff <= 4:
                confidence = 0.75
            else:
                confidence = 0.6
        
        return {
            'status': status,
            'risk_level': risk_level,
            'description': description,
            'primary_score': primary_score,
            'secondary_score': secondary_score,
            'confidence': confidence,
            'cutoff_used': 23.5,
            'recommendations': self._get_recommendations(status, primary_score)
        }
    
    def _get_recommendations(self, status: str, score: float) -> List[str]:
        """Get clinical recommendations based on cognitive status."""
        recommendations = []
        
        if status == "normal":
            recommendations = [
                "Duy trì lối sống lành mạnh",
                "Tập thể dục thường xuyên",
                "Duy trì hoạt động trí tuệ",
                "Theo dõi sức khỏe định kỳ"
            ]
        elif status == "mild_impairment":
            recommendations = [
                "Tham khảo ý kiến bác sĩ chuyên khoa",
                "Đánh giá chi tiết hơn về nhận thức",
                "Theo dõi tiến triển",
                "Can thiệp sớm nếu cần thiết"
            ]
        elif status == "moderate_impairment":
            recommendations = [
                "Cần đánh giá bác sĩ chuyên khoa ngay",
                "Xem xét điều trị y tế",
                "Hỗ trợ chăm sóc hàng ngày",
                "Tham khảo dịch vụ tâm lý"
            ]
        else:  # severe_impairment
            recommendations = [
                "Cần điều trị y tế khẩn cấp",
                "Chăm sóc toàn diện",
                "Hỗ trợ gia đình",
                "Lập kế hoạch chăm sóc dài hạn"
            ]
        
        return recommendations
    
    def get_questions(self) -> List[Dict]:
        """Get MMSE questions schema."""
        questions_path = self.model_dir / "questions.json"
        try:
            with open(questions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load questions: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status."""
        return {
            'model_available': self.model is not None,
            'metadata_available': self.metadata is not None,
            'scorer_available': self.scorer is not None,
            'feature_extractor_available': self.feature_extractor is not None,
            'weights': self.weights,
            'feature_count': len(self.feature_names),
            'model_version': self.metadata.get('model_version', 'unknown') if self.metadata else 'unknown',
            'training_date': self.metadata.get('date_trained', 'unknown') if self.metadata else 'unknown'
        }
    
    def validate_audio_file(self, audio_path: str) -> Tuple[bool, str]:
        """Validate audio file for processing."""
        try:
            if not os.path.exists(audio_path):
                return False, "File không tồn tại"
            
            # Check file size (should be reasonable)
            file_size = os.path.getsize(audio_path)
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                return False, "File quá lớn (> 100MB)"
            
            if file_size < 1024:  # 1KB minimum
                return False, "File quá nhỏ"
            
            # Try to load with librosa to validate format
            import librosa
            try:
                audio, sr = librosa.load(audio_path, sr=None, duration=1.0)  # Load first second
                if len(audio) == 0:
                    return False, "File audio rỗng"
            except Exception as e:
                return False, f"Format audio không hợp lệ: {str(e)}"
            
            return True, "Audio file hợp lệ"
            
        except Exception as e:
            return False, f"Lỗi kiểm tra file: {str(e)}"


# Global instance
_mmse_service = None

def get_mmse_service() -> MMSEAssessmentService:
    """Get global MMSE service instance."""
    global _mmse_service
    if _mmse_service is None:
        _mmse_service = MMSEAssessmentService()
    return _mmse_service
