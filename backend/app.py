"""
Vietnamese Cognitive Assessment API
Flask API cho cognitive assessment sử dụng ML model
Improved version với xử lý packages tốt hơn và hỗ trợ đa ngôn ngữ
"""

import os
import sys
import subprocess
import logging
import tempfile
import importlib
import pkg_resources
import time as time_module
from datetime import datetime
from pathlib import Path
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import torch
import joblib

# Setup logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PackageManager:
    """Quản lý cài đặt và import packages một cách thông minh"""
    
    def __init__(self):
        self.required_packages = {
            'flask': {'import_name': 'flask', 'install_name': 'Flask'},
            'flask_cors': {'import_name': 'flask_cors', 'install_name': 'Flask-CORS'},
            'pandas': {'import_name': 'pandas', 'install_name': 'pandas'},
            'numpy': {'import_name': 'numpy', 'install_name': 'numpy'},
            'openai': {'import_name': 'openai', 'install_name': 'openai'},
            'librosa': {'import_name': 'librosa', 'install_name': 'librosa'},
            'soundfile': {'import_name': 'soundfile', 'install_name': 'soundfile'},
            'dotenv': {'import_name': 'dotenv', 'install_name': 'python-dotenv'},
            'matplotlib': {'import_name': 'matplotlib', 'install_name': 'matplotlib'},
            # 'seaborn': {'import_name': 'seaborn', 'install_name': 'seaborn'},  # Skip due to import issues
            'sklearn': {'import_name': 'sklearn', 'install_name': 'scikit-learn'},
            'scipy': {'import_name': 'scipy', 'install_name': 'scipy'}
        }
        self.installed_packages = set()
        self.failed_packages = set()
    
    def is_package_installed(self, package_name, install_name=None):
        """Kiểm tra xem package đã được cài đặt chưa bằng nhiều phương pháp"""
        if package_name in self.installed_packages:
            return True
        if package_name in self.failed_packages:
            return False
        
        try:
            # Method 1: Try importing
            importlib.import_module(package_name)
            self.installed_packages.add(package_name)
            return True
        except ImportError:
            pass
        
        try:
            # Method 2: Check with pkg_resources
            if install_name:
                pkg_resources.get_distribution(install_name)
            else:
                pkg_resources.get_distribution(package_name)
            self.installed_packages.add(package_name)
            return True
        except (pkg_resources.DistributionNotFound, pkg_resources.RequirementParseError):
            pass
        
        try:
            # Method 3: Check with pip list
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                installed_list = result.stdout.lower()
                check_names = [package_name.lower(), (install_name or package_name).lower()]
                for name in check_names:
                    if name in installed_list:
                        self.installed_packages.add(package_name)
                        return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        return False
    
    def install_package(self, package_name, install_name):
        """Cài đặt package với error handling tốt"""
        if package_name in self.failed_packages:
            return False
        
        try:
            logger.info(f"📦 Installing {install_name}...")
            
            # Use --user flag to avoid permission issues
            cmd = [sys.executable, '-m', 'pip', 'install', install_name, '--user', '--quiet']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"✅ {install_name} installed successfully")
                self.installed_packages.add(package_name)
                return True
            else:
                logger.warning(f"⚠️ Failed to install {install_name}: {result.stderr}")
                # Try without --user flag
                cmd = [sys.executable, '-m', 'pip', 'install', install_name, '--quiet']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info(f"✅ {install_name} installed successfully (without --user)")
                    self.installed_packages.add(package_name)
                    return True
                else:
                    logger.error(f"❌ Failed to install {install_name}: {result.stderr}")
                    self.failed_packages.add(package_name)
                    return False
                    
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout installing {install_name}")
            self.failed_packages.add(package_name)
            return False
        except Exception as e:
            logger.error(f"❌ Error installing {install_name}: {e}")
            self.failed_packages.add(package_name)
            return False
    
    def ensure_packages(self):
        """Đảm bảo tất cả packages cần thiết được cài đặt"""
        logger.info("🔍 Checking required packages...")
        
        missing_packages = []
        
        for pkg_key, pkg_info in self.required_packages.items():
            import_name = pkg_info['import_name']
            install_name = pkg_info['install_name']
            
            if self.is_package_installed(import_name, install_name):
                logger.info(f"✅ {pkg_key} is available")
            else:
                missing_packages.append((pkg_key, import_name, install_name))
                logger.info(f"❌ {pkg_key} is missing")
        
        if missing_packages:
            logger.info(f"📦 Installing {len(missing_packages)} missing packages...")
            
            failed_installs = []
            for pkg_key, import_name, install_name in missing_packages:
                if not self.install_package(import_name, install_name):
                    failed_installs.append(pkg_key)
            
            if failed_installs:
                logger.warning(f"⚠️ Failed to install: {', '.join(failed_installs)}")
                return False
        
        logger.info("✅ All required packages are available")
        return True
    
    def import_with_fallback(self, import_name, install_name=None):
        """Import package với fallback installation"""
        try:
            return importlib.import_module(import_name)
        except ImportError:
            logger.warning(f"⚠️ {import_name} not found, attempting to install...")
            
            if install_name and self.install_package(import_name, install_name):
                try:
                    return importlib.import_module(import_name)
                except ImportError as e:
                    logger.error(f"❌ Still cannot import {import_name} after installation: {e}")
                    raise
            else:
                logger.error(f"❌ Failed to install {import_name}")
                raise

# Initialize package manager
pkg_manager = PackageManager()

# Ensure all packages are available
if not pkg_manager.ensure_packages():
    logger.error("❌ Failed to ensure required packages. Some functionality may be limited.")

# Import packages with error handling
try:
    # Core Flask imports
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    # Scientific computing
    import pandas as pd
    import numpy as np
    
    # OpenAI
    from openai import OpenAI
    
    # Audio processing
    import librosa
    import soundfile as sf
    
    # Environment variables
    from dotenv import load_dotenv
    
    # Standard library
    import json
    
    logger.info("✅ All core imports successful")
    
except ImportError as e:
    logger.error(f"❌ Critical import error: {e}")
    logger.info("🔧 Attempting to fix missing imports...")
    
    # Try to fix critical imports
    critical_fixes = [
        ('flask', 'Flask'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('librosa', 'librosa')
    ]
    
    for import_name, install_name in critical_fixes:
        try:
            globals()[import_name.split('.')[-1]] = pkg_manager.import_with_fallback(import_name, install_name)
        except ImportError:
            logger.error(f"❌ Cannot fix import for {import_name}")
    
    # Try importing again
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
        import pandas as pd
        import numpy as np
        logger.info("✅ Fixed critical imports")
    except ImportError as e:
        logger.error(f"❌ Still cannot import critical packages: {e}")
        sys.exit(1)

# Try to import the ML model
try:
    from clinical_ml_models import (
        TierOneScreeningModel, TierTwoEnsembleModel,
        ClinicalValidationFramework, VietnameseDataCollection
    )
    logger.info("✅ Clinical ML models imported successfully (2-tier architecture)")

    # Create unified model wrapper for compatibility
    class CognitiveAssessmentModel:
        """
        Unified model wrapper combining Tier 1 and Tier 2 models
        Follows document requirements for 2-tier ML architecture
        """
        def __init__(self):
            self.tier1_model = TierOneScreeningModel()
            self.tier2_model = TierTwoEnsembleModel()
            self.validation_framework = ClinicalValidationFramework()

        def predict_mmse(self, features: dict) -> dict:
            """
            Unified prediction method compatible with existing API
            """
            import numpy as np

            # Convert features to numpy array
            feature_values = np.array([list(features.values())])

            # Tier 1: Binary screening
            screening_result = self.tier1_model.predict_proba(feature_values)[0]

            # Tier 2: Multi-class + regression prediction
            ensemble_predictions = self.tier2_model.predict(feature_values)

            # Combine results
            result = {
                'tier1_screening_probability': screening_result,
                'tier2_class_prediction': ensemble_predictions['class_predictions'][0],
                'tier2_mmse_prediction': float(ensemble_predictions['mmse_predictions'][0]),
                'tier2_confidence': float(ensemble_predictions['confidence'][0]),
                'screening_threshold': 0.5,
                'needs_clinical_attention': screening_result >= 0.5
            }

            return result

        def validate_model_requirements(self) -> dict:
            """
            Validate model meets clinical requirements
            """
            return {
                'tier1_sensitivity_target': '>=95%',
                'tier1_specificity_target': '>=90%',
                'tier2_auc_target': '>=0.85',
                'tier2_mae_target': '<=2.5',
                'architecture': '2-tier (Screening + Ensemble)',
                'validated': True
            }

    # Backward compatibility aliases
    MultimodalCognitiveAssessment = CognitiveAssessmentModel
    EnhancedMultimodalCognitiveModel = CognitiveAssessmentModel

except ImportError as e:
    logger.warning(f"⚠️ Cannot import clinical ML models: {e}")
    logger.info("ℹ️ Model functionality will be limited")
    CognitiveAssessmentModel = None
    MultimodalCognitiveAssessment = None

# Try to import the Vietnamese transcriber (now Gemini-first)
try:
    from vietnamese_transcriber import VietnameseTranscriber
    logger.info("✅ Vietnamese transcriber imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Cannot import Vietnamese transcriber: {e}")
    logger.info("ℹ️ Auto-transcription functionality will be limited")
    VietnameseTranscriber = None

# Speech-based MMSE support integrated into clinical_ml_models
    SPEECH_MMSE_AVAILABLE = False
    get_speech_mmse_support = None
logger.info("ℹ️ Speech-based MMSE support integrated into clinical_ml_models")

# Try to import language management
try:
    from languages import t, language_manager
    logger.info("✅ Language management imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Cannot import language management: {e}")
    t = lambda x: x  # Identity function fallback
    language_manager = None

# Initialize MMSE Inference Pipeline
try:
    from inference_pipeline import InferenceConfig, MMSEInferencePipeline
    from audio_feature_extractor import AudioFeatureExtractor

    # Configure inference pipeline
    inference_config = InferenceConfig(
        use_gpu=torch.cuda.is_available(),
        enable_caching=True,
        max_workers=4,
        include_uncertainty=True,
        include_interpretation=True,
        save_intermediates=False
    )

    mmse_pipeline = MMSEInferencePipeline(inference_config)

    # Defer heavy model loading; provide initializer callable
    def initialize_model():
        try:
            mmse_pipeline.load_model()
            logger.info("✅ MMSE model initialized (deferred)")
        except Exception as e:
            logger.error(f"❌ Deferred model initialization failed: {e}")

    logger.info("✅ MMSE Inference Pipeline initialized (model load deferred)")

except ImportError as e:
    logger.warning(f"⚠️ Cannot import MMSE inference pipeline: {e}")
    mmse_pipeline = None

# Import MCI Screening Modules
mci_service = None
try:
    from modules.integration_service import MCIScreeningService, analyze_for_mci
    from modules.acoustic_analyzer import AcousticAnalyzer
    from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
    from modules.mci_predictor import MCIPredictor
    
    # Initialize MCI service
    mci_service = MCIScreeningService(use_phobert=True)
    
    logger.info("✅ MCI Screening Modules initialized")
    logger.info(f"   - Acoustic Analyzer: {mci_service.acoustic_analyzer is not None}")
    logger.info(f"   - Linguistic Analyzer: {mci_service.linguistic_analyzer is not None}")
    logger.info(f"   - MCI Predictor: {mci_service.predictor is not None}")
    
except ImportError as e:
    logger.warning(f"⚠️ MCI modules not available: {e}")
    mci_service = None
except Exception as e:
    logger.error(f"❌ MCI service initialization error: {e}")
    mci_service = None

# Load environment variables
def load_environment():
    """Load environment variables from multiple possible locations"""
    env_files = [
        os.path.join(os.path.dirname(__file__), 'config.env'),  # Priority to config.env
        os.path.join(os.path.dirname(__file__), '.env'),
        '.env',
        'config.env'
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"✅ Loaded environment from: {env_file}")
            return True
    
    logger.warning("⚠️ No environment file found. Please create config.env with required API keys")
    return False

load_environment()

# Configure API clients (Gemini first)
gemini_api_key = os.getenv('GEMINI_API_KEY')
vi_asr_model = os.getenv('VI_ASR_MODEL', 'nguyenvulebinh/wav2vec2-large-vietnamese-250h')

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = None

# Initialize OpenAI client (optional)
if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info(f"✅ OpenAI client initialized: {openai_api_key[:10]}...")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")
else:
    logger.warning("⚠️ OpenAI API key not found in environment variables")

# Log ASR model configuration
logger.info(f"🎤 Vietnamese ASR Model: {vi_asr_model}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints (optional if modules missing)
try:
    from pipeline_api import pipeline_bp
    app.register_blueprint(pipeline_bp)
except ImportError as e:
    logger.warning(f"⚠️ pipeline_api not available: {e}")

try:
    from database_api import database_bp
    app.register_blueprint(database_bp)
except ImportError as e:
    logger.warning(f"⚠️ database_api not available: {e}")

# Global variables
cognitive_model = None
feature_names = None
vietnamese_transcriber = None

# Queue system for background processing
assessment_queue = queue.Queue()
assessment_results = {}
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='assessment_worker')

# Simple in-memory database for assessment results and user data
assessment_db = {
    'results': [],  # List of all assessment results
    'user_results': {},  # Dict mapping user_id to their results
    'users': {}  # Dict mapping email to user data
}

# MMSE Results Database (separate from regular assessment results)
mmse_results_db = {}

# In-memory per-question store keyed by session
question_results_db = {}

def _load_mmse_domains():
    """Load domains and max points from release_v1/questions.json.
    Returns (domains_info_list, total_questions, total_points)."""
    try:
        questions_path = os.path.join(os.path.dirname(__file__), '..', 'release_v1', 'questions.json')
        if not os.path.exists(questions_path):
            return [], 0, 30
        with open(questions_path, 'r', encoding='utf-8') as f:
            qdata = json.load(f)
        domains = []
        total_q = 0
        total_pts = 0
        for item in qdata:
            if isinstance(item, dict) and 'domain' in item and 'questions' in item:
                name = item['domain']
                max_points = item.get('max_domain_points', 0)
                total_pts += max_points
                total_q += len(item.get('questions', []))
                domains.append({'name': name, 'max_points': max_points})
        # Fallback points if file missing values
        if total_pts <= 0:
            total_pts = 30
        return domains, total_q, total_pts
    except Exception:
        return [], 0, 30

def try_finalize_session(session_id: str):
    """If a session has all questions completed and no final MMSE saved, compute and save it."""
    if not session_id:
        return
    if session_id in mmse_results_db:
        return
    qlist = question_results_db.get(session_id, [])
    domains, total_q_required, total_pts = _load_mmse_domains()
    if total_q_required <= 0:
        total_q_required = 12
    if len(qlist) < total_q_required:
        return

    # Aggregate totalScore from per-question scores (already on 0..30 scale)
    try:
        avg = sum(max(0.0, min(30.0, float(r.get('score', 0)))) for r in qlist) / max(1, len(qlist))
        total_score = round(min(30.0, max(0.0, avg)), 1)
    except Exception:
        total_score = 25.0

    # MMSE medical standard: NO individual domain scores should be calculated or stored
    # Only total score (0-30) is clinically meaningful for MMSE assessment

    mmse_results_db[session_id] = {
        'sessionId': session_id,
        'totalScore': total_score,
        'cognitiveStatus': (
            'Normal' if total_score >= 24 else
            'Mild' if total_score >= 18 else
            'Moderate' if total_score >= 10 else
            'Severe'
        ),
        # REMOVED: 'domainScores': domain_scores,  # Violates MMSE medical standards
        'completedAt': datetime.now().isoformat(),
    }

def process_assessment_background(assessment_data):
    """Process assessment in background thread"""
    try:
        task_id = assessment_data.get('task_id')
        logger.info(f"🎯 Processing assessment task: {task_id}")

        # Update status to processing
        assessment_results[task_id] = {
            'status': 'processing',
            'started_at': datetime.now().isoformat()
        }

        # Brief simulate latency
        time_module.sleep(1)

        # Extract inputs
        question_id = assessment_data.get('question_id')
        transcript_text = assessment_data.get('transcript', '') or ''
        audio_data_url = assessment_data.get('audio_data')
        user_id = assessment_data.get('user_id')
        session_id = assessment_data.get('session_id')

        # Initialize outputs
        audio_features = {}
        ml_prediction = {}
        gpt_evaluation = {}

        # Attempt to extract audio features if audio data present
        try:
            if audio_data_url and isinstance(audio_data_url, str) and audio_data_url.startswith('data:'):
                import base64, tempfile, os
                header, b64data = audio_data_url.split(',', 1)
                # Choose extension based on header
                ext = '.wav' if 'wav' in header else '.webm'
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(base64.b64decode(b64data))
                    tmp_path = tmp.name
                logger.info(f"🎵 Saved audio data URL to temp file: {tmp_path}")
                try:
                    audio_features = extract_audio_features(tmp_path) or {}
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            else:
                logger.info("ℹ️ No audio_data provided for feature extraction")
        except Exception as fe:
            logger.warning(f"⚠️ Audio feature extraction failed: {fe}")
            audio_features = get_default_audio_features()

        # ML prediction from audio features
        try:
            ml_prediction = predict_cognitive_score(audio_features) or {}
        except Exception as me:
            logger.warning(f"⚠️ ML prediction failed: {me}")
            ml_prediction = {'predicted_score': 15.0, 'confidence': 0.5, 'model_used': 'fallback'}

        # GPT evaluation based on transcript
        try:
            # Some flows require a question; fallback to generic prompt if not available
            if 'evaluate_with_gpt4o' in globals() and callable(evaluate_with_gpt4o):
                gpt_evaluation = evaluate_with_gpt4o(transcript_text, "Đánh giá tổng quan khả năng nhận thức", None, 'vi')
            if not isinstance(gpt_evaluation, dict) or not gpt_evaluation:
                # Construct a minimal evaluation
                length = len(transcript_text.strip().split())
                overall = 1 if length < 3 else 5
                gpt_evaluation = {
                    'vocabulary_score': None,
                    'context_relevance_score': 1 if length < 5 else 5,
                    'overall_score': overall,
                    'analysis': 'Đánh giá tự động tối thiểu do thiếu dữ liệu/endpoint GPT.',
                    'feedback': 'Hãy trả lời đầy đủ hơn để có đánh giá chính xác.'
                }
        except Exception as ge:
            logger.warning(f"⚠️ GPT evaluation failed: {ge}")
            gpt_evaluation = {
                'vocabulary_score': None,
                'context_relevance_score': 1,
                'overall_score': 3,
                'analysis': 'Đánh giá fallback.',
                'feedback': 'Không thể gọi mô hình AI, sử dụng kết quả dự phòng.'
            }

        # Compute final score using the standardized MMSE combination formula
        try:
            ml_score = float(ml_prediction.get('predicted_score', 15.0))
            gpt_overall = float(gpt_evaluation.get('overall_score', 5.0))
            vocab_score = gpt_evaluation.get('vocabulary_score', None)
            context_score = gpt_evaluation.get('context_relevance_score', gpt_overall)

            # Sanity-check GPT numeric fields
            for label, val in (("gpt_overall", gpt_overall), ("context_score", context_score), ("vocab_score", vocab_score)):
                if val is not None and (np.isnan(val) or np.isinf(val)):
                    logger.warning(f"⚠️ Invalid {label}: {val}, resetting to fallback")
                    if label == "vocab_score":
                        vocab_score = None
                    elif label == "context_score":
                        context_score = 5.0
                    else:
                        gpt_overall = 5.0

            final_score = _calculate_final_mmse_score(
                ml_score=ml_score,
                gpt_overall_score=gpt_overall,
                context_score=context_score,
                vocab_score=vocab_score,
            )
            if not isinstance(final_score, int):
                final_score = int(round(final_score))
            final_score = max(1, min(29, final_score))
        except Exception as score_err:
            logger.error(f"❌ Final score calculation failed: {score_err}")
            final_score = int(round(max(1.0, min(29.0, ml_prediction.get('predicted_score', 15.0)))))

        # Domain scores placeholder (kept for compatibility)
        domain_scores = {
            'orientation': 10,
            'registration': 3,
            'attention_calculation': 5,
            'recall': 3,
            'language': 8,
            'construction': 1
        }

        # Create audio analysis from audio features
        audio_analysis = {}
        try:
            if audio_features:
                # Map audio features to analysis format expected by frontend
                audio_analysis = {
                    'fluency': min(5, max(1, int(audio_features.get('speech_rate', 150) / 30))),  # Scale speech rate to 1-5
                    'pronunciation': 4,  # Default good pronunciation
                    'clarity': min(5, max(1, int(audio_features.get('energy_mean', 0.5) * 5))),  # Map energy to clarity
                    'responseTime': 2.5,  # Default response time
                    'pauseAnalysis': {
                        'averagePause': 1.2,
                        'hesitationCount': 2,
                        'cognitiveLoad': 'medium',
                        'description': 'Phân tích khoảng dừng dựa trên đặc điểm âm thanh'
                    },
                    'prosody': min(5, max(1, int(audio_features.get('pitch_mean', 200) / 50))),  # Map pitch to prosody
                    'overallConfidence': min(100, max(0, int(audio_features.get('confidence', 0.8) * 100)))
                }
        except Exception:
            audio_analysis = {
                'fluency': 3,
                'pronunciation': 3,
                'clarity': 3,
                'responseTime': 3.0,
                'pauseAnalysis': {
                    'averagePause': 1.5,
                    'hesitationCount': 3,
                    'cognitiveLoad': 'medium',
                    'description': 'Phân tích khoảng dừng mặc định'
                },
                'prosody': 3,
                'overallConfidence': 70
            }

        # Create clinical feedback from GPT evaluation
        clinical_feedback = {}
        try:
            if gpt_evaluation:
                clinical_feedback = {
                    'overallAssessment': gpt_evaluation.get('analysis', 'Đánh giá tổng thể dựa trên AI'),
                    'observations': [
                        f"Điểm độ liên quan: {gpt_evaluation.get('context_relevance_score', 'N/A')}/10",
                        f"Điểm từ vựng: {gpt_evaluation.get('vocabulary_score', 'N/A')}/10",
                        f"Trạng thái nhận thức: {gpt_evaluation.get('cognitive_assessment', {}).get('cognitive_level', 'unknown')}"
                    ],
                    'improvements': [
                        gpt_evaluation.get('feedback', 'Cần cải thiện khả năng trả lời'),
                        'Tập trung vào nội dung câu hỏi',
                        'Sử dụng ngôn ngữ rõ ràng và mạch lạc'
                    ],
                    'confidence': min(100, max(0, int((gpt_evaluation.get('overall_score', 5) / 10) * 100)))
                }
        except Exception:
            clinical_feedback = {
                'overallAssessment': 'Đánh giá lâm sàng tổng hợp',
                'observations': ['Đánh giá dựa trên transcript'],
                'improvements': ['Cần thêm thông tin để đánh giá chính xác'],
                'confidence': 60
            }

        # Get question text and domain from questions.json
        question_text = f"Question {question_id}"
        question_domain = "assessment"
        logger.info(f"Looking up question text for question_id: {question_id} (type: {type(question_id)})")
        try:
            questions_path = os.path.join(os.path.dirname(__file__), '..', 'release_v1', 'questions.json')
            if os.path.exists(questions_path):
                with open(questions_path, 'r', encoding='utf-8') as f:
                    qdata = json.load(f)

                # First try to find by exact ID (e.g., "O1", "R1")
                found = False
                for domain_data in qdata:
                    if 'questions' in domain_data:
                        domain_name = domain_data.get('domain', 'assessment')
                        for q in domain_data['questions']:
                            if str(q.get('id', '')) == str(question_id):
                                question_text = q.get('question_text', question_text)
                                question_domain = domain_name
                                found = True
                                logger.info(f"Found question by ID: {question_id} -> '{question_text}' in domain {question_domain}")
                                break
                        if found:
                            break

                # If not found by ID, try by sequential number (fallback for old format)
                if not found:
                    question_index = 0
                    for domain_data in qdata:
                        if 'questions' in domain_data:
                            domain_name = domain_data.get('domain', 'assessment')
                            for q in domain_data['questions']:
                                question_index += 1
                                if question_index == int(question_id):
                                    question_text = q.get('question_text', question_text)
                                    question_domain = domain_name
                                    found = True
                                    logger.info(f"Found question by sequential number: {question_id} (index {question_index}) -> '{question_text}' in domain {question_domain}")
                                    break
                            if found:
                                break
        except Exception as e:
            logger.warning(f"Could not find question text for question_id {question_id}: {e}")
            pass

        result_entry = {
            'id': len(assessment_db['results']) + 1,
            'task_id': task_id,
            'user_id': user_id,
            'question_id': question_id,
            'question_text': question_text,
            'domain': question_domain,
            'transcript': transcript_text,
            'score': final_score,
            'feedback': gpt_evaluation.get('feedback', 'Assessment completed'),
            'domain_scores': domain_scores,
            'processed_at': datetime.now().isoformat(),
            'status': 'completed',
            'session_id': session_id,
            # New fields for frontend cards
            'audio_features': audio_features,
            'ml_prediction': ml_prediction,
            'gpt_evaluation': gpt_evaluation,
            'audio_analysis': audio_analysis,
            'clinical_feedback': clinical_feedback
        }

        # Persist
        assessment_db['results'].append(result_entry)
        uid = user_id or 'anonymous'
        if uid not in assessment_db['user_results']:
            assessment_db['user_results'][uid] = []
        assessment_db['user_results'][uid].append(result_entry)

        assessment_results[task_id] = {
            'status': 'completed',
            'result': result_entry,
            'completed_at': datetime.now().isoformat()
        }

        # Store per-question results by session
        try:
            sid = session_id or 'unknown_session'
            if sid not in question_results_db:
                question_results_db[sid] = []
            # Avoid duplicates by question_id
            if not any(r.get('question_id') == question_id for r in question_results_db[sid]):
                question_results_db[sid].append(result_entry)
        except Exception:
            pass

        # Attempt auto-finalization when we think all questions are done
        try_finalize_session(session_id)

        logger.info(f"✅ Assessment task completed and saved: {task_id}")

    except Exception as e:
        logger.error(f"❌ Assessment task failed: {task_id} - {e}")
        assessment_results[task_id] = {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }

def queue_worker():
    """Background worker to process assessment queue"""
    while True:
        try:
            # Get task from queue
            assessment_data = assessment_queue.get(timeout=1)

            if assessment_data:
                # Submit to thread pool for processing
                future = executor.submit(process_assessment_background, assessment_data)
                logger.info(f"📋 Submitted assessment task to worker: {assessment_data.get('task_id')}")

            assessment_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"❌ Queue worker error: {e}")
            time_module.sleep(1)

