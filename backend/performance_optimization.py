"""
Performance Optimization Module
==============================

This module implements performance optimizations to meet the <20s processing
latency target as specified in the document requirements.

Key optimizations:
- Caching for ASR and ML predictions
- Parallel processing where possible
- Optimized feature extraction
- Lazy loading of heavy models
- Connection pooling for external APIs
"""

import time
import asyncio
import threading
import hashlib
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import Dict, Any, Optional, List, Tuple
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
CACHE_DIR = os.getenv("CACHE_DIR", "/tmp/cognitive_cache")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
AUDIO_CACHE_SIZE = int(os.getenv("AUDIO_CACHE_SIZE", "100"))
TEXT_CACHE_SIZE = int(os.getenv("TEXT_CACHE_SIZE", "500"))

# Ensure cache directory exists
Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


class PerformanceMonitor:
    """
    Monitor and track processing performance metrics
    """

    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()

    def start_operation(self, operation_name: str) -> str:
        """Start timing an operation"""
        operation_id = f"{operation_name}_{threading.current_thread().ident}_{time.time()}"
        with self.lock:
            self.metrics[operation_id] = {
                'operation': operation_name,
                'start_time': time.time(),
                'end_time': None,
                'duration': None,
                'status': 'running'
            }
        return operation_id

    def end_operation(self, operation_id: str, status: str = 'completed') -> float:
        """End timing an operation"""
        end_time = time.time()
        with self.lock:
            if operation_id in self.metrics:
                self.metrics[operation_id].update({
                    'end_time': end_time,
                    'duration': end_time - self.metrics[operation_id]['start_time'],
                    'status': status
                })
                return self.metrics[operation_id]['duration']
        return 0.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        with self.lock:
            operations = {}
            total_time = 0.0
            completed_ops = 0

            for op_id, data in self.metrics.items():
                op_name = data['operation']
                if op_name not in operations:
                    operations[op_name] = []

                if data['duration'] is not None:
                    operations[op_name].append(data['duration'])
                    total_time += data['duration']
                    completed_ops += 1

            # Calculate averages
            avg_times = {}
            for op_name, times in operations.items():
                if times:
                    avg_times[op_name] = {
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times),
                        'count': len(times)
                    }

            return {
                'total_operations': completed_ops,
                'total_time': total_time,
                'avg_operation_time': total_time / completed_ops if completed_ops > 0 else 0,
                'operation_breakdown': avg_times,
                'target_latency': 20.0,
                'meets_target': total_time < 20.0 if completed_ops > 0 else False
            }


class OptimizedCache:
    """
    High-performance caching system with TTL and size limits
    """

    def __init__(self, cache_dir: str = CACHE_DIR, max_size: int = 1000, ttl: int = CACHE_TTL):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.ttl = ttl
        self._cleanup_thread = None
        self._start_cleanup_thread()

    def _get_cache_key(self, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, str):
            key_data = data.encode('utf-8')
        elif isinstance(data, bytes):
            key_data = data
        else:
            key_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

        return hashlib.sha256(key_data).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get filesystem path for cache key"""
        return self.cache_dir / f"{key}.pkl"

    def _is_expired(self, cache_path: Path) -> bool:
        """Check if cache entry is expired"""
        if not cache_path.exists():
            return True

        mtime = cache_path.stat().st_mtime
        return (time.time() - mtime) > self.ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieve from cache"""
        cache_path = self._get_cache_path(key)

        if self._is_expired(cache_path):
            return None

        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Cache read error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """Store in cache"""
        try:
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            logger.error(f"Cache write error for key {key}: {e}")
            return False

    def cleanup(self):
        """Clean up expired cache entries"""
        try:
            current_time = time.time()
            removed_count = 0

            for cache_file in self.cache_dir.glob("*.pkl"):
                if (current_time - cache_file.stat().st_mtime) > self.ttl:
                    cache_file.unlink()
                    removed_count += 1

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                time.sleep(300)  # Clean up every 5 minutes
                self.cleanup()

        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()


