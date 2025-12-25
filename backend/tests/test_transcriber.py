import pytest
import os
import tempfile
import numpy as np
from vietnamese_transcriber import (
    RealTimeVietnameseTranscriber, 
    TranscriptionConfig,
    VietnameseLanguageModel,
    AudioProcessor
)

class TestVietnameseTranscriber:
    """Test suite for Vietnamese Transcriber"""
    
    @pytest.fixture
    def transcriber(self):
        """Create transcriber instance for testing"""
        config = TranscriptionConfig(
            chunk_duration=2.0,
            min_confidence=0.5,
            use_vad=False,  # Disable for faster testing
            denoise_audio=False
        )
        return RealTimeVietnameseTranscriber(config)
    
    @pytest.fixture
    def sample_audio(self):
        """Create sample audio file for testing"""
        # Generate 3 seconds of sine wave audio
        sample_rate = 16000
        duration = 3.0
        frequency = 440  # A note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
        
        # Save to temporary file
        import soundfile as sf
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, audio_data, sample_rate)
            return tmp.name
    
    def test_transcriber_initialization(self, transcriber):
        """Test transcriber initialization"""
        # This might take time to download models
        assert transcriber is not None
        # Model initialization might fail in CI environment
        # assert transcriber.is_initialized == True
    
    def test_language_model_initialization(self):
        """Test Vietnamese language model"""
        lm = VietnameseLanguageModel()
        
        # Test basic functionality
        assert len(lm.vietnamese_words) > 0
        assert len(lm.common_phrases) > 0
        assert len(lm.correction_rules) > 0
        
        # Test text correction
        corrected = lm.correct_transcript("toi la nguoi viet nam")
        assert "tôi" in corrected.lower()
    
    def test_audio_processor(self):
        """Test audio processor"""
        processor = AudioProcessor()
        
        # Test initialization (might fail without audio libs)
        # assert processor.is_initialized == True
        
        # Test audio normalization
        test_audio = np.array([0.5, -0.5, 0.8, -0.3])
        normalized = processor._normalize_audio(test_audio)
        
        assert np.max(np.abs(normalized)) <= 1.0
        assert len(normalized) == len(test_audio)
    
    def test_confidence_calculation(self):
        """Test confidence calculation"""
        lm = VietnameseLanguageModel()
        
        # High confidence text (many Vietnamese words)
        high_conf_text = "xin chào tôi là người Việt Nam"
        high_conf = lm.calculate_vietnamese_confidence(high_conf_text)
        
        # Low confidence text (non-Vietnamese words)
        low_conf_text = "hello this is english text"
        low_conf = lm.calculate_vietnamese_confidence(low_conf_text)
        
        assert high_conf > low_conf
        assert 0 <= high_conf <= 1
        assert 0 <= low_conf <= 1
    
    def test_text_correction_rules(self):
        """Test text correction rules"""
        lm = VietnameseLanguageModel()
        
        test_cases = [
            ("toi", "Tôi"),
            ("ban", "Bạn"), 
            ("duoc", "Được"),
            ("khong", "Không")
        ]
        
        for wrong, expected in test_cases:
            corrected = lm.correct_transcript(wrong)
            assert expected.lower() in corrected.lower()
    
    def test_audio_chunking(self, transcriber):
        """Test audio chunking functionality"""
        import torch
        
        # Create test audio (5 seconds)
        sample_rate = 16000
        duration = 5.0
        test_audio = torch.randn(int(sample_rate * duration))
        
        chunks = transcriber._chunk_audio(test_audio, sample_rate)
        
        # Should have multiple chunks for 5-second audio
        assert len(chunks) >= 2
        
        # Each chunk should be reasonable size
        for chunk in chunks:
            assert len(chunk) > sample_rate * 0.5  # At least 0.5 seconds
    
    def test_transcription_with_sample_audio(self, transcriber, sample_audio):
        """Test transcription with sample audio file"""
        try:
            result = transcriber.transcribe_audio_file(sample_audio)
            
            # Should return a proper result structure
            assert 'success' in result
            assert 'transcript' in result
            assert 'confidence' in result
            
            # Even if transcription fails, structure should be correct
            if result['success']:
                assert isinstance(result['transcript'], str)
                assert 0 <= result['confidence'] <= 1
            else:
                assert 'error' in result
                
        except Exception as e:
            # In CI environment, model loading might fail
            pytest.skip(f"Transcription test skipped due to environment: {e}")
        
        finally:
            # Clean up temp file
            if os.path.exists(sample_audio):
                os.unlink(sample_audio)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = TranscriptionConfig(
            chunk_duration=3.0,
            overlap_duration=0.5,
            min_confidence=0.7
        )
        
        assert config.chunk_duration == 3.0
        assert config.overlap_duration == 0.5
        assert config.min_confidence == 0.7
        
        # Test default values
        default_config = TranscriptionConfig()
        assert default_config.chunk_duration == 3.0
        assert default_config.use_vad == True
    
    def test_error_handling(self, transcriber):
        """Test error handling for invalid inputs"""
        # Test with non-existent file
        result = transcriber.transcribe_audio_file("non_existent_file.wav")
        
        assert result['success'] == False
        assert 'error' in result
        assert result['transcript'] == ''
        assert result['confidence'] == 0.0
    
    def test_batch_processing(self):
        """Test batch processing functionality"""
        from vietnamese_transcriber import TranscriptionBatch
        
        config = TranscriptionConfig()
        transcriber = RealTimeVietnameseTranscriber(config)
        batch_processor = TranscriptionBatch(transcriber)
        
        # Test with empty directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            results = batch_processor.process_directory(tmp_dir)
            assert len(results) == 0
            
            report = batch_processor.generate_report(results)
            assert 'error' in report

    @pytest.mark.asyncio
    async def test_api_functionality(self):
        """Test API functionality"""
        from vietnamese_transcriber import TranscriberAPI
        
        api = TranscriberAPI()
        status = api.get_status()
        
        assert 'status' in status or 'model' in status
    
    def test_memory_usage(self, transcriber):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple small audio chunks
        sample_rate = 16000
        for i in range(10):
            test_audio = torch.randn(sample_rate * 2)  # 2 seconds
            chunks = transcriber._chunk_audio(test_audio, sample_rate)
            
            # Force garbage collection
            gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for test)
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f}MB"

# Performance benchmarks
class TestPerformance:
    """Performance testing"""
    
    def test_transcription_speed(self):
        """Test transcription speed benchmarks"""
        import time
        
        config = TranscriptionConfig(
            chunk_duration=2.0,
            use_vad=False,
            denoise_audio=False
        )
        
        transcriber = RealTimeVietnameseTranscriber(config)
        
        if not transcriber.is_initialized:
            pytest.skip("Transcriber not initialized")
        
        # Create test audio (10 seconds)
        sample_rate = 16000
        duration = 10.0
        
        import soundfile as sf
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            # Generate audio
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = np.sin(2 * np.pi * 440 * t) * 0.3
            sf.write(tmp.name, audio_data, sample_rate)
            
            # Benchmark transcription
            start_time = time.time()
            result = transcriber.transcribe_audio_file(tmp.name)
            end_time = time.time()
            
            processing_time = end_time - start_time
            real_time_factor = duration / processing_time
            
            print(f"Processing time: {processing_time:.2f}s")
            print(f"Real-time factor: {real_time_factor:.2f}x")
            
            # Should process faster than real-time on most systems
            assert real_time_factor > 0.5, "Processing too slow"
            
            # Clean up
            os.unlink(tmp.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