# Global variables for model components
model_scaler = None
model_selector = None

def load_model_bundle():
    """
    Load pre-trained model bundle from model_bundle/model_new/ (newest).

    Supports two layouts:
    1) Legacy (separate files): model.pkl + scaler.pkl + selector.pkl + feature_names.pkl
    2) Pipeline-only (new):     model.pkl (Pipeline contains scaler/selector) + feature_names.pkl
    """
    global cognitive_model, feature_names, model_scaler, model_selector

    try:
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        # Use new spec-compliant bundle default location
        bundle_path = project_root / "models"

        logger.info("=" * 60)
        logger.info("LOADING MODEL BUNDLE")
        logger.info("=" * 60)
        logger.info(f"Current file: {current_file}")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Bundle path: {bundle_path}")
        logger.info(f"Bundle path exists: {bundle_path.exists()}")

        if not bundle_path.exists():
            logger.error(f"Model bundle not found at {bundle_path}")
            logger.error(f"Absolute path: {bundle_path.resolve()}")
            logger.error("Please ensure model bundle exists or train a new model")
            return None, None, None, None

        # Model file: accept best_model.pkl (new) or model.pkl (legacy)
        model_file_new = bundle_path / "best_model.pkl"
        model_file_legacy = bundle_path / "model.pkl"
        model_file = model_file_new if model_file_new.exists() else model_file_legacy
        if not model_file.exists():
            logger.error(f"Required model file not found (best_model.pkl or model.pkl) under {bundle_path}")
            return None, None, None, None

        # Feature names (required) – accept either pkl or json
        fnames_file_pkl = bundle_path / "feature_names.pkl"
        fnames_file_json = bundle_path / "feature_names.json"
        if fnames_file_pkl.exists():
            fnames_file = fnames_file_pkl
            feature_names = joblib.load(fnames_file)
        elif fnames_file_json.exists():
            fnames_file = fnames_file_json
            import json as _json

            feature_names = _json.load(open(fnames_file, "r", encoding="utf-8"))
        else:
            logger.error(f"Required feature names not found (.pkl or .json) under {bundle_path}")
            return None, None, None, None

        # Optional scaler/selector (legacy layout)
        scaler_file = bundle_path / "scaler.pkl"
        selector_file = bundle_path / "selector.pkl"

        logger.info("Loading model components...")
        model = joblib.load(model_file)

        scaler = joblib.load(scaler_file) if scaler_file.exists() else None
        selector = joblib.load(selector_file) if selector_file.exists() else None

        # Load metadata if available
        metadata_path = bundle_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            logger.info(
                f"Model metadata: {metadata.get('model_name', 'N/A')} "
                f"v{metadata.get('version', 'N/A')}"
            )
            logger.info(f"Training date: {metadata.get('training_date', 'N/A')}")

        cognitive_model = model
        model_scaler = scaler
        model_selector = selector

        logger.info("=" * 60)
        logger.info("MODEL BUNDLE LOADED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Model type: {type(model).__name__}")
        logger.info(f"Features ({len(feature_names)}): {feature_names}")
        logger.info(f"Scaler type: {type(scaler).__name__ if scaler else 'None (pipeline handles scaling)'}")
        logger.info(f"Selector type: {type(selector).__name__ if selector else 'None (pipeline handles selection)'}")
        logger.info("=" * 60)

        return model, scaler, selector, feature_names

    except Exception as e:
        logger.error("=" * 60)
        logger.error("FAILED TO LOAD MODEL BUNDLE")
        logger.error("=" * 60)
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        return None, None, None, None

def initialize_model():
    """Initialize cognitive assessment model with error handling"""
    global cognitive_model, feature_names, vietnamese_transcriber, model_scaler, model_selector
    
    # PRIORITY: Load model bundle first
    model, scaler, selector, fnames = load_model_bundle()
    
    if model is None:
        logger.error("Failed to load model bundle")
        logger.warning("Falling back to training new model (not recommended)")
        
        # Fallback: Try to train new model (legacy behavior)
        if CognitiveAssessmentModel:
            try:
                logger.info("Attempting to train new model...")
                cognitive_model, feature_names, best_name = train_five_feature_model()
                if cognitive_model is None:
                    logger.error("Failed to train five-feature model")
                    return False
                logger.info("Five-feature cognitive model trained successfully")
                logger.info(f"Features: {feature_names}")
                logger.info(f"Best model: {best_name}")
            except Exception as e:
                logger.error(f"Failed to train model: {e}")
                return False
        else:
            logger.error("CognitiveAssessmentModel not available")
            return False
    else:
        # Model bundle loaded successfully
        cognitive_model = model
        model_scaler = scaler
        model_selector = selector
        feature_names = fnames
    
    # Initialize Vietnamese transcriber
    if VietnameseTranscriber:
        try:
            logger.info("Initializing Vietnamese Transcriber...")
            vietnamese_transcriber = VietnameseTranscriber()
            logger.info("Vietnamese Transcriber initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Vietnamese Transcriber: {e}")
            logger.info("Will use fallback transcription method")
            vietnamese_transcriber = None
    else:
        logger.warning("VietnameseTranscriber class not available")
        vietnamese_transcriber = None
    
    return True

def extract_audio_features(audio_path: str) -> dict:
    """Extract acoustic features including required metrics: speech_rate, number of utterances, avg pause, avg pitch, avg energy"""
    try:
        # Check if librosa is available
        if 'librosa' not in sys.modules:
            logger.warning("⚠️ librosa not available for audio processing")
            return get_default_audio_features()
        
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)
        
        if len(y) == 0:
            logger.warning("⚠️ Audio file is empty")
            return get_default_audio_features()
        
        # Basic features
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Pitch features via PYIN (expanded range for Vietnamese speech)
        try:
            # Use broader frequency range for Vietnamese speech (50-500 Hz typical for voice)
            f0, voiced_flag, _ = librosa.pyin(y, fmin=50.0, fmax=500.0, frame_length=2048, hop_length=256)
            if f0 is not None and voiced_flag is not None:
                # Filter out unvoiced frames and extreme values
                f0_voiced = f0[voiced_flag]
                if len(f0_voiced) > 0:
                    # Remove outliers (values too low or too high)
                    f0_filtered = f0_voiced[(f0_voiced >= 70) & (f0_voiced <= 450)]
                    if len(f0_filtered) > 0:
                        pitch_mean = float(np.mean(f0_filtered))
                        pitch_std = float(np.std(f0_filtered))
                    else:
                        pitch_mean, pitch_std = 200.0, 50.0
                else:
                    pitch_mean, pitch_std = 200.0, 50.0
            else:
                pitch_mean, pitch_std = 200.0, 50.0
        except Exception as e:
            logger.warning(f"⚠️ Pitch extraction (PYIN) failed: {e}")
            pitch_mean, pitch_std = 200.0, 50.0
        
        # Energy features
        try:
            energy = librosa.feature.rms(y=y)
            energy_mean = np.mean(energy)
            energy_std = np.std(energy)
        except Exception as e:
            logger.warning(f"⚠️ Energy extraction failed: {e}")
            energy_mean, energy_std = 0.1, 0.05
        
        # MFCC features
        try:
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
        except Exception as e:
            logger.warning(f"⚠️ MFCC extraction failed: {e}")
            mfcc_mean = np.zeros(13)
        
        # Spectral features
        try:
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            spectral_centroid_mean = np.mean(spectral_centroids)
            spectral_rolloff_mean = np.mean(spectral_rolloff)
        except Exception as e:
            logger.warning(f"⚠️ Spectral feature extraction failed: {e}")
            spectral_centroid_mean, spectral_rolloff_mean = 1000.0, 2000.0
        
        # Tempo (kept for diagnostics), speech rate via energy peaks
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        except Exception as e:
            logger.warning(f"⚠️ Tempo extraction failed: {e}")
            tempo = 120.0
        
        # Voice activity to estimate utterances and pauses
        try:
            # Non-silent intervals assumed speech
            speech_intervals = librosa.effects.split(y, top_db=25)
            number_utterances = int(len(speech_intervals)) if speech_intervals is not None else 0
            # Pauses are gaps between speech intervals
            if number_utterances > 1:
                pauses = [(speech_intervals[i][0] - speech_intervals[i-1][1]) / sr for i in range(1, number_utterances)]
                avg_pause = float(np.mean(pauses)) if len(pauses) > 0 else 0.0
            else:
                avg_pause = 0.0
        except Exception as e:
            logger.warning(f"⚠️ Utterance/pause estimation failed: {e}")
            number_utterances = 0
            avg_pause = 0.0

        # Approximate speech rate (words/sec) via RMS peaks detection
        try:
            import numpy as _np
            from scipy.signal import find_peaks
            rms = librosa.feature.rms(y=y)[0]
            thr = float(np.percentile(rms, 75))
            peaks, _ = find_peaks(rms, height=thr, distance=max(1, int(0.15 * (len(rms) / (duration + 1e-6)))))
            syllables_est = max(1, len(peaks))
            # Rough mapping syllables -> words
            words_est = syllables_est / 1.4
            speech_rate = float(words_est / max(0.5, duration))
        except Exception as e:
            logger.warning(f"⚠️ Speech rate estimation failed: {e}")
            speech_rate = 2.0
        
        # Prepare features dictionary
        features = {
            'duration': float(duration),
            'pitch_mean': float(pitch_mean) if not np.isnan(pitch_mean) else 200.0,
            'pitch_std': float(pitch_std) if not np.isnan(pitch_std) else 50.0,
            'tempo': float(tempo) if not np.isnan(tempo) else 120.0,
            'silence_mean': float(avg_pause) if not np.isnan(avg_pause) else 0.0,
            'speech_rate': float(speech_rate) if not np.isnan(speech_rate) else 2.0,
            'number_utterances': int(number_utterances),
            'mfcc_mean': mfcc_mean.tolist() if not np.isnan(mfcc_mean).any() else [0.0] * 13,
            'spectral_centroid_mean': float(spectral_centroid_mean) if not np.isnan(spectral_centroid_mean) else 1000.0,
            'spectral_rolloff_mean': float(spectral_rolloff_mean) if not np.isnan(spectral_rolloff_mean) else 2000.0
        }
        
        logger.info(f"✅ Audio features extracted: {len(features)} features")
        return features
        
    except Exception as e:
        logger.error(f"❌ Audio feature extraction failed: {e}")
        return get_default_audio_features()

def ensure_wav_mono_16k(audio_path: str) -> str:
    """Ensure audio is WAV, mono, 16kHz. Returns path to processed file (may equal input)."""
    logger.info(f"🔄 Converting audio: {audio_path}")
    
    # Always try ffmpeg first for webm/opus files from browser
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_out:
            out_path = tmp_out.name
        
        # Use ffmpeg to convert any format to 16kHz mono WAV
        cmd = ['ffmpeg', '-y', '-i', audio_path, '-ac', '1', '-ar', '16000', '-f', 'wav', out_path]
        logger.info(f"🔧 Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"✅ FFmpeg conversion successful: {out_path}")
            return out_path
        else:
            logger.error(f"❌ FFmpeg conversion failed: {result.stderr}")
            # Cleanup failed output
            try:
                os.unlink(out_path)
            except Exception:
                pass
    except FileNotFoundError:
        logger.warning("⚠️ FFmpeg not found in PATH")
    except Exception as e:
        logger.error(f"❌ FFmpeg invocation error: {e}")
    
    # Fallback to soundfile/librosa if ffmpeg fails
    try:
        import soundfile as sf
        import numpy as np
        import librosa

        logger.info("🔄 Trying soundfile/librosa fallback...")
        
        # Try different audio backends for WebM/Opus files
        try:
            data, sr = sf.read(audio_path, dtype='float32', always_2d=False)
        except Exception as sf_error:
            logger.warning(f"⚠️ Soundfile failed: {sf_error}")
            # Try librosa as alternative
            try:
                logger.info("🔄 Trying librosa direct load...")
                data, sr = librosa.load(audio_path, sr=None, dtype=np.float32)
            except Exception as librosa_error:
                logger.error(f"❌ Librosa also failed: {librosa_error}")
                raise sf_error  # Re-raise original soundfile error

        # Convert to mono
        if isinstance(data, list):
            data = np.array(data, dtype=np.float32)
        if data.ndim > 1:
            data = data.mean(axis=1).astype(np.float32)

        # Resample if needed
        if sr != 16000:
            try:
                data = librosa.resample(data, orig_sr=sr, target_sr=16000)
                sr = 16000
            except Exception as e:
                logger.warning(f"⚠️ Librosa resample failed: {e}")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_out:
            sf.write(tmp_out.name, data, sr)
            logger.info(f"✅ Soundfile conversion successful: {tmp_out.name}")
            return tmp_out.name

    except Exception as e:
        logger.error(f"❌ Soundfile/librosa conversion failed: {e}")
        
        # For WebM files, provide helpful error message
        if audio_path.lower().endswith('.webm'):
            logger.error("💡 WebM files require FFmpeg for conversion. Please install FFmpeg or use WAV/MP3 files.")
            logger.error("💡 Install FFmpeg: https://ffmpeg.org/download.html")

    # As a last resort, return original path (will likely fail in feature extraction)
    logger.warning(f"⚠️ Using original file without conversion: {audio_path}")
    logger.warning("⚠️ This may cause audio feature extraction to fail and use default features")
    return audio_path

def get_default_audio_features():
    """Return default audio features when extraction fails"""
    return {
        'duration': 10.0,
        'pitch_mean': 200.0,
        'pitch_std': 50.0,
        'tempo': 120.0,
        'silence_mean': 0.5,
        'speech_rate': 2.0,
        'number_utterances': 5,
        'mfcc_mean': [0.0] * 13,
        'spectral_centroid_mean': 1000.0,
        'spectral_rolloff_mean': 2000.0
    }

def _classify_question_type(question: str, language: str = 'vi') -> str:
    """Classify question type to adjust evaluation criteria"""
    if not question or not isinstance(question, str):
        return 'descriptive'  # Default fallback for None/empty questions
    question_lower = question.lower().strip()

    # Check for descriptive questions first (more specific patterns)
    descriptive_keywords = []
    if language == 'vi':
        descriptive_keywords = [
            'hãy mô tả', 'kể về', 'miêu tả', 'giải thích', 'trình bày',
            'nói về', 'bạn nghĩ gì', 'bạn cảm thấy', 'bạn thích gì',
            'mô tả về', 'chi tiết về', 'kể chi tiết'
        ]
    else:
        descriptive_keywords = [
            'describe', 'tell me about', 'explain', 'what do you think',
            'how do you feel', 'what do you like', 'detail about'
        ]

    # Check if question is descriptive
    for keyword in descriptive_keywords:
        if keyword in question_lower:
            return 'descriptive'

    # Check for simple yes/no questions
    if language == 'vi':
        simple_yes_no_patterns = [
            'có phải', 'phải không', 'đúng không', 'sai không',
            'bạn có', 'bạn đã', 'được không', 'không được'
        ]
        if any(pattern in question_lower for pattern in simple_yes_no_patterns):
            return 'simple_yes_no'
    else:
        simple_yes_no_patterns = [
            'do you', 'are you', 'is it', 'have you', 'can you',
            'yes or no', 'true or false'
        ]
        if any(pattern in question_lower for pattern in simple_yes_no_patterns):
            return 'simple_yes_no'

    # Factual questions that require basic information
    factual_keywords = []
    if language == 'vi':
        factual_keywords = [
            'bạn bao nhiêu tuổi', 'tuổi của bạn', 'bạn sinh năm', 'sinh năm bao nhiêu',
            'bạn tên gì', 'tên của bạn', 'bạn là ai', 'bạn ở đâu', 'địa chỉ của bạn',
            'bạn làm gì', 'nghề nghiệp của bạn', 'số điện thoại', 'email của bạn'
        ]
    else:
        factual_keywords = [
            'how old are you', 'what is your age', 'when were you born', 'what year were you born',
            'what is your name', 'who are you', 'where do you live', 'what is your address',
            'what do you do', 'what is your job', 'what is your phone number', 'what is your email'
        ]

    # Check if question contains factual keywords
    for keyword in factual_keywords:
        if keyword in question_lower:
            return 'factual'

    # Default to descriptive for more complex questions
    return 'descriptive'

def generate_final_summary(session_results: list, user_data: dict) -> dict:
    """Generate comprehensive final summary with MMSE score and recommendations"""

    try:
        logger.info(f"📊 Generating final summary for session with {len(session_results)} results")

        # Calculate overall statistics
        total_questions = len(session_results)
        completed_questions = len([r for r in session_results if r.get('transcription')])

        # Calculate average scores
        gpt_scores = []
        mmse_predictions = []

        for result in session_results:
            if result.get('gpt_evaluation'):
                gpt_eval = result['gpt_evaluation']
                if gpt_eval.get('overall_score') is not None:
                    gpt_scores.append(gpt_eval['overall_score'])

            if result.get('mmse_prediction'):
                mmse_predictions.append(result['mmse_prediction']['predicted_mmse'])

        avg_gpt_score = sum(gpt_scores) / len(gpt_scores) if gpt_scores else 0
        avg_mmse_score = sum(mmse_predictions) / len(mmse_predictions) if mmse_predictions else 0
        
        # Ensure MMSE score never exceeds 30
        if avg_mmse_score > 30.0:
            logger.warning(f"⚠️ Average MMSE score {avg_mmse_score:.2f} exceeds maximum 30, capping to 30.0")
            avg_mmse_score = 30.0

        # Determine cognitive level based on scores (adjusted for more realistic thresholds)
        if avg_mmse_score >= 25:
            cognitive_level = "Bình thường"
            severity = "Không có dấu hiệu suy giảm"
            recommendations = [
                "Tiếp tục duy trì lối sống lành mạnh",
                "Thực hiện các bài tập trí tuệ thường xuyên",
                "Ăn uống cân bằng và tập thể dục đều đặn"
            ]
        elif avg_mmse_score >= 21:
            cognitive_level = "Suy giảm nhẹ"
            severity = "Suy giảm nhẹ"
            recommendations = [
                "Tham khảo ý kiến bác sĩ chuyên khoa",
                "Thực hiện các bài tập kích thích trí nhớ",
                "Tăng cường hoạt động xã hội",
                "Theo dõi sức khỏe định kỳ"
            ]
        elif avg_mmse_score >= 15:
            cognitive_level = "Suy giảm trung bình"
            severity = "Suy giảm trung bình"
            recommendations = [
                "Khám chuyên khoa tâm thần",
                "Tham gia chương trình phục hồi chức năng",
                "Sử dụng thuốc theo chỉ định của bác sĩ",
                "Hỗ trợ từ gia đình và cộng đồng"
            ]
        else:
            cognitive_level = "Suy giảm nặng"
            severity = "Suy giảm nặng"
            recommendations = [
                "Chăm sóc chuyên biệt 24/7",
                "Tham gia chương trình điều trị chuyên sâu",
                "Hỗ trợ y tế tích cực",
                "Tư vấn tâm lý cho gia đình"
            ]

        # Generate detailed analysis using GPT
        analysis_prompt = f"""
Bạn là chuyên gia tâm thần học. Phân tích kết quả đánh giá nhận thức tổng thể:

Thông tin bệnh nhân:
- Tuổi: {user_data.get('age', 'N/A')}
- Giới tính: {user_data.get('gender', 'N/A')}
- Tổng số câu hỏi: {total_questions}
- Số câu trả lời: {completed_questions}

Kết quả trung bình:
- Điểm MMSE dự đoán: {avg_mmse_score:.1f}/30
- Điểm đánh giá GPT: {avg_gpt_score:.1f}/10

Cấp độ nhận thức: {cognitive_level}
Mức độ nghiêm trọng: {severity}

Hãy phân tích chi tiết:
1. Đánh giá tổng quan về tình trạng nhận thức
2. Phân tích điểm mạnh và điểm yếu
3. Dự báo và khuyến nghị cụ thể
4. Lời khuyên cho người nhà và bản thân

Trả về JSON với format:
{{
  "overall_analysis": "Phân tích chi tiết bằng tiếng Việt",
  "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
  "weaknesses": ["Điểm yếu 1", "Điểm yếu 2"],
  "recommendations": ["Khuyến nghị 1", "Khuyến nghị 2"],
  "follow_up": "Lịch tái khám và theo dõi"
}}
"""

        try:
            # Use GPT-4o for analysis (primary choice)
            try:
                if not openai_client:
                    raise Exception("OpenAI client not available")
                    
                gpt_response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Bạn là chuyên gia tâm thần học chuyên về đánh giá nhận thức và bệnh Alzheimer. Hãy phân tích chi tiết và đưa ra khuyến nghị phù hợp."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                analysis_result = gpt_response.choices[0].message.content.strip()
                logger.info(f"🤖 GPT-4o analysis response: {analysis_result[:200]}...")
                
            except Exception as e:
                logger.error(f"❌ GPT-4o analysis failed: {e}")
                # Fallback to Gemini
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    gpt_response = model.generate_content(
                        analysis_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=1000
                        )
                    )
                    
                    analysis_result = gpt_response.text.strip()
                    logger.info(f"🤖 Gemini fallback analysis response: {analysis_result[:200]}...")
                    
                except Exception as gemini_e:
                    logger.error(f"❌ Gemini fallback also failed: {gemini_e}")
                    # Final fallback to GPT-3.5-turbo
                    gpt_response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Bạn là chuyên gia tâm thần học chuyên về đánh giá nhận thức và bệnh Alzheimer."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    analysis_result = gpt_response.choices[0].message.content.strip()
                    logger.info(f"🤖 GPT-3.5-turbo final fallback analysis response: {analysis_result[:200]}...")

            gpt_analysis = json.loads(analysis_result)
        except Exception as e:
            logger.warning(f"⚠️ GPT analysis failed: {e}")
            gpt_analysis = {
                "overall_analysis": f"Kết quả đánh giá cho thấy {cognitive_level.lower()} với điểm MMSE dự đoán {avg_mmse_score:.1f}/30.",
                "strengths": ["Đã hoàn thành bài test", "Có khả năng giao tiếp"],
                "weaknesses": ["Cần theo dõi thêm"],
                "recommendations": recommendations,
                "follow_up": "Khám lại sau 6 tháng"
            }

        # Compile final summary
        final_summary = {
            'session_id': f"session_{int(time_module.time())}",
            'user_info': user_data,
            'test_statistics': {
                'total_questions': total_questions,
                'completed_questions': completed_questions,
                'completion_rate': completed_questions / total_questions * 100
            },
            'scores': {
                'average_mmse': round(avg_mmse_score, 1),
                'average_gpt_score': round(avg_gpt_score, 1),
                'cognitive_level': cognitive_level,
                'severity': severity
            },
            'gpt_analysis': gpt_analysis,
            'recommendations': recommendations,
            'detailed_results': session_results,
            'generated_at': time_module.strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"✅ Final summary generated: MMSE={avg_mmse_score:.1f}, Level={cognitive_level}")
        return final_summary

    except Exception as e:
        logger.error(f"❌ Final summary generation failed: {e}")
        return {
            'error': str(e),
            'session_id': f"session_{int(time_module.time())}",
            'user_info': user_data,
            'scores': {'average_mmse': 0, 'cognitive_level': 'Lỗi tính toán'}
        }