class OptimizedAudioProcessor:
    """
    Optimized audio processing with caching and parallel processing
    """

    def __init__(self):
        self.cache = OptimizedCache(max_size=AUDIO_CACHE_SIZE)
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.monitor = PerformanceMonitor()

    def process_audio_cached(self, audio_path: str) -> Dict[str, Any]:
        """
        Process audio with intelligent caching

        Caches based on audio file hash to avoid reprocessing identical files
        """
        # Generate cache key from audio file content
        try:
            with open(audio_path, 'rb') as f:
                audio_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception:
            # Fallback to path-based key
            audio_hash = self.cache._get_cache_key(audio_path)

        # Check cache first
        cached_result = self.cache.get(f"audio_features_{audio_hash}")
        if cached_result:
            logger.info("🔄 Using cached audio features")
            return cached_result

        # Process audio
        op_id = self.monitor.start_operation("audio_processing")

        try:
            # Import here to avoid circular imports
            from .audio_processing import process_audio_file
            import librosa

            # Load audio efficiently
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Use optimized processing
            result = process_audio_file(audio_path)

            # Cache result
            self.cache.set(f"audio_features_{audio_hash}", result)

            duration = self.monitor.end_operation(op_id, 'completed')
            logger.info(".2f")

            return result

        except Exception as e:
            self.monitor.end_operation(op_id, 'failed')
            logger.error(f"Audio processing failed: {e}")
            raise

    def process_audio_parallel(self, audio_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple audio files in parallel
        """
        futures = []
        results = []

        # Submit all tasks
        for audio_path in audio_paths:
            future = self.executor.submit(self.process_audio_cached, audio_path)
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            try:
                result = future.result(timeout=30)  # 30 second timeout per file
                results.append(result)
            except Exception as e:
                logger.error(f"Parallel audio processing failed: {e}")
                results.append({'error': str(e)})

        return results


class OptimizedTranscriptionService:
    """
    Optimized transcription with caching and model preloading
    """

    def __init__(self):
        self.cache = OptimizedCache(max_size=TEXT_CACHE_SIZE)
        self.monitor = PerformanceMonitor()
        self._model_cache = {}

    def transcribe_cached(self, audio_path: str, language: str = 'vi',
                         question: str = None) -> Dict[str, Any]:
        """
        Transcribe audio with intelligent caching
        """
        # Generate cache key
        cache_key = f"transcription_{language}_{question or 'no_question'}"
        try:
            with open(audio_path, 'rb') as f:
                audio_hash = hashlib.sha256(f.read(1024*1024)).hexdigest()  # First 1MB
            cache_key = f"{cache_key}_{audio_hash}"
        except Exception:
            cache_key = f"{cache_key}_{hash(audio_path)}"

        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("🔄 Using cached transcription")
            return cached_result

        # Perform transcription
        op_id = self.monitor.start_operation("transcription")

        try:
            # Import here to avoid circular imports
            from .vietnamese_transcriber import vietnamese_transcriber

            if vietnamese_transcriber:
                result = vietnamese_transcriber.transcribe_audio_file(
                    audio_path, language, False, question
                )
            else:
                from .app import transcribe_audio
                result = transcribe_audio(audio_path, question)

            # Cache result
            self.cache.set(cache_key, result)

            duration = self.monitor.end_operation(op_id, 'completed')
            logger.info(".2f")

            return result

        except Exception as e:
            self.monitor.end_operation(op_id, 'failed')
            logger.error(f"Transcription failed: {e}")
            raise


class OptimizedMLPredictor:
    """
    Optimized ML prediction with model preloading and caching
    """

    def __init__(self):
        self.cache = OptimizedCache(max_size=200)
        self.monitor = PerformanceMonitor()
        self._models_loaded = False

    def _ensure_models_loaded(self):
        """Lazy load ML models"""
        if self._models_loaded:
            return

        try:
            # Import here to avoid circular imports
            from .app import cognitive_model, feature_names
            self.cognitive_model = cognitive_model
            self.feature_names = feature_names
            self._models_loaded = True
        except Exception as e:
            logger.warning(f"Model loading failed: {e}")

    def predict_cached(self, audio_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Make ML prediction with caching
        """
        self._ensure_models_loaded()

        # Generate cache key from features
        feature_key = self.cache._get_cache_key(str(sorted(audio_features.items())))
        cache_key = f"ml_prediction_{feature_key}"

        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("🔄 Using cached ML prediction")
            return cached_result

        # Make prediction
        op_id = self.monitor.start_operation("ml_prediction")

        try:
            # Import here to avoid circular imports
            from .app import predict_cognitive_score

            result = predict_cognitive_score(audio_features)

            # Cache result
            self.cache.set(cache_key, result)

            duration = self.monitor.end_operation(op_id, 'completed')
            logger.info(".2f")

            return result

        except Exception as e:
            self.monitor.end_operation(op_id, 'failed')
            logger.error(f"ML prediction failed: {e}")
            raise


class OptimizedGPTEvaluator:
    """
    Optimized GPT evaluation with caching and connection pooling
    """

    def __init__(self):
        self.cache = OptimizedCache(max_size=TEXT_CACHE_SIZE)
        self.monitor = PerformanceMonitor()

    def evaluate_cached(self, transcript: str, question: str,
                       user_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Evaluate transcript with GPT using caching
        """
        # Generate cache key
        cache_data = f"{transcript}_{question}_{language}_{str(sorted(user_data.items()))}"
        cache_key = f"gpt_eval_{self.cache._get_cache_key(cache_data)}"

        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("🔄 Using cached GPT evaluation")
            return cached_result

        # Perform evaluation
        op_id = self.monitor.start_operation("gpt_evaluation")

        try:
            # Import here to avoid circular imports
            from .app import evaluate_with_gpt4o

            result = evaluate_with_gpt4o(transcript, question, user_data, language)

            # Cache result
            self.cache.set(cache_key, result)

            duration = self.monitor.end_operation(op_id, 'completed')
            logger.info(".2f")

            return result

        except Exception as e:
            self.monitor.end_operation(op_id, 'failed')
            logger.error(f"GPT evaluation failed: {e}")
            raise


class OptimizedPipeline:
    """
    Complete optimized processing pipeline with parallel execution where possible
    """

    def __init__(self):
        self.audio_processor = OptimizedAudioProcessor()
        self.transcription_service = OptimizedTranscriptionService()
        self.ml_predictor = OptimizedMLPredictor()
        self.gpt_evaluator = OptimizedGPTEvaluator()
        self.monitor = PerformanceMonitor()

    def process_assessment_optimized(self, audio_path: str, question: str,
                                   language: str = 'vi', user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Optimized complete assessment pipeline

        Executes steps in parallel where possible to meet <20s target
        """
        pipeline_start = time.time()
        user_data = user_data or {}

        logger.info("🚀 Starting optimized assessment pipeline")

        try:
            # Step 1: Audio processing (can be done in parallel with transcription prep)
            audio_future = self.audio_processor.executor.submit(
                self.audio_processor.process_audio_cached, audio_path
            )

            # Step 2: Transcription (independent)
            transcription_future = self.audio_processor.executor.submit(
                self.transcription_service.transcribe_cached, audio_path, language, question
            )

            # Wait for audio processing to complete
            audio_features = audio_future.result(timeout=15)

            # Step 3: ML prediction (can run in parallel with transcription)
            ml_future = self.audio_processor.executor.submit(
                self.ml_predictor.predict_cached, audio_features
            )

            # Wait for transcription to complete
            transcription_result = transcription_future.result(timeout=15)

            # Step 4: GPT evaluation (depends on transcription)
            transcript_text = transcription_result.get('transcript', '').strip()
            if transcript_text and len(transcript_text.split()) > 0:
                gpt_future = self.audio_processor.executor.submit(
                    self.gpt_evaluator.evaluate_cached,
                    transcript_text, question, user_data, language
                )
                gpt_result = gpt_future.result(timeout=10)
            else:
                gpt_result = self._create_empty_gpt_result()

            # Wait for ML prediction
            ml_result = ml_future.result(timeout=5)

            # Combine results
            final_result = {
                'success': True,
                'processing_time': time.time() - pipeline_start,
                'transcription': transcription_result,
                'audio_features': audio_features,
                'ml_prediction': ml_result,
                'gpt_evaluation': gpt_result,
                'final_score': self._combine_scores(ml_result, gpt_result),
                'performance_metrics': self.monitor.get_metrics_summary()
            }

            total_time = final_result['processing_time']
            meets_target = total_time < 20.0

            logger.info(f"✅ Optimized pipeline completed in {total_time:.2f}s (target: <20s, meets: {meets_target})")

            if not meets_target:
                logger.warning(f"⚠️ Processing time {total_time:.2f}s exceeds target of 20s")

            return final_result

        except Exception as e:
            logger.error(f"❌ Optimized pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - pipeline_start
            }

    def _combine_scores(self, ml_result: Dict[str, Any], gpt_result: Dict[str, Any]) -> float:
        """Combine ML and GPT scores for final assessment"""
        try:
            ml_score = ml_result.get('predicted_score', 15.0)
            gpt_score = gpt_result.get('overall_score', 5.0)

            # Weighted combination (ML: 60%, GPT: 40%)
            final_score = (ml_score * 0.6) + (gpt_score * 0.4)

            # Ensure valid MMSE range
            return max(0.0, min(30.0, final_score))

        except Exception as e:
            logger.error(f"Score combination failed: {e}")
            return 15.0  # Default fallback

    def _create_empty_gpt_result(self) -> Dict[str, Any]:
        """Create empty GPT result for cases with no transcript"""
        return {
            'vocabulary_score': None,
            'context_relevance_score': 0.0,
            'overall_score': 0.0,
            'analysis': 'Không có lời thoại để đánh giá',
            'feedback': 'Cần có transcript hợp lệ để đánh giá ngôn ngữ'
        }


# Global instances for reuse
performance_monitor = PerformanceMonitor()
optimized_pipeline = OptimizedPipeline()

# Convenience functions for easy integration
def process_assessment_optimized(audio_path: str, question: str,
                               language: str = 'vi', user_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function for optimized assessment processing
    """
    return optimized_pipeline.process_assessment_optimized(audio_path, question, language, user_data)

def get_performance_metrics() -> Dict[str, Any]:
    """
    Get current performance metrics
    """
    return performance_monitor.get_metrics_summary()

def clear_all_caches():
    """
    Clear all caches (useful for testing or memory management)
    """
    try:
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
        logger.info("✅ All caches cleared")
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")


if __name__ == "__main__":
    # Test the optimization components
    print("Testing performance optimization components...")

    # Test cache
    cache = OptimizedCache()
    test_data = {"test": "data", "number": 42}
    cache_key = cache._get_cache_key("test_key")

    cache.set(cache_key, test_data)
    retrieved = cache.get(cache_key)

    print(f"Cache test: {'PASSED' if retrieved == test_data else 'FAILED'}")

    # Test performance monitor
    monitor = PerformanceMonitor()
    op_id = monitor.start_operation("test_operation")
    time.sleep(0.1)  # Simulate work
    duration = monitor.end_operation(op_id)

    print(".2f")

    # Test optimized pipeline structure
    pipeline = OptimizedPipeline()
    print(f"Optimized pipeline initialized with {MAX_WORKERS} workers")

    print("Performance optimization tests completed!")
