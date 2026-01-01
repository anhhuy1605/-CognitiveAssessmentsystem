"""
Advanced Vietnamese Real-time Speech Transcriber
Sử dụng Whisper với VAD, noise reduction và Vietnamese language model
"""
from __future__ import annotations

import os
import sys
import subprocess
import logging
import tempfile
import json
import asyncio
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, TYPE_CHECKING
import numpy as np
from dataclasses import dataclass

# Import torch with proper handling for type hints
TORCH_AVAILABLE = False
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    # Create a mock module for type hints when torch is not installed
    class MockTorch:
        class Tensor:
            pass
    torch = MockTorch()  # type: ignore

from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcriber.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionSegment:
    """Đại diện cho một segment âm thanh được transcribe"""
    text: str
    confidence: float
    start_time: float
    end_time: float
    language_confidence: float
    is_vietnamese: bool

@dataclass
class TranscriptionConfig:
    """Cấu hình cho transcriber"""
    chunk_duration: float = 3.0  # seconds
    overlap_duration: float = 0.5  # seconds
    min_confidence: float = 0.6
    use_vad: bool = True
    denoise_audio: bool = True
    language_detection: bool = True
    real_time_callback: Optional[Callable] = None
    max_workers: int = 2

class AudioProcessor:
    """Xử lý audio với VAD và denoising"""
    
    def __init__(self):
        self.is_initialized = False
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo các thư viện audio processing"""
        try:
            # Cài đặt dependencies nếu cần
            self._install_audio_dependencies()
            
            import librosa
            import noisereduce as nr
            
            # Try to import webrtcvad (optional, requires gcc)
            try:
                import webrtcvad
                self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3
                self.has_webrtcvad = True
                logger.info("✅ Audio processor initialized with webrtcvad")
            except ImportError:
                self.vad = None
                self.has_webrtcvad = False
                logger.info("⚠️ webrtcvad not available - will use librosa fallback for VAD")
            
            self.librosa = librosa
            self.nr = nr
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize audio processor: {e}")
            self.is_initialized = False
            self.vad = None
            self.has_webrtcvad = False
    
    def _install_audio_dependencies(self):
        """Cài đặt các thư viện audio processing - chỉ chạy nếu cần"""
        packages = [
            "librosa>=0.10.0",
            "noisereduce>=3.0.0",
            # Removed webrtcvad - requires gcc and causes build issues
            "soundfile>=0.12.1",
            "scipy>=1.9.0"
        ]
        
        missing_packages = []
        
        # Check what's already installed
        for package in packages:
            try:
                module_name = package.split('>=')[0].replace('-', '_')
                __import__(module_name)
                logger.info(f"✅ {module_name} already available")
            except ImportError:
                missing_packages.append(package)
        
        # Only install missing packages
        if missing_packages:
            logger.info(f"📦 Installing {len(missing_packages)} missing audio packages: {', '.join(missing_packages)}")
            for package in missing_packages:
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package, "--quiet"
                    ], timeout=300)
                    logger.info(f"✅ {package} installed")
                except subprocess.TimeoutExpired:
                    logger.error(f"⏰ Timeout installing {package}")
                    raise
                except Exception as e:
                    logger.error(f"❌ Failed to install {package}: {e}")
                    raise
        else:
            logger.info("✅ All audio packages already available")
    
    def preprocess_audio(self, audio_path: str, config: TranscriptionConfig) -> str:
        """Tiền xử lý audio với denoising và VAD"""
        try:
            if not self.is_initialized:
                return audio_path
            
            # Load audio
            y, sr = self.librosa.load(audio_path, sr=16000, mono=True)
            
            # Denoise if enabled
            if config.denoise_audio:
                try:
                    y = self.nr.reduce_noise(y=y, sr=sr, prop_decrease=0.6, time_mask_smooth_ms=32)
                    logger.info("🔇 Audio denoised")
                except Exception as de:
                    logger.warning(f"⚠️ Denoise failed: {de}")
            
            # Voice Activity Detection
            if config.use_vad:
                try:
                    y = self._apply_vad(y, sr)
                    logger.info("🎤 VAD applied")
                except Exception as ve:
                    logger.warning(f"⚠️ VAD failed: {ve}")
            
            # Normalize audio
            y = self._normalize_audio(y)
            
            # Save processed audio
            import soundfile as sf
            processed_path = audio_path.replace('.', '_processed.')
            sf.write(processed_path, y, sr)
            
            return processed_path
            
        except Exception as e:
            logger.warning(f"⚠️ Audio preprocessing failed: {e}")
            return audio_path
    
    def _apply_vad(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Áp dụng Voice Activity Detection với timeout"""
        try:
            # Use webrtcvad if available, otherwise use librosa fallback
            if self.has_webrtcvad and self.vad is not None:
                return self._apply_webrtc_vad(audio, sr)
            else:
                # Fallback to librosa-based VAD
                return self._apply_librosa_vad(audio, sr)
        except Exception as e:
            logger.warning(f"⚠️ VAD failed: {e}")
            return audio
    
    def _apply_webrtc_vad(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply webrtcvad-based VAD"""
        import threading
        import time
        
        result = [audio]  # Default fallback
        exception = [None]
        
        def vad_worker():
            try:
                # Convert to 16-bit PCM for webrtcvad
                audio_16bit = (audio * 32767).astype(np.int16).tobytes()
                
                # Frame duration in ms
                frame_duration = 30  # ms
                frame_length = int(sr * frame_duration / 1000)
                
                # Process frames
                voiced_frames = []
                frame_count = 0
                max_frames = min(1000, len(audio_16bit) // (frame_length * 2))  # Limit frames
                
                for i in range(0, len(audio_16bit), frame_length * 2):
                    if frame_count >= max_frames:
                        break
                        
                    frame = audio_16bit[i:i + frame_length * 2]
                    if len(frame) == frame_length * 2:
                        is_speech = self.vad.is_speech(frame, sr)
                        if is_speech:
                            start_sample = i // 2
                            end_sample = start_sample + frame_length
                            voiced_frames.append(audio[start_sample:end_sample])
                    frame_count += 1
                
                if voiced_frames:
                    result[0] = np.concatenate(voiced_frames)
                else:
                    result[0] = audio  # Use original if no speech detected
                    
            except Exception as e:
                exception[0] = e
        
        # Run VAD with timeout
        thread = threading.Thread(target=vad_worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=10)  # 10 second timeout
        
        if thread.is_alive():
            logger.warning("⚠️ VAD timeout, using original audio")
            return audio
        elif exception[0]:
            logger.warning(f"⚠️ VAD failed: {exception[0]}")
            return audio
        else:
            return result[0]
    
    def _apply_librosa_vad(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Fallback VAD using librosa (no webrtcvad available)"""
        try:
            # Use librosa's voice activity detection
            intervals = self.librosa.effects.split(audio, top_db=30)
            if len(intervals) > 0:
                # Concatenate all voice intervals
                voiced_audio = np.concatenate([audio[start:end] for start, end in intervals])
                return voiced_audio if len(voiced_audio) > 0 else audio
            else:
                return audio
        except Exception as e:
            logger.warning(f"⚠️ Librosa VAD failed: {e}")
            return audio
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Chuẩn hóa audio"""
        # Remove DC offset
        audio = audio - np.mean(audio)
        
        # Normalize to [-1, 1]
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.9
        
        return audio

class VietnameseLanguageModel:
    """Vietnamese language model để cải thiện accuracy"""
    
    def __init__(self):
        self.vietnamese_words = set()
        self.no_accent_words = set()
        self.no_accent_map = {}
        self.common_phrases = {}
        self.name_entities = set()
        self.correction_rules = {}
        self.hotwords = set()
        self.context_corrector = None
        self._load_language_resources()
    
    def _load_language_resources(self):
        """Load Vietnamese language resources"""
        try:
            # Load từ điển
            tudien_path = Path(__file__).parent.parent / "tudien"
            
            vocab_files = {
                "tudien.txt": "general",
                "tudien-khongdau.txt": "no_accent", 
                "danhtu.txt": "nouns",
                "dongtu.txt": "verbs",
                "tinhtu.txt": "adjectives",
                "tenrieng.txt": "names"
            }
            
            for filename, category in vocab_files.items():
                file_path = tudien_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        words = [w.strip().lower() for w in f.readlines() if w.strip()]
                        
                        if category == "names":
                            self.name_entities.update(words)
                        elif category == "no_accent":
                            self.no_accent_words.update(words)
                        else:
                            self.vietnamese_words.update(words)
                            # Build no-accent map for restoration
                            for w in words:
                                key = self._strip_accents(w)
                                if key:
                                    self.no_accent_map.setdefault(key, set()).add(w)
            
            # Load any extra *.txt wordlists in tudien as hotwords
            if tudien_path.exists():
                for extra_file in tudien_path.glob('*.txt'):
                    if extra_file.name in vocab_files:
                        continue
                    try:
                        with open(extra_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                word = line.strip().lower()
                                if not word:
                                    continue
                                self.hotwords.add(word)
                                self.vietnamese_words.add(word)
                                key = self._strip_accents(word)
                                if key:
                                    self.no_accent_map.setdefault(key, set()).add(word)
                    except Exception:
                        pass
            
            # Load common Vietnamese phrases
            self._load_common_phrases()
            
            # Load correction rules
            self._load_correction_rules()
            
            logger.info(f"✅ Loaded {len(self.vietnamese_words)} Vietnamese words")
            logger.info(f"✅ Loaded {len(self.common_phrases)} common phrases")
            logger.info(f"✅ Loaded {len(self.no_accent_words)} no-accent words; {len(self.no_accent_map)} accent groups")
            if self.hotwords:
                logger.info(f"✅ Loaded {len(self.hotwords)} hotwords from tudien/*")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load language resources: {e}")
            self._load_fallback_vocabulary()
    
    def _load_common_phrases(self):
        """Load các cụm từ phổ biến tiếng Việt"""
        self.common_phrases = {
            # Greetings
            "xin chào": "xin chào",
            "chào bạn": "chào bạn", 
            "cảm ơn": "cảm ơn",
            "xin lỗi": "xin lỗi",
            
            # Common expressions
            "không sao": "không sao",
            "được rồi": "được rồi",
            "tất nhiên": "tất nhiên",
            "có thể": "có thể",
            "không thể": "không thể",
            
            # Questions
            "bao nhiêu": "bao nhiêu",
            "ở đâu": "ở đâu",
            "như thế nào": "như thế nào",
            "tại sao": "tại sao",
            "khi nào": "khi nào",
            
            # Time expressions
            "hôm nay": "hôm nay",
            "ngày mai": "ngày mai", 
            "hôm qua": "hôm qua",
            "tuần trước": "tuần trước",
            "tháng tới": "tháng tới",
        }
    
    
    def _load_correction_rules(self):
        """Load các quy tắc sửa lỗi phổ biến"""
        self.correction_rules = {
            # Common OCR-like errors in speech recognition
            "toi": "tôi",
            "ban": "bạn",
            "duoc": "được",
            "khong": "không",
            "mot": "một",
            "hai": "hai",
            "ba": "ba",
            "bon": "bốn", 
            "nam": "năm",
            "sau": "sáu",
            "bay": "bây",
            "tam": "tám",
            "chin": "chín",
            "muoi": "mười",
            
            # Common speech recognition errors
            "xe ở": "xin chào",
            "kem on": "cảm ơn",
            "sin loi": "xin lỗi",
            "vang a": "vâng ạ",
            "kong a": "không ạ",
        }

    @staticmethod
    def _strip_accents(text: str) -> str:
        try:
            import unicodedata
            return ''.join(c for c in unicodedata.normalize('NFD', text)
                           if unicodedata.category(c) != 'Mn')
        except Exception:
            return text
    
    def _load_fallback_vocabulary(self):
        """Load vocabulary dự phòng nếu không có file từ điển"""
        self.vietnamese_words = {
            "tôi", "bạn", "anh", "chị", "em", "ông", "bà", "con", "cháu",
            "là", "có", "không", "được", "rất", "nhiều", "ít", "lớn", "nhỏ",
            "đẹp", "xấu", "tốt", "xấu", "nhanh", "chậm", "cao", "thấp",
            "xin", "chào", "cảm", "ơn", "lỗi", "vâng", "không", "được",
            "nhà", "trường", "công", "ty", "bệnh", "viện", "siêu", "thị",
            "ăn", "uống", "ngủ", "làm", "việc", "học", "đi", "về",
            "hôm", "nay", "mai", "qua", "tuần", "tháng", "năm",
            "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười"
        }
    
    def correct_transcript(self, text: str, question: str = None) -> str:
        """Sửa lỗi transcript dựa trên language model và context"""
        try:
            if not text:
                return text
            
            # Apply traditional correction (context corrector removed)
            corrected = text.lower()
            
            # Apply phrase corrections first
            for wrong, correct in self.common_phrases.items():
                corrected = corrected.replace(wrong, correct)
            
            # Apply word-level corrections
            for wrong, correct in self.correction_rules.items():
                corrected = corrected.replace(wrong, correct)
            
            # Join spelled letters into words if they form a known term (e.g., "p h u c")
            corrected = self._join_spelled_letters(corrected)

            # Fuzzy-correct OOV tokens to nearest dictionary/hotword
            corrected = self._apply_fuzzy_dictionary_bias(corrected)

            # Capitalize names and proper nouns
            words = corrected.split()
            corrected_words = []
            
            for word in words:
                if word in self.name_entities:
                    corrected_words.append(word.capitalize())
                else:
                    corrected_words.append(word)
            
            result = " ".join(corrected_words)
            
            # Capitalize first letter
            if result:
                result = result[0].upper() + result[1:]
            
            return result
            
        except Exception as e:
            # DISABLED: Text correction error logging
            return text

    def _join_spelled_letters(self, text: str) -> str:
        tokens = text.split()
        output: List[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if len(token) == 1 and token.isalpha():
                # collect run of single letters
                j = i
                letters = []
                while j < len(tokens) and len(tokens[j]) == 1 and tokens[j].isalpha():
                    letters.append(tokens[j])
                    j += 1
                # Only join runs of >=2 letters
                if len(letters) >= 2:
                    joined = ''.join(letters).lower()
                    restored = self._restore_accents_if_possible(joined)
                    output.append(restored)
                    i = j
                    continue
            output.append(token)
            i += 1
        return ' '.join(output)

    def _restore_accents_if_possible(self, token: str) -> str:
        # If token exists as no-accent word or has accent variants, choose a known variant
        if token in self.no_accent_words and token in self.no_accent_map:
            # Prefer the most frequent or shortest variant; here choose first sorted
            candidates = sorted(self.no_accent_map[token], key=len)
            return candidates[0] if candidates else token
        # Fallback: try map even if token not listed in no_accent_words
        if token in self.no_accent_map:
            candidates = sorted(self.no_accent_map[token], key=len)
            return candidates[0] if candidates else token
        return token

    def _apply_fuzzy_dictionary_bias(self, text: str) -> str:
        import difflib
        words = text.split()
        corrected_words: List[str] = []
        vocab = self.vietnamese_words or set()
        # Merge hotwords to vocab
        if self.hotwords:
            vocab = set(vocab) | set(self.hotwords)
        for w in words:
            if w in vocab or len(w) <= 2 or any(ch.isdigit() for ch in w):
                corrected_words.append(w)
                continue
            # Try no-accent matching
            key = self._strip_accents(w)
            if key in self.no_accent_map:
                candidates = list(self.no_accent_map[key])
                # choose closest by difflib ratio on stripped
                best = max(candidates, key=lambda c: difflib.SequenceMatcher(None, key, self._strip_accents(c)).ratio())
                corrected_words.append(best)
                continue
            # Fallback: approximate match in vocab
            try:
                candidate = difflib.get_close_matches(w, vocab, n=1, cutoff=0.9)
                if candidate:
                    corrected_words.append(candidate[0])
                else:
                    corrected_words.append(w)
            except Exception:
                corrected_words.append(w)
        return ' '.join(corrected_words)
    
    def calculate_vietnamese_confidence(self, text: str) -> float:
        """Tính confidence cho Vietnamese text"""
        try:
            if not text:
                return 0.0
            
            words = text.lower().split()
            if not words:
                return 0.0
            
            # Count Vietnamese words
            vietnamese_count = sum(1 for word in words if word in self.vietnamese_words)
            
            # Count common phrases
            text_lower = text.lower()
            phrase_bonus = sum(0.2 for phrase in self.common_phrases.keys() 
                             if phrase in text_lower)
            
            base_confidence = vietnamese_count / len(words)
            final_confidence = min(base_confidence + phrase_bonus, 1.0)
            
            return round(final_confidence, 3)
            
        except Exception as e:
            logger.warning(f"⚠️ Confidence calculation failed: {e}")
            return 0.5

class RealTimeVietnameseTranscriber:
    """Real-time Vietnamese Speech Transcriber với độ chính xác cao"""
    
    def __init__(self, config: TranscriptionConfig = None):
        self.config = config or TranscriptionConfig()
        self.base_model_name = "gemini-2.5-flash"
        self.model = None
        self.processor = None
        self.is_initialized = False
        
        # Components
        self.audio_processor = AudioProcessor()
        self.language_model = VietnameseLanguageModel()
        
        # Real-time processing
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.is_processing = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Segments tracking
        self.processed_segments = []
        self.current_transcript = ""
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Gemini API does not require local model init."""
        self.is_initialized = True
        logger.info("✅ Vietnamese transcriber initialized (Gemini API)")
    
    def _install_dependencies(self):
        """No heavy deps needed for Gemini path; keep noop."""
        packages = []
        missing_packages = []
        
        # Check what's already installed
        for package in packages:
            try:
                module_name = package.split('>=')[0]
                if module_name == "torch":
                    import torch
                    logger.info("✅ torch already available")
                elif module_name == "transformers":
                    import transformers
                    logger.info("✅ transformers already available")
                elif module_name == "torchaudio":
                    import torchaudio
                    logger.info("✅ torchaudio already available")
            except ImportError:
                missing_packages.append(package)
        
        # Only install missing packages
        if missing_packages:
            logger.info(f"📦 Installing {len(missing_packages)} missing packages: {', '.join(missing_packages)}")
            for package in missing_packages:
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package, "--quiet"
                    ], timeout=300)
                    logger.info(f"✅ {package} installed")
                except subprocess.TimeoutExpired:
                    logger.error(f"⏰ Timeout installing {package}")
                    raise
                except Exception as e:
                    logger.error(f"❌ Failed to install {package}: {e}")
                    raise
        else:
            logger.info("✅ All required packages already available")
    
    def transcribe_audio_file(self, audio_path: str, language: str = 'vi', use_vietnamese_asr: bool = False, question: str = None) -> Dict[str, Any]:
        """Transcribe một file audio (Gemini-first)."""
        try:
            if not os.path.exists(audio_path):
                return self._error_result(f"Audio file not found: {audio_path}")
            
            logger.info(f"🎵 Transcribing with Gemini (Google AI): {audio_path}")
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            logger.info(f"📁 File size: {file_size / 1024:.1f} KB")
            
            # ✅ FIX: Reload API key from environment (supports hot-reload)
            # Check Gemini API key (support both GEMINI_API_KEY and GOOGLE_API_KEY)
            gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            
            # ✅ Try to reload from config.env if not found in environment
            if not gemini_api_key:
                try:
                    config_path = os.path.join(os.path.dirname(__file__), 'config.env')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith('GEMINI_API_KEY='):
                                    gemini_api_key = line.split('=', 1)[1].strip()
                                    # Set in environment for this session
                                    os.environ['GEMINI_API_KEY'] = gemini_api_key
                                    logger.info("✅ Reloaded GEMINI_API_KEY from config.env")
                                    break
                except Exception as e:
                    logger.warning(f"⚠️ Failed to reload API key from config.env: {e}")
            
            if not gemini_api_key:
                return self._error_result("Gemini API key not configured (set GEMINI_API_KEY or GOOGLE_API_KEY)")

            # ASR option removed; always use Gemini model
            transcription_model = os.getenv('GEMINI_STT_MODEL', 'gemini-2.5-flash')
            logger.info(f"🎤 Using Gemini model: {transcription_model}")
            
            # Use Gemini API for transcription
            try:
                import google.generativeai as genai
                import base64
                
                genai.configure(api_key=gemini_api_key)
                model_name = transcription_model
                model = genai.GenerativeModel(model_name)
                
                # Compute duration (best-effort)
                try:
                    import soundfile as sf
                    f = sf.SoundFile(audio_path)
                    duration = len(f) / f.samplerate
                except Exception:
                    duration = 0.0
                
                logger.info("🚀 Starting Gemini transcription...")
                start_time = time.time()
                
                # Prefer file upload API for robustness
                gemini_file = genai.upload_file(path=audio_path, mime_type="audio/wav")
                # Language-specific prompts for Gemini
                if language == 'vi':
                    logger.info("🇻🇳 Using enhanced Vietnamese-focused prompt for Gemini")
                    # Enhanced Vietnamese-focused prompt for Gemini
                    prompt = f"""
Hãy chép lại CHÍNH XÁC nội dung tiếng Việt trong audio này với độ chính xác cao nhất:

🎯 YÊU CẦU ĐẶC BIỆT CHO TIẾNG VIỆT:
- Chú ý đặc biệt đến các từ có dấu: á, à, ả, ã, ạ, é, è, ẻ, ẽ, ẹ, í, ì, ỉ, ĩ, ị, ó, ò, ỏ, õ, ọ, ú, ù, ủ, ũ, ụ, ý, ỳ, ỷ, ỹ, ỵ
- Chú ý các phụ âm đặc biệt: đ, nh, ng, ph, th, tr, ch, kh, gh, qu
- Chú ý các từ có thể bị nhầm lẫn: "tôi" (không phải "toi"), "bạn" (không phải "ban"), "được" (không phải "duoc")
- Chú ý các tên riêng Việt Nam: Nguyễn, Trần, Lê, Phạm, Hoàng, Vũ, Võ, Đặng, Bùi, Đỗ, Hồ, Ngô, Dương, Lý

🔍 HƯỚNG DẪN CHI TIẾT:
1. Lắng nghe kỹ từng âm tiết và từ
2. Phân biệt rõ các thanh điệu: ngang, huyền, hỏi, ngã, nặng, sắc
3. Chú ý ngữ cảnh để hiểu đúng từ được nói
4. Nếu không chắc chắn, hãy ghi lại âm thanh gần nhất
5. Giữ nguyên cấu trúc câu và ý nghĩa

📝 ĐỊNH DẠNG KẾT QUẢ:
- Chỉ trả về transcript thuần văn bản
- Không thêm dấu câu nếu không chắc chắn
- Không thêm từ hoặc câu không có trong audio
- Viết hoa đầu câu nếu cần thiết

Hãy bắt đầu chép lại nội dung audio:
"""
                else:
                    logger.info(f"🌍 Using standard prompt for {language.upper()} language")
                    # English or other languages
                    prompt = f"""
Please transcribe the audio content accurately in {language.upper()} language.

🎯 REQUIREMENTS:
- Listen carefully to each word and syllable
- Pay attention to pronunciation and context
- If uncertain, write the closest sound you hear
- Maintain sentence structure and meaning

📝 OUTPUT FORMAT:
- Return only plain text transcript
- Don't add punctuation unless certain
- Don't add words or sentences not in the audio
- Capitalize first letter of sentences if needed

Please start transcribing the audio content:
"""
                response = model.generate_content([gemini_file, prompt])
                
                gemini_time = time.time()
                gemini_processing_time = gemini_time - start_time
                # Backward-compatible field name expected downstream
                whisper_processing_time = gemini_processing_time
                logger.info(f"✅ Gemini transcription completed in {gemini_processing_time:.2f}s")
                
                # Extract text
                text = (getattr(response, 'text', None) or "").strip()
                confidence = 0.8  # Gemini does not provide confidence; set a reasonable default
                
                # Gemini-only transcription - NO GPT-4o improvement
                improved_text = text
                gpt4o_processing_time = 0
                used_gpt = False  # Gemini doesn't use GPT-4o
                
                # Check if text is meaningful (not just noise or silence)
                text_stripped = text.strip()
                
                # Moderately strict validation - only block explicit noise tokens
                meaningless_patterns = [
                    'silence', 'noise', 'background', 'static', 'hum', 'buzz'
                ]

                # Only block very specific marketing/marketing-related words
                suspicious_words = [
                    'ghién mì gõ', 'bỏ lỡ video hấp dẫn', 'subscribe ngay',
                    'đăng ký kênh để không bỏ lỡ', 'hãy subscribe cho kênh',
                    'youtube channel', 'facebook page', 'instagram account',
                    'tiktok creator', 'social media platform'
                ]
                
                # Check if text contains any suspicious words
                text_lower = text_stripped.lower()
                has_suspicious_content = any(word in text_lower for word in suspicious_words)
                
                # Only block very specific marketing phrases
                generic_phrases = [
                    'hãy subscribe cho kênh ghiền mì gõ để không bỏ lỡ những video hấp dẫn',
                    'subscribe ngay để không bỏ lỡ video hấp dẫn',
                    'đăng ký kênh để xem những video hấp dẫn',
                    'hẹn gặp lại các bạn trong những video tiếp theo',
                    'những video tiếp theo'
                ]

                has_generic_phrases = any(phrase in text_lower for phrase in generic_phrases)

                # Treat clearly hallucinated/marketing-like content as invalid speech
                is_suspicious = False
                # Only treat as no speech for explicit marketing phrases/words or common YT closing
                if has_suspicious_content or has_generic_phrases or ('hẹn gặp lại' in text_lower and 'video' in text_lower):
                    logger.warning("⚠️ Marketing-like transcript detected; treating as no speech")
                    text = ""
                    text_stripped = ""
                    improved_text = ""
                    confidence = 0.0
                    is_suspicious = True
                
                # Gemini transcription is used directly without GPT-4o improvement
                logger.info(f"🎯 Using Gemini transcription directly (no GPT-4o improvement)")
                
                total_processing_time = time.time() - start_time
                logger.info(f"⏱️ Total processing time: {total_processing_time:.2f}s")
                
                # Apply comprehensive language model corrections based on language
                if language == 'vi':
                    # Enhanced Vietnamese processing with multiple correction layers
                    logger.info("🎯 Applying comprehensive Vietnamese language processing...")

                    # Step 1: Basic language model correction
                    corrected_text = self.language_model.correct_transcript(improved_text, question)
                    vietnamese_confidence = self.language_model.calculate_vietnamese_confidence(corrected_text)

                    # Step 2: Apply comprehensive Vietnamese-specific corrections
                    corrected_text = self._apply_comprehensive_vietnamese_corrections(corrected_text, question)

                    # Step 3: Calculate final confidence after corrections
                    vietnamese_confidence = max(vietnamese_confidence, 0.85)  # Boost confidence for Vietnamese

                    # DISABLED: Vietnamese processing completion logging
                    # DISABLED: Final corrected text logging

                else:
                    # Enhanced English processing
                    # DISABLED: English processing logging
                    corrected_text = improved_text
                    vietnamese_confidence = confidence

                    # Apply basic English corrections
                    corrected_text = self._apply_english_specific_corrections(corrected_text)

                    # DISABLED: English processing completion logging

                # If transcript is empty after processing, use original Whisper text if available
                if not corrected_text or corrected_text.strip() == "":
                    if text and text.strip():
                        # DISABLED: Using original Whisper text logging
                        corrected_text = text.strip()
                        # Keep original confidence but lower it slightly
                        confidence = max(0.1, confidence * 0.7)
                        vietnamese_confidence = max(0.1, vietnamese_confidence * 0.7)
                    else:
                        # Only use "Không có lời thoại" if truly no content
                        logger.warning("⚠️ No speech content detected")
                        corrected_text = "Không có lời thoại"
                        confidence = 0.0
                        vietnamese_confidence = 0.0
                
                return {
                    'success': True,
                    'transcript': corrected_text,
                    'confidence': confidence,
                    'vietnamese_confidence': vietnamese_confidence,
                    'segments': 1,
                    'duration': duration,
                    'model': transcription_model + (' + gpt-4o' if used_gpt else ''),
                    'language': language,
                    'use_vietnamese_asr': False,
                    'processing_time': total_processing_time,
                    'whisper_time': whisper_processing_time,
                    'gpt4o_time': gpt4o_processing_time,
                    'original_text': text,
                    'improved_text': improved_text,
                    'is_suspicious': is_suspicious
                }
                
            except Exception as gemini_error:
                error_str = str(gemini_error).lower()
                is_quota_error = (
                    'quota' in error_str or 
                    '429' in error_str or 
                    'rate limit' in error_str or
                    'exceeded' in error_str
                )
                
                if is_quota_error:
                    logger.error(f"🚨 Gemini quota/rate limit exceeded: {gemini_error}")
                    logger.warning("⚠️ Skipping transcription due to quota limit (Whisper fallback disabled)")
                    return self._error_result(f"Gemini quota exceeded: {gemini_error}")
                
                logger.error(f"❌ Gemini transcription failed: {gemini_error}")
                return self._error_result(f"Gemini transcription failed: {gemini_error}")
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return self._error_result(str(e))
    

    
    def _improve_with_gpt4o(self, text: str, language: str = 'vi') -> str:
        """
        DEPRECATED: GPT-4o improvement disabled.
        Transcription uses Gemini only, MMSE evaluation uses GPT-4o only.
        This method now returns the original text unchanged.
        """
        # GPT-4o is no longer used for transcript improvement
        # Return original text unchanged
        logger.info("⏭️ GPT-4o transcript improvement disabled - using Gemini transcription directly")
        return text
    
    def _chunk_audio(self, waveform: torch.Tensor, sample_rate: int) -> List[torch.Tensor]:
        """Chia audio thành chunks để xử lý tốt hơn"""
        duration = len(waveform) / sample_rate
        
        # Nếu audio ngắn hơn 10 giây, xử lý toàn bộ một lần
        if duration <= 10.0:
            logger.info(f"🎵 Audio duration {duration:.1f}s <= 10s, processing as single chunk")
            return [waveform]
        
        # Nếu audio dài hơn, chia thành chunks
        chunk_samples = int(self.config.chunk_duration * sample_rate)
        overlap_samples = int(self.config.overlap_duration * sample_rate)
        
        chunks = []
        start = 0
        max_chunks = 3  # Giảm xuống 3 chunks để tránh treo
        
        while start < len(waveform) and len(chunks) < max_chunks:
            end = min(start + chunk_samples, len(waveform))
            chunk = waveform[start:end]
            
            # Ensure minimum chunk size - tăng lên 1 giây
            if len(chunk) > sample_rate * 1.0:  # At least 1 second
                chunks.append(chunk)
                logger.info(f"📦 Created chunk {len(chunks)}: {len(chunk)} samples ({len(chunk)/sample_rate:.1f}s)")
            
            start = end - overlap_samples
            if start >= len(waveform):
                break
        
        logger.info(f"🎯 Total chunks created: {len(chunks)}")
        return chunks
    
    def _transcribe_segment(self, audio_segment: torch.Tensor, sample_rate: int) -> Dict[str, Any]:
        """Transcribe một segment audio - ĐƠN GIẢN HÓA"""
        try:
            import torch
            import time
            import threading
            
            logger.info(f"🎵 Processing segment: {len(audio_segment)} samples")
            
            # Prepare input
            inputs = self.processor(
                audio_segment.numpy(),
                sampling_rate=sample_rate,
                return_tensors="pt"
            )
            
            logger.info("✅ Input prepared, starting generation...")
            
            # Generate transcription với timeout dài hơn và error handling tốt hơn
            start_time = time.time()
            
            result = None
            error = None
            
            def generate_with_timeout():
                nonlocal result, error
                try:
                    with torch.no_grad():
                        result = self.model.generate(
                            inputs["input_features"],
                            language="vi",
                            task="transcribe",
                            max_length=128,  # Rất ngắn
                            num_beams=1,     # Nhanh nhất
                            temperature=0.0,
                            do_sample=False,
                            max_time=25.0    # Tăng timeout lên 25 giây
                        )
                except Exception as e:
                    error = e
            
            # Start generation in a separate thread
            thread = threading.Thread(target=generate_with_timeout)
            thread.daemon = True
            thread.start()
            
            # Wait for completion or timeout
            thread.join(timeout=60)  # Tăng timeout lên 60 giây
            
            if thread.is_alive():
                logger.error("❌ Transcription timeout after 60 seconds")
                raise TimeoutError("Transcription timeout after 60 seconds")
            
            if error:
                raise error
            
            generated_ids = result
            
            end_time = time.time()
            logger.info(f"✅ Generation completed in {end_time - start_time:.2f}s")
            
            # Decode
            transcription = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            # Calculate confidence
            confidence = self._estimate_confidence(transcription, audio_segment)
            
            return {
                'success': True,
                'text': transcription.strip(),
                'confidence': confidence,
                'duration': len(audio_segment) / sample_rate
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Segment transcription failed: {e}")
            return {
                'success': False,
                'text': '',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _combine_segments(self, segments: List[Dict]) -> str:
        """Kết hợp các segments thành transcript hoàn chỉnh"""
        texts = []
        
        for segment in segments:
            text = segment.get('text', '').strip()
            if text and segment.get('confidence', 0) >= self.config.min_confidence:
                texts.append(text)
        
        # Join and clean up
        combined = ' '.join(texts)
        
        # Remove duplicate words at boundaries
        words = combined.split()
        cleaned_words = []
        
        for i, word in enumerate(words):
            if i == 0 or word != words[i-1]:
                cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    def _estimate_confidence(self, text: str, audio: torch.Tensor) -> float:
        """Ước tính confidence score"""
        try:
            # Base confidence từ text quality
            text_confidence = self.language_model.calculate_vietnamese_confidence(text)
            
            # Audio quality score (simplified)
            audio_quality = min(1.0, torch.std(audio).item() * 2)
            
            # Combine scores
            final_confidence = (text_confidence * 0.8 + audio_quality * 0.2)
            
            return round(final_confidence, 3)
            
        except Exception:
            return 0.5
    
    def start_real_time_transcription(self, callback: Callable = None):
        """Bắt đầu transcription real-time"""
        if callback:
            self.config.real_time_callback = callback
        
        self.is_processing = True
        processing_thread = threading.Thread(target=self._process_audio_queue)
        processing_thread.daemon = True
        processing_thread.start()
        
        logger.info("🎙️ Real-time transcription started")
    
    def stop_real_time_transcription(self):
        """Dừng transcription real-time"""
        self.is_processing = False
        logger.info("⏹️ Real-time transcription stopped")
    
    def add_audio_chunk(self, audio_data: bytes, timestamp: float = None):
        """Thêm audio chunk vào queue để xử lý"""
        if timestamp is None:
            timestamp = time.time()
        
        self.audio_queue.put((audio_data, timestamp))
    
    def _process_audio_queue(self):
        """Xử lý audio queue trong background"""
        while self.is_processing:
            try:
                if not self.audio_queue.empty():
                    audio_data, timestamp = self.audio_queue.get(timeout=1.0)
                    
                    # Process audio chunk
                    future = self.executor.submit(self._process_audio_chunk, audio_data, timestamp)
                    
                else:
                    time.sleep(0.1)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Audio queue processing error: {e}")
    
    def _process_audio_chunk(self, audio_data: bytes, timestamp: float):
        """Xử lý một audio chunk"""
        try:
            # Convert bytes to audio file (temporary)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            # Transcribe
            result = self.transcribe_audio_file(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
            
            # Call callback if available
            if self.config.real_time_callback and result['success']:
                self.config.real_time_callback(result, timestamp)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audio chunk processing failed: {e}")
            return self._error_result(str(e))
    
    def _apply_comprehensive_vietnamese_corrections(self, text: str, question: str = None) -> str:
        """Apply comprehensive Vietnamese corrections in optimal order with context awareness"""
        if not text:
            return text

        try:
            # DISABLED: Comprehensive corrections logging

            # Step 1: Normalize text
            corrected_text = text.lower().strip()

            # Step 2: ALL CORRECTIONS DISABLED - Return text as-is
            # DISABLED: All corrections logging
            corrected_text = text.lower().strip()

            # DISABLED: Skip all correction steps to preserve original transcript
            # corrected_text = self._apply_single_letter_spelling_corrections(corrected_text)
            # corrected_text = self._apply_problematic_words_corrections(corrected_text)
            # corrected_text = self._apply_pronunciation_corrections(corrected_text)
            # corrected_text = self._apply_regional_corrections(corrected_text)
            # corrected_text = self._apply_common_asr_corrections(corrected_text)
            # corrected_text = self._apply_name_database_corrections(corrected_text)
            # corrected_text = self._apply_spelling_to_names(corrected_text)
            # corrected_text = self._apply_vietnamese_spelling_corrections(corrected_text)
            # corrected_text = self._apply_context_improvements(corrected_text)
            # corrected_text = self._apply_specialized_corrections(corrected_text)
            # corrected_text = self._apply_final_formatting(corrected_text, text)
            # DISABLED: Final formatting logging

            # DISABLED: Comprehensive corrections completion logging
            return corrected_text

        except Exception as e:
            # DISABLED: Comprehensive corrections error logging
            return text

    def _apply_name_database_corrections(self, text: str) -> str:
        """Apply name corrections trained from Vietnamese Name Database"""
        try:
            # Load name database if not already loaded
            if not hasattr(self, '_name_corrections_cache'):
                self._name_corrections_cache = self._load_vietnamese_name_database()
                # DISABLED: Name corrections loaded logging

            name_corrections = self._name_corrections_cache

            # Debug: Show first few corrections
            if len(name_corrections) > 0:
                sample_corrections = list(name_corrections.items())[:3]
                # DISABLED: Sample corrections logging

            original_text = text

            # Apply name corrections to full names first (more specific)
            for unsigned, signed in name_corrections.items():
                if len(unsigned.split()) >= 2:  # Only full names (surname + given name)
                    text = text.replace(unsigned, signed)
                    if text != original_text:
                        # DISABLED: Full name corrected logging
                        pass

            # Then apply single name corrections
            words = text.split()
            corrected_words = []

            for word in words:
                # Check if single word needs name correction
                if word in name_corrections:
                    corrected_words.append(name_corrections[word])
                    # DISABLED: Single name corrected logging
                else:
                    corrected_words.append(word)

            result = ' '.join(corrected_words)

            if result != original_text:
                # DISABLED: Name corrections applied logging
                pass
            else:
                # DISABLED: No name corrections logging
                pass

            return result

        except Exception as e:
            # DISABLED: Name database corrections error logging
            return text

    def _apply_single_letter_spelling_corrections(self, text: str) -> str:
        """Apply corrections for single letter spelling pronunciations - DISABLED"""
        # DISABLED: Return text as-is without spelling corrections
        return text

        try:
            # Simple word replacements for common misrecognitions
            spelling_corrections = {
                # === NGUYÊN ÂM (Vowels) ===

                # A variations
                "a": "A", "à": "A", "á": "A", "ả": "A", "ã": "A", "ạ": "A",
                "ă": "A", "ằ": "A", "ắ": "A", "ẳ": "A", "ẵ": "A", "ặ": "A",
                "â": "A", "ầ": "A", "ấ": "A", "ẩ": "A", "ẫ": "A", "ậ": "A",

                # E variations
                "e": "E", "è": "E", "é": "E", "ẻ": "E", "ẽ": "E", "ẹ": "E",
                "ê": "E", "ề": "E", "ế": "E", "ể": "E", "ễ": "E", "ệ": "E",

                # I variations
                "i": "I", "ì": "I", "í": "I", "ỉ": "I", "ĩ": "I", "ị": "I",

                # O variations
                "o": "O", "ò": "O", "ó": "O", "ỏ": "O", "õ": "O", "ọ": "O",
                "ô": "O", "ồ": "O", "ố": "O", "ổ": "O", "ỗ": "O", "ộ": "O",
                "ơ": "O", "ờ": "O", "ớ": "O", "ở": "O", "ỡ": "O", "ợ": "O",

                # U variations
                "u": "U", "ù": "U", "ú": "U", "ủ": "U", "ũ": "U", "ụ": "U",
                "ư": "U", "ừ": "U", "ứ": "U", "ử": "U", "ữ": "U", "ự": "U",

                # Y variations
                "y": "Y", "ỳ": "Y", "ý": "Y", "ỷ": "Y", "ỹ": "Y", "ỵ": "Y",

                # === PHỤ ÂM (Consonants) ===

                # B variations
                "bê": "B", "bế": "B", "bé": "B", "bì": "B", "bí": "B", "bè": "B", "bé": "B",
                "b": "B", "bờ": "B", "bơ": "B", "bó": "B", "bớ": "B", "be": "B", "bê": "B",

                # C variations
                "cờ": "C", "co": "C", "cơ": "C", "có": "C", "cớ": "C", "cà": "C", "cá": "C",
                "c": "C", "cê": "C", "cé": "C", "cì": "C", "cí": "C", "ce": "C", "ci": "C",

                # D variations (regular D)
                "dê": "D", "dé": "D", "dè": "D", "dì": "D", "dí": "D", "dờ": "D", "dơ": "D",
                "d": "D", "do": "D", "dó": "D", "dớ": "D", "de": "D", "di": "D", "dê": "D",

                # Đ variations (special D with bar)
                "đê": "Đ", "đế": "Đ", "đé": "Đ", "đè": "Đ", "đì": "Đ", "đí": "Đ", "đờ": "Đ", "đơ": "Đ",
                "đ": "Đ", "đo": "Đ", "đó": "Đ", "đớ": "Đ", "đe": "Đ", "đi": "Đ", "đê": "Đ",

                # G variations
                "gờ": "G", "gơ": "G", "gó": "G", "gớ": "G", "gà": "G", "gá": "G", "gì": "G",
                "g": "G", "go": "G", "gê": "G", "gé": "G", "ge": "G", "gi": "G", "gê": "G",

                # H variations
                "hê": "H", "hế": "H", "hé": "H", "hì": "H", "hí": "H", "hè": "H", "hé": "H",
                "hô": "H", "hố": "H", "hớ": "H", "hà": "H", "há": "H", "hờ": "H", "hơ": "H",
                "h": "H", "ho": "H", "hu": "H", "hú": "H", "hủ": "H", "hứ": "H", "he": "H", "hi": "H",

                # K variations
                "kờ": "K", "kơ": "K", "kó": "K", "kớ": "K", "kà": "K", "ká": "K", "kì": "K",
                "k": "K", "ko": "K", "kê": "K", "ké": "K", "ke": "K", "ki": "K", "kê": "K",

                # L variations (removed "là" and "lá" to avoid confusion with common Vietnamese words)
                "lờ": "L", "lơ": "L", "ló": "L", "lớ": "L", "lì": "L",
                "l": "L", "lo": "L", "lê": "L", "lé": "L", "le": "L", "li": "L", "lê": "L",

                # M variations
                "mờ": "M", "mơ": "M", "mó": "M", "mớ": "M", "mà": "M", "má": "M", "mì": "M",
                "m": "M", "mo": "M", "mê": "M", "mé": "M", "me": "M", "mi": "M", "mê": "M",

                # N variations
                "nờ": "N", "nơ": "N", "nó": "N", "nớ": "N", "nà": "N", "ná": "N", "nì": "N",
                "n": "N", "no": "N", "nê": "N", "né": "N", "ne": "N", "ni": "N", "nê": "N",

                # P variations
                "pê": "P", "pế": "P", "pé": "P", "pì": "P", "pí": "P", "pè": "P", "pé": "P",
                "p": "P", "pờ": "P", "pơ": "P", "pó": "P", "pớ": "P", "pe": "P", "pi": "P",

                # Q variations
                "qờ": "Q", "qơ": "Q", "qó": "Q", "qớ": "Q", "qà": "Q", "qá": "Q", "qì": "Q",
                "q": "Q", "qo": "Q", "qê": "Q", "qé": "Q", "qe": "Q", "qi": "Q", "qê": "Q",

                # R variations
                "rờ": "R", "rơ": "R", "ró": "R", "rớ": "R", "rà": "R", "rá": "R", "rì": "R",
                "r": "R", "ro": "R", "rê": "R", "ré": "R", "re": "R", "ri": "R", "rê": "R",

                # S variations
                "sờ": "S", "sơ": "S", "só": "S", "sớ": "S", "sà": "S", "sá": "S", "sì": "S",
                "s": "S", "so": "S", "sê": "S", "sé": "S", "se": "S", "si": "S", "sê": "S",

                # T variations
                "tờ": "T", "tơ": "T", "tó": "T", "tớ": "T", "tà": "T", "tá": "T", "tì": "T",
                "t": "T", "to": "T", "tê": "T", "té": "T", "te": "T", "ti": "T", "tê": "T",

                # V variations
                "vờ": "V", "vơ": "V", "vó": "V", "vớ": "V", "và": "V", "vá": "V", "vì": "V",
                "v": "V", "vo": "V", "vê": "V", "vé": "V", "ve": "V", "vi": "V", "vê": "V",

                # X variations
                "xờ": "X", "xơ": "X", "xó": "X", "xớ": "X", "xà": "X", "xá": "X", "xì": "X",
                "x": "X", "xo": "X", "xê": "X", "xé": "X", "xe": "X", "xi": "X", "xê": "X",
            }

            corrected_text = text.lower()

            # Apply single word replacements
            for wrong, correct in spelling_corrections.items():
                # Handle words with spaces around
                corrected_text = corrected_text.replace(f" {wrong} ", f" {correct} ")
                corrected_text = corrected_text.replace(f" {wrong}.", f" {correct}.")
                corrected_text = corrected_text.replace(f" {wrong},", f" {correct},")
                corrected_text = corrected_text.replace(f" {wrong}!", f" {correct}!")
                corrected_text = corrected_text.replace(f" {wrong}?", f" {correct}?")

                # Handle words at the beginning of text
                if corrected_text.startswith(f"{wrong} "):
                    corrected_text = corrected_text.replace(f"{wrong} ", f"{correct} ", 1)
                if corrected_text == wrong:
                    corrected_text = correct

            # Handle phrase replacements - Common spelling patterns
            phrase_corrections = {
                # Common spelling patterns for names
                "bê hét hô cơ": "B H O C",
                "bé hét hu cờ": "B H U C",
                "bê hét hu cờ": "B H U C",
                "pê hát u cờ": "P H U C",
                "pê hát u cơ": "P H U C",
                "pê hét u cờ": "P H U C",
                "pê hét u cơ": "P H U C",

                # Additional common patterns
                "ê hát": "H A",
                "ê hát u": "H U",
                "ê hát u cờ": "H U C",
                "ê hét": "H E",
                "ê hét u": "H U",
                "ê hét u cờ": "H U C",

                # More comprehensive patterns for all letters
                "dê": "D",
                "gờ": "G",
                "kờ": "K",
                "lờ": "L",
                "mờ": "M",
                "nờ": "N",
                "qờ": "Q",
                "rờ": "R",
                "sờ": "S",
                "tờ": "T",
                "vờ": "V",
                "xờ": "X",

                # Combined patterns for spelling sequences
                "bê ê": "B E",
                "cờ ê": "C E",
                "dê ê": "D E",
                "gờ ê": "G E",
                "pê ê": "P E",
                "tờ ê": "T E",
                "vờ ê": "V E",

                "bê a": "B A",
                "cờ a": "C A",
                "dê a": "D A",
                "gờ a": "G A",
                "pê a": "P A",
                "tờ a": "T A",
                "vờ a": "V A",

                "bê i": "B I",
                "cờ i": "C I",
                "dê i": "D I",
                "gờ i": "G I",
                "pê i": "P I",
                "tờ i": "T I",
                "vờ i": "V I",

                "bê o": "B O",
                "cờ o": "C O",
                "dê o": "D O",
                "gờ o": "G O",
                "pê o": "P O",
                "tờ o": "T O",
                "vờ o": "V O",

                "bê u": "B U",
                "cờ u": "C U",
                "dê u": "D U",
                "gờ u": "G U",
                "pê u": "P U",
                "tờ u": "T U",
                "vờ u": "V U",

                "bê y": "B Y",
                "cờ y": "C Y",
                "dê y": "D Y",
                "gờ y": "G Y",
                "pê y": "P Y",
                "tờ y": "T Y",
                "vờ y": "V Y",

                # Complex spelling sequences
                "bê cờ dờ": "B C D",
                "pê hờ u cờ": "P H U C",
                "tờ ê o": "T E O",
                "vờ ă n": "V A N",
                "gờ i ă n g": "G I A N G",
            }

            for wrong_phrase, correct_phrase in phrase_corrections.items():
                corrected_text = corrected_text.replace(wrong_phrase, correct_phrase)

            if corrected_text != text.lower():
                # DISABLED: Single letter spelling corrections logging
                pass

            return corrected_text

        except Exception as e:
            # DISABLED: Single letter spelling corrections error logging
            return text

    def _apply_problematic_words_corrections(self, text: str) -> str:
        """Apply corrections for words that commonly cause conflicts first"""
        try:
            problematic_corrections = {
                # Words that conflict with other corrections - handle these first
                " toi ": " tôi ",  # Ensure space to avoid conflicts
                " toi.": " tôi.",  # Handle end of sentence
                " toi!": " tôi!",  # Handle exclamation
                " toi?": " tôi?",  # Handle question
                " toi,": " tôi,",  # Handle comma

                " ban ": " bạn ",  # Ensure space to avoid conflicts
                " ban.": " bạn.",  # Handle end of sentence
                " ban!": " bạn!",  # Handle exclamation
                " ban?": " bạn?",  # Handle question
                " ban,": " bạn,",  # Handle comma

                " viet nam ": " Việt Nam ",  # Proper noun
                " troi ": " trời ",  # Weather/sky
                " thich ": " thích ",  # Like/enjoy
                " muon ": " muốn ",  # Want
                " cam thay ": " cảm thấy ",  # Feel
                " rat vui ": " rất vui ",  # Very happy
                " bac si ": " bác sĩ ",  # Doctor
                " benh vien ": " bệnh viện ",  # Hospital
                " dau dau ": " đau đầu ",  # Headache
                " uong thuoc ": " uống thuốc ",  # Take medicine

                # Numbers that might conflict
                " mot ": " một ",
                " hai ": " hai ",
                " nam ": " năm ",
                " tuoi ": " tuổi ",

                # Additional common problematic words
                " co gai ": " cô gái ",  # Avoid "cơ gai"
                " co giao ": " cô giáo ",  # Avoid "cơ giao"
                " nguoi ban ": " người bạn ",  # Avoid conflicts
                " ban than ": " bạn thân ",  # Avoid conflicts
            }

            for incorrect, correct in problematic_corrections.items():
                text = text.replace(incorrect, correct)

            return text

        except Exception as e:
            # DISABLED: Problematic words corrections error logging
            return text

    def _load_vietnamese_name_database(self):
        """Load Vietnamese name database for training name corrections"""
        try:
            name_corrections = {}
            name_db_path = os.path.join(os.path.dirname(__file__), '..', 'vietnamese-namedb')

            # Load boy names
            boy_file = os.path.join(name_db_path, 'boy.txt')
            if os.path.exists(boy_file):
                with open(boy_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        name = line.strip()
                        if name:
                            # Create multiple mappings for better matching
                            unsigned_name = self._convert_to_unsigned(name)
                            lowercase_name = name.lower()
                            lowercase_unsigned = unsigned_name.lower()

                            # Store all variations
                            if unsigned_name != name:
                                name_corrections[unsigned_name] = name
                            if lowercase_name != name:
                                name_corrections[lowercase_name] = name
                            if lowercase_unsigned != name:
                                name_corrections[lowercase_unsigned] = name

                            # Also store the original name for exact matches
                            name_corrections[name] = name

            # Load girl names
            girl_file = os.path.join(name_db_path, 'girl.txt')
            if os.path.exists(girl_file):
                with open(girl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        name = line.strip()
                        if name:
                            unsigned_name = self._convert_to_unsigned(name)
                            lowercase_name = name.lower()
                            lowercase_unsigned = unsigned_name.lower()

                            # Store all variations
                            if unsigned_name != name:
                                name_corrections[unsigned_name] = name
                            if lowercase_name != name:
                                name_corrections[lowercase_name] = name
                            if lowercase_unsigned != name:
                                name_corrections[lowercase_unsigned] = name

                            # Also store the original name for exact matches
                            name_corrections[name] = name

            # Load JSON database for full names
            json_file = os.path.join(name_db_path, 'uit_member.json')
            if os.path.exists(json_file):
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    members = json.load(f)
                    for member in members:
                        if 'full_name' in member:
                            full_name = member['full_name']
                            unsigned_full_name = self._convert_to_unsigned(full_name)
                            lowercase_full_name = full_name.lower()
                            lowercase_unsigned_full = unsigned_full_name.lower()

                            # Store all variations for full names
                            if unsigned_full_name != full_name:
                                name_corrections[unsigned_full_name] = full_name
                            if lowercase_full_name != full_name:
                                name_corrections[lowercase_full_name] = full_name
                            if lowercase_unsigned_full != full_name:
                                name_corrections[lowercase_unsigned_full] = full_name

                        # Handle first and last names
                        if 'first_name' in member and 'last_name' in member:
                            first_name = member['first_name']
                            last_name = member['last_name']

                            # Create full name from parts
                            if last_name and first_name:
                                combined_name = f"{last_name} {first_name}"
                                unsigned_combined = self._convert_to_unsigned(combined_name)
                                lowercase_combined = combined_name.lower()

                                if unsigned_combined != combined_name:
                                    name_corrections[unsigned_combined] = combined_name
                                if lowercase_combined != combined_name:
                                    name_corrections[lowercase_combined] = combined_name

            # Add some common name corrections manually for better coverage
            manual_corrections = {
                "nguyen van minh": "Nguyễn Văn Minh",
                "tran thi mai": "Trần Thị Mai",
                "le hoang quan": "Lê Hoàng Quân",
                "pham van duc": "Phạm Văn Đức",
                "hoang thi lan": "Hoàng Thị Lan",
                "nguyen van nam": "Nguyễn Văn Nam",
                "tran thi thu": "Trần Thị Thu",
                "le thi hoa": "Lê Thị Hoa",
                "pham thi linh": "Phạm Thị Linh",
                "hoang van tung": "Hoàng Văn Tùng",
                "nguyen van anh": "Nguyễn Văn Anh",
                "tran thi linh": "Trần Thị Linh",
            }

            for unsigned, signed in manual_corrections.items():
                name_corrections[unsigned] = signed

            # DISABLED: Vietnamese Name DB loaded logging
            return name_corrections

        except Exception as e:
            logger.warning(f"⚠️ Failed to load Vietnamese name database: {e}")
            return {}

    def _convert_to_unsigned(self, text: str) -> str:
        """Convert Vietnamese text with accents to unsigned version"""
        try:
            # Vietnamese character mapping
            vietnamese_map = {
                'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
                'đ': 'd',
                'Á': 'A', 'À': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
                'Ă': 'A', 'Ắ': 'A', 'Ằ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
                'Â': 'A', 'Ấ': 'A', 'Ầ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
                'É': 'E', 'È': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
                'Ê': 'E', 'Ế': 'E', 'Ề': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
                'Í': 'I', 'Ì': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
                'Ó': 'O', 'Ò': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
                'Ô': 'O', 'Ố': 'O', 'Ồ': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
                'Ơ': 'O', 'Ớ': 'O', 'Ờ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
                'Ú': 'U', 'Ù': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
                'Ư': 'U', 'Ứ': 'U', 'Ừ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
                'Ý': 'Y', 'Ỳ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
                'Đ': 'D'
            }

            result = text
            for accented, plain in vietnamese_map.items():
                result = result.replace(accented, plain)

            return result

        except Exception as e:
            logger.warning(f"⚠️ Failed to convert to unsigned: {e}")
            return text

    def _find_signed_equivalent(self, unsigned_name: str) -> str:
        """Find signed equivalent from name database"""
        try:
            # This is a simplified version - in practice you'd want to search the database
            # For now, return None and let the main corrections handle it
            return None
        except Exception as e:
            logger.warning(f"⚠️ Failed to find signed equivalent: {e}")
            return None

    def _create_spelling_pronunciation(self, name: str) -> str:
        """Create spelling pronunciation for Vietnamese names (e.g., 'Phúc' → 'P H U C Phúc')"""
        if not name or len(name.strip()) == 0:
            return name

        try:
            # Convert to uppercase for spelling, but keep original for reference
            name_upper = name.upper()
            name_original = name

            # Create spelling by breaking down each character
            spelling_parts = []

            for char in name_upper:
                if char.isalpha():
                    # For Vietnamese characters with diacritics, we need special handling
                    if char in ['Á', 'À', 'Ả', 'Ã', 'Ạ']:
                        spelling_parts.append('A')
                    elif char in ['Ă', 'Ắ', 'Ằ', 'Ẳ', 'Ẵ', 'Ặ']:
                        spelling_parts.append('A')
                    elif char in ['Â', 'Ấ', 'Ầ', 'Ẩ', 'Ẫ', 'Ậ']:
                        spelling_parts.append('A')
                    elif char in ['É', 'È', 'Ẻ', 'Ẽ', 'Ẹ']:
                        spelling_parts.append('E')
                    elif char in ['Ê', 'Ế', 'Ề', 'Ể', 'Ễ', 'Ệ']:
                        spelling_parts.append('E')
                    elif char in ['Í', 'Ì', 'Ỉ', 'Ĩ', 'Ị']:
                        spelling_parts.append('I')
                    elif char in ['Ó', 'Ò', 'Ỏ', 'Õ', 'Ọ']:
                        spelling_parts.append('O')
                    elif char in ['Ô', 'Ố', 'Ồ', 'Ổ', 'Ỗ', 'Ộ']:
                        spelling_parts.append('O')
                    elif char in ['Ơ', 'Ớ', 'Ờ', 'Ở', 'Ỡ', 'Ợ']:
                        spelling_parts.append('O')
                    elif char in ['Ú', 'Ù', 'Ủ', 'Ũ', 'Ụ']:
                        spelling_parts.append('U')
                    elif char in ['Ư', 'Ứ', 'Ừ', 'Ử', 'Ữ', 'Ự']:
                        spelling_parts.append('U')
                    elif char in ['Ý', 'Ỳ', 'Ỷ', 'Ỹ', 'Ỵ']:
                        spelling_parts.append('Y')
                    elif char == 'Đ':
                        spelling_parts.append('D')
                    else:
                        # Regular ASCII letters
                        spelling_parts.append(char)
                elif char.isspace():
                    spelling_parts.append(' ')
                # Skip other characters like punctuation

            # Join spelling parts
            spelling = ' '.join(spelling_parts).strip()

            # Return format: "P H U C Phúc"
            if spelling and spelling != name_upper:
                return f"{spelling} {name_original}"
            else:
                return name_original

        except Exception as e:
            logger.warning(f"⚠️ Failed to create spelling pronunciation for '{name}': {e}")
            return name

    def _apply_spelling_to_names(self, text: str) -> str:
        """Apply spelling pronunciation to names found in text - DISABLED"""
        # DISABLED: Return text as-is without spelling corrections for names
        return text

        try:
            # Common patterns to identify names in Vietnamese text
            name_indicators = [
                "tên là", "tên tôi là", "tôi tên là",
                "bạn tên là", "cô ấy tên là", "anh ấy tên là",
                "chị tên là", "em tên là", "bác sĩ", "giáo viên",
                "cô giáo", "thầy", "cô", "bà", "ông", "cháu",
                "con", "chị", "em", "anh", "chị"
            ]

            result = text
            words = text.split()

            for i, word in enumerate(words):
                # Special handling for single letter spelling patterns
                if len(word) == 1 and word.isupper():
                    # This might be a letter in spelling (P, H, U, C)
                    context_before = ' '.join(words[max(0, i-2):i])
                    context_after = ' '.join(words[i+1:min(len(words), i+3)])

                    # Check if this looks like a spelling pattern
                    is_spelling_pattern = (
                        any(letter in context_before.upper() for letter in ['P', 'H', 'U', 'C', 'B', 'A', 'E', 'I', 'O']) or
                        any(letter in context_after.upper() for letter in ['P', 'H', 'U', 'C', 'B', 'A', 'E', 'I', 'O'])
                    )

                    if is_spelling_pattern:
                        # Convert single letter to proper spelling format
                        spelled_name = f"{word} {word}"
                        result = result.replace(word, spelled_name, 1)
                        logger.debug(f"🔤 Single letter spelling: '{word}' → '{spelled_name}'")
                        continue

                # Skip very short words and common Vietnamese words
                if len(word) < 2 or len(word) > 10:
                    continue

                # Check if word looks like a Vietnamese name
                if self._is_likely_vietnamese_name(word):
                    # Check context to see if it's a name
                    context_before = ' '.join(words[max(0, i-3):i])
                    context_after = ' '.join(words[i+1:min(len(words), i+4)])

                    # Check if context suggests this is a name
                    is_name_context = any(indicator in f"{context_before} {context_after}"
                                        for indicator in name_indicators)

                    # More restrictive conditions for adding spelling
                    should_add_spelling = (
                        is_name_context or  # Clear name context
                        (len(word) >= 3 and word[0].isupper() and i > 0) or  # Longer capitalized words after first position
                        self._has_vietnamese_diacritics(word)  # Words with Vietnamese diacritics
                    )

                    if should_add_spelling:
                        spelled_name = self._create_spelling_pronunciation(word)
                        if spelled_name != word:
                            result = result.replace(word, spelled_name, 1)
                            logger.debug(f"📝 Added spelling to name: '{word}' → '{spelled_name}'")

            return result

        except Exception as e:
            logger.warning(f"⚠️ Failed to apply spelling to names: {e}")
            return text

    def _is_likely_vietnamese_name(self, word: str) -> bool:
        """Check if a word is likely a Vietnamese name"""
        try:
            if not word or len(word) < 2:
                return False

            # Vietnamese names typically have these characteristics:
            # 1. Capitalized first letter
            # 2. May contain Vietnamese diacritics
            # 3. Reasonable length (2-10 characters)
            # 4. Not common Vietnamese function words

            if not word[0].isupper():
                return False

            # Common Vietnamese function words to exclude (expanded list)
            function_words = {
                # Basic function words
                'và', 'của', 'cái', 'là', 'được', 'có', 'không',
                'trong', 'trên', 'dưới', 'sang', 'từ', 'đến',
                'cho', 'với', 'tại', 'này', 'đó', 'mà', 'thì',
                'nhưng', 'vậy', 'sao', 'tại', 'đây', 'kia',

                # Pronouns that are commonly used and shouldn't get spelling
                'tôi', 'bạn', 'chị', 'em', 'ông', 'bà', 'cháu',
                'anh', 'chị', 'em', 'ông', 'bà', 'cháu',
                'nó', 'chúng', 'ta', 'tao', 'mình', 'con',

                # Common titles and professions (without specific names)
                'bác', 'cô', 'thầy', 'bà', 'ông', 'chị', 'anh', 'em',
                'bác sĩ', 'y tá', 'giáo viên', 'học sinh', 'sinh viên',
                'công nhân', 'kỹ sư', 'giám đốc', 'nhân viên',

                # Common verbs and adjectives
                'đi', 'đến', 'về', 'làm', 'học', 'ăn', 'uống',
                'ngủ', 'thức', 'đọc', 'viết', 'nói', 'nghe',
                'xem', 'thấy', 'biết', 'muốn', 'cần', 'phải',
                'tốt', 'xấu', 'đẹp', 'sạch', 'bẩn', 'lớn', 'nhỏ'
            }

            word_lower = word.lower()
            if word_lower in function_words:
                return False

            # Check for Vietnamese diacritics (common in names)
            vietnamese_chars = set('áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ')
            has_diacritics = any(char.lower() in vietnamese_chars for char in word)

            # Vietnamese names often have diacritics or are common name patterns
            return has_diacritics or len(word) >= 3

        except Exception as e:
            logger.warning(f"⚠️ Failed to check if likely Vietnamese name: {e}")
            return False

    def _has_vietnamese_diacritics(self, word: str) -> bool:
        """Check if word contains Vietnamese diacritical marks"""
        try:
            vietnamese_diacritics = set('áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ')
            return any(char.lower() in vietnamese_diacritics for char in word)
        except Exception as e:
            logger.warning(f"⚠️ Failed to check Vietnamese diacritics: {e}")
            return False

    def _apply_vietnamese_spelling_corrections(self, text: str) -> str:
        """Apply comprehensive Vietnamese spelling corrections with proper tone marks and accents - DISABLED"""
        # DISABLED: Return text as-is without spelling corrections
        return text

        try:
            spelling_corrections = {
                # Basic words with tone marks
                # Words with tone marks (excluding those handled by problematic words)
                "nguoi": "người",
                "nhung": "nhưng",
                "nhieu": "nhiều",
                "yeu": "yêu",
                "moi": "mới",
                "cuoi": "cuối",
                "trong": "trong",
                "ngoai": "ngoài",
                "tren": "trên",
                "duoi": "dưới",
                "phai": "phải",
                "trai": "trái",
                "chan": "chân",
                "cuop": "cướp",
                "thay": "thay",
                "doi": "đổi",
                "mua": "mua",
                "an": "ăn",
                "uong": "uống",
                "xem": "xem",
                "nghe": "nghe",
                "noi": "nói",
                "viet": "viết",
                "doc": "đọc",
                "hoc": "học",
                "lam": "làm",
                "di": "đi",
                "ve": "về",
                "den": "đến",
                "tu": "từ",
                "voi": "với",
                "cua": "của",
                "la": "là",
                "va": "và",
                "nhu": "như",
                "neu": "nếu",
                "khi": "khi",
                "thi": "thì",
                "ma": "mà",
                "vi": "vì",

                # Names and proper nouns
                "viet nam": "Việt Nam",
                "ha noi": "Hà Nội",
                "ho chi minh": "Hồ Chí Minh",
                "da nang": "Đà Nẵng",
                "hai phong": "Hải Phòng",
                "can tho": "Cần Thơ",

                # Time expressions with correct spelling
                "hom nay": "hôm nay",
                "hom qua": "hôm qua",
                "hom kia": "hôm kia",
                "sang nay": "sáng nay",
                "chieu nay": "chiều nay",
                "toi nay": "tối nay",
                "sang som": "sáng sớm",
                "chieu muon": "chiều muộn",

                # Question words with proper spelling
                "gi": "gì",
                "tai sao": "tại sao",
                "o dau": "ở đâu",
                "tu dau": "từ đâu",
                "den dau": "đến đâu",
                "bao gio": "bao giờ",
                "khi nao": "khi nào",
                "the nao": "thế nào",
                "nhu the nao": "như thế nào",

                # Common phrases with correct spelling (excluding problematic ones)
                "cam on": "cảm ơn",
                "xin loi": "xin lỗi",
                "khong sao": "không sao",
                "duoc roi": "được rồi",
                "tam biet": "tạm biệt",
                "chao ban": "chào bạn",
                "co le": "có lẽ",
                "chac chan": "chắc chắn",
                "can than": "cẩn thận",
                "nhanh len": "nhanh lên",
                "doi chut": "đợi chút",

                # Numbers with proper spelling
                "mot": "một",
                "hai": "hai",
                "ba": "ba",
                "bon": "bốn",
                "nam": "năm",
                "sau": "sáu",
                "bay": "bảy",
                "tam": "tám",
                "chin": "chín",
                "muoi": "mười",
                "tram": "trăm",
                "nghin": "nghìn",
                "trieu": "triệu",
                "ty": "tỷ",

                # Family relationships
                "bo me": "bố mẹ",
                "cha me": "cha mẹ",
                "ong ba": "ông bà",
                "co di": "cô dì",
                "chu bac": "chú bác",
                "anh chi": "anh chị",
                "em gai": "em gái",
                "em trai": "em trai",

                # Colors with proper spelling
                "do": "đỏ",
                "xanh": "xanh",
                "vang": "vàng",
                "trang": "trắng",
                "den": "đen",
                "tim": "tím",
                "nau": "nâu",
                "xam": "xám",

                # Days of the week with correct accents
                "thu hai": "thứ hai",
                "thu ba": "thứ ba",
                "thu tu": "thứ tư",
                "thu nam": "thứ năm",
                "thu sau": "thứ sáu",
                "thu bay": "thứ bảy",
                "chu nhat": "chủ nhật",

                # Months with correct accents
                "thang mot": "tháng một",
                "thang hai": "tháng hai",
                "thang ba": "tháng ba",
                "thang tu": "tháng tư",
                "thang nam": "tháng năm",
                "thang sau": "tháng sáu",
                "thang bay": "tháng bảy",
                "thang tam": "tháng tám",
                "thang chin": "tháng chín",
                "thang muoi": "tháng mười",
                "thang muoi mot": "tháng mười một",
                "thang muoi hai": "tháng mười hai",

                # Advanced spelling corrections with multiple syllables
                "thay doi": "thay đổi",
                "cam thay": "cảm thấy",
                "cam on": "cảm ơn",
                "xin loi": "xin lỗi",
                "tam biet": "tạm biệt",
                "chao ban": "chào bạn",
                "rat vui": "rất vui",
                "co le": "có lẽ",
                "chac chan": "chắc chắn",
                "co the": "có thể",
                "khong the": "không thể",
                "can than": "cẩn thận",
                "nhanh len": "nhanh lên",
                "doi chut": "đợi chút",

                # Cognitive assessment specific spelling
                "ban ten gi": "bạn tên gì",
                "ban bao nhieu tuoi": "bạn bao nhiêu tuổi",
                "ban dang o dau": "bạn đang ở đâu",
                "hom nay la thu may": "hôm nay là thứ mấy",
                "ban nam tuoi": "bạn năm tuổi",
                "ban muoi tuoi": "bạn mười tuổi",
                "ban hai muoi tuoi": "bạn hai mươi tuổi",

                # Medical terms with correct spelling
                "benh vien": "bệnh viện",
                "bac si": "bác sĩ",
                "y ta": "y tá",
                "duoc si": "dược sĩ",
                "thuoc": "thuốc",
                "vien thuoc": "viên thuốc",
                "uong thuoc": "uống thuốc",
                "dau dau": "đau đầu",
                "dau bung": "đau bụng",
                "dau nguc": "đau ngực",
                "dau tay": "đau tay",
                "dau chan": "đau chân",
                "dau rang": "đau răng",
            }

            for incorrect, correct in spelling_corrections.items():
                text = text.replace(incorrect, correct)

            return text

        except Exception as e:
            # DISABLED: Vietnamese spelling corrections error logging
            return text

    def _apply_specialized_corrections(self, text: str) -> str:
        """Apply specialized corrections for complex cases"""
        try:
            specialized_corrections = {
                # Numbers in context
                "hai nghin": "hai nghìn",
                "chin tram": "chín trăm",
                "chin muoi": "chín mươi",
                "muoi chin": "mười chín",

                # Medical terms
                "benh vien": "bệnh viện",
                "bac si": "bác sĩ",
                "thuoc": "thuốc",

                # Complex phrases
                "la ban": "là bạn",
                "nam tuoi": "năm tuổi",
                "hom nay": "hôm nay",
                "la thu": "là thứ",
                "thang mot": "tháng một",
                "nam hai": "năm hai",
                "nghin chin": "nghìn chín",
                "tram chin": "trăm chín",
                "muoi chin": "mười chín",
                "bao nhieu": "bao nhiêu",
                "la thu may": "là thứ mấy",
                "dang o dau": "đang ở đâu",

                # Regional expressions that need multiple corrections
                "chung tao": "chúng tôi",
                "chung tao": "chúng tôi",  # Apply twice for better results
                "biet khong": "biết không",
                "tao la": "tôi là",

                # Numbers in sentences
                "mot nam": "một năm",
                "hai nam": "hai năm",
                "ba nam": "ba năm",
                "bon nam": "bốn năm",
                "nam nam": "năm năm",

                # Age expressions
                "tuoi toi": "tuổi tôi",
                "tuoi ban": "tuổi bạn",

                # Medical terms corrections
                "bénh vien": "bệnh viện",
                "bàc si": "bác sĩ",
                "thuóc": "thuốc",

                # Common phrase corrections
                "ten gi": "tên gì",
                "o dau": "ở đâu",
                "lam gi": "làm gì",
                "bào nhiểu": "bao nhiêu",
                "dang o đau": "đang ở đâu",
                "vi đau đau": "vì đau đầu",

                # Final pronunciation fixes
                "tui la": "tôi là",
                "chung tui": "chúng tôi",
                "nghĩn chịn": "nghìn chín",
                "tram chịn": "trăm chín",
                "mười chịn": "mười chín",

                # Cognitive assessment specific
                "ban ten gi": "bạn tên gì",
                "ban bao nhieu tuoi": "bạn bao nhiêu tuổi",
                "ban dang o dau": "bạn đang ở đâu",
                "hom nay la thu may": "hôm nay là thứ mấy",

                # Time expressions
                "hom qua": "hôm qua",
                "hom kia": "hôm kia",
                "tuan truoc": "tuần trước",
                "thang truoc": "tháng trước",
                "nam truoc": "năm trước",
            }

            for incorrect, correct in specialized_corrections.items():
                text = text.replace(incorrect, correct)

            return text

        except Exception as e:
            # DISABLED: Specialized corrections error logging
            return text

    def _apply_tone_accent_corrections(self, text: str) -> str:
        """Apply Vietnamese tone/accent corrections for better audio processing"""
        try:
            tone_corrections = {
                # Common tone misrecognition patterns
                "nghien": "nghiện",  # sắc → ngang (addiction)
                "nghien cuu": "nghiên cứu",  # research
                "nghien": "nghiền",  # crush/grind
                "thuong": "thương",  # thương (love/pity)
                "thuong": "thường",  # thường (usually)
                "thuong": "thưởng",  # thưởng (reward)
                "thuong": "thượng",  # thượng (upper)
                "thuong": "thưởng",  # thưởng (reward)

                # Medical terms tone corrections
                "dau dau": "đau đầu",  # headache
                "dau bung": "đau bụng",  # stomachache
                "dau nguc": "đau ngực",  # chest pain
                "dau tay": "đau tay",  # hand pain
                "dau chan": "đau chân",  # foot pain

                # Cognitive assessment terms
                "nho": "nhớ",  # remember
                "quen": "quên",  # forget
                "biet": "biết",  # know
                "hieu": "hiểu",  # understand
                "muon": "muốn",  # want
                "can": "cần",  # need
                "phai": "phải",  # must

                # Common words with tone variations
                "di": "đi",  # go
                "di": "dị",  # strange (rare)
                "ma": "mà",  # but
                "ma": "mã",  # code
                "ma": "má",  # mother
                "ba": "ba",  # father
                "ba": "bá",  # uncle
                "ba": "bà",  # grandmother
                "me": "mẹ",  # mother
                "me": "mế",  # drunk (slang)
            }

            for incorrect, correct in tone_corrections.items():
                text = text.replace(incorrect, correct)

            return text

        except Exception as e:
            # DISABLED: Tone/accent corrections error logging
            return text

    def _apply_semantic_context_corrections(self, text: str) -> str:
        """Apply semantic and context-based corrections for Vietnamese"""
        try:
            # Context-based corrections for medical/cognitive terms
            semantic_corrections = {
                # Medical context
                "benh nhan": "bệnh nhân",  # patient
                "bac si": "bác sĩ",  # doctor
                "y ta": "y tá",  # nurse
                "thuoc": "thuốc",  # medicine
                "kham benh": "khám bệnh",  # medical examination
                "uống thuốc": "uống thuốc",  # take medicine
                "đau đầu": "đau đầu",  # headache
                "đau bụng": "đau bụng",  # stomachache

                # Cognitive assessment context
                "nhớ": "nhớ",  # remember
                "quên": "quên",  # forget
                "biết": "biết",  # know
                "hiểu": "hiểu",  # understand
                "tập trung": "tập trung",  # concentrate
                "chú ý": "chú ý",  # pay attention

                # Time context
                "hôm nay": "hôm nay",  # today
                "hôm qua": "hôm qua",  # yesterday
                "hôm kia": "hôm kia",  # day before yesterday
                "tuần này": "tuần này",  # this week
                "tháng này": "tháng này",  # this month

                # Age context
                "tuổi": "tuổi",  # age
                "sinh nhật": "sinh nhật",  # birthday
                "lớn tuổi": "lớn tuổi",  # elderly

                # Common phrases
                "tôi tên là": "tôi tên là",  # my name is
                "bạn tên là": "bạn tên là",  # your name is
                "bao nhiêu tuổi": "bao nhiêu tuổi",  # how old
                "ở đâu": "ở đâu",  # where
                "làm gì": "làm gì",  # what do
            }

            for incorrect, correct in semantic_corrections.items():
                text = text.replace(incorrect, correct)

            return text

        except Exception as e:
            # DISABLED: Semantic context corrections error logging
            return text

    def _apply_phonological_corrections(self, text: str) -> str:
        """Apply advanced phonological corrections for Vietnamese speech patterns"""
        try:
            phonological_corrections = {
                # Consonant cluster corrections (common ASR errors)
                "khong": "không",  # not
                "nguoi": "người",  # person
                "nghe": "nghe",  # hear
                "nghi": "nghĩ",  # think
                "ngay": "ngày",  # day
                "trong": "trong",  # in/inside
                "thanh": "thành",  # become
                "thanh": "thanh",  # voice/sound
                "thanh": "thắng",  # win

                # Vowel sequence corrections
                "uong": "uống",  # drink
                "uong": "ương",  # related to mother
                "ien": "iên",  # related to connection
                "ien": "iện",  # related to electricity
                "ien": "iễn",  # related to far

                # Dipthong corrections
                "ai": "ai",  # who
                "ao": "ao",  # pond
                "au": "au",  # oh
                "ay": "ay",  # here
                "eo": "eo",  # narrow
                "eu": "eu",  # oh (southern)
                "ia": "ia",  # related to mother
                "ieu": "iều",  # willow
                "iu": "iu",  # oh
                "oa": "oa",  # related to grandmother
                "oai": "oai",  # majestic
                "oe": "oe",  # related to sister
                "oi": "oi",  # oh
                "oo": "oo",  # oh (dialect)
                "ua": "ua",  # fall
                "uai": "uai",  # dialect variation
                "ue": "ue",  # dialect variation
                "ui": "ui",  # ash
                "uo": "uo",  # dialect variation
                "uu": "uu",  # dialect variation
                "uy": "uy",  # dialect variation

                # Common assimilation errors
                "cua": "của",  # of
                "voi": "với",  # with
                "tu": "từ",  # from
                "den": "đến",  # to/arrive
                "ve": "về",  # return
                "di": "đi",  # go
                "lai": "lại",  # again
                "nhau": "nhau",  # each other

                # Medical phonological patterns
                "kham": "khám",  # examine
                "benh": "bệnh",  # disease
                "vien": "viện",  # institute
                "vien": "viên",  # pill/round
                "uong": "uống",  # drink
                "an": "ăn",  # eat
                "ngu": "ngủ",  # sleep

                # Cognitive phonological patterns
                "nho": "nhớ",  # remember
                "quen": "quên",  # forget
                "biet": "biết",  # know
                "hieu": "hiểu",  # understand
                "muon": "muốn",  # want
                "can": "cần",  # need
                "phai": "phải",  # must/correct
                "dung": "đúng",  # correct
                "sai": "sai",  # wrong
            }

            for incorrect, correct in phonological_corrections.items():
                text = text.replace(incorrect, correct)

            return text

        except Exception as e:
            # DISABLED: Phonological corrections error logging
            return text

    def _apply_vietnamese_specific_corrections(self, text: str) -> str:
        """Apply comprehensive Vietnamese-specific corrections and improvements with enhanced audio processing"""
        if not text:
            return text

        try:
            corrected_text = text.lower()

            # Step 1: Apply tone/accent corrections (ưu tiên cao nhất)
            corrected_text = self._apply_tone_accent_corrections(corrected_text)

            # Step 2: Apply pronunciation-based corrections (đánh vần)
            corrected_text = self._apply_pronunciation_corrections(corrected_text)

            # Step 3: Apply regional/dialect corrections (ngôn ngữ địa phương)
            corrected_text = self._apply_regional_corrections(corrected_text)

            # Step 4: Apply semantic/context corrections (ngữ nghĩa)
            corrected_text = self._apply_semantic_context_corrections(corrected_text)

            # Step 5: Apply common ASR error corrections
            corrected_text = self._apply_common_asr_corrections(corrected_text)

            # Step 6: Apply advanced phonological corrections
            corrected_text = self._apply_phonological_corrections(corrected_text)

            # Step 7: Apply spelling and grammatical corrections
            corrected_text = self._apply_spelling_corrections(corrected_text)

            # Step 8: Apply context-aware improvements
            corrected_text = self._apply_context_improvements(corrected_text)

            # Step 9: Final formatting and capitalization
            corrected_text = self._apply_final_formatting(corrected_text, text)

            return corrected_text

        except Exception as e:
            # DISABLED: Vietnamese-specific corrections error logging
            return text

    def _apply_pronunciation_corrections(self, text: str) -> str:
        """Correct common pronunciation-based errors in Vietnamese"""
        pronunciation_corrections = {
            # Southern Vietnamese pronunciation
            "thì": ["thi", "thì", "thì"],
            "thế": ["the", "thế", "thế"],
            "thế nào": ["the nao", "thế nào", "thế nào"],
            "thế mà": ["the ma", "thế mà", "thế mà"],

            # Northern Vietnamese pronunciation
            "không": ["khong", "không", "không"],
            "người": ["nguoi", "người", "người"],
            "chúng tôi": ["chung toi", "chúng tôi", "chúng tôi"],
            "chúng ta": ["chung ta", "chúng ta", "chúng ta"],

            # Common mispronunciations
            "tôi": ["toi", "tôi", "tôi"],
            "bạn": ["ban", "bạn", "bạn"],
            "anh": ["anh", "anh", "anh"],
            "chị": ["chi", "chị", "chị"],
            "em": ["em", "em", "em"],
            "ông": ["ong", "ông", "ông"],
            "bà": ["ba", "bà", "bà"],
            "cậu": ["cau", "cậu", "cậu"],
            "bé": ["be", "bé", "bé"],

            # Numbers and quantities (very important for cognitive assessment)
            "một": ["mot", "một", "một"],
            "hai": ["hai", "hai", "hai"],
            "ba": ["ba", "ba", "ba"],
            "bốn": ["bon", "bốn", "bốn"],
            "năm": ["nam", "năm", "năm"],
            "sáu": ["sau", "sáu", "sáu"],
            "bảy": ["bay", "bảy", "bảy"],
            "tám": ["tam", "tám", "tám"],
            "chín": ["chin", "chín", "chín"],
            "mười": ["muoi", "mười", "mười"],
            "hai mươi": ["hai muoi", "hai mươi", "hai mươi"],
            "ba mươi": ["ba muoi", "ba mươi", "ba mươi"],

            # Days of the week (critical for cognitive assessment)
            "thứ hai": ["thu hai", "thứ hai", "thứ hai"],
            "thứ ba": ["thu ba", "thứ ba", "thứ ba"],
            "thứ tư": ["thu tu", "thứ tư", "thứ tư"],
            "thứ năm": ["thu nam", "thứ năm", "thứ năm"],
            "thứ sáu": ["thu sau", "thứ sáu", "thứ sáu"],
            "thứ bảy": ["thu bay", "thứ bảy", "thứ bảy"],
            "chủ nhật": ["chu nhat", "chủ nhật", "chủ nhật"],

            # Months (important for orientation assessment)
            "tháng một": ["thang mot", "tháng một", "tháng một"],
            "tháng hai": ["thang hai", "tháng hai", "tháng hai"],
            "tháng ba": ["thang ba", "tháng ba", "tháng ba"],
            "tháng tư": ["thang tu", "tháng tư", "tháng tư"],
            "tháng năm": ["thang nam", "tháng năm", "tháng năm"],
            "tháng sáu": ["thang sau", "tháng sáu", "tháng sáu"],
            "tháng bảy": ["thang bay", "tháng bảy", "tháng bảy"],
            "tháng tám": ["thang tam", "tháng tám", "tháng tám"],
            "tháng chín": ["thang chin", "tháng chín", "tháng chín"],
            "tháng mười": ["thang muoi", "tháng mười", "tháng mười"],
            "tháng mười một": ["thang muoi mot", "tháng mười một", "tháng mười một"],
            "tháng mười hai": ["thang muoi hai", "tháng mười hai", "tháng mười hai"],
        }

        for correct, variations in pronunciation_corrections.items():
            for variation in variations:
                text = text.replace(variation, correct)

        return text

    def _apply_regional_corrections(self, text: str) -> str:
        """Correct regional/dialect variations in Vietnamese"""
        regional_corrections = {
            # Southern dialect
            "thì": ["thi", "thì"],
            "thế": ["the", "thế"],
            "chị": ["chi", "chị"],
            "anh": ["anh", "anh"],
            "em": ["em", "em"],
            "tôi": ["tui", "tôi"],  # Southern "tui" → "tôi"
            "tui": ["tôi", "tôi"],  # Southern "tui" → "tôi"
            "mình": ["mih", "mình"],

            # Northern dialect
            "không": ["không", "không"],
            "người": ["người", "người"],
            "chúng tôi": ["bọn tôi", "chúng tôi"],
            "chúng tao": ["chúng tôi", "chúng tôi"],
            "tao": ["tôi", "tôi"],  # Northern "tao" → "tôi"

            # Central dialect
            "chị": ["cô", "chị"],  # Central sometimes use "cô" for "chị"
            "anh": ["ông", "anh"],  # Central sometimes use "ông" for "anh"

            # Common regional expressions
            "đi chơi": ["đi chơi", "đi chơi"],
            "ăn cơm": ["ăn cơm", "ăn cơm"],
            "uống nước": ["uống nước", "uống nước"],
        }

        for correct, variations in regional_corrections.items():
            for variation in variations:
                text = text.replace(variation, correct)

        return text

    def _apply_common_asr_corrections(self, text: str) -> str:
        """Correct common ASR (Automatic Speech Recognition) errors"""
        asr_corrections = {
            # Common ASR misrecognitions
            "có thể": ["có thể", "có thế", "có thể"],
            "không thể": ["không thể", "không thế", "không thể"],
            "được": ["được", "được", "được"],
            "nhưng": ["nhưng", "nhưng", "nhưng"],
            "nhiều": ["nhiều", "nhiều", "nhiều"],
            "bạn": ["bạn", "bạn", "bạn"],
            "tôi": ["tôi", "tôi", "tôi"],
            "cảm ơn": ["cảm ơn", "cảm ơn", "cảm ơn"],
            "xin chào": ["xin chào", "xin chào", "xin chào"],
            "tốt": ["tốt", "tốt", "tốt"],
            "xấu": ["xấu", "xấu", "xấu"],
            "nhà": ["nhà", "nhà", "nhà"],
            "trường": ["trường", "trường", "trường"],
            "học": ["học", "học", "học"],
            "đi": ["đi", "đi", "đi"],
            "về": ["về", "về", "về"],
            "ăn": ["ăn", "ăn", "ăn"],
            "uống": ["uống", "uống", "uống"],
            "ngủ": ["ngủ", "ngủ", "ngủ"],
            "làm": ["làm", "làm", "làm"],
            "việc": ["việc", "việc", "việc"],

            # Medical/cognitive assessment specific terms
            "nhớ": ["nhớ", "nhớ", "nhớ"],
            "quên": ["quên", "quên", "quên"],
            "hôm nay": ["hôm nay", "hôm nay", "hôm nay"],
            "hôm qua": ["hôm qua", "hôm qua", "hôm qua"],
            "tuần trước": ["tuần trước", "tuần trước", "tuần trước"],
            "tháng trước": ["tháng trước", "tháng trước", "tháng trước"],
            "năm trước": ["năm trước", "năm trước", "năm trước"],
            "bệnh viện": ["bệnh viện", "bệnh viện", "bệnh viện"],
            "bác sĩ": ["bác sĩ", "bác sĩ", "bác sĩ"],
            "thuốc": ["thuốc", "thuốc", "thuốc"],
            "đau": ["đau", "đau", "đau"],
            "mệt": ["mệt", "mệt", "mệt"],
            "ngủ": ["ngủ", "ngủ", "ngủ"],
            "ăn": ["ăn", "ăn", "ăn"],
            "uống": ["uống", "uống", "uống"],

            # Cognitive assessment specific phrases (prioritize these)
            "bạn tên gì": ["ban ten gi", "bạn tên gì", "bạn tên gì"],
            "bạn bao nhiêu tuổi": ["ban bao nhieu tuoi", "bạn bao nhiêu tuổi", "bạn bao nhiêu tuổi"],
            "hôm nay là thứ mấy": ["hom nay la thu may", "hôm nay là thứ mấy", "hôm nay là thứ mấy"],
            "bạn đang ở đâu": ["ban dang o dau", "bạn đang ở đâu", "bạn đang ở đâu"],

            # Additional cognitive assessment terms
            "tuổi": ["tuoi", "tuổi", "tuổi"],
            "sinh nhật": ["sinh nhat", "sinh nhật", "sinh nhật"],
            "bệnh viện": ["benh vien", "bệnh viện", "bệnh viện"],
            "bác sĩ": ["bac si", "bác sĩ", "bác sĩ"],
            "thuốc": ["thuoc", "thuốc", "thuốc"],
            "đau ": ["dau ", "đau ", "đau "],  # Add space to distinguish from "đầu"
            "nhớ": ["nho", "nhớ", "nhớ"],
            "quên": ["quen", "quên", "quên"],

            # Question words
            "tên gì": ["ten gi", "tên gì", "tên gì"],
            "ở đâu": ["o dau", "ở đâu", "ở đâu"],
            "làm gì": ["lam gi", "làm gì", "làm gì"],
            "bao nhiêu": ["bao nhieu", "bao nhiêu", "bao nhiêu"],
            "thứ mấy": ["thu may", "thứ mấy", "thứ mấy"],

            # Context-specific corrections to avoid conflicts
            "bạn ": ["ban ", "bạn ", "bạn "],  # Prioritize "bạn" over "bán"
            "tôi ": ["toi ", "tôi ", "tôi "],  # Ensure correct pronoun
        }

        for correct, variations in asr_corrections.items():
            for variation in variations:
                text = text.replace(variation, correct)

        return text

    def _apply_spelling_corrections(self, text: str) -> str:
        """Apply Vietnamese spelling corrections for ASR errors - DISABLED"""
        # DISABLED: Return text as-is without spelling corrections
        return text

        # This method now focuses on ASR-specific spelling corrections
        # The comprehensive spelling corrections are handled by _apply_vietnamese_spelling_corrections
        spelling_corrections = {
            # Common ASR misspellings that need special handling
            "nghĩ": ["nghi", "nghĩ"],
            "nghe": ["nghe", "nghe"],
            "viết": ["viet", "viết"],
            "đọc": ["doc", "đọc"],
            "biết": ["biet", "biết"],
            "muốn": ["muon", "muốn"],
            "hiểu": ["hieu", "hiểu"],
            "hỏi": ["hoi", "hỏi"],
            "thấy": ["thay", "thấy"],
            "trả lời": ["tra loi", "trả lời"],
            "câu hỏi": ["cau hoi", "câu hỏi"],
            "đáp án": ["dap an", "đáp án"],

            # Age-related terms (important for cognitive assessment)
            "tuổi": ["tuoi", "tuổi"],
            "sinh nhật": ["sinh nhat", "sinh nhật"],
            "tuổi tác": ["tuoi tac", "tuổi tác"],
            "già": ["gia", "già"],
            "trẻ": ["tre", "trẻ"],
            "lớn tuổi": ["lon tuoi", "lớn tuổi"],

            # Time-related terms
            "giờ": ["gio", "giờ"],
            "phút": ["phut", "phút"],
            "giây": ["giay", "giây"],
            "ngày": ["ngay", "ngày"],
            "tháng": ["thang", "tháng"],
            "năm": ["nam", "năm"],
            "tuần": ["tuan", "tuần"],
        }

        for correct, variations in spelling_corrections.items():
            for variation in variations:
                text = text.replace(variation, correct)

        return text

    def _apply_context_improvements(self, text: str) -> str:
        """Apply context-aware improvements for Vietnamese text"""
        # Improve sentence structure and flow
        improvements = {
            "tôi là": ["tôi là", "tôi là"],
            "tôi có": ["tôi có", "tôi có"],
            "tôi đã": ["tôi đã", "tôi đã"],
            "tôi sẽ": ["tôi sẽ", "tôi sẽ"],
            "tôi muốn": ["tôi muốn", "tôi muốn"],
            "tôi cần": ["tôi cần", "tôi cần"],
        }

        for correct, variations in improvements.items():
            for variation in variations:
                text = text.replace(variation, correct)

        return text

    def _apply_final_formatting(self, text: str, original_text: str) -> str:
        """Apply final formatting and capitalization"""
        # Split into sentences and capitalize properly
        sentences = text.split('. ')
        capitalized_sentences = []

        for sentence in sentences:
            if sentence.strip():
                sentence = sentence.strip()
                # Capitalize first letter
                if sentence and sentence[0].islower():
                    sentence = sentence[0].upper() + sentence[1:]

                # Capitalize "Tôi" at start of sentence
                if sentence.lower().startswith('tôi'):
                    sentence = 'Tôi' + sentence[3:]

                # Capitalize other pronouns at start
                pronouns = ['bạn', 'anh', 'chị', 'em', 'ông', 'bà', 'cháu', 'cậu', 'bé']
                for pronoun in pronouns:
                    if sentence.lower().startswith(pronoun + ' '):
                        sentence = pronoun.capitalize() + sentence[len(pronoun):]
                        break

                capitalized_sentences.append(sentence)

        result = '. '.join(capitalized_sentences)

        # Ensure result ends with proper punctuation if original had it
        if original_text.endswith('.') and not result.endswith('.'):
            result += '.'
        elif original_text.endswith('!') and not result.endswith('!'):
            result += '!'
        elif original_text.endswith('?') and not result.endswith('?'):
            result += '?'

        return result

    def _apply_english_specific_corrections(self, text: str) -> str:
        """Apply English-specific corrections and improvements"""
        if not text:
            return text

        try:
            # English common corrections
            english_corrections = {
                # Common ASR errors for English
                "i": "I",  # Capitalize "I"
                "im": "I'm",
                "dont": "don't",
                "cant": "can't",
                "wont": "won't",
                "shouldnt": "shouldn't",
                "couldnt": "couldn't",
                "wouldnt": "wouldn't",
                "didnt": "didn't",
                "doesnt": "doesn't",
                "isnt": "isn't",
                "arent": "aren't",
                "wasnt": "wasn't",
                "werent": "weren't",
                "havent": "haven't",
                "hasnt": "hasn't",
                "hadnt": "hadn't",
                "its": "it's",
                "thats": "that's",
                "heres": "here's",
                "theres": "there's",
                "wheres": "where's"
            }

            corrected_text = text

            # Apply corrections (case-insensitive)
            for wrong, correct in english_corrections.items():
                # Use regex for word boundaries to avoid partial replacements
                import re
                pattern = r'\b' + re.escape(wrong) + r'\b'
                corrected_text = re.sub(pattern, correct, corrected_text, flags=re.IGNORECASE)

            # Capitalize first letter of sentences
            sentences = corrected_text.split('. ')
            capitalized_sentences = []

            for sentence in sentences:
                if sentence.strip():
                    sentence = sentence.strip()
                    if sentence and sentence[0].islower():
                        sentence = sentence[0].upper() + sentence[1:]
                    capitalized_sentences.append(sentence)

            result = '. '.join(capitalized_sentences)

            # Ensure result ends with proper punctuation if original had it
            if text.endswith('.') and not result.endswith('.'):
                result += '.'

            return result

        except Exception as e:
            # DISABLED: English-specific corrections error logging
            return text

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Tạo error result"""
        return {
            'success': False,
            'error': error_msg,
            'transcript': '',
            'confidence': 0.0,
            'vietnamese_confidence': 0.0,
            'segments': 0,
            'duration': 0.0,
            'model': 'error',
            'language': 'unknown',
            'processing_time': 0.0,
            'whisper_time': 0.0,
            'gpt4o_time': 0.0,
            'original_text': '',
            'improved_text': ''
        }
    
    def _transcribe_with_gemini_only(self, audio_path: str, language: str = 'vi') -> Dict[str, Any]:
        """Transcribe using Gemini ONLY, no GPT-4o improvement"""
        try:
            start_time = time.time()
            
            # Validate audio file
            if not os.path.exists(audio_path):
                return self._error_result("Audio file not found")
            
            # Get audio duration
            try:
                import librosa
                duration = librosa.get_duration(path=audio_path)
            except:
                duration = 0.0
            
            # Process audio
            processed_path = self.audio_processor.preprocess_audio(audio_path, self.config)
            if not processed_path:
                return self._error_result("Failed to process audio file")
            
            # Transcribe with Gemini
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if not gemini_api_key:
                return self._error_result("Gemini API key not configured")
            
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model_name = os.getenv('GEMINI_STT_MODEL', 'gemini-2.5-flash')
            model = genai.GenerativeModel(model_name)
            
            gemini_start = time.time()
            
            # Upload and transcribe
            gemini_file = genai.upload_file(path=processed_path, mime_type="audio/wav")
            
            if language == 'vi':
                prompt = """
Hãy chép lại CHÍNH XÁC nội dung tiếng Việt trong audio này:
- Chú ý dấu thanh tiếng Việt
- Chỉ trả về transcript thuần văn bản
Transcript:
"""
            else:
                prompt = """
Please transcribe the audio content accurately:
- Only return plain text transcript
Transcript:
"""
            
            response = model.generate_content([gemini_file, prompt])
            text = (getattr(response, 'text', None) or "").strip()
            
            gemini_time = time.time()
            gemini_processing_time = gemini_time - gemini_start
            
            # Gemini doesn't provide confidence scores
            confidence = 0.8
            
            total_processing_time = time.time() - start_time
            
            logger.info(f"🎵 Gemini-only transcription completed in {gemini_processing_time:.2f}s")
            logger.info(f"📝 Raw transcript: {text}")
            logger.info(f"🎯 Confidence: {confidence:.2f}")
            
            # Apply enhanced language model corrections (no GPT-4o)
            if language == 'vi':
                corrected_text = self.language_model.correct_transcript(text)
                corrected_text = self._apply_vietnamese_specific_corrections(corrected_text)
                vietnamese_confidence = self.language_model.calculate_vietnamese_confidence(corrected_text)
                vietnamese_confidence = max(vietnamese_confidence, 0.85)  # Boost confidence for Vietnamese
            else:
                corrected_text = self._apply_english_specific_corrections(text)
                vietnamese_confidence = confidence
            
            return {
                'success': True,
                'transcript': corrected_text,
                'confidence': confidence,
                'vietnamese_confidence': vietnamese_confidence,
                'segments': 1,
                'duration': duration,
                'model': 'gemini-only',
                'language': language,
                'processing_time': total_processing_time,
                'gemini_time': gemini_processing_time,
                'gpt4o_time': 0.0,
                'original_text': text,
                'improved_text': text  # No improvement
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini-only transcription failed: {e}")
            return self._error_result(f"Gemini-only transcription failed: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Lấy thông tin system"""
        return {
            'model': getattr(self, 'model_name', 'Not loaded'),
            'is_initialized': self.is_initialized,
            'audio_processor_ready': self.audio_processor.is_initialized,
            'vocabulary_size': len(self.language_model.vietnamese_words),
            'config': {
                'chunk_duration': self.config.chunk_duration,
                'overlap_duration': self.config.overlap_duration,
                'min_confidence': self.config.min_confidence,
                'use_vad': self.config.use_vad,
                'denoise_audio': self.config.denoise_audio
            }
        }

# API cho Flask/FastAPI
class TranscriberAPI:
    """API wrapper cho transcriber"""
    
    def __init__(self):
        self.transcriber = None
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo transcriber"""
        try:
            config = TranscriptionConfig(
                chunk_duration=5.0,
                overlap_duration=1.0,
                min_confidence=0.7,
                use_vad=True,
                denoise_audio=True
            )
            
            self.transcriber = RealTimeVietnameseTranscriber(config)
            logger.info("✅ Transcriber API initialized")
            
        except Exception as e:
            logger.error(f"❌ API initialization failed: {e}")
    
    async def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """API endpoint để transcribe file"""
        if not self.transcriber or not self.transcriber.is_initialized:
            return {'error': 'Transcriber not ready', 'success': False}
        
        return self.transcriber.transcribe_audio_file(file_path)
    
    async def transcribe_audio_data(self, audio_data: bytes) -> Dict[str, Any]:
        """API endpoint để transcribe audio data"""
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            # Transcribe
            result = await self.transcribe_file(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audio data transcription failed: {e}")
            return {'error': str(e), 'success': False}
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái API"""
        if self.transcriber:
            return self.transcriber.get_system_info()
        else:
            return {'status': 'not_initialized'}

# Test functions
def test_transcriber():
    """Test transcriber với file audio mẫu"""
    try:
        # Khởi tạo
        config = TranscriptionConfig(
            chunk_duration=3.0,
            overlap_duration=0.5,
            min_confidence=0.6
        )
        
        transcriber = RealTimeVietnameseTranscriber(config)
        
        # Test với file audio
        test_file = "../frontend/test.mp3"
        if os.path.exists(test_file):
            result = transcriber.transcribe_audio_file(test_file)
            print("🎯 Test Result:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ Test file not found")
        
        # System info
        info = transcriber.get_system_info()
        print("\n🔧 System Info:")
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_transcriber()

# Flask API example
def create_flask_app():
    """Tạo Flask app cho transcription API"""
    try:
        from flask import Flask, request, jsonify, send_from_directory
        from werkzeug.utils import secure_filename
        import uuid
        
        app = Flask(__name__)
        app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
        app.config['UPLOAD_FOLDER'] = 'uploads'
        
        # Tạo upload folder
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Initialize API
        api = TranscriberAPI()
        
        @app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify(api.get_status())
        
        @app.route('/api/transcribe', methods=['POST'])
        def transcribe_endpoint():
            """Main transcription endpoint"""
            try:
                if 'audio' not in request.files:
                    return jsonify({'error': 'No audio file provided', 'success': False}), 400
                
                file = request.files['audio']
                if file.filename == '':
                    return jsonify({'error': 'No file selected', 'success': False}), 400
                
                # Save uploaded file
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                try:
                    # Transcribe
                    result = asyncio.run(api.transcribe_file(filepath))
                    
                    # Clean up
                    if os.path.exists(filepath):
                        os.unlink(filepath)
                    
                    return jsonify(result)
                    
                except Exception as e:
                    # Clean up on error
                    if os.path.exists(filepath):
                        os.unlink(filepath)
                    raise e
                
            except Exception as e:
                logger.error(f"❌ Transcription endpoint error: {e}")
                return jsonify({'error': str(e), 'success': False}), 500
        
        @app.route('/api/transcribe/stream', methods=['POST'])
        def transcribe_stream():
            """Stream transcription endpoint"""
            try:
                audio_data = request.get_data()
                if not audio_data:
                    return jsonify({'error': 'No audio data provided', 'success': False}), 400
                
                result = asyncio.run(api.transcribe_audio_data(audio_data))
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"❌ Stream transcription error: {e}")
                return jsonify({'error': str(e), 'success': False}), 500
        
        @app.route('/api/models/info', methods=['GET'])
        def model_info():
            """Get model information"""
            return jsonify(api.get_status())
        
        return app
        
    except ImportError:
        logger.error("❌ Flask not installed. Install with: pip install flask")
        return None

# FastAPI example
def create_fastapi_app():
    """Tạo FastAPI app cho transcription API"""
    try:
        from fastapi import FastAPI, UploadFile, File, HTTPException
        from fastapi.responses import JSONResponse
        from fastapi.middleware.cors import CORSMiddleware
        import uuid
        
        app = FastAPI(
            title="Vietnamese Speech Transcriber",
            description="Real-time Vietnamese speech-to-text API",
            version="2.0.0"
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize API
        api = TranscriberAPI()
        
        @app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return api.get_status()
        
        @app.post("/api/transcribe")
        async def transcribe_file_endpoint(audio: UploadFile = File(...)):
            """Main file transcription endpoint"""
            try:
                # Validate file type
                if not audio.content_type.startswith('audio/'):
                    raise HTTPException(status_code=400, detail="Invalid audio file")
                
                # Save uploaded file
                filename = f"{uuid.uuid4()}_{audio.filename}"
                filepath = f"uploads/{filename}"
                
                os.makedirs("uploads", exist_ok=True)
                
                with open(filepath, "wb") as f:
                    content = await audio.read()
                    f.write(content)
                
                try:
                    # Transcribe
                    result = await api.transcribe_file(filepath)
                    
                    # Clean up
                    if os.path.exists(filepath):
                        os.unlink(filepath)
                    
                    return result
                    
                except Exception as e:
                    # Clean up on error
                    if os.path.exists(filepath):
                        os.unlink(filepath)
                    raise HTTPException(status_code=500, detail=str(e))
                
            except Exception as e:
                logger.error(f"❌ FastAPI transcription error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/transcribe/stream")
        async def transcribe_stream_endpoint(audio_data: bytes):
            """Stream transcription endpoint"""
            try:
                result = await api.transcribe_audio_data(audio_data)
                return result
                
            except Exception as e:
                logger.error(f"❌ Stream transcription error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/models/info")
        async def get_model_info():
            """Get model information"""
            return api.get_status()
        
        return app
        
    except ImportError:
        logger.error("❌ FastAPI not installed. Install with: pip install fastapi uvicorn")
        return None

# Real-time WebSocket support
class WebSocketTranscriber:
    """WebSocket support cho real-time transcription"""
    
    def __init__(self):
        self.transcriber = None
        self.clients = set()
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo transcriber với real-time config"""
        config = TranscriptionConfig(
            chunk_duration=2.0,  # Shorter chunks for real-time
            overlap_duration=0.3,
            min_confidence=0.5,  # Lower threshold for real-time
            use_vad=True,
            denoise_audio=True,
            real_time_callback=self._broadcast_result
        )
        
        self.transcriber = RealTimeVietnameseTranscriber(config)
        self.transcriber.start_real_time_transcription()
    
    def _broadcast_result(self, result: Dict[str, Any], timestamp: float):
        """Broadcast kết quả đến tất cả clients"""
        message = {
            'type': 'transcription',
            'data': result,
            'timestamp': timestamp
        }
        
        # Remove disconnected clients
        disconnected = set()
        for client in self.clients:
            try:
                asyncio.create_task(client.send_json(message))
            except Exception:
                disconnected.add(client)
        
        self.clients -= disconnected
    
    def add_client(self, websocket):
        """Thêm WebSocket client"""
        self.clients.add(websocket)
    
    def remove_client(self, websocket):
        """Xóa WebSocket client"""
        self.clients.discard(websocket)
    
    def process_audio_chunk(self, audio_data: bytes):
        """Xử lý audio chunk từ WebSocket"""
        if self.transcriber:
            self.transcriber.add_audio_chunk(audio_data)

# Usage examples and utilities
class TranscriptionBatch:
    """Batch processing multiple audio files"""
    
    def __init__(self, transcriber: RealTimeVietnameseTranscriber):
        self.transcriber = transcriber
    
    def process_directory(self, directory_path: str, output_file: str = None) -> List[Dict]:
        """Process tất cả audio files trong directory"""
        results = []
        
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"❌ Directory not found: {directory_path}")
            return results
        
        audio_files = [f for f in directory.iterdir() 
                      if f.suffix.lower() in audio_extensions]
        
        logger.info(f"📁 Processing {len(audio_files)} audio files...")
        
        for audio_file in audio_files:
            logger.info(f"🎵 Processing: {audio_file.name}")
            
            result = self.transcriber.transcribe_audio_file(str(audio_file))
            result['filename'] = audio_file.name
            results.append(result)
        
        # Save results if output file specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Results saved to: {output_file}")
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict[str, Any]:
        """Tạo báo cáo tổng kết"""
        if not results:
            return {'error': 'No results to analyze'}
        
        successful = [r for r in results if r.get('success', False)]
        total_files = len(results)
        success_rate = len(successful) / total_files if total_files > 0 else 0
        
        # Calculate statistics
        confidences = [r.get('confidence', 0) for r in successful]
        vietnamese_confidences = [r.get('vietnamese_confidence', 0) for r in successful]
        durations = [r.get('duration', 0) for r in successful]
        
        report = {
            'summary': {
                'total_files': total_files,
                'successful_transcriptions': len(successful),
                'success_rate': round(success_rate, 3),
                'total_duration': round(sum(durations), 2) if durations else 0
            },
            'quality_metrics': {
                'avg_confidence': round(np.mean(confidences), 3) if confidences else 0,
                'min_confidence': round(np.min(confidences), 3) if confidences else 0,
                'max_confidence': round(np.max(confidences), 3) if confidences else 0,
                'avg_vietnamese_confidence': round(np.mean(vietnamese_confidences), 3) if vietnamese_confidences else 0
            },
            'performance': {
                'avg_duration': round(np.mean(durations), 2) if durations else 0,
                'total_processing_time': round(sum(durations), 2) if durations else 0
            }
        }
        
        return report

# Backward compatibility: expose expected class name
VietnameseTranscriber = RealTimeVietnameseTranscriber

# Configuration management
class TranscriberConfig:
    """Quản lý cấu hình cho transcriber"""
    
    @staticmethod
    def create_high_accuracy_config() -> TranscriptionConfig:
        """Cấu hình cho độ chính xác cao"""
        return TranscriptionConfig(
            chunk_duration=5.0,
            overlap_duration=1.0,
            min_confidence=0.8,
            use_vad=True,
            denoise_audio=True,
            language_detection=True
        )
    
    @staticmethod
    def create_real_time_config() -> TranscriptionConfig:
        """Cấu hình cho real-time processing"""
        return TranscriptionConfig(
            chunk_duration=2.0,
            overlap_duration=0.5,
            min_confidence=0.6,
            use_vad=True,
            denoise_audio=False,  # Skip for speed
            language_detection=False,
            max_workers=1
        )
    
    @staticmethod
    def create_fast_config() -> TranscriptionConfig:
        """Cấu hình cho xử lý nhanh"""
        return TranscriptionConfig(
            chunk_duration=3.0,
            overlap_duration=0.3,
            min_confidence=0.5,
            use_vad=False,
            denoise_audio=False,
            language_detection=False,
            max_workers=4
        )

# Main execution
def main():
    """Main function với command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vietnamese Speech Transcriber')
    parser.add_argument('--mode', choices=['test', 'flask', 'fastapi', 'batch'], 
                       default='test', help='Running mode')
    parser.add_argument('--file', type=str, help='Audio file to transcribe')
    parser.add_argument('--directory', type=str, help='Directory containing audio files')
    parser.add_argument('--output', type=str, help='Output file for results')
    parser.add_argument('--config', choices=['accuracy', 'realtime', 'fast'], 
                       default='accuracy', help='Configuration preset')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='API host')
    parser.add_argument('--port', type=int, default=8000, help='API port')
    
    args = parser.parse_args()
    
    # Select configuration
    config_map = {
        'accuracy': TranscriberConfig.create_high_accuracy_config(),
        'realtime': TranscriberConfig.create_real_time_config(),
        'fast': TranscriberConfig.create_fast_config()
    }
    config = config_map[args.config]
    
    if args.mode == 'test':
        if args.file:
            # Test specific file
            transcriber = RealTimeVietnameseTranscriber(config)
            result = transcriber.transcribe_audio_file(args.file)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Run default test
            test_transcriber()
    
    elif args.mode == 'batch':
        if not args.directory:
            print("❌ --directory required for batch mode")
            return
        
        transcriber = RealTimeVietnameseTranscriber(config)
        batch_processor = TranscriptionBatch(transcriber)
        
        results = batch_processor.process_directory(args.directory, args.output)
        report = batch_processor.generate_report(results)
        
        print("📊 Batch Processing Report:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.mode == 'flask':
        app = create_flask_app()
        if app:
            print(f"🚀 Starting Flask server on {args.host}:{args.port}")
            app.run(host=args.host, port=args.port, debug=False)
    
    elif args.mode == 'fastapi':
        app = create_fastapi_app()
        if app:
            try:
                import uvicorn
                print(f"🚀 Starting FastAPI server on {args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
            except ImportError:
                print("❌ uvicorn not installed. Install with: pip install uvicorn")

if __name__ == "__main__":
    main()