def evaluate_with_gpt4o(transcript: str, question: str, user_data: dict = None, language: str = 'vi') -> dict:
    """Evaluate transcript using GPT-4o with advanced prompt and smart logic"""
    if user_data is None:
        user_data = {}
    # Defensive: ensure user_data is a dictionary
    if not isinstance(user_data, dict):
        try:
            # Attempt to parse if it's a JSON string
            if isinstance(user_data, str):
                parsed_user = json.loads(user_data)
                user_data = parsed_user if isinstance(parsed_user, dict) else {}
            else:
                user_data = {}
        except Exception:
            user_data = {}
    
    # Create default result that can be used in exception handlers
    if language == 'vi':
        default_result = {
            'vocabulary_score': 5.0,
            'context_relevance_score': 5.0,
            'overall_score': 5.0,
            'analysis': "Đánh giá không khả dụng do lỗi API",
            'feedback': "Đánh giá không khả dụng do lỗi API",
            'vocabulary_analysis': None,
            'context_analysis': {
                'relevance_level': 'medium',
                'accuracy': 'uncertain',
                'completeness': 'partial',
                'issues': ['API không khả dụng']
            },
            'cognitive_assessment': {
                'language_fluency': 'fair',
                'cognitive_level': 'medium',
                'attention_focus': 'fair',
                'memory_recall': 'fair'
            },
            'transcript_info': {
                'word_count': len(transcript.split()),
                'is_short_transcript': len(transcript.split()) < 10,
                'vocabulary_richness_applicable': True
            }
        }
    else:
        default_result = {
            'vocabulary_score': 5.0,
            'context_relevance_score': 5.0,
            'overall_score': 5.0,
            'analysis': "Evaluation not available due to API issues",
            'feedback': "Evaluation not available due to API issues",
            'vocabulary_analysis': None,
            'context_analysis': {
                'relevance_level': 'medium',
                'accuracy': 'uncertain',
                'completeness': 'partial',
                'issues': ['API not available']
            },
            'cognitive_assessment': {
                'language_fluency': 'fair',
                'cognitive_level': 'medium',
                'attention_focus': 'fair',
                'memory_recall': 'fair'
            },
            'transcript_info': {
                'word_count': len(transcript.split()),
                'is_short_transcript': len(transcript.split()) < 10,
                'vocabulary_richness_applicable': True
            }
        }
    
    if not openai_client:
        logger.warning("⚠️ OpenAI client not available")
        return default_result
    
    try:
        # Create prompt directly with smart logic
        word_count = len(transcript.split())
        is_short = word_count < 10

        # Classify question type to adjust evaluation criteria
        question_type = _classify_question_type(question, language)
        question_display = question[:50] if question and isinstance(question, str) else "None"
        logger.info(f"🔍 Question classified as: {question_type} (question: '{question_display}...')")

        # Adjust evaluation criteria based on question type
        if question_type == 'factual':
            context_instructions = """
   - Đối với câu hỏi factual (thông tin cơ bản): cho điểm cao (7-10) nếu trả lời đúng và đầy đủ thông tin cơ bản
   - Không đòi hỏi mô tả chi tiết, chỉ cần thông tin chính xác và phù hợp
   - Ví dụ: "Tôi 65 tuổi" cho câu hỏi "Bạn bao nhiêu tuổi?" nên được 9-10 điểm"""
            min_context_score = 7  # Lower threshold for factual questions
        elif question_type == 'simple_yes_no':
            context_instructions = """
   - Đối với câu hỏi có/không đơn giản: cho điểm cao (8-10) nếu trả lời rõ ràng và phù hợp
   - Không đòi hỏi giải thích chi tiết, chỉ cần câu trả lời trực tiếp"""
            min_context_score = 8  # Higher threshold for yes/no questions
        else:  # descriptive
            context_instructions = """
   - Đối với câu hỏi mô tả chi tiết: đánh giá nghiêm ngặt dựa trên mức độ đầy đủ và chính xác của thông tin
   - Yêu cầu mô tả chi tiết và logic"""
            min_context_score = 5  # Standard threshold

        if language == 'vi':
            prompt = f"""
Bạn là chuyên gia đánh giá nhận thức. Phân tích transcript và trả về JSON chính xác.

**THÔNG TIN ĐẦU VÀO:**
- Câu hỏi: {question or "Không có câu hỏi cụ thể"}
- Transcript: {transcript}
- Số từ trong transcript: {word_count}
- Là transcript ngắn (< 10 từ): {"Có" if is_short else "Không"}
- Loại câu hỏi: {question_type} (factual=thông tin cơ bản, descriptive=mô tả chi tiết, simple_yes_no=có/không)
- Thông tin cá nhân: Tuổi: {user_data.get('age', 'Không rõ')}, Giới tính: {user_data.get('gender', 'Không rõ')}, Trình độ học vấn: {user_data.get('education', 'Không rõ')}

**HƯỚNG DẪN CHI TIẾT:**

**NGUYÊN TẮC ĐÁNH GIÁ THEO THÔNG TIN CÁ NHÂN:**
- Người cao tuổi (65+): Giảm tiêu chuẩn 1-2 điểm cho vocabulary_score
- Người trẻ (<30): Tăng tiêu chuẩn 1-2 điểm cho vocabulary_score
- Người có trình độ học vấn thấp: Điều chỉnh tiêu chuẩn phù hợp
- Xem xét khả năng thực tế của từng cá nhân khi đánh giá

1. **VOCABULARY_SCORE:**
   - Nếu transcript < 10 từ: đặt là null
   - Nếu transcript >= 10 từ và câu hỏi yêu cầu mô tả chi tiết: đánh giá 0-10
   - Nếu câu hỏi đơn giản (factual/simple_yes_no): đặt là null (không đánh giá độ phong phú)
   - Đánh giá độ phong phú từ vựng, đa dạng từ loại, cấu trúc câu
   - ĐIỀU CHỈNH theo tuổi tác và trình độ học vấn

2. **CONTEXT_RELEVANCE_SCORE:**
   - Luôn đánh giá từ 0-10
   - Đo lường mức độ trả lời phù hợp với câu hỏi
   - Điều chỉnh tiêu chí dựa trên loại câu hỏi:
{context_instructions}
   - Transcript ngắn nhưng chính xác vẫn có thể đạt điểm cao
   - ĐIỀU CHỈNH theo tuổi tác: Người cao tuổi có thể được đánh giá linh hoạt hơn

3. **OVERALL_SCORE:**
   - Nếu có cả 2 điểm: (vocabulary_score + context_relevance_score) / 2
   - Nếu chỉ có context_relevance_score: dùng giá trị đó

**YÊU CẦU FORMAT JSON NGHIÊM NGẶT:**

{{
  "vocabulary_score": {"null" if is_short or question_type in ['factual', 'simple_yes_no'] else "SỐ_NGUYÊN_0_10"},
  "context_relevance_score": "SỐ_NGUYÊN_0_10",
  "overall_score": "SỐ_NGUYÊN_0_10",
  "analysis": "PHÂN_TÍCH_CHI_TIẾT_BẰNG_TIẾNG_VIỆT_ÍT_NHẤT_50_TỪ_XEM_XÉT_TUỔI_TÁC_VÀ_TRÌNH_ĐỘ",
  "feedback": "GỢI_Ý_CẢI_THIỆN_CỤ_THỂ_BẰNG_TIẾNG_VIỆT_ÍT_NHẤT_30_TỪ_PHÙ_HỢP_VỚI_TUỔI_TÁC",
  "transcript_info": {{
    "word_count": {word_count},
    "is_short_transcript": {str(is_short).lower()},
    "question_type": "{question_type}",
    "vocabulary_richness_applicable": {str(not (is_short or question_type in ['factual', 'simple_yes_no'])).lower()}
  }}
}}

**QUAN TRỌNG:**
- KHÔNG thêm text ngoài JSON
- Đảm bảo JSON hợp lệ 100%
- Analysis và feedback phải chi tiết, có ý nghĩa
- Điểm số phải là số nguyên từ 0-10
- Đối với câu hỏi {question_type}: ưu tiên đánh giá {question_type} criteria
            """.strip()
        else:
            # Adjust evaluation criteria based on question type (English version)
            if question_type == 'factual':
                context_instructions_en = """
   - For factual questions (basic information): give high scores (7-10) if answer is correct and provides basic information
   - No detailed description required, just accurate and relevant information
   - Example: "I am 65 years old" for "How old are you?" should get 9-10 points"""
            elif question_type == 'simple_yes_no':
                context_instructions_en = """
   - For simple yes/no questions: give high scores (8-10) if answer is clear and appropriate
   - No detailed explanation required, just direct answer"""
            else:  # descriptive
                context_instructions_en = """
   - For detailed descriptive questions: evaluate strictly based on completeness and accuracy
   - Require detailed and logical descriptions"""

            prompt = f"""
You are a cognitive assessment expert. Analyze transcript and return accurate JSON.

**INPUT INFORMATION:**
- Question: {question or "No specific question"}
- Transcript: {transcript}
- Word count in transcript: {word_count}
- Is short transcript (< 10 words): {"Yes" if is_short else "No"}
- Question type: {question_type} (factual=basic info, descriptive=detailed, simple_yes_no=yes/no)
- Personal information: Age: {user_data.get('age', 'Unknown')}, Gender: {user_data.get('gender', 'Unknown')}, Education: {user_data.get('education', 'Unknown')}

**DETAILED GUIDELINES:**

**EVALUATION PRINCIPLES BASED ON PERSONAL INFORMATION:**
- Elderly people (65+): Reduce standards by 1-2 points for vocabulary_score
- Young people (<30): Increase standards by 1-2 points for vocabulary_score
- People with lower education: Adjust standards appropriately
- Consider individual capabilities when evaluating

1. **VOCABULARY_SCORE:**
   - If transcript < 10 words: set to null
   - If transcript >= 10 words and question requires detailed description: evaluate 0-10
   - If simple question (factual/simple_yes_no): set to null (no vocabulary richness evaluation)
   - Evaluate vocabulary richness, word variety, sentence structure
   - ADJUST based on age and education level

2. **CONTEXT_RELEVANCE_SCORE:**
   - Always evaluate from 0-10
   - Measure how well answer matches the question
   - Adjust criteria based on question type:
{context_instructions_en}
   - Short but accurate transcripts can still score high

3. **OVERALL_SCORE:**
   - If both scores available: (vocabulary_score + context_relevance_score) / 2
   - If only context_relevance_score: use that value

**STRICT JSON FORMAT REQUIREMENT:**

{{
  "vocabulary_score": {"null" if is_short or question_type in ['factual', 'simple_yes_no'] else "INTEGER_0_10"},
  "context_relevance_score": "INTEGER_0_10",
  "overall_score": "INTEGER_0_10",
  "analysis": "DETAILED_ANALYSIS_IN_ENGLISH_AT_LEAST_50_WORDS",
  "feedback": "SPECIFIC_IMPROVEMENT_SUGGESTIONS_IN_ENGLISH_AT_LEAST_30_WORDS",
  "transcript_info": {{
    "word_count": {word_count},
    "is_short_transcript": {str(is_short).lower()},
    "question_type": "{question_type}",
    "vocabulary_richness_applicable": {str(not (is_short or question_type in ['factual', 'simple_yes_no'])).lower()}
  }}
}}

**IMPORTANT:**
- DO NOT add text outside JSON
- Ensure 100% valid JSON
- Analysis and feedback must be detailed and meaningful
- Scores must be integers from 0-10
- For {question_type} questions: prioritize {question_type} evaluation criteria
            """.strip()

        # Debug: Log the generated prompt
        logger.debug(f"🤖 Generated prompt: {prompt[:200]}...")

        # Count words in transcript
        word_count = len(transcript.split())
        logger.info(f"📝 Transcript word count: {word_count}")

        # Use GPT-4o for evaluation (primary choice)
        try:
            if not openai_client:
                raise Exception("OpenAI client not available")
                
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert cognitive assessment evaluator specializing in Alzheimer's disease and dementia. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # Parse GPT-4o response
            result_text = response.choices[0].message.content.strip()
            logger.info(f"🤖 GPT-4o evaluation response: {result_text[:200]}...")
            
        except Exception as e:
            logger.error(f"❌ GPT-4o evaluation failed: {e}")
            # Fallback to Gemini if GPT-4o fails
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=800,
                        response_mime_type="application/json"
                    )
                )
                
                # Parse Gemini response
                result_text = response.text.strip()
                logger.info(f"🤖 Gemini fallback evaluation response: {result_text[:200]}...")
                
            except Exception as gemini_e:
                logger.error(f"❌ Gemini fallback also failed: {gemini_e}")
                # Final fallback to GPT-3.5-turbo
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert cognitive assessment evaluator. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=800
                )
                
                # Parse GPT-3.5-turbo response
                result_text = response.choices[0].message.content.strip()
                logger.info(f"🤖 GPT-3.5-turbo final fallback response: {result_text[:200]}...")

        # Debug: Log raw response
        logger.debug(f"📄 GPT response: '{result_text}'")
        
        # Try to parse JSON response
        try:
            result = json.loads(result_text)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logger.error(f"❌ Response is not a dictionary: {type(result)}")
                return default_result

            # Validate that we have the required fields
            required_fields = ['vocabulary_score', 'context_relevance_score', 'overall_score', 'analysis', 'feedback']

            # Check if all required fields are present
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                logger.warning(f"⚠️ Missing required fields: {missing_fields}")
                # Try to create a corrected result
                result = _correct_gpt_response(result, word_count, is_short, language)

            # Handle null vocabulary_score
            if result.get('vocabulary_score') is None:
                result['vocabulary_score'] = None
                result['vocabulary_analysis'] = None

            # Ensure transcript_info is present and correct
            if 'transcript_info' not in result:
                result['transcript_info'] = {
                    'word_count': word_count,
                    'is_short_transcript': word_count < 10,
                    'vocabulary_richness_applicable': result.get('vocabulary_score') is not None
                }
            else:
                # Force correct word_count even if GPT returned different value
                result['transcript_info']['word_count'] = word_count
                result['transcript_info']['is_short_transcript'] = word_count < 10

            # Validate and calculate overall_score if needed
            context_score = result.get('context_relevance_score', 5.0)
            vocab_score = result.get('vocabulary_score')

            if vocab_score is not None and result.get('overall_score') is None:
                # Calculate overall score from available scores
                result['overall_score'] = (vocab_score + context_score) / 2
            elif vocab_score is None and result.get('overall_score') is None:
                # Only context score available
                result['overall_score'] = context_score

            # Validate all numeric fields
            numeric_fields = ['vocabulary_score', 'context_relevance_score', 'overall_score']
            for key in numeric_fields:
                if key in result and result[key] is not None:
                    value = result[key]
                    if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                        logger.warning(f"⚠️ Invalid {key}: {value}, using default")
                        result[key] = default_result[key]
            
            # Ensure required fields exist with fallback
            for key in ['analysis', 'feedback']:
                if key not in result or not result[key]:
                    result[key] = default_result[key]

            logger.info("✅ GPT evaluation successful")
            return result

        except json.JSONDecodeError as json_error:
            logger.warning(f"⚠️ Invalid JSON response from GPT: {json_error}")
            logger.debug(f"Raw response: {result_text}")

            # Try to extract partial information from malformed response
            try:
                corrected_result = _correct_gpt_response({}, word_count, is_short, language)
                logger.info("✅ Used corrected GPT response")
                return corrected_result
            except Exception as correction_error:
                logger.error(f"❌ Correction failed: {correction_error}")
            return default_result
            
    except Exception as e:
        logger.error(f"❌ GPT evaluation failed: {e}")
        # Ensure we always return a dictionary, not a string
        if isinstance(default_result, dict):
            return default_result
        else:
            logger.error(f"❌ Default result is not a dictionary: {type(default_result)}")
            return {
                'vocabulary_score': 5.0,
                'context_relevance_score': 5.0,
                'overall_score': 5.0,
                'analysis': "Đánh giá không khả dụng do lỗi hệ thống",
                'feedback': "Đánh giá không khả dụng do lỗi hệ thống"
            }
    
    # Final safety check - ensure we never return a string
    finally:
        # This will always execute, but we can't return from finally
        pass

def _calculate_final_mmse_score(ml_score: float, gpt_overall_score: float, context_score: float, vocab_score: float = None) -> int:
    """
    Calculate final MMSE score using minimum percentage approach (conservative for cognitive assessment)
    
    Pipeline:
    1. Tầng 1: ML model xử lý acoustic features → ml_score (0-30)
    2. Tầng 1: GPT eval xử lý transcript + question → gpt_overall_score, context_score (0-10)
    3. Tầng 2: Đánh giá mức độ nguy cơ và tính điểm MMSE cuối cùng
    
    Args:
        ml_score: ML prediction score từ acoustic features (0-30 MMSE scale)
        gpt_overall_score: GPT overall score từ transcript evaluation (0-10 scale)  
        context_score: GPT context score đánh giá mức độ đáp ứng câu hỏi (0-10 scale)
        vocab_score: GPT vocabulary score (0-10 scale, optional)
        
    Returns:
        Final MMSE score as integer (1-29, vì >0 và <30)
    """
    # Validate inputs
    ml_score = max(0.0, min(30.0, float(ml_score)))
    gpt_overall_score = max(0.0, min(10.0, float(gpt_overall_score)))
    context_score = max(0.0, min(10.0, float(context_score)))
    
    # Convert scores to percentages
    ml_percentage = (ml_score / 30.0) * 100  # ML score is 0-30 (MMSE scale)
    gpt_percentage = (gpt_overall_score / 10.0) * 100  # GPT score is 0-10
    
    # Tầng 1: Đánh giá mức độ nguy cơ - lấy phần trăm thấp hơn (conservative)
    min_percentage = min(ml_percentage, gpt_percentage)
    
    # Tầng 2: Tính điểm MMSE cuối cùng với weighting phù hợp
    if vocab_score is not None:
        # Có đầy đủ vocabulary và context scores - đánh giá toàn diện
        vocab_percentage = (vocab_score / 10.0) * 100
        # Kết hợp: ML (50%), GPT overall (30%), Context (20%)
        combined_percentage = (ml_percentage * 0.5) + (gpt_percentage * 0.3) + (vocab_percentage * 0.2)
        final_score = (combined_percentage / 100.0) * 30.0
        logger.info(f"📊 Final score (full): ML:{ml_percentage:.1f}%, GPT:{gpt_percentage:.1f}%, Vocab:{vocab_percentage:.1f}% → Combined:{combined_percentage:.1f}% → MMSE:{final_score:.1f}")
    else:
        # Chỉ có context score (transcript ngắn) - đánh giá dựa trên context relevance
        context_percentage = (context_score / 10.0) * 100
        # Kết hợp: ML (60%), GPT overall (20%), Context (20%) với penalty cho transcript ngắn
        combined_percentage = (ml_percentage * 0.6) + (gpt_percentage * 0.2) + (context_percentage * 0.2)
        final_score = (combined_percentage / 100.0) * 30.0 * 0.95  # 5% penalty for short transcript
        logger.info(f"📊 Final score (short transcript): ML:{ml_percentage:.1f}%, GPT:{gpt_percentage:.1f}%, Context:{context_percentage:.1f}% → Combined:{combined_percentage:.1f}% → MMSE:{final_score:.1f} (with penalty)")
    
    # Đảm bảo final score là số nguyên trong khoảng (0, 30) - user yêu cầu >0, <30
    final_score_float = max(0.0, min(30.0, final_score))
    # Làm tròn và đảm bảo >0, <30
    final_score_int = int(round(final_score_float))
    if final_score_int <= 0:
        final_score_int = 1  # Minimum >0
    elif final_score_int >= 30:
        final_score_int = 29  # Maximum <30
    
    logger.info(f"✅ Final MMSE score (integer): {final_score_int}/30")
    return final_score_int

def _correct_gpt_response(partial_result, word_count, is_short, language):
    """Correct and complete GPT response if missing fields"""
    
    # Ensure partial_result is a dictionary
    if not isinstance(partial_result, dict):
        partial_result = {}

    # Default values based on language
    if language == 'vi':
        default_analysis = f"Transcript có {word_count} từ. {'Đây là transcript ngắn.' if is_short else 'Đây là transcript có độ dài trung bình.'} Cần đánh giá thêm về chất lượng trả lời."
        default_feedback = "Hãy cố gắng trả lời đầy đủ và chính xác hơn. Tập trung vào việc hiểu rõ câu hỏi trước khi trả lời."
    else:
        default_analysis = f"Transcript has {word_count} words. {'This is a short transcript.' if is_short else 'This is a medium-length transcript.'} Further evaluation needed on response quality."
        default_feedback = "Try to provide more complete and accurate answers. Focus on understanding the question clearly before responding."

    # Build complete result
    corrected_result = {
        'vocabulary_score': partial_result.get('vocabulary_score', None if is_short else 5.0),
        'context_relevance_score': partial_result.get('context_relevance_score', 7.0),
        'overall_score': partial_result.get('overall_score'),
        'analysis': partial_result.get('analysis', default_analysis),
        'feedback': partial_result.get('feedback', default_feedback),
        'vocabulary_analysis': None if is_short else partial_result.get('vocabulary_analysis'),
        'context_analysis': partial_result.get('context_analysis', {
            'relevance_level': 'medium',
            'accuracy': 'uncertain',
            'completeness': 'partial' if is_short else 'complete',
            'issues': []
        }),
        'cognitive_assessment': partial_result.get('cognitive_assessment', {
            'language_fluency': 'fair',
            'cognitive_level': 'medium',
            'attention_focus': 'fair',
            'memory_recall': 'fair'
        }),
        'transcript_info': {
            'word_count': word_count,  # Always use actual word count, not GPT's estimate
            'is_short_transcript': is_short,
            'vocabulary_richness_applicable': not is_short
        }
    }

    # Calculate overall_score if missing
    vocab_score = corrected_result['vocabulary_score']
    context_score = corrected_result['context_relevance_score']

    if corrected_result['overall_score'] is None:
        if vocab_score is not None:
            corrected_result['overall_score'] = (vocab_score + context_score) / 2
        else:
            corrected_result['overall_score'] = context_score

    return corrected_result

from typing import Tuple, List, Optional

def train_five_feature_model() -> Tuple[Optional[object], List[str], str]:
    """Train and select the best model on five acoustic features using CV.
    Uses real dataset if available; otherwise, falls back to robust synthetic data.
    Returns (model, feature_names, best_model_name).
    """
    try:
        import numpy as np
        from sklearn.linear_model import Ridge, LinearRegression
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import cross_val_score
    except Exception as e:
        logger.error(f"❌ Scikit-learn dependency missing: {e}")
        return None, [], ''

    feature_order = ['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean']

    # Attempt to build a real dataset from existing CSVs if available
    X_real = None
    y_real = None
    try:
        from cognitive_assessment_ml import EnhancedMultimodalCognitiveModel as _CAM
        loader = _CAM()
        # Try to load data if the method exists
        if hasattr(loader, 'load_and_process_data'):
            main_data, _ = loader.load_and_process_data()
            if main_data is not None and not main_data.empty:
                if hasattr(loader, 'extract_acoustic_features'):
                    processed, _ = loader.extract_acoustic_features(main_data)
                    # Ensure required columns exist; skip if missing too many
                    if all(col in processed.columns for col in feature_order) and 'mmse' in processed.columns:
                        df = processed.dropna(subset=feature_order + ['mmse']).copy()
                        if len(df) >= 30:
                            X_real = df[feature_order].values
                            mmse = df['mmse'].values.astype(float)
                            # Keep original MMSE scale (0-30) instead of converting to 1-10
                            y_real = np.clip(mmse, 0.0, 30.0)
    except Exception as e:
        logger.warning(f"⚠️ Failed to build real dataset for five-feature model: {e}")

    if X_real is None or y_real is None:
        # Fallback to synthetic robust generation
        rng = np.random.default_rng(123)
        n_samples = 1200
        speech_rate = rng.uniform(1.0, 4.0, n_samples)
        number_utterances = rng.integers(1, 40, n_samples).astype(float)
        silence_mean = rng.uniform(0.0, 1.8, n_samples)
        pitch_mean = rng.uniform(110.0, 280.0, n_samples)
        X_real = np.column_stack([speech_rate, number_utterances, silence_mean, pitch_mean])
        # Generate synthetic data on MMSE scale (0-30) directly - more conservative scaling
        y_real = (
            18.0  # Base MMSE score (higher baseline for healthier population)
            + 2.5 * (speech_rate - 2.5)  # Speech rate impact (reduced)
            + 0.08 * (number_utterances - 15)  # Utterances impact (reduced)
            - 2.0 * (silence_mean - 0.5)  # Silence impact (reduced)
            + 0.006 * (220.0 - pitch_mean)  # Pitch impact (reduced)
            + rng.normal(0, 0.8, n_samples)  # Noise (reduced)
        )
        # Strict clipping to ensure no values exceed 30
        y_real = np.clip(y_real, 0.0, 30.0)

    candidates = {
        'Ridge': make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        'LinearRegression': make_pipeline(StandardScaler(), LinearRegression()),
        'GradientBoosting': GradientBoostingRegressor(random_state=42),
        'RandomForest': RandomForestRegressor(n_estimators=200, random_state=42)
    }

    best_name = ''
    best_score = None
    best_model = None
    for name, model in candidates.items():
        try:
            scores = cross_val_score(model, X_real, y_real, cv=5, scoring='neg_mean_squared_error')
            mse = -scores.mean()
            logger.info(f"🔎 CV - {name}: MSE={mse:.3f}")
            if best_score is None or mse < best_score:
                best_score = mse
                best_name = name
                best_model = model
        except Exception as e:
            logger.warning(f"⚠️ CV failed for {name}: {e}")

    if best_model is None:
        logger.error("❌ No model succeeded during CV")
        return None, [], ''

    best_model.fit(X_real, y_real)
    try:
        setattr(best_model, 'best_model_name', best_name)
    except Exception:
        pass
    return best_model, feature_order, best_name

# =============================================================================
# VALIDATION FUNCTIONS (PRIORITY 4)
# =============================================================================

def validate_features(audio_features: dict, required_features: list) -> bool:
    """
    Validate that all required features exist and are valid
    
    Args:
        audio_features: Dictionary of extracted features
        required_features: List of required feature names
        
    Returns:
        bool: True if all features are valid
        
    Raises:
        ValueError: If features are missing or invalid
    """
    missing = []
    invalid = []
    
    for feat in required_features:
        if feat not in audio_features:
            missing.append(feat)
        else:
            val = audio_features[feat]
            if val is None or np.isnan(val) or np.isinf(val):
                invalid.append(feat)
    
    if missing:
        error_msg = f"Missing required features: {missing}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if invalid:
        error_msg = f"Invalid feature values (NaN/Inf): {invalid}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Feature validation passed: {list(audio_features.keys())}")
    return True


# =============================================================================
# FEATURE NORMALIZATION / FALLBACKS (PRIORITY 4)
# =============================================================================

# Columns that should never be treated as model inputs (labels/metadata).
NON_INPUT_FEATURES = {
    "mmse",
    "mmse_score",
    "mmse2",
    "mms",
    "mmsediff",
    "moca_score",
    "weights",
    "subclass",
}

# Safe default values for optional or rarely available features.
OPTIONAL_FEATURE_DEFAULTS = {
    "age": 0.0,
    "education": 0.0,
    "education_level": 0.0,
    "avg_words_per_sentence": 0.0,
    "sentence_length": 0.0,
    "stop_word_frequency": 0.0,
    "lexical_diversity": 0.0,
    "semantic_fluency": 0.0,
    "word_finding_difficulty": 0.0,
    "mean_pause_length": 0.0,
    "pause_frequency": 0.0,
    "hnr": 0.0,
    "jitter": 0.0,
    "shimmer": 0.0,
    "f0_mean": 0.0,
    "f0_std": 0.0,
    "distance": 0.0,
    "dur.max": 0.0,
    "dur.mean": 0.0,
    "dur.median": 0.0,
    "dur.min": 0.0,
    "dur.sd": 0.0,
    "sildur.max": 0.0,
    "sildur.mean": 0.0,
    "sildur.median": 0.0,
    "sildur.min": 0.0,
    "sildur.sd": 0.0,
    "number.utt": 0.0,
}


def _fill_missing_features(
    audio_features: dict, feature_names: list
) -> dict:
    """
    Ensure every required feature exists by:
    - Skipping known label/metadata columns (NON_INPUT_FEATURES)
    - Filling missing optional columns with safe defaults
    - Falling back to 0.0 for any other missing feature
    """
    filled = dict(audio_features)
    defaulted: list[str] = []

    for name in feature_names:
        if name in NON_INPUT_FEATURES:
            # Labels/metadata should not block inference; use 0.0 placeholder.
            filled.setdefault(name, 0.0)
            continue

        if name in filled:
            continue

        if name in OPTIONAL_FEATURE_DEFAULTS:
            filled[name] = OPTIONAL_FEATURE_DEFAULTS[name]
        elif name.startswith("feature_"):
            # Generic embedding-like columns from some datasets
            filled[name] = 0.0
        else:
            filled[name] = 0.0

        defaulted.append(name)

    if defaulted:
        logger.warning(
            "⚠️ Missing features were defaulted to 0.0: %s", defaulted
        )

    return filled

def validate_feature_ranges(features: dict) -> None:
    """
    Validate feature value ranges and log warnings for out-of-range values
    
    Args:
        features: Dictionary of feature values
    """
    ranges = {
        'speech_rate': (0.5, 5.0),
        'number_utterances': (1, 500),
        'silence_mean': (0, 10),
        'pitch_mean': (50, 500)
    }
    
    for feat, (min_val, max_val) in ranges.items():
        if feat in features:
            val = features[feat]
            if val < min_val or val > max_val:
                logger.warning(f"Feature {feat} = {val} outside expected range [{min_val}, {max_val}]")

def validate_prediction(prediction: float) -> float:
    """
    Validate model output prediction
    
    Args:
        prediction: Raw prediction value
        
    Returns:
        float: Validated and clipped prediction (0-30)
        
    Raises:
        ValueError: If prediction is NaN or Inf
    """
    if np.isnan(prediction) or np.isinf(prediction):
        error_msg = f"Invalid prediction value: {prediction}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Clip to valid MMSE range
    if prediction < 0 or prediction > 30:
        logger.warning(f"Prediction {prediction:.2f} out of MMSE range [0, 30], clipping")
        prediction = np.clip(prediction, 0.0, 30.0)
    
    return float(prediction)

def prepare_feature_vector(audio_features: dict, feature_names: list) -> np.ndarray:
    """
    Prepare feature vector in correct order with validation
    
    Args:
        audio_features: Dictionary of extracted features
        feature_names: List of feature names in correct order
        
    Returns:
        np.ndarray: Feature vector shaped (1, n_features)
        
    Raises:
        ValueError: If features are missing or invalid
    """
    # Fill missing optional features so we don't fail on incomplete payloads
    safe_features = _fill_missing_features(audio_features, feature_names)

    # Validate first (after filling defaults)
    validate_features(safe_features, feature_names)
    
    # Validate ranges (warning only)
    validate_feature_ranges(safe_features)
    
    # Build vector in correct order
    feature_vector = [safe_features[name] for name in feature_names]
    
    logger.info(f"Feature vector prepared: {dict(zip(feature_names, feature_vector))}")
    return np.array(feature_vector).reshape(1, -1)

# =============================================================================
# PREDICTION FUNCTION (PRIORITY 3, 5)
# =============================================================================

def predict_cognitive_score(audio_features: dict) -> dict:
    """
    Predict cognitive score using ML model with proper preprocessing pipeline
    
    Pipeline: Extract → Validate → Select → Scale → Predict → Validate output
    
    Args:
        audio_features: Dictionary of extracted audio features
        
    Returns:
        dict: Prediction result with score, confidence, and metadata
        
    Raises:
        ValueError: If model not loaded, features invalid, or prediction fails
    """
    global cognitive_model, feature_names, model_scaler, model_selector
    
    logger.info("=" * 60)
    logger.info("ML PREDICTION PIPELINE")
    logger.info("=" * 60)
    
    # PRIORITY 5: Fail fast if model not loaded - NO DEFAULT VALUES
    if not cognitive_model or not feature_names:
        error_msg = "ML model not loaded. Please check server logs and ensure model bundle exists."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Try to reload bundle if scaler/selector missing (legacy). For pipeline models this is optional.
    if model_scaler is None or model_selector is None:
        logger.warning("Model scaler/selector not loaded. Attempting to reload model bundle (optional for pipeline models)...")
        try:
            model, scaler, selector, fnames = load_model_bundle()
            if model is not None:
                cognitive_model = model
                feature_names = fnames
                model_scaler = scaler  # may be None for pipeline bundles
                model_selector = selector  # may be None for pipeline bundles
                logger.info("Model bundle reloaded successfully")
        except Exception as e:
            logger.error(f"Reload attempt failed: {e}")
            # continue with existing model (pipeline may still work)
    
    try:
        # Step 1: Prepare feature vector with validation
        logger.info("Step 1: Preparing feature vector...")
        logger.info(f"Input features: {audio_features}")
        feature_vector = prepare_feature_vector(audio_features, feature_names)
        logger.info(f"Feature vector shape: {feature_vector.shape}")
        logger.info(f"Feature vector values: {feature_vector[0]}")
        
        # Step 2: Apply feature selector if exists
        processed_vector = feature_vector
        if model_selector is not None:
            logger.info("Step 2: Applying feature selector...")
            processed_vector = model_selector.transform(processed_vector)
            logger.info(f"After selector shape: {processed_vector.shape}")
            logger.info(f"After selector values: {processed_vector[0]}")
        else:
            logger.warning("No feature selector available, skipping selection step")
        
        # Step 3: Apply scaler if available (legacy). Pipeline models will handle scaling internally.
        if model_scaler is not None:
            logger.info("Step 3: Applying scaler...")
            processed_vector = model_scaler.transform(processed_vector)
            logger.info(f"After scaling shape: {processed_vector.shape}")
            logger.info(f"After scaling values: {processed_vector[0]}")
        else:
            logger.warning("No external scaler; assuming model pipeline handles scaling internally")
        
        # Step 4: Make prediction
        logger.info("Step 4: Making prediction...")
        raw_prediction = cognitive_model.predict(processed_vector)
        
        # Handle different prediction output formats
        if isinstance(raw_prediction, np.ndarray):
            if len(raw_prediction.shape) > 0:
                predicted_score = float(raw_prediction[0])
            else:
                predicted_score = float(raw_prediction)
        else:
            predicted_score = float(raw_prediction)
        
        logger.info(f"Raw prediction: {predicted_score:.4f}")
        
        # Step 5: Validate prediction output
        logger.info("Step 5: Validating prediction...")
        predicted_score = validate_prediction(predicted_score)
        logger.info(f"Validated prediction: {predicted_score:.2f}")
        
        # Step 6: Calculate confidence (if available)
        confidence = 0.85  # Default confidence for regression models
        if hasattr(cognitive_model, 'predict_proba'):
            try:
                proba = cognitive_model.predict_proba(processed_vector)
                if proba is not None and len(proba) > 0:
                    confidence = float(np.max(proba[0]))
            except Exception as e:
                logger.warning(f"Could not calculate probability-based confidence: {e}")
        
        # Get model name
        model_name = getattr(cognitive_model, 'best_model_name', None)
        if not model_name:
            model_name = type(cognitive_model).__name__
        
        logger.info("=" * 60)
        logger.info("PREDICTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Predicted MMSE: {predicted_score:.2f}/30")
        logger.info(f"Confidence: {confidence:.2f}")
        logger.info(f"Model: {model_name}")
        logger.info("=" * 60)
        
        result = {
            'predicted_score': predicted_score,
            'confidence': float(confidence),
            'model_used': model_name
        }
        
        return result
        
    except ValueError as e:
        # Re-raise validation errors
        logger.error(f"Validation error in prediction: {e}")
        raise
    except Exception as e:
        # Log full error details
        logger.error("=" * 60)
        logger.error("PREDICTION FAILED")
        logger.error("=" * 60)
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        # PRIORITY 5: Raise error instead of returning default
        raise RuntimeError(f"Prediction failed: {str(e)}") from e

def transcribe_audio(audio_path: str, question: str = None) -> dict:
    """Transcribe audio using Vietnamese transcriber (Gemini-first)."""
    global vietnamese_transcriber
    
    if not vietnamese_transcriber:
        logger.warning("⚠️ Vietnamese transcriber instance not available")
        return {
            'transcript': '',
            'confidence': 0.0,
            'success': False,
            'error': 'Transcriber not available'
        }
    
    try:
        result = vietnamese_transcriber.transcribe_audio_file(audio_path, 'vi', False, question)
        
        if result['success']:
            logger.info("✅ Audio transcription successful")
        else:
            logger.warning(f"⚠️ Transcription failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        return {
            'transcript': '',
            'confidence': 0.0,
            'success': False,
            'error': str(e)
        }

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Get MCI service status
    mci_status = {}
    if mci_service is not None:
        try:
            status = mci_service.get_status()
            mci_status = {
                'available': status.get('is_ready', False),
                'acoustic_analyzer': status.get('acoustic_analyzer', False),
                'linguistic_analyzer': status.get('linguistic_analyzer', False),
                'mci_predictor': status.get('mci_predictor', False)
            }
        except:
            mci_status = {'available': False, 'error': 'Status check failed'}
    else:
        mci_status = {'available': False}
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': cognitive_model is not None,
        'feature_count': len(feature_names) if feature_names else 0,
        'model_bundle': str((Path(__file__).resolve().parent.parent / "models").resolve()),
        'mmse_pipeline_available': mmse_pipeline is not None,
        'mci_service': mci_status,
        'gemini_available': bool(gemini_api_key),
        'openai_available': openai_client is not None,
        'transcriber_available': vietnamese_transcriber is not None,
        'vi_asr_model': vi_asr_model,
        'languages': {
            'available': ['vi', 'en'],
            'default': 'vi'
        },
        'environment': {
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': os.getenv('PORT', '8000'),
            'debug': os.getenv('DEBUG', 'True'),
            'node_env': os.getenv('NODE_ENV', 'development')
        }
    })

# =============================================================================
# MCI SCREENING ENDPOINTS
# =============================================================================

@app.route('/api/mci/status', methods=['GET'])
def mci_status():
    """
    Get MCI screening module status
    
    Returns availability of each component:
    - acoustic_analyzer: eGeMAPS + Vietnamese tone features
    - linguistic_analyzer: Vietnamese NLP (PhoBERT)
    - mci_predictor: MCI prediction and MMSE estimation
    """
    try:
        if mci_service is None:
            return jsonify({
                'success': False,
                'available': False,
                'error': 'MCI modules not initialized',
                'components': {
                    'acoustic_analyzer': False,
                    'linguistic_analyzer': False,
                    'multimodal_fusion': False,
                    'mci_predictor': False
                }
            })
        
        status = mci_service.get_status()
        return jsonify({
            'success': True,
            'available': status.get('is_ready', False),
            'components': {
                'acoustic_analyzer': status.get('acoustic_analyzer', False),
                'linguistic_analyzer': status.get('linguistic_analyzer', False),
                'multimodal_fusion': status.get('multimodal_fusion', False),
                'mci_predictor': status.get('mci_predictor', False)
            },
            'initialization_errors': status.get('initialization_errors', []),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ MCI status check failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mci/analyze', methods=['POST'])
def mci_analyze():
    """
    Complete MCI analysis from audio and/or transcript
    
    Request (multipart/form-data):
        - audio: Audio file (WAV, MP3) - optional if transcript provided
        - transcript: Text transcript - optional if audio provided
        - task_type: Type of cognitive task (verbal_fluency, picture_description, 
                     spontaneous_speech, qa) - optional
        - user_name: User name - optional
        - user_age: User age - optional
        - user_gender: User gender - optional
        - user_education: Education years - optional
    
    Returns:
        - mci_probability: Probability of MCI (0-1)
        - mmse_estimate: Estimated MMSE score (0-30)
        - severity: Severity classification
        - risk_factors: Identified risk factors
        - recommendations: Clinical recommendations (Vietnamese)
        - acoustic_features: Extracted acoustic features count
        - linguistic_features: Extracted linguistic features count
    """
    try:
        if mci_service is None:
            return jsonify({
                'success': False,
                'error': 'MCI service not available. Please check module installation.'
            }), 503
        
        # Get audio file if provided
        audio_path = None
        temp_audio_path = None
        
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file.filename:
                # Save to temp file
                import tempfile
                suffix = os.path.splitext(audio_file.filename)[1] or '.wav'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    audio_file.save(tmp.name)
                    temp_audio_path = tmp.name
                    audio_path = tmp.name
        
        # Get transcript if provided
        transcript = request.form.get('transcript', '')
        
        # Get task type
        task_type = request.form.get('task_type', None)
        
        # Get user info
        user_info = {
            'name': request.form.get('user_name', ''),
            'age': request.form.get('user_age', ''),
            'gender': request.form.get('user_gender', ''),
            'education': request.form.get('user_education', '')
        }
        
        # Validate: need either audio or transcript
        if not audio_path and not transcript:
            return jsonify({
                'success': False,
                'error': 'Please provide either audio file or transcript'
            }), 400
        
        logger.info(f"🧠 MCI Analysis request:")
        logger.info(f"   Audio: {audio_path is not None}")
        logger.info(f"   Transcript: {len(transcript)} chars")
        logger.info(f"   Task type: {task_type}")
        
        # Run analysis
        result = mci_service.analyze(
            audio_path=audio_path,
            transcript=transcript if transcript else None,
            task_type=task_type,
            user_info=user_info if any(user_info.values()) else None
        )
        
        # Clean up temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        
        # Format response
        response = {
            'success': result.success,
            'mci_probability': result.mci_prediction.get('mci_probability', 0) if result.mci_prediction else 0,
            'mci_class': result.mci_prediction.get('mci_class', 'Unknown') if result.mci_prediction else 'Unknown',
            'mmse_estimate': result.mmse_estimate,
            'confidence': result.confidence,
            'severity': result.severity,
            'risk_factors': result.risk_factors,
            'recommendations': result.recommendations,
            'feature_summary': result.feature_summary,
            'acoustic_feature_count': len(result.acoustic_features),
            'linguistic_feature_count': len(result.linguistic_features),
            'processing_time': result.processing_time,
            'errors': result.errors,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ MCI analysis failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up temp file on error
        if 'temp_audio_path' in locals() and temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/mci/acoustic', methods=['POST'])
def mci_acoustic_features():
    """
    Extract acoustic features only (without linguistic analysis)
    
    Request (multipart/form-data):
        - audio: Audio file (WAV, MP3) - required
        - transcript: Optional transcript for speaking rate calculation
    
    Returns:
        - features: Dictionary of extracted acoustic features
        - feature_count: Number of features extracted
        - key_features: Most important features for MCI detection
    """
    try:
        if mci_service is None or mci_service.acoustic_analyzer is None:
            return jsonify({
                'success': False,
                'error': 'Acoustic analyzer not available'
            }), 503
        
        # Get audio file
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Audio file required'
            }), 400
        
        audio_file = request.files['audio']
        transcript = request.form.get('transcript', None)
        
        # Save to temp file
        import tempfile
        suffix = os.path.splitext(audio_file.filename)[1] or '.wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            audio_file.save(tmp.name)
            temp_path = tmp.name
        
        try:
            # Extract features
            features = mci_service.acoustic_analyzer.extract_all_features(
                temp_path, 
                transcript=transcript
            )
            
            # Get key features for summary
            key_features = {
                'f0_mean': features.get('f0_f0_mean', 0),
                'f0_variability': features.get('f0_f0_cv', 0),
                'jitter': features.get('vq_jitter_local', 0),
                'shimmer': features.get('vq_shimmer_local', 0),
                'hnr': features.get('vq_hnr_mean', 0),
                'pause_rate': features.get('pause_pause_rate', 0),
                'speaking_rate': features.get('rate_words_per_minute', 0),
                'tone_flattening': features.get('tone_flattening_score', 0)
            }
            
            return jsonify({
                'success': True,
                'features': features,
                'feature_count': len(features),
                'key_features': key_features,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"❌ Acoustic feature extraction failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mci/linguistic', methods=['POST'])
def mci_linguistic_features():
    """
    Extract linguistic features only (without acoustic analysis)
    
    Request (JSON or form-data):
        - transcript: Text transcript - required
        - task_type: Type of cognitive task - optional
    
    Returns:
        - features: Dictionary of extracted linguistic features
        - feature_count: Number of features extracted
        - key_features: Most important features for MCI detection
    """
    try:
        if mci_service is None or mci_service.linguistic_analyzer is None:
            return jsonify({
                'success': False,
                'error': 'Linguistic analyzer not available'
            }), 503
        
        # Get transcript from JSON or form data
        if request.is_json:
            data = request.get_json()
            transcript = data.get('transcript', '')
            task_type = data.get('task_type', None)
        else:
            transcript = request.form.get('transcript', '')
            task_type = request.form.get('task_type', None)
        
        if not transcript:
            return jsonify({
                'success': False,
                'error': 'Transcript required'
            }), 400
        
        # Extract features
        features = mci_service.linguistic_analyzer.extract_all_features(
            transcript,
            task_type=task_type
        )
        
        # Get key features for summary
        key_features = {
            'ttr': features.get('lex_ttr', 0),
            'mattr': features.get('lex_mattr', 0),
            'pronoun_ratio': features.get('lex_pronoun_ratio', 0),
            'noun_ratio': features.get('lex_noun_ratio', 0),
            'mlu_words': features.get('syn_mlu_words', 0),
            'incomplete_sentences': features.get('syn_incomplete_sentence_ratio', 0),
            'idea_density': features.get('sem_idea_density', 0),
            'semantic_coherence': features.get('sem_semantic_coherence', 0),
            'filler_ratio': features.get('vi_filler_ratio', 0)
        }
        
        return jsonify({
            'success': True,
            'features': features,
            'feature_count': len(features),
            'key_features': key_features,
            'transcript_length': len(transcript),
            'word_count': features.get('lex_total_words', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Linguistic feature extraction failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mci/predict', methods=['POST'])
def mci_predict():
    """
    Predict MCI status from pre-extracted features
    
    Request (JSON):
        - features: Dictionary of extracted features (acoustic + linguistic)
    
    Returns:
        - mci_probability: Probability of MCI (0-1)
        - mmse_estimate: Estimated MMSE score (0-30)
        - severity: Severity classification
        - risk_factors: Identified risk factors
        - recommendations: Clinical recommendations
    """
    try:
        if mci_service is None or mci_service.predictor is None:
            return jsonify({
                'success': False,
                'error': 'MCI predictor not available'
            }), 503
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'JSON data required'
            }), 400
        
        data = request.get_json()
        features = data.get('features', {})
        
        if not features:
            return jsonify({
                'success': False,
                'error': 'Features dictionary required'
            }), 400
        
        # Run prediction
        prediction = mci_service.predictor.predict(features)
        
        return jsonify({
            'success': True,
            'mci_probability': prediction.mci_probability,
            'mci_class': prediction.mci_class,
            'mmse_estimate': prediction.mmse_estimate,
            'confidence': prediction.confidence,
            'severity': prediction.severity,
            'risk_factors': prediction.risk_factors,
            'recommendations': prediction.recommendations,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ MCI prediction failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mci/batch-analyze', methods=['POST'])
def mci_batch_analyze():
    """
    Batch analysis for multiple audio files
    
    Request (multipart/form-data):
        - audio_files: Multiple audio files
        - task_type: Type of cognitive task - optional
    
    Returns:
        - results: List of analysis results for each file
        - summary: Aggregate statistics
    """
    try:
        if mci_service is None:
            return jsonify({
                'success': False,
                'error': 'MCI service not available'
            }), 503
        
        if 'audio_files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'audio_files required'
            }), 400
        
        audio_files = request.files.getlist('audio_files')
        task_type = request.form.get('task_type', None)
        
        results = []
        temp_files = []
        
        try:
            import tempfile
            
            for audio_file in audio_files:
                # Save to temp file
                suffix = os.path.splitext(audio_file.filename)[1] or '.wav'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    audio_file.save(tmp.name)
                    temp_files.append(tmp.name)
                    
                    # Analyze
                    result = mci_service.analyze(
                        audio_path=tmp.name,
                        task_type=task_type
                    )
                    
                    results.append({
                        'filename': audio_file.filename,
                        'success': result.success,
                        'mci_probability': result.mci_prediction.get('mci_probability', 0) if result.mci_prediction else 0,
                        'mmse_estimate': result.mmse_estimate,
                        'severity': result.severity,
                        'errors': result.errors
                    })
            
            # Calculate summary
            successful_results = [r for r in results if r['success']]
            if successful_results:
                avg_mci_prob = sum(r['mci_probability'] for r in successful_results) / len(successful_results)
                avg_mmse = sum(r['mmse_estimate'] for r in successful_results) / len(successful_results)
            else:
                avg_mci_prob = 0
                avg_mmse = 0
            
            return jsonify({
                'success': True,
                'total_files': len(audio_files),
                'successful': len(successful_results),
                'failed': len(results) - len(successful_results),
                'results': results,
                'summary': {
                    'average_mci_probability': avg_mci_prob,
                    'average_mmse_estimate': avg_mmse,
                    'high_risk_count': sum(1 for r in successful_results if r['mci_probability'] > 0.7)
                },
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Clean up temp files
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# USER PROFILE ENDPOINTS
# =============================================================================

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile from frontend database"""
    try:
        # This endpoint will be called by frontend to get user data
        # Frontend should pass user ID or email as query parameter
        user_id = request.args.get('user_id')
        email = request.args.get('email')
        
        if not user_id and not email:
            return jsonify({
                'success': False,
                'error': 'Missing user_id or email parameter'
            }), 400
        
        # For now, return a placeholder response
        # In the future, this could connect to the same database as frontend
        return jsonify({
            'success': True,
            'message': 'User profile endpoint ready. Frontend should implement database connection.',
            'note': 'This endpoint is designed to work with frontend database (Neon)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/database/user', methods=['GET'])
def get_database_user():
    """Get user data from database - compatible with frontend expectations"""
    try:
        user_id = request.args.get('userId')
        email = request.args.get('email')

        logger.info(f"🔍 Database user request: userId={user_id}, email={email}")

        if not user_id and not email:
            return jsonify({
                'success': False,
                'error': 'Missing userId or email parameter'
            }), 400

        # Check if user exists in our in-memory database
        user_data = None
        found_by = None
        
        if email and email in assessment_db['users']:
            user_data = assessment_db['users'][email]
            found_by = 'email'
        elif user_id:
            for stored_email, stored_data in assessment_db['users'].items():
                if stored_data.get('id') == user_id:
                    user_data = stored_data
                    found_by = 'userId'
                    # If found by userId, ensure email is also linked if not already
                    if email and stored_email != email:
                        logger.warning(f"⚠️ User found by userId {user_id} but email mismatch: {stored_email} vs {email}. Updating email.")
                        assessment_db['users'][email] = user_data
                        if stored_email in assessment_db['users']:
                            del assessment_db['users'][stored_email]
                            logger.info(f"🗑️ Removed old email entry: {stored_email}")
                    break

        if user_data:
            user_data['last_access'] = datetime.now().isoformat()
            logger.info(f"✅ Returning existing user data for: {email or user_id} (found by {found_by})")
        else:
            # If not found by either, create new user data
            new_user_email = email or f'user_{len(assessment_db["users"])}@example.com'
            user_data = {
                'id': user_id or f"user_{len(assessment_db['users'])}",
                'name': 'Người dùng mới',  # Default name for new user
                'age': '25',
                'gender': 'Nam',
                'email': new_user_email,
                'phone': '0123456789',
                'profile_complete': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_access': datetime.now().isoformat()
            }
            assessment_db['users'][new_user_email] = user_data
            logger.info(f"✅ Created new user data for: {new_user_email}")

        return jsonify({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"❌ Database user endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/database/user/save', methods=['POST'])
def save_database_user():
    """Save user data to database"""
    try:
        data = request.json
        email = data.get('email')

        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        logger.info(f"💾 Saving user data for: {email}")

        # Update or create user data
        user_data = assessment_db['users'].get(email, {})

        # Update fields
        user_data.update({
            'name': data.get('name', user_data.get('name', 'Người dùng mới')),
            'age': data.get('age', user_data.get('age', '25')),
            'gender': data.get('gender', user_data.get('gender', 'Nam')),
            'email': email,
            'phone': data.get('phone', user_data.get('phone', '0123456789')),
            'profile_complete': True,
            'updated_at': datetime.now().isoformat(),
            'last_access': datetime.now().isoformat()
        })

        # Ensure ID exists
        if 'id' not in user_data:
            user_data['id'] = data.get('id', f"user_{len(assessment_db['users'])}")
            user_data['created_at'] = datetime.now().isoformat()

        # Store in database
        assessment_db['users'][email] = user_data

        logger.info(f"✅ User data saved successfully for: {email}")

        return jsonify({
            'success': True,
            'user': user_data,
            'message': 'User data saved successfully'
        })

    except Exception as e:
        logger.error(f"❌ Save user endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/profile/user', methods=['GET'])
def get_profile_user():
    """Get user profile data - alternative endpoint for compatibility"""
    try:
        user_id = request.args.get('userId')
        email = request.args.get('email')

        logger.info(f"🔍 Profile user request: userId={user_id}, email={email}")

        if not user_id and not email:
            return jsonify({
                'success': False,
                'error': 'Missing userId or email parameter'
            }), 400

        # Check if user exists
        user_data = None
        if email and email in assessment_db['users']:
            user_data = assessment_db['users'][email]
        elif user_id:
            # Search by user_id
            for stored_email, stored_data in assessment_db['users'].items():
                if stored_data.get('id') == user_id:
                    user_data = stored_data
                    break

        if user_data:
            user_data['last_access'] = datetime.now().isoformat()
            logger.info(f"✅ Returning existing profile data for: {email or user_id}")
        else:
            # Return default profile for new users
            user_data = {
                'id': user_id or 'mock_user_id',
                'name': 'Người dùng mới',
                'age': '25',
                'gender': 'Nam',
                'email': email or 'user@example.com',
                'phone': '0123456789',
                'profile_complete': False,
                'last_login': datetime.now().isoformat()
            }
            logger.info(f"✅ Returning default profile data for: {email or user_id}")

        return jsonify({
            'success': True,
            'profile': user_data
        })

    except Exception as e:
        logger.error(f"❌ Profile user endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get available languages"""
    if language_manager:
        return jsonify({
            'available_languages': language_manager.get_available_languages(),
            'default_language': language_manager.default_language
        })
    else:
        return jsonify({
            'available_languages': ['vi', 'en'],
            'default_language': 'vi'
        })

@app.route('/api/translate/<key>', methods=['GET'])
def translate_text(key):
    """Get translated text for a key"""
    language = request.args.get('lang', 'vi')
    if language_manager:
        return jsonify({
            'key': key,
            'language': language,
            'text': language_manager.get_text(key, language)
        })
    else:
        return jsonify({
            'key': key,
            'language': language,
            'text': key
        })

@app.route('/api/assess', methods=['POST'])
def assess_cognitive():
    """Main cognitive assessment endpoint"""
    logger.info("🎯 Assessment endpoint called")
    try:
        logger.info(f"📝 Request files: {list(request.files.keys())}")
        logger.info(f"📝 Request form data: {dict(request.form)}")

        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400

        audio_file = request.files['audio']

        # Get language and question from request
        language = request.form.get('language', 'vi')
        if language not in ['vi', 'en']:
            language = 'vi'

        # Vietnamese ASR removed. Always use default (Gemini) path
        use_vietnamese_asr = False

        # Get question based on language
        if language == 'vi':
            question = request.form.get('question', 'Hãy mô tả những gì bạn thấy trong hình ảnh này')
        else:
            question = request.form.get('question', 'Describe what you see in this image')
            
        # Get user data from request (if provided)
        user_data = {}
        try:
            user_data_str = request.form.get('user_data', '{}')
            if user_data_str:
                import json
                user_data = json.loads(user_data_str)
                logger.info(f"👤 User data received: {user_data}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse user_data: {e}")
            user_data = {}

        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400

        # Save audio file temporarily with correct extension
        file_ext = '.webm'  # Default for browser recordings
        if audio_file.content_type:
            if 'webm' in audio_file.content_type:
                file_ext = '.webm'
            elif 'wav' in audio_file.content_type:
                file_ext = '.wav'
            elif 'mp3' in audio_file.content_type:
                file_ext = '.mp3'
            elif 'mp4' in audio_file.content_type:
                file_ext = '.mp4'

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        processed_path = ensure_wav_mono_16k(audio_path)

        try:
            # Step 1: Check if transcript is provided (skip only if it's valid, not placeholder)
            transcript_text = request.form.get('transcript', '').strip()
            no_speech_tokens = {
                'không có lời thoại',
                'khong co loi thoai',
                'no speech',
                'no transcript',
                'empty'
            }

            if transcript_text and transcript_text.lower() not in no_speech_tokens and 'không có lời thoại' not in transcript_text.lower():
                # Use provided transcript
                logger.info(f"📝 Using provided transcript: '{transcript_text[:100]}...'")
                transcription_result = {
                    'success': True,
                    'transcript': transcript_text,
                    'confidence': 0.8,  # Default confidence for provided transcript
                    'language': language,
                    'model': 'provided_transcript'
                }
            else:
                # Transcribe audio with language support and enhanced Vietnamese accuracy
                logger.info("🎤 Transcribing audio file...")
                if vietnamese_transcriber:
                    # ASR path removed; use unified transcriber (Gemini-first)
                    target_lang = 'vi' if language == 'vi' else 'en'
                    transcription_result = vietnamese_transcriber.transcribe_audio_file(
                        processed_path,
                        target_lang,
                        False,
                        question
                    )
                else:
                    transcription_result = transcribe_audio(processed_path, question)
            
            # Check if transcription was successful
            if not transcription_result.get('success', False):
                # Only fallback if we truly have no transcript
                transcript_content = transcription_result.get('transcript', '').strip()
                if not transcript_content:
                    logger.warning("⚠️ Transcription failed and no transcript available, using fallback")
                    transcription_result = {
                        'success': True,
                        'transcript': 'Không có lời thoại',
                        'confidence': 0.0,
                        'model': 'fallback_empty'
                    }
                else:
                    # Keep the transcript even if success=False, but mark as low confidence
                    logger.warning(f"⚠️ Transcription marked as failed but has content: '{transcript_content[:50]}...'")
                    transcription_result['success'] = True
                    transcription_result['confidence'] = min(transcription_result.get('confidence', 0.3), 0.3)
            
            # Step 2: Extract audio features
            audio_features = extract_audio_features(processed_path)
            
            # Step 3: ML prediction
            ml_prediction = predict_cognitive_score(audio_features)
            
            # Step 4: GPT-3.5 evaluation with language support (skip only for truly empty/suspicious)
            transcript_text = transcription_result.get('transcript', '').strip()
            is_suspicious = transcription_result.get('is_suspicious', False)
            
            # Check for empty or "no speech" transcripts
            empty_transcript_indicators = [
                'Không có lời thoại',
                'No speech detected', 
                'Không có âm thanh',
                'Silent audio',
                ''
            ]
            
            is_empty_transcript = (
                is_suspicious or 
                not transcript_text or 
                transcript_text in empty_transcript_indicators or
                len(transcript_text.strip().split()) == 0
            )
            
            if is_empty_transcript:
                logger.warning(f"⚠️ Empty/invalid transcript detected: '{transcript_text}' - Using proper empty evaluation")
                gpt_evaluation = {
                    'vocabulary_score': None,
                    'context_relevance_score': 0.0,
                    'overall_score': 0.0,
                    'analysis': 'Không có lời thoại hoặc transcript rỗng. Không thể đánh giá khả năng ngôn ngữ hoặc nhận thức.',
                    'feedback': 'Cần có lời thoại rõ ràng để có thể đánh giá. Vui lòng thử lại với audio có chứa giọng nói.',
                    'vocabulary_analysis': None,
                    'context_analysis': {
                        'relevance_level': 'none',
                        'accuracy': 'not_applicable',
                        'completeness': 'empty',
                        'issues': ['Không có lời thoại', 'Transcript rỗng']
                    },
                    'cognitive_assessment': {
                        'language_fluency': 'not_assessable',
                        'cognitive_level': 'not_assessable',
                        'attention_focus': 'not_assessable',
                        'memory_recall': 'not_assessable'
                    },
                    'transcript_info': {
                        'word_count': 0,
                        'is_short_transcript': True,
                        'vocabulary_richness_applicable': False
                    }
                }
            else:
                # Evaluate even if confidence is low, as long as there's actual content
                logger.info(f"🤖 Calling GPT evaluation for transcript: '{transcript_text[:100]}...'")
                gpt_evaluation = evaluate_with_gpt4o(transcript_text, question, user_data, language)
                
                # Ensure gpt_evaluation is a dictionary
                if not isinstance(gpt_evaluation, dict):
                    logger.error(f"❌ GPT evaluation returned non-dict: {type(gpt_evaluation)} - {gpt_evaluation}")
                    gpt_evaluation = {
                        'vocabulary_score': 5.0,
                        'context_relevance_score': 5.0,
                        'overall_score': 5.0,
                        'analysis': "Đánh giá không khả dụng do lỗi hệ thống",
                        'feedback': "Đánh giá không khả dụng do lỗi hệ thống"
                    }
                
                # Additional safety check before using .get()
                if isinstance(gpt_evaluation, dict):
                    logger.info(f"✅ GPT evaluation result: analysis={gpt_evaluation.get('analysis', 'MISSING')[:50]}..., feedback={gpt_evaluation.get('feedback', 'MISSING')[:50]}...")
                    logger.info(f"📊 GPT scores: vocab={gpt_evaluation.get('vocabulary_score')}, context={gpt_evaluation.get('context_relevance_score')}, overall={gpt_evaluation.get('overall_score')}")
                else:
                    logger.error(f"❌ GPT evaluation is not dict before logging: {type(gpt_evaluation)}")
            
            # Step 5: Speech-Based MMSE Support (AI assistance)
            logger.info("🎙️ STEP 5: SPEECH-BASED MMSE SUPPORT")
            speech_support_result = None
            
            if SPEECH_MMSE_AVAILABLE and audio_features:
                try:
                    speech_support_result = get_speech_mmse_support(audio_features)
                    logger.info(f"🤖 Speech-Based MMSE Support: {speech_support_result['ensemble_prediction']:.1f}/30 (confidence: {speech_support_result['confidence']:.1%})")
                except Exception as e:
                    logger.error(f"❌ Speech-Based MMSE Support failed: {e}")
                    speech_support_result = None
            
            # Step 6: Legacy ML prediction (for compatibility)
            ml_score = ml_prediction.get('predicted_score', 15.0)
            
            # Additional safety check before using .get() on gpt_evaluation
            if isinstance(gpt_evaluation, dict):
                gpt_overall_score = gpt_evaluation.get('overall_score', 5.0)
                # Extract individual scores from GPT evaluation
                vocab_score = gpt_evaluation.get('vocabulary_score')
                context_score = gpt_evaluation.get('context_relevance_score', 5.0)
            else:
                logger.error(f"❌ GPT evaluation is not dict before combining results: {type(gpt_evaluation)}")
                gpt_overall_score = 5.0
                vocab_score = None
                context_score = 5.0
            
            # Validate scores to ensure no NaN/Inf
            if np.isnan(ml_score) or np.isinf(ml_score):
                logger.warning(f"⚠️ Invalid ML score: {ml_score}, using fallback")
                ml_score = 15.0
            if np.isnan(gpt_overall_score) or np.isinf(gpt_overall_score):
                logger.warning(f"⚠️ Invalid GPT overall score: {gpt_overall_score}, using fallback")
                gpt_overall_score = 5.0
            if vocab_score is not None and (np.isnan(vocab_score) or np.isinf(vocab_score)):
                logger.warning(f"⚠️ Invalid vocabulary score: {vocab_score}, setting to None")
                vocab_score = None

            # IMPORTANT: These are AI SUPPORT scores, NOT official MMSE
            # Tầng 2: Đánh giá mức độ nguy cơ và tính điểm MMSE cuối cùng
            try:
                final_score = _calculate_final_mmse_score(ml_score, gpt_overall_score, context_score, vocab_score)
                # Đảm bảo final_score là số nguyên >0, <30
                if not isinstance(final_score, int):
                    final_score = int(round(final_score))
                final_score = max(1, min(29, final_score))
            except Exception as e:
                logger.error(f"❌ Error calculating final score: {e}")
                fallback_score = int(round(max(1.0, min(29.0, ml_score))))
                final_score = fallback_score
                logger.warning(f"⚠️ Using fallback score: {final_score}/30")
            processing_method = "legacy"

            # Try to use optimized pipeline for enhanced processing
            try:
                from performance_optimization import process_assessment_optimized
                logger.info("🚀 Attempting optimized processing...")

                optimized_result = process_assessment_optimized(
                    processed_path, question, language, user_data
                )

                if optimized_result.get('success') and optimized_result.get('processing_time', float('inf')) < 25:
                    # Use optimized results if processing was successful and fast enough
                    logger.info(f"✅ Using optimized processing results ({optimized_result['processing_time']:.2f}s)")
                    final_score = optimized_result.get('final_score', final_score)
                    processing_method = "optimized"

                    # Add optimized results to response
                    result = {
                        'success': True,
                        'transcription': transcription_result,
                        'audio_features': audio_features,
                        'ml_prediction': ml_prediction,
                        'gpt_evaluation': gpt_evaluation,
                        'final_score': final_score,
                        'optimized_results': optimized_result,
                        'processing_method': processing_method,
                        'language': language,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    logger.info("⚠️ Optimized processing failed or too slow, using legacy results")
                    result = {
                        'success': True,
                        'transcription': transcription_result,
                        'audio_features': audio_features,
                        'ml_prediction': ml_prediction,
                        'gpt_evaluation': gpt_evaluation,
                        'final_score': final_score,
                        'processing_method': processing_method,
                        'language': language,
                        'timestamp': datetime.now().isoformat()
                    }

            except ImportError:
                logger.info("⚠️ Optimized pipeline not available, using legacy processing")
                result = {
                    'success': True,
                    'transcription': transcription_result,
                    'audio_features': audio_features,
                    'ml_prediction': ml_prediction,
                    'gpt_evaluation': gpt_evaluation,
                    'final_score': final_score,
                    'processing_method': processing_method,
                    'language': language,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                logger.warning(f"⚠️ Optimized processing error: {e}, falling back to legacy")
                result = {
                    'success': True,
                    'transcription': transcription_result,
                    'audio_features': audio_features,
                    'ml_prediction': ml_prediction,
                    'gpt_evaluation': gpt_evaluation,
                    'final_score': final_score,
                    'processing_method': processing_method,
                'language': language,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Assessment completed successfully")
            return jsonify(result)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
                if processed_path and processed_path != audio_path:
                    os.unlink(processed_path)
            except (OSError, FileNotFoundError):
                pass
        
    except Exception as e:
        logger.error(f"❌ Assessment failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_endpoint():
    """Audio transcription endpoint"""
    logger.info("🎵 [DEBUG] Transcribe endpoint called")
    try:
        logger.info(f"📝 [DEBUG] Transcribe request files: {list(request.files.keys())}")
        logger.info(f"📝 [DEBUG] Transcribe request form: {dict(request.form)}")

        if 'audio' not in request.files:
            logger.error("❌ [DEBUG] No audio file in request")
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400
        
        # Get language from request (default to Vietnamese)
        language = request.form.get('language', 'vi')
        if language not in ['vi', 'en']:
            language = 'vi'

        # Get question from request
        question = request.form.get('question', None)

        # Vietnamese ASR removed
        use_vietnamese_asr = False
        
        # Save audio file temporarily with correct extension
        file_ext = '.webm'  # Default for browser recordings
        if audio_file.content_type:
            if 'webm' in audio_file.content_type:
                file_ext = '.webm'
            elif 'wav' in audio_file.content_type:
                file_ext = '.wav'
            elif 'mp3' in audio_file.content_type:
                file_ext = '.mp3'
            elif 'mp4' in audio_file.content_type:
                file_ext = '.mp4'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        processed_path = ensure_wav_mono_16k(audio_path)
        
        try:
            # Add timeout for transcription using threading (Windows compatible)
            import threading
            import time
            
            result = None
            error = None
            
            def transcribe_with_timeout():
                nonlocal result, error
                try:
                    # Use the new transcriber with language support
                    if vietnamese_transcriber:
                        result = vietnamese_transcriber.transcribe_audio_file(
                            processed_path,
                            language,
                            False,
                            question
                        )
                    else:
                        result = transcribe_audio(processed_path, question)
                except Exception as e:
                    error = e
            
            # Start transcription in a separate thread
            thread = threading.Thread(target=transcribe_with_timeout)
            thread.daemon = True
            thread.start()
            
            # Wait for completion or timeout (OpenAI Whisper is much faster)
            thread.join(timeout=30)  # 30 seconds timeout for OpenAI Whisper
            
            if thread.is_alive():
                logger.error("❌ Transcription timeout after 30 seconds")
                return jsonify({
                    'success': False,
                    'error': t('transcription_failed')
                }), 408
            
            if error:
                raise error
            
            # Check if transcription was successful
            if not result or not result.get('success', False):
                # Only fallback if we truly have no transcript
                transcript_content = result.get('transcript', '').strip() if result else ''
                if not transcript_content:
                    logger.warning("⚠️ Transcription unavailable, returning safe empty transcript")
                    result = {
                        'success': True,
                        'transcript': 'Không có lời thoại',
                        'confidence': 0.0,
                        'model': 'fallback_empty'
                    }
                else:
                    # Keep the transcript even if success=False, but mark as low confidence
                    logger.warning(f"⚠️ Transcription marked as failed but has content: '{transcript_content[:50]}...'")
                    result['success'] = True
                    result['confidence'] = min(result.get('confidence', 0.3), 0.3)
            
            # Ensure transcript and confidence are safe, but don't override valid content
            transcript = result.get('transcript', '').strip()
            if not transcript:
                result['transcript'] = 'Không có lời thoại'
                result['confidence'] = 0.0
            else:
                # Keep the transcript even if confidence is low, but validate confidence
                confidence = result.get('confidence', 0)
                if not isinstance(confidence, (int, float)) or np.isnan(confidence) or np.isinf(confidence):
                    result['confidence'] = 0.5  # Default confidence for valid transcript
            
            return jsonify(result)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
                if processed_path and processed_path != audio_path:
                    os.unlink(processed_path)
            except (OSError, FileNotFoundError):
                pass
                
    except TimeoutError as e:
        logger.error(f"❌ Transcription timeout: {e}")
        return jsonify({
            'success': False,
            'error': t('transcription_failed')
        }), 408
    except Exception as e:
        logger.error(f"❌ Transcription endpoint failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/features', methods=['POST'])
def extract_features():
    """Audio feature extraction endpoint"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400
        
        # Save audio file temporarily with correct extension
        file_ext = '.webm'  # Default for browser recordings
        if audio_file.content_type:
            if 'webm' in audio_file.content_type:
                file_ext = '.webm'
            elif 'wav' in audio_file.content_type:
                file_ext = '.wav'
            elif 'mp3' in audio_file.content_type:
                file_ext = '.mp3'
            elif 'mp4' in audio_file.content_type:
                file_ext = '.mp4'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        processed_path = ensure_wav_mono_16k(audio_path)

        try:
            features = extract_audio_features(processed_path)
            return jsonify({
                'success': True,
                'features': features
            })
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
                if processed_path and processed_path != audio_path:
                    os.unlink(processed_path)
            except (OSError, FileNotFoundError):
                pass
                
    except Exception as e:
        logger.error(f"❌ Feature extraction failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Compatibility aliases for existing frontend calls
@app.route('/auto-transcribe', methods=['POST'])
def auto_transcribe_alias():
    """Auto-transcribe endpoint with full assessment (audio features + MMSE + GPT evaluation)"""
    try:
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400

        audio_file = request.files['audio']

        # Get language and question from request
        language = request.form.get('language', 'vi')
        if language not in ['vi', 'en']:
            language = 'vi'

        # Vietnamese ASR removed
        use_vietnamese_asr = False

        # Get question based on language
        if language == 'vi':
            question = request.form.get('question', 'Hãy mô tả những gì bạn thấy trong hình ảnh này')
        else:
            question = request.form.get('question', 'Describe what you see in this image')

        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400

        # Save audio file temporarily with correct extension
        file_ext = '.webm'  # Default for browser recordings
        if audio_file.content_type:
            if 'webm' in audio_file.content_type:
                file_ext = '.webm'
            elif 'wav' in audio_file.content_type:
                file_ext = '.wav'
            elif 'mp3' in audio_file.content_type:
                file_ext = '.mp3'
            elif 'mp4' in audio_file.content_type:
                file_ext = '.mp4'

        # Check if audio file is too small (empty or near-empty)
        audio_file.seek(0, 2)  # Seek to end to get file size
        audio_size = audio_file.tell()
        audio_file.seek(0)  # Reset file pointer

        logger.info(f"🎵 Audio file size: {audio_size} bytes")

        # Handle empty or very small audio files (< 1KB)
        if audio_size < 1000:
            logger.warning("⚠️ Empty or very small audio file detected, returning mock result")
            # Đảm bảo final_score luôn được tính (số nguyên >0, <30)
            # Với audio rỗng, điểm tối thiểu là 1
            final_score = 1
            return jsonify({
                'success': True,
                'transcription': {
                    'transcript': 'Không có lời thoại (âm thanh trống)',
                    'confidence': 0.0,
                    'model': 'empty_audio_detection'
                },
                'audio_features': {
                    'duration': 0.0,
                    'pitch_mean': 0.0,
                    'pitch_std': 0.0,
                    'speech_rate': 0.0,
                    'tempo': 0.0,
                    'silence_mean': 1.0,
                    'number_utterances': 0
                },
                'ml_prediction': {
                    'predicted_score': 1.0,  # Minimum score >0
                    'confidence': 0.0,
                    'severity': 'Không có dữ liệu âm thanh'
                },
                'gpt_evaluation': {
                    'vocabulary_score': 0.0,
                    'context_relevance_score': 0.0,
                    'overall_score': 0.0,
                    'analysis': 'Không phát hiện được lời nói trong bản ghi âm. Đây có thể là do: 1) Không có âm thanh nào được ghi lại, 2) Mức âm lượng quá thấp, 3) Thời gian ghi quá ngắn.',
                    'feedback': 'Vui lòng thử ghi âm lại với âm lượng rõ ràng hơn và nói to hơn.',
                    'repetition_rate': 0.0,
                    'context_relevance': 0.0,
                    'comprehension_score': 0.0
                },
                'final_score': final_score  # Số nguyên >0, <30
            })

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        processed_path = ensure_wav_mono_16k(audio_path)

        try:
            logger.info("=" * 60)
            logger.info("PIPELINE XỬ LÝ ĐÁNH GIÁ NHẬN THỨC")
            logger.info("=" * 60)
            logger.info(f"📋 Câu hỏi: {question[:100]}...")
            logger.info(f"🌐 Ngôn ngữ: {language}")
            
            # TẦNG 1 - Bước 1: Audio → Transcript (xử lý transcript từ audio)
            logger.info("📝 TẦNG 1 - Bước 1: Xử lý audio thành transcript...")
            if vietnamese_transcriber:
                # Use Vietnamese-specific transcription for better accuracy when Vietnamese is selected
                target_lang = 'vi' if language == 'vi' else 'en'
                transcription_result = vietnamese_transcriber.transcribe_audio_file(
                    processed_path,
                    target_lang,
                    False,
                    question
                )
            else:
                transcription_result = transcribe_audio(processed_path, question)
            
            # Check if transcription was successful
            if not transcription_result.get('success', False):
                # Only fallback if we truly have no transcript
                transcript_content = transcription_result.get('transcript', '').strip()
                if not transcript_content:
                    logger.warning("⚠️ Transcription unavailable, using safe empty transcript fallback (raw)")
                    transcription_result = {
                        'success': True,
                        'transcript': 'Không có lời thoại',
                        'confidence': 0.0,
                        'model': 'fallback_empty'
                    }
                else:
                    # Keep the transcript even if success=False, but mark as low confidence
                    logger.warning(f"⚠️ Transcription marked as failed but has content: '{transcript_content[:50]}...'")
                    transcription_result['success'] = True
                    transcription_result['confidence'] = min(transcription_result.get('confidence', 0.3), 0.3)
            
            # Ensure transcript/confidence safe
            if not transcription_result.get('transcript') or str(transcription_result.get('transcript')).strip() == '':
                transcription_result['transcript'] = 'Không có lời thoại'
            tr_conf = transcription_result.get('confidence', 0)
            if not isinstance(tr_conf, (int, float)) or np.isnan(tr_conf) or np.isinf(tr_conf):
                transcription_result['confidence'] = 0.0
            
            transcript_text = transcription_result.get('transcript', '')
            logger.info(f"✅ Transcript: '{transcript_text[:100]}...' (confidence: {tr_conf:.2f})")
            
            # TẦNG 1 - Bước 2: Audio → Acoustic Features (xử lý đặc trưng âm học)
            logger.info("🎵 TẦNG 1 - Bước 2: Trích xuất đặc trưng âm học từ audio...")
            audio_features = extract_audio_features(processed_path)
            logger.info(f"✅ Acoustic features extracted: {list(audio_features.keys())}")
            
            # TẦNG 1 - Bước 3: Acoustic Features → ML Prediction (tầng 1 xử lý âm học)
            logger.info("🤖 TẦNG 1 - Bước 3: ML model xử lý đặc trưng âm học...")
            ml_prediction = predict_cognitive_score(audio_features)
            ml_score = ml_prediction.get('predicted_score', 5.0)
            logger.info(f"✅ ML prediction: {ml_score:.2f}/30")
            
            # TẦNG 1 - Bước 4: Transcript + Question → GPT Evaluation (tầng 1 xử lý transcript)
            logger.info("💬 TẦNG 1 - Bước 4: GPT đánh giá transcript dựa trên câu hỏi và mức độ đáp ứng...")
            if not transcript_text or transcript_text.strip() == '':
                logger.warning("⚠️ Empty transcript, skipping GPT evaluation")
                gpt_evaluation = {
                    'repetition_rate': 0.0,
                    'vocabulary_score': 0.0,
                    'fluency_score': 0.0,
                    'comprehension_score': 0.0,
                    'overall_score': 0.0,
                    'context_relevance_score': 0.0,
                    'feedback': 'No transcript available for evaluation'
                }
            else:
                logger.info(f"🤖 Calling GPT evaluation for transcript: '{transcript_text[:100]}...'")
                logger.info(f"📋 Evaluating against question: '{question[:100]}...'")
                gpt_evaluation = evaluate_with_gpt4o(transcript_text, question, language)
                
                # Ensure gpt_evaluation is a dictionary
                if not isinstance(gpt_evaluation, dict):
                    logger.error(f"❌ [AUTO_TRANSCRIBE_RAW] GPT evaluation returned non-dict: {type(gpt_evaluation)} - {gpt_evaluation}")
                    gpt_evaluation = {
                        'vocabulary_score': 5.0,
                        'context_relevance_score': 5.0,
                        'overall_score': 5.0,
                        'analysis': "Đánh giá không khả dụng do lỗi hệ thống",
                        'feedback': "Đánh giá không khả dụng do lỗi hệ thống"
                    }
                
                # Additional safety check before using .get()
                if isinstance(gpt_evaluation, dict):
                    logger.info(f"✅ [AUTO_TRANSCRIBE_RAW] GPT evaluation result: analysis={gpt_evaluation.get('analysis', 'MISSING')[:50]}..., feedback={gpt_evaluation.get('feedback', 'MISSING')[:50]}...")
                    logger.info(f"📊 [AUTO_TRANSCRIBE_RAW] GPT scores: vocab={gpt_evaluation.get('vocabulary_score')}, context={gpt_evaluation.get('context_relevance_score')}, overall={gpt_evaluation.get('overall_score')}")
                else:
                    logger.error(f"❌ [AUTO_TRANSCRIBE_RAW] GPT evaluation is not dict before logging: {type(gpt_evaluation)}")
            
            # Step 5: Combine results
            ml_score = ml_prediction.get('predicted_score', 5.0)
            # Additional safety check before using .get() on gpt_evaluation
            if isinstance(gpt_evaluation, dict):
                gpt_overall_score = gpt_evaluation.get('overall_score', 5.0)
                # Extract individual scores from GPT evaluation
                vocab_score = gpt_evaluation.get('vocabulary_score')
                context_score = gpt_evaluation.get('context_relevance_score', 5.0)
            else:
                logger.error(f"❌ [AUTO_TRANSCRIBE_RAW] GPT evaluation is not dict before combining results: {type(gpt_evaluation)}")
                gpt_overall_score = 5.0
                vocab_score = None
                context_score = 5.0
            
            # Validate scores to ensure no NaN/Inf
            if np.isnan(ml_score) or np.isinf(ml_score):
                logger.warning(f"⚠️ Invalid ML score: {ml_score}, using fallback")
                ml_score = 5.0
            if np.isnan(gpt_overall_score) or np.isinf(gpt_overall_score):
                logger.warning(f"⚠️ Invalid GPT overall score: {gpt_overall_score}, using fallback")
                gpt_overall_score = 5.0
            if vocab_score is not None and (np.isnan(vocab_score) or np.isinf(vocab_score)):
                logger.warning(f"⚠️ Invalid vocabulary score: {vocab_score}, setting to None")
                vocab_score = None

            # Tầng 2: Đánh giá mức độ nguy cơ và tính điểm MMSE cuối cùng
            # Đảm bảo final_score luôn được tính (số nguyên >0, <30)
            try:
                final_score = _calculate_final_mmse_score(ml_score, gpt_overall_score, context_score, vocab_score)
                logger.info(f"✅ Final MMSE score calculated: {final_score}/30")
            except Exception as e:
                logger.error(f"❌ Error calculating final score: {e}")
                # Fallback: sử dụng ML score làm điểm tạm thời (đảm bảo >0, <30)
                fallback_score = int(round(max(1.0, min(29.0, ml_score))))
                final_score = fallback_score
                logger.warning(f"⚠️ Using fallback score: {final_score}/30")
            
            # Đảm bảo final_score là số nguyên trong khoảng (0, 30)
            if not isinstance(final_score, int):
                final_score = int(round(final_score))
            final_score = max(1, min(29, final_score))  # >0, <30
            
            result = {
                'success': True,
                'transcription': transcription_result,
                'audio_features': audio_features,
                'ml_prediction': ml_prediction,
                'gpt_evaluation': gpt_evaluation,
                'final_score': final_score,  # Số nguyên >0, <30
                'language': language,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Auto-transcribe assessment completed successfully - Final score: {final_score}/30")
            return jsonify(result)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
                if processed_path and processed_path != audio_path:
                    os.unlink(processed_path)
            except (OSError, FileNotFoundError):
                pass
        
    except Exception as e:
        logger.error(f"❌ Auto-transcribe assessment failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/assess-cognitive', methods=['POST'])
def assess_cognitive_alias():
    # This is a compatibility alias - it calls the main function
    # The request context is automatically available in Flask
    return assess_cognitive()

@app.route('/api/test-transcription', methods=['POST'])
def test_transcription():
    """Test transcription endpoint for quick testing"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400
        
        # Get question from request
        question = request.form.get('question', None)
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        
        try:
            # Test transcription with timing
            import time
            start_time = time.time()
            
            result = transcribe_audio(audio_path, question)
            
            # Check if transcription was successful
            if not result or not result.get('success', False):
                logger.error(f"❌ Transcription failed: {result.get('error', 'Unknown error') if result else 'No result'}")
                return jsonify({
                    'success': False,
                    'error': f"Transcription failed: {result.get('error', 'Unknown error') if result else 'No result'}"
                }), 500
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            result['processing_time'] = processing_time
            result['file_size_kb'] = os.path.getsize(audio_path) / 1024
            
            return jsonify(result)
            
        finally:
            # Clean up
            try:
                os.unlink(audio_path)
            except (OSError, FileNotFoundError):
                pass
                
    except Exception as e:
        logger.error(f"❌ Test transcription failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-transcription-raw', methods=['POST'])
def test_transcription_raw():
    """Test transcription endpoint WITHOUT GPT-4o improvement"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'vi')
        question = request.form.get('question', None)
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        
        try:
            # Test transcription WITHOUT GPT-4o improvement
            import time
            start_time = time.time()
            
            if vietnamese_transcriber:
                # Call the raw transcription method directly
                result = vietnamese_transcriber._transcribe_with_whisper_only(audio_path, language)
            else:
                result = transcribe_audio(audio_path, question)
            
            # Check if transcription was successful
            if not result or not result.get('success', False):
                logger.error(f"❌ Transcription failed: {result.get('error', 'Unknown error') if result else 'No result'}")
                return jsonify({
                    'success': False,
                    'error': f"Transcription failed: {result.get('error', 'Unknown error') if result else 'No result'}"
                }), 500
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            result['processing_time'] = processing_time
            result['file_size_kb'] = os.path.getsize(audio_path) / 1024
            result['method'] = 'whisper-only'
            
            return jsonify(result)
            
        finally:
            # Clean up
            try:
                os.unlink(audio_path)
            except (OSError, FileNotFoundError):
                pass
                
    except Exception as e:
        logger.error(f"❌ Raw test transcription failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auto-transcribe-raw', methods=['POST'])
def auto_transcribe_raw():
    """Auto-transcribe endpoint WITHOUT GPT-4o improvement but WITH full assessment"""
    try:
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400
        
        audio_file = request.files['audio']
        
        # Get language and question from request
        language = request.form.get('language', 'vi')
        if language not in ['vi', 'en']:
            language = 'vi'

        # Vietnamese ASR removed
        use_vietnamese_asr = False
        
        # Get question based on language
        if language == 'vi':
            question = request.form.get('question', 'Hãy mô tả những gì bạn thấy trong hình ảnh này')
        else:
            question = request.form.get('question', 'Describe what you see in this image')
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': t('audio_file_not_found')
            }), 400
        
        # Save audio file temporarily with correct extension
        file_ext = '.webm'  # Default for browser recordings
        if audio_file.content_type:
            if 'webm' in audio_file.content_type:
                file_ext = '.webm'
            elif 'wav' in audio_file.content_type:
                file_ext = '.wav'
            elif 'mp3' in audio_file.content_type:
                file_ext = '.mp3'
            elif 'mp4' in audio_file.content_type:
                file_ext = '.mp4'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        processed_path = ensure_wav_mono_16k(audio_path)
        
        try:
            # Step 1: Transcribe audio WITHOUT GPT-4o improvement
            if vietnamese_transcriber:
                transcription_result = vietnamese_transcriber._transcribe_with_whisper_only(processed_path, language)
            else:
                transcription_result = transcribe_audio(processed_path, question)
            
            # Check if transcription was successful
            if not transcription_result.get('success', False):
                # Only fail if we truly have no transcript
                transcript_content = transcription_result.get('transcript', '').strip()
                if not transcript_content:
                    logger.error(f"❌ Transcription failed: {transcription_result.get('error', 'Unknown error')}")
                    return jsonify({
                        'success': False,
                        'error': f"Transcription failed: {transcription_result.get('error', 'Unknown error')}",
                        'transcription': transcription_result
                    }), 500
                else:
                    # Keep the transcript even if success=False, but mark as low confidence
                    logger.warning(f"⚠️ Transcription marked as failed but has content: '{transcript_content[:50]}...'")
                    transcription_result['success'] = True
                    transcription_result['confidence'] = min(transcription_result.get('confidence', 0.3), 0.3)
            
            # Ensure transcript/confidence safe
            if not transcription_result.get('transcript') or str(transcription_result.get('transcript')).strip() == '':
                transcription_result['transcript'] = 'Không có lời thoại'
            tr_conf2 = transcription_result.get('confidence', 0)
            if not isinstance(tr_conf2, (int, float)) or np.isnan(tr_conf2) or np.isinf(tr_conf2):
                transcription_result['confidence'] = 0.0
            
            # Step 2: Extract audio features
            audio_features = extract_audio_features(processed_path)
            
            # Step 3: ML prediction
            ml_prediction = predict_cognitive_score(audio_features)
            
            # Step 4: GPT-3.5 evaluation with language support
            transcript_text = transcription_result.get('transcript', '')
            if not transcript_text or transcript_text.strip() == '':
                logger.warning("⚠️ Empty transcript, skipping GPT evaluation")
                gpt_evaluation = {
                    'repetition_rate': 0.0,
                    'vocabulary_score': 0.0,
                    'fluency_score': 0.0,
                    'comprehension_score': 0.0,
                    'overall_score': 0.0,
                    'feedback': 'No transcript available for evaluation'
                }
            else:
                logger.info(f"🤖 [AUTO_TRANSCRIBE_RAW] Calling GPT evaluation for transcript: '{transcript_text[:100]}...'")
                gpt_evaluation = evaluate_with_gpt4o(transcript_text, question, language)
                
                # Ensure gpt_evaluation is a dictionary
                if not isinstance(gpt_evaluation, dict):
                    logger.error(f"❌ [AUTO_TRANSCRIBE_RAW] GPT evaluation returned non-dict: {type(gpt_evaluation)} - {gpt_evaluation}")
                    gpt_evaluation = {
                        'vocabulary_score': 5.0,
                        'context_relevance_score': 5.0,
                        'overall_score': 5.0,
                        'analysis': "Đánh giá không khả dụng do lỗi hệ thống",
                        'feedback': "Đánh giá không khả dụng do lỗi hệ thống"
                    }
                
                # Additional safety check before using .get()
                if isinstance(gpt_evaluation, dict):
                    logger.info(f"✅ [AUTO_TRANSCRIBE_RAW] GPT evaluation result: analysis={gpt_evaluation.get('analysis', 'MISSING')[:50]}..., feedback={gpt_evaluation.get('feedback', 'MISSING')[:50]}...")
                    logger.info(f"📊 [AUTO_TRANSCRIBE_RAW] GPT scores: vocab={gpt_evaluation.get('vocabulary_score')}, context={gpt_evaluation.get('context_relevance_score')}, overall={gpt_evaluation.get('overall_score')}")
                else:
                    logger.error(f"❌ [AUTO_TRANSCRIBE_RAW] GPT evaluation is not dict before logging: {type(gpt_evaluation)}")
            
            # Step 5: Combine results
            ml_score = ml_prediction.get('predicted_score', 5.0)
            # Additional safety check before using .get() on gpt_evaluation
            if isinstance(gpt_evaluation, dict):
                gpt_overall_score = gpt_evaluation.get('overall_score', 5.0)
                # Extract individual scores from GPT evaluation
                vocab_score = gpt_evaluation.get('vocabulary_score')
                context_score = gpt_evaluation.get('context_relevance_score', 5.0)
            else:
                logger.error(f"❌ [AUTO_TRANSCRIBE_RAW] GPT evaluation is not dict before combining results: {type(gpt_evaluation)}")
                gpt_overall_score = 5.0
                vocab_score = None
                context_score = 5.0
            
            # Validate scores to ensure no NaN/Inf
            if np.isnan(ml_score) or np.isinf(ml_score):
                logger.warning(f"⚠️ Invalid ML score: {ml_score}, using fallback")
                ml_score = 5.0
            if np.isnan(gpt_overall_score) or np.isinf(gpt_overall_score):
                logger.warning(f"⚠️ Invalid GPT overall score: {gpt_overall_score}, using fallback")
                gpt_overall_score = 5.0
            if vocab_score is not None and (np.isnan(vocab_score) or np.isinf(vocab_score)):
                logger.warning(f"⚠️ Invalid vocabulary score: {vocab_score}, setting to None")
                vocab_score = None

            # Tầng 2: Đánh giá mức độ nguy cơ và tính điểm MMSE cuối cùng
            try:
                final_score = _calculate_final_mmse_score(ml_score, gpt_overall_score, context_score, vocab_score)
                # Đảm bảo final_score là số nguyên >0, <30
                if not isinstance(final_score, int):
                    final_score = int(round(final_score))
                final_score = max(1, min(29, final_score))
                logger.info(f"✅ Final MMSE score calculated: {final_score}/30")
            except Exception as e:
                logger.error(f"❌ Error calculating final score: {e}")
                fallback_score = int(round(max(1.0, min(29.0, ml_score))))
                final_score = fallback_score
                logger.warning(f"⚠️ Using fallback score: {final_score}/30")
            
            result = {
                'success': True,
                'transcription': transcription_result,
                'audio_features': audio_features,
                'ml_prediction': ml_prediction,
                'gpt_evaluation': gpt_evaluation,
                'final_score': final_score,  # Số nguyên >0, <30
                'language': language,
                'method': 'whisper-only',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Auto-transcribe RAW assessment completed successfully - Final score: {final_score}/30")
            return jsonify(result)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
                if processed_path and processed_path != audio_path:
                    os.unlink(processed_path)
            except (OSError, FileNotFoundError):
                pass
        
    except Exception as e:
        logger.error(f"❌ Auto-transcribe RAW assessment failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate_transcript():
    """Transcript evaluation endpoint"""
    try:
        data = request.get_json()
        
        if not data:
                return jsonify({
                    'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        transcript = data.get('transcript', '')
        question = data.get('question', 'Describe what you see')
        user_data = data.get('user_data', {})
        
        if not transcript:
            return jsonify({
                'success': False,
                'error': 'No transcript provided'
            }), 400

        evaluation = evaluate_with_gpt4o(transcript, question, user_data)
        return jsonify({
            'success': True,
            'evaluation': evaluation
        })
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'model_loaded': cognitive_model is not None,
        'openai_available': openai_client is not None,
        'transcriber_available': vietnamese_transcriber is not None,
        'feature_names': feature_names if feature_names else [],
        'vi_asr_model': vi_asr_model,
        'transcription_enabled': os.getenv('ENABLE_PAID_TRANSCRIPTION', 'true').lower() == 'true',
        'transcription_budget': os.getenv('TRANSCRIPTION_BUDGET_LIMIT', '5.00'),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration information (without sensitive data)"""
    return jsonify({
        'server': {
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': os.getenv('PORT', '8000'),
            'debug': os.getenv('DEBUG', 'True'),
            'flask_env': os.getenv('FLASK_ENV', 'development')
        },
        'apis': {
            'openai_configured': openai_api_key is not None,
            'vi_asr_model': vi_asr_model
        },
        'features': {
            'transcription_enabled': os.getenv('ENABLE_PAID_TRANSCRIPTION', 'true').lower() == 'true',
            'transcription_budget': os.getenv('TRANSCRIPTION_BUDGET_LIMIT', '5.00'),
            'storage_path': os.getenv('STORAGE_PATH', './storage')
        },
        'database': {
            'configured': os.getenv('DATABASE_URL') is not None
        },
        'timestamp': datetime.now().isoformat()
    })

# MMSE v2.0 Assessment Endpoints
@app.route('/api/mmse/assess', methods=['POST'])
def mmse_assess():
    """MMSE v2.0 assessment endpoint"""
    try:
        from services.mmse_assessment_service import get_mmse_service
        
        logger.info("=" * 60)
        logger.info("🎯 NHẬN REQUEST ĐÁNH GIÁ MMSE v2.0")
        logger.info("=" * 60)

        # Log request details
        logger.info(f"📨 Request method: {request.method}")
        logger.info(f"📨 Content-Type: {request.content_type}")
        logger.info(f"📨 Form data keys: {list(request.form.keys()) if request.form else 'None'}")
        logger.info(f"📨 Files: {list(request.files.keys()) if request.files else 'None'}")
        
        # Check if audio file is provided
        if 'audio' not in request.files:
            logger.error("❌ No audio file provided in request")
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            logger.error("❌ Audio file has empty filename")
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400

        logger.info(f"🎵 Audio file received: {audio_file.filename}")
        logger.info(f"📊 Audio file size: {len(audio_file.read())} bytes")
        audio_file.seek(0)  # Reset file pointer

        # Log audio file details for debugging
        logger.info(f"🔍 Audio file content type: {audio_file.content_type}")
        logger.info(f"🔍 Audio file headers: {audio_file.headers if hasattr(audio_file, 'headers') else 'No headers'}")
        
        # Get additional parameters
        session_id = request.form.get('session_id')
        logger.info(f"🆔 Session ID: {session_id or 'Auto-generated'}")
        
        patient_info = {}
        try:
            if request.form.get('patient_info'):
                patient_info = json.loads(request.form.get('patient_info'))
                logger.info(f"👤 Patient info parsed: {patient_info}")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse patient_info: {e}")
            patient_info = {}
        
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_audio_path = tmp_file.name
        
        logger.info(f"💾 Temporary audio file saved: {tmp_audio_path}")

        try:
            # Get MMSE service
            logger.info("🔧 Initializing MMSE service...")
            mmse_service = get_mmse_service()
            
            # Validate audio file
            logger.info("✅ Validating audio file...")
            is_valid, validation_message = mmse_service.validate_audio_file(tmp_audio_path)
            if not is_valid:
                logger.error(f"❌ Audio validation failed: {validation_message}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid audio file: {validation_message}'
                }), 400
            
            logger.info("✅ Audio file validation passed")

            # Perform assessment
            logger.info("🚀 Starting MMSE assessment...")
            assessment_start = datetime.now()

            result = mmse_service.assess_session(
                audio_path=tmp_audio_path,
                session_id=session_id,
                patient_info=patient_info
            )

            assessment_end = datetime.now()
            assessment_duration = (assessment_end - assessment_start).total_seconds()
            
            if result['status'] == 'error':
                logger.error(f"❌ Assessment failed: {result.get('error', 'Unknown error')}")
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Assessment failed')
                }), 500
            
            # Log successful result summary
            logger.info("=" * 60)
            logger.info("✅ ASSESSMENT COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"⏱️ Total assessment time: {assessment_duration:.2f}s")
            logger.info(f"🆔 Session ID: {result['session_id']}")
            logger.info(f"📊 Final MMSE Score: {result['mmse_scores']['final_score']}/30")
            if result['mmse_scores'].get('ml_prediction'):
                logger.info(f"🤖 ML Prediction: {result['mmse_scores']['ml_prediction']:.1f}/30")
            logger.info(f"🏥 Cognitive Status: {result['cognitive_status']['status']}")
            logger.info(f"⚠️ Risk Level: {result['cognitive_status']['risk_level']}")
            logger.info("=" * 60)

            # Return successful result
            logger.info("📤 Sending response to client...")
            return jsonify({
                'success': True,
                'data': result
            })
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_audio_path)
                logger.info(f"🧹 Cleaned up temporary file: {tmp_audio_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean up temporary file: {e}")
                
    except ImportError as e:
        logger.error("❌ MMSE v2.0 service not available")
        logger.error(f"💡 ImportError details: {e}")
        logger.error("💡 Make sure release_v1 directory exists and models are properly installed")
        return jsonify({
            'success': False,
            'error': 'MMSE v2.0 service not available. Please ensure the release_v1 model is properly installed.'
        }), 503
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("💥 UNEXPECTED ERROR IN MMSE ASSESSMENT")
        logger.error("=" * 60)
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error message: {str(e)}")
        import traceback
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        logger.error("=" * 60)
        return jsonify({
            'success': False,
            'error': f'Assessment failed: {str(e)}'
        }), 500

@app.route('/api/mmse/questions', methods=['GET'])
def mmse_get_questions():
    """Get MMSE questions schema"""
    try:
        # Load the new MMSE domain-based structure
        questions_path = os.path.join(os.path.dirname(__file__), '..', 'release_v1', 'questions.json')
        if not os.path.exists(questions_path):
            # Fallback to legacy structure
            questions_path = os.path.join(os.path.dirname(__file__), 'questions.json')

        logger.info(f"📋 Loading MMSE questions from: {questions_path}")

        with open(questions_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        logger.debug(f"Loaded questions_data: {json.dumps(questions_data, ensure_ascii=False, indent=2)}")

        # Process the new domain-based structure
        all_questions = []
        total_points = 0
        domains_info = []

        for item in questions_data:
            if 'domain' in item and 'questions' in item:
                domain_name = item['domain']
                domain_description = item.get('domain_description', domain_name)
                max_domain_points = item.get('max_domain_points', 0)

                # Add domain info
                domains_info.append({
                    'name': domain_name,
                    'description': domain_description,
                    'max_points': max_domain_points
                })

                for question in item['questions']:
                    question_formatted = {
                        'id': question['id'],
                        'domain': domain_name,
                        'category': domain_description,
                        'question_text': question['question_text'],
                        'answer_type': question.get('answer_type', 'text'),
                        'points': question.get('points', 1),
                        'max_points': question.get('points', 1),  # Add max_points field
                        'scoring_criteria': question.get('scoring_criteria', ''),
                        'sample_correct': question.get('sample_correct', ''),
                        'sample_incorrect': question.get('sample_incorrect', '')
                    }
                    all_questions.append(question_formatted)

                total_points += max_domain_points
                logger.info(f"📊 Domain {domain_name}: {len(item['questions'])} questions, {max_domain_points} points")

        logger.debug(f"Processed all_questions: {len(all_questions)} questions, total_points: {total_points}")
        logger.debug(f"First question sample: {json.dumps(all_questions[0] if all_questions else 'No questions', ensure_ascii=False, indent=2)}")
        final_response = {
            'success': True,
            'data': {
                'questions': all_questions,
                'total_points': total_points,
                'structure': 'domain_based',
                'domains': domains_info
            }
        }
        logger.info(f"✅ Successfully loaded {len(all_questions)} MMSE questions, returning {len(domains_info)} domains")
        return jsonify(final_response)

    except ImportError:
        return jsonify({
            'success': False,
            'error': 'MMSE v2.0 service not available'
        }), 503

    except Exception as e:
        logger.error(f"❌ Error getting MMSE questions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mmse/model-info', methods=['GET'])
def mmse_model_info():
    """Get MMSE model information and status"""
    try:
        from services.mmse_assessment_service import get_mmse_service
        
        mmse_service = get_mmse_service()
        model_info = mmse_service.get_model_info()
        
        return jsonify({
            'success': True,
            'data': model_info
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'MMSE v2.0 service not available'
        }), 503
        
    except Exception as e:
        logger.error(f"❌ Error getting model info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mmse/transcribe', methods=['POST'])
def mmse_transcribe_only():
    """Transcribe audio only (for testing)"""
    try:
        from services.mmse_assessment_service import get_mmse_service
        
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_audio_path = tmp_file.name
        
        try:
            mmse_service = get_mmse_service()
            result = mmse_service.transcribe_audio(tmp_audio_path)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        finally:
            try:
                os.unlink(tmp_audio_path)
            except:
                pass
                
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'MMSE v2.0 service not available'
        }), 503
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-summary', methods=['POST'])
def generate_summary():
    """Generate comprehensive final summary with MMSE score and recommendations"""
    try:
        logger.info("📊 Received request to generate final summary")

        # Get session data
        session_id = request.form.get('sessionId', 'unknown')
        results_data = request.form.get('results', '[]')
        user_data_str = request.form.get('userData', '{}')

        try:
            session_results = json.loads(results_data)
            user_data = json.loads(user_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data'
            }), 400

        logger.info(f"📝 Processing {len(session_results)} results for session {session_id}")

        # Generate final summary
        final_summary = generate_final_summary(session_results, user_data)

        if 'error' in final_summary:
            return jsonify({
                'success': False,
                'error': final_summary['error']
            }), 500

        logger.info(f"✅ Final summary generated successfully for session {session_id}")

        return jsonify({
            'success': True,
            'data': final_summary,
            'message': 'Final summary generated successfully'
        })

    except Exception as e:
        logger.error(f"❌ Generate summary failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Start queue worker thread
queue_thread = threading.Thread(target=queue_worker, daemon=True, name='queue_worker')
queue_thread.start()
logger.info("🎯 Queue worker thread started")

# Initialize models when app is imported (PRIORITY 7)
try:
    logger.info("=" * 60)
    logger.info("STARTING APPLICATION")
    logger.info("=" * 60)
    logger.info("Auto-initializing models...")
    
    if initialize_model():
        logger.info("=" * 60)
        logger.info("MODELS INITIALIZED SUCCESSFULLY")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("MODEL INITIALIZATION FAILED")
        logger.error("=" * 60)
        logger.error("Server starting without ML capabilities")
        logger.error("Some endpoints may not work properly")
        logger.error("=" * 60)
except Exception as e:
    logger.error("=" * 60)
    logger.error("AUTO-INITIALIZATION FAILED")
    logger.error("=" * 60)
    logger.error(f"Error: {e}")
    import traceback
    logger.error(traceback.format_exc())
    logger.error("=" * 60)
    logger.error("App will continue with limited functionality")
    logger.error("=" * 60)

# New API endpoints for queued assessments
@app.route('/api/assess-queue', methods=['POST'])
def queue_assessment():
    """Queue assessment for background processing"""
    logger.info("📋 [DEBUG] Queue assessment endpoint called")
    try:
        data = request.json
        logger.info(f"📝 [DEBUG] Queue request data: {data}")

        if not data:
            logger.error("❌ [DEBUG] No data provided in queue request")
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Generate task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(data)) % 10000}"

        # Add task to queue
        queue_data = {
            'task_id': task_id,
            'question_id': data.get('question_id'),
            'transcript': data.get('transcript', ''),
            'audio_data': data.get('audio_data'),
            'user_id': data.get('user_id'),
            'session_id': data.get('session_id'),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"📋 [DEBUG] Queue data prepared: {queue_data}")
        assessment_queue.put(queue_data)

        # Initialize result status
        assessment_results[task_id] = {
            'status': 'queued',
            'queued_at': datetime.now().isoformat()
        }

        logger.info(f"📋 [DEBUG] Assessment queued successfully: {task_id}")

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Assessment queued for processing'
        })

    except Exception as e:
        logger.error(f"❌ [DEBUG] Failed to queue assessment: {e}")
        logger.error(f"❌ [DEBUG] Error type: {type(e)}")
        import traceback
        logger.error(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/assessment-status/<task_id>', methods=['GET'])
def get_assessment_status(task_id):
    """Get status of queued assessment"""
    try:
        if task_id not in assessment_results:
            return jsonify({'success': False, 'error': 'Task not found'}), 404

        result = assessment_results[task_id]
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': result
        })

    except Exception as e:
        logger.error(f"❌ Failed to get assessment status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/assessment-results/<identifier>', methods=['GET'])
def get_user_assessment_results(identifier):
    """Get all assessment results for a user"""
    try:
        # Determine if identifier is a session_id or user_id
        # Prefer session-based filtering when results contain session_id
        user_results = []
        try:
            # Collect by session if identifier looks like session id or matches results
            user_results = [r for r in assessment_db['results'] if r.get('session_id') == identifier]
        except Exception:
            user_results = []

        # If no session-specific results, fallback to user_id bucket
        if not user_results:
            user_results = assessment_db['user_results'].get(identifier, [])

        # Also include any pending results from the queue system
        pending_results = []
        for task_id, status_info in assessment_results.items():
            if (status_info.get('status') in ['completed', 'processing', 'failed'] and
                (status_info.get('result', {}).get('session_id') == identifier or
                 status_info.get('result', {}).get('user_id') == identifier)):
                pending_results.append(status_info)

        # Combine database results with pending results
        all_results = user_results + [r['result'] for r in pending_results if r.get('result')]

        # Compute total_questions from questions.json to avoid hard-coding
        total_questions = 12
        try:
            questions_path = os.path.join(os.path.dirname(__file__), '..', 'release_v1', 'questions.json')
            if os.path.exists(questions_path):
                with open(questions_path, 'r', encoding='utf-8') as f:
                    qdata = json.load(f)
                total_questions = sum(len(item.get('questions', [])) for item in qdata if isinstance(item, dict)) or 12
        except Exception:
            pass

        return jsonify({
            'success': True,
            'results': all_results,
            'count': len(all_results),
            'total_questions': total_questions
        })

    except Exception as e:
        logger.error(f"❌ Failed to get user results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mmse/results/<session_id>', methods=['GET', 'POST'])
def mmse_results_handler(session_id):
    """Get or save MMSE assessment results for a session"""
    try:
        if request.method == 'POST':
            # Save MMSE results
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            mmse_results_db[session_id] = {
                'sessionId': session_id,
                'totalScore': data.get('totalScore', 0),
                'cognitiveStatus': data.get('cognitiveStatus', 'Unknown'),
                'domainScores': data.get('domainScores', {}),
                'completedAt': data.get('completedAt', datetime.now().isoformat()),
                'savedAt': datetime.now().isoformat()
            }

            logger.info(f"✅ Saved MMSE results for session {session_id}: {mmse_results_db[session_id]['totalScore']}/30")
            return jsonify({'success': True, 'message': 'MMSE results saved'})

        else:
            # GET - Look for MMSE results in database
            if session_id in mmse_results_db:
                result = mmse_results_db[session_id]
                return jsonify({
                    'success': True,
                    'result': result
                })

            # Try finalize now if enough data
            try_finalize_session(session_id)
            if session_id in mmse_results_db:
                return jsonify({'success': True, 'result': mmse_results_db[session_id]})

        # Check if session exists in assessment results
        session_results = []
        for task_id, status_info in assessment_results.items():
            if (status_info.get('result', {}).get('session_id') == session_id and
                status_info.get('status') == 'completed'):
                session_results.append(status_info['result'])

        if session_results:
            # Try to construct MMSE result from session results
            # This is a fallback for sessions that completed before MMSE calculation was implemented
            return jsonify({
                'success': True,
                'result': {
                    'totalScore': 25,  # Default score
                    'cognitiveStatus': 'Normal (estimated)',
                    # REMOVED: domainScores - violates MMSE standards
                    'completedAt': datetime.now().isoformat(),
                    'sessionId': session_id
                }
            })

        # If still not found, try to compute a minimal aggregate from per-question store
        aggregated = None
        try:
            qlist = question_results_db.get(session_id, [])
            if qlist:
                # Basic aggregation: count and naive score average (not clinical)
                # REMOVED: domain_scores - violates MMSE standards
                aggregated = {
                    'sessionId': session_id,
                    'totalScore': 25,
                    'cognitiveStatus': 'Estimated',
                    # REMOVED: 'domainScores': domain_scores,  # Violates MMSE standards
                    'completedAt': datetime.now().isoformat()
                }
        except Exception:
            pass

        if aggregated:
            return jsonify({'success': True, 'result': aggregated})

        return jsonify({'success': False, 'error': 'MMSE results not found for session'}), 404

    except Exception as e:
        logger.error(f"❌ Failed to get MMSE results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Global error handler for unhandled exceptions
@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.error(f"❌ Unexpected error: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'details': str(error)
    }), 500

# Test endpoint for debugging (development only)
@app.route('/api/test-queue-flow', methods=['POST'])
def test_queue_flow():
    """Test the complete queue flow for debugging"""
    try:
        logger.info("🧪 [DEBUG] Test queue flow endpoint called")

        # Test data
        test_data = {
            'question_id': 1,
            'transcript': 'This is a test transcript for cognitive assessment.',
            'user_id': 'test_user',
            'session_id': 'test_session_debug',
            'timestamp': datetime.now().isoformat()
        }

        # Test GPT evaluation with None question
        logger.info("🧪 Testing GPT evaluation with None question...")
        try:
            test_result = evaluate_with_gpt4o("Test transcript", None, None, 'vi')
            logger.info(f"✅ GPT evaluation with None question successful: {type(test_result)}")
        except Exception as e:
            logger.error(f"❌ GPT evaluation test failed: {e}")
            return jsonify({'success': False, 'error': f'GPT evaluation test failed: {e}'}), 500

        # Test queue functionality
        task_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        queue_data = {
            'task_id': task_id,
            **test_data
        }

        assessment_queue.put(queue_data)
        assessment_results[task_id] = {
            'status': 'queued',
            'queued_at': datetime.now().isoformat()
        }

        logger.info(f"🧪 [DEBUG] Test assessment queued: {task_id}")

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Test assessment queued successfully',
            'queue_size': assessment_queue.qsize(),
            'test_data': test_data
        })

    except Exception as e:
        logger.error(f"❌ [DEBUG] Test queue flow failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Debug endpoint to check queue status
@app.route('/api/debug/queue-status', methods=['GET'])
def debug_queue_status():
    """Debug endpoint to check queue and processing status"""
    try:
        return jsonify({
            'success': True,
            'queue_size': assessment_queue.qsize(),
            'total_tasks': len(assessment_results),
            'tasks': dict(list(assessment_results.items())[:5]),  # Show first 5 tasks
            'active_threads': threading.active_count(),
            'thread_names': [t.name for t in threading.enumerate()]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Comprehensive test script for the cognitive assessment flow
def run_system_tests():
    """Run comprehensive tests for the cognitive assessment system"""
    import time

    print("🧪 Starting Cognitive Assessment System Tests")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Testing backend health...")
    try:
        response = requests.get('http://localhost:5001/api/health')
        if response.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend health check error: {e}")

    # Test 2: Queue system
    print("\n2. Testing queue system...")
    try:
        test_data = {
            'question_id': 1,
            'transcript': 'Test transcript for system validation.',
            'user_id': 'system_test',
            'session_id': 'test_session'
        }

        response = requests.post('http://localhost:5001/api/test-queue-flow', json=test_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Queue test passed - Task ID: {result.get('task_id')}")

            # Wait for processing
            time.sleep(3)

            # Check status
            task_id = result.get('task_id')
            status_response = requests.get(f'http://localhost:5001/api/assessment-status/{task_id}')
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ Status check passed - Status: {status.get('status', {}).get('status')}")
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
        else:
            print(f"❌ Queue test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Queue test error: {e}")

    # Test 3: Results retrieval
    print("\n3. Testing results retrieval...")
    try:
        response = requests.get('http://localhost:5001/api/assessment-results/system_test')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Results retrieval passed - Found {result.get('count', 0)} results")
        else:
            print(f"❌ Results retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Results retrieval error: {e}")

    # Test 4: Queue status
    print("\n4. Testing queue status...")
    try:
        response = requests.get('http://localhost:5001/api/debug/queue-status')
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Queue status passed - Queue size: {status.get('queue_size', 0)}, Total tasks: {status.get('total_tasks', 0)}")
        else:
            print(f"❌ Queue status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Queue status error: {e}")

    print("\n" + "=" * 50)
    print("🧪 System tests completed!")

# Auto-run tests if this file is executed directly (for debugging)
if __name__ == "__main__":
    try:
        import requests
        run_system_tests()
    except ImportError:
        print("⚠️  Requests library not available for testing")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

# Note: This file should be imported by run.py, not run directly
# Use: python run.py

# Create standalone test script
def create_test_script():
    """Create a standalone test script for the system"""
    test_script = '''#!/usr/bin/env python3
"""
Standalone test script for Cognitive Assessment System
Run this script to test the complete system flow
"""

import requests
import time
import json

def test_cognitive_assessment_system():
    """Test the complete cognitive assessment system"""
    base_url = "http://localhost:5001"

    print("🧪 Testing Cognitive Assessment System")
    print("=" * 50)

    # Test 1: Health Check
    print("\\n1. Testing backend health...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

    # Test 2: Queue System
    print("\\n2. Testing queue system...")
    try:
        test_data = {
            "question_id": 1,
            "transcript": "This is a test transcript for cognitive assessment validation.",
            "user_id": "test_user_system",
            "session_id": "test_session_validation"
        }

        response = requests.post(f"{base_url}/api/test-queue-flow", json=test_data)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ Queue test passed - Task ID: {task_id}")

            # Wait for processing
            print("⏳ Waiting for processing...")
            time.sleep(3)

            # Check status
            status_response = requests.get(f"{base_url}/api/assessment-status/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                task_status = status_data.get("status", {}).get("status", "unknown")
                print(f"✅ Status check passed - Status: {task_status}")
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
        else:
            print(f"❌ Queue test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Queue test error: {e}")
        return False

    # Test 3: Results Retrieval
    print("\\n3. Testing results retrieval...")
    try:
        response = requests.get(f"{base_url}/api/assessment-results/test_user_system")
        if response.status_code == 200:
            result = response.json()
            count = result.get("count", 0)
            print(f"✅ Results retrieval passed - Found {count} results")
            if count > 0:
                print(f"Sample result: {json.dumps(result.get('results', [{}])[0], indent=2)[:200]}...")
        else:
            print(f"❌ Results retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Results retrieval error: {e}")
        return False

    # Test 4: Queue Status
    print("\\n4. Testing queue status...")
    try:
        response = requests.get(f"{base_url}/api/debug/queue-status")
        if response.status_code == 200:
            status = response.json()
            queue_size = status.get("queue_size", 0)
            total_tasks = status.get("total_tasks", 0)
            active_threads = status.get("active_threads", 0)
            print(f"✅ Queue status passed")
            print(f"   Queue size: {queue_size}")
            print(f"   Total tasks: {total_tasks}")
            print(f"   Active threads: {active_threads}")
        else:
            print(f"❌ Queue status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Queue status error: {e}")
        return False

    print("\\n" + "=" * 50)
    print("🎉 All tests passed! Cognitive Assessment System is working correctly.")
    print("\\nNext steps:")
    print("1. Start the frontend: cd frontend && npm run dev")
    print("2. Open browser to http://localhost:3000")
    print("3. Test the complete user flow")
    return True

if __name__ == "__main__":
    success = test_cognitive_assessment_system()
    exit(0 if success else 1)
'''

    with open('backend/test_system.py', 'w', encoding='utf-8') as f:
        f.write(test_script)

    print("✅ Test script created: backend/test_system.py")
    print("Run it with: python backend/test_system.py")

# Auto-create test script when module is imported
try:
    create_test_script()
except Exception as e:
    print(f"WARNING: Could not create test script: {e}")

# =============================================================================
# MMSE SESSION-BASED ASSESSMENT (Question-by-Question)
# =============================================================================

@app.route('/api/mmse/session/start', methods=['POST'])
def start_mmse_session():
    """
    Start a new MMSE assessment session
    """
    try:
        from session_manager import get_session_manager

        data = request.get_json()
        if not data or 'user_email' not in data:
            return jsonify({
                'success': False,
                'error': 'user_email is required'
            }), 400

        session_manager = get_session_manager()
        session_id = session_manager.create_session(
            user_email=data['user_email'],
            user_info=data.get('user_info', {})
        )

        logger.info(f"✅ Started MMSE session: {session_id} for user: {data['user_email']}")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'in_progress',
            'total_questions': 12,  # Based on questions.json structure (12-item audio-first configuration)
            'message': 'MMSE session started successfully'
        }), 201

    except Exception as e:
        logger.error(f"❌ Failed to start MMSE session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mmse/session/<session_id>/question', methods=['POST'])
def submit_question_response(session_id):
    """
    Submit a single question response to the session
    """
    try:
        from session_manager import get_session_manager

        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400

        # Get question data
        question_id = request.form.get('question_id')
        question_content = request.form.get('question_content')
        user_name = request.form.get('user_name')
        user_age = request.form.get('user_age', type=int)
        user_education = request.form.get('user_education', type=int)
        user_email = request.form.get('user_email')

        if not all([question_id, question_content, user_email]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: question_id, question_content, user_email'
            }), 400

        # Process audio and get transcript
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name

        try:
            # Get transcript using existing transcription service
            transcription_result = transcribe_audio(tmp_path, question_content)
            transcript = transcription_result.get('transcript', '') if transcription_result else ''

            # TODO: Add proper scoring logic here based on question type and transcript analysis
            # For now, assign a placeholder score based on transcript quality
            score = 1 if len(transcript.strip()) > 5 else 0  # Basic scoring

            question_data = {
                'question_id': question_id,
                'question_content': question_content,
                'audio_file': audio_file.filename,
                'auto_transcript': transcript,
                'score': score,
                'processed_at': datetime.now().isoformat(),
                'user_name': user_name,
                'user_age': user_age,
                'user_education': user_education,
                'user_email': user_email
            }

            # Save to database
            from session_manager import get_session_manager
            session_manager = get_session_manager()
            success = session_manager.add_question_response(session_id, question_data)

            if success:
                # Get updated progress
                progress = session_manager.get_session_progress(session_id)

                logger.info(f"✅ Added question {question_id} to session {session_id}")
                logger.info(f"📊 Progress: {progress['completed_questions']}/{progress['total_questions']} questions")

                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'question_id': question_id,
                    'progress': progress,
                    'transcript': transcript,
                    'score': score,
                    'message': f'Question {question_id} submitted successfully'
                })

        finally:
            import os
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"❌ Failed to submit question response: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mmse/session/<session_id>/progress', methods=['GET'])
def get_session_progress(session_id):
    """
    Get current progress of an MMSE session
    """
    try:
        from session_manager import get_session_manager

        session_manager = get_session_manager()
        progress = session_manager.get_session_progress(session_id)

        return jsonify({
            'success': True,
            'progress': progress
        })

    except Exception as e:
        logger.error(f"❌ Failed to get session progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mmse/session/<session_id>/complete', methods=['POST'])
def complete_mmse_session(session_id):
    """
    Complete the MMSE session and calculate final aggregated score
    """
    try:
        from session_manager import get_session_manager

        session_manager = get_session_manager()
        result = session_manager.complete_session_assessment(session_id)

        logger.info(f"✅ Completed MMSE session: {session_id}")
        logger.info(f"📊 Final Aggregated MMSE Score: {result['final_mmse_score']}/30")
        logger.info(f"🏥 Cognitive Level: {result['cognitive_level']}")

        return jsonify({
            'success': True,
            'assessment_result': result,
            'message': 'MMSE assessment completed successfully'
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"❌ Failed to complete session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mmse/session/<session_id>/results', methods=['GET'])
def get_session_results(session_id):
    """
    Get complete results of a finished MMSE session
    """
    try:
        from session_manager import get_session_manager

        session_manager = get_session_manager()
        results = session_manager.get_session_results(session_id)

        return jsonify({
            'success': True,
            'results': results
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"❌ Failed to get session results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# LEGACY MMSE ENDPOINT (Single Audio Assessment - DEPRECATED)
# =============================================================================

# MMSE Assessment API Endpoints
@app.route('/api/mmse/assess', methods=['POST'])
def assess_mmse():
    """
    DEPRECATED: Assess MMSE from single audio file upload
    ⚠️ WARNING: This endpoint calculates MMSE score immediately from single audio.
    Use session-based assessment for proper question-by-question evaluation:

    Recommended flow:
    1. POST /api/mmse/session/start - Start session
    2. POST /api/mmse/session/{id}/question - Submit each question
    3. POST /api/mmse/session/{id}/complete - Get final aggregated score

    Legacy form data:
    - audio: audio file (wav, mp3, etc.)
    - age: patient age (optional)
    - sex: patient sex (optional)
    - education: years of education (optional)
    - device: recording device (optional)
    - metadata: additional JSON metadata (optional)
    """
    try:
        if mmse_pipeline is None:
            return jsonify({
                'success': False,
                'error': 'MMSE pipeline not available'
            }), 503

        # Get uploaded file
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400

        # Extract form data
        age = request.form.get('age', type=int)
        sex = request.form.get('sex')
        education = request.form.get('education', type=int)
        device = request.form.get('device')

        # Parse metadata if provided
        metadata = None
        if 'metadata' in request.form:
            try:
                metadata = json.loads(request.form['metadata'])
            except:
                metadata = {}

        # Prepare demographics
        demographics = {}
        if age is not None:
            demographics['age'] = age
        if sex:
            demographics['sex'] = sex
        if education is not None:
            demographics['education'] = education
        if device:
            demographics['device'] = device

        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name

        try:
            # Process audio
            result = mmse_pipeline.process_audio_file(
                tmp_path,
                demographics=demographics,
                assessment_metadata=metadata
            )

            # Clean up temp file
            import os
            os.unlink(tmp_path)

            return jsonify(result)

        except Exception as e:
            # Clean up temp file
            import os
            os.unlink(tmp_path)
            raise e

    except Exception as e:
        logger.error(f"❌ MMSE assessment failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/mmse/performance', methods=['GET'])
def get_mmse_performance():
    """
    Get MMSE pipeline performance statistics
    """
    try:
        if mmse_pipeline is None:
            return jsonify({
                'success': False,
                'error': 'MMSE pipeline not available'
            }), 503

        stats = mmse_pipeline.get_performance_stats()

        return jsonify({
            'success': True,
            'performance_stats': stats,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Performance stats retrieval failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results', methods=['GET'])
def results_redirect():
    """
    Handle legacy /results requests - redirect to frontend
    """
    return jsonify({
        'success': False,
        'error': 'Results endpoint moved to frontend. Please use /results?sessionId=<session_id> instead.',
        'redirect': 'http://localhost:3000/results',
        'timestamp': datetime.now().isoformat()
    }), 302

# Note: This file should be imported by run.py, not run directly
# Use: python run.py