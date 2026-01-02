"""
Audio Preprocessor for MMSE Assessment
Converts any audio format to analysis-ready WAV (16kHz, mono, PCM)
OPTIMIZED: Fast format check using ffprobe, optimized FFmpeg flags
"""

import subprocess
import tempfile
import os
import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """
    Optimized audio preprocessor with format checking
    """
    def __init__(self, target_sr=16000, target_channels=1):
        self.target_sr = target_sr
        self.target_channels = target_channels
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Verify FFmpeg is available"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            logger.info("✅ FFmpeg available")
        except Exception as e:
            logger.error(f"❌ FFmpeg not found: {e}")
            raise Exception("FFmpeg is required but not found")
    
    def convert(self, input_file: str, output_file: str = None) -> str:
        """
        Convert audio to WAV 16kHz mono (optimized)
        
        Returns:
            str: Path to preprocessed audio file
        """
        if not input_file or not os.path.exists(input_file):
            raise FileNotFoundError(f"Audio file not found: {input_file}")
        
        start_time = time.time()
        
        # Generate output path if not provided
        if output_file is None:
            output_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                prefix='preprocessed_',
                delete=False
            ).name
        
        # Step 1: Check if already in correct format (FAST!)
        if self._is_correct_format(input_file):
            elapsed = time.time() - start_time
            logger.info(f"✅ Audio already in correct format ({elapsed:.2f}s): {input_file}")
            return input_file
        
        # Step 2: Convert with optimized FFmpeg
        logger.info(f"🔧 Converting: {input_file} → {output_file}")
        
        cmd = [
            'ffmpeg',
            '-y',                              # Overwrite output
            '-hide_banner',                    # Less verbose
            '-loglevel', 'error',              # Only errors
            '-i', input_file,                  # Input
            '-ac', str(self.target_channels),  # Mono
            '-ar', str(self.target_sr),        # 16kHz
            '-acodec', 'pcm_s16le',            # 16-bit PCM
            '-f', 'wav',                       # WAV format
            output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=30,  # Max 30 seconds
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            elapsed = time.time() - start_time
            file_size = Path(output_file).stat().st_size / 1024  # KB
            
            logger.info(f"✅ Audio converted in {elapsed:.2f}s: {input_file} → {output_file} ({file_size:.1f} KB)")
            
            # Verify output file exists and has content
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                raise RuntimeError("Conversion produced empty file")
            
            return output_file
            
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            logger.error(f"❌ FFmpeg timeout after {elapsed:.0f}s")
            # Clean up failed output file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            raise Exception("Audio conversion timeout (>30s)")
        
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"❌ FFmpeg error after {elapsed:.2f}s: {error_msg}")
            # Clean up failed output file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            raise Exception(f"Audio conversion failed: {error_msg}")
    
    def _is_correct_format(self, file_path: str) -> bool:
        """
        Quick check if file is already WAV 16kHz mono
        Uses ffprobe to inspect without decoding entire file
        
        Returns:
            bool: True if format is correct
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,sample_rate,channels',
                '-of', 'json',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            
            info = json.loads(result.stdout)
            
            if 'streams' not in info or len(info['streams']) == 0:
                logger.warning(f"⚠️ No audio stream found in {file_path}")
                return False
            
            stream = info['streams'][0]
            codec = stream.get('codec_name', '')
            sample_rate = int(stream.get('sample_rate', 0))
            channels = int(stream.get('channels', 0))
            
            is_correct = (
                codec in ['pcm_s16le', 'pcm_s16be'] and
                sample_rate == self.target_sr and
                channels == self.target_channels
            )
            
            if is_correct:
                logger.info(f"✅ Format check passed: {codec}, {sample_rate}Hz, {channels}ch")
            else:
                logger.info(f"ℹ️ Format conversion needed: {codec}, {sample_rate}Hz, {channels}ch → WAV 16kHz mono")
            
            return is_correct
            
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ ffprobe timeout for {file_path}")
            return False
        
        except Exception as e:
            logger.warning(f"⚠️ Format check failed: {e}")
            return False
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        Get detailed audio file information
        
        Returns:
            dict: Audio properties
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_format',
                '-show_streams',
                '-of', 'json',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            
            info = json.loads(result.stdout)
            
            if 'streams' in info and len(info['streams']) > 0:
                stream = info['streams'][0]
                return {
                    'codec': stream.get('codec_name'),
                    'sample_rate': int(stream.get('sample_rate', 0)),
                    'channels': int(stream.get('channels', 0)),
                    'duration': float(info.get('format', {}).get('duration', 0)),
                    'size': int(info.get('format', {}).get('size', 0))
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get audio info: {e}")
            return {}


# ✅ Backward compatibility: Create singleton instance and function wrapper
_preprocessor_instance = None

def _get_preprocessor():
    """Get or create singleton preprocessor instance"""
    global _preprocessor_instance
    if _preprocessor_instance is None:
        _preprocessor_instance = AudioPreprocessor()
    return _preprocessor_instance

def preprocess_audio_for_analysis(input_file: str) -> str:
    """
    OPTIMIZED: Convert any audio format to analysis-ready WAV (backward compatibility)
    - Fast format check using ffprobe (avoids unnecessary conversion)
    - Optimized FFmpeg flags for faster conversion
    - Timeout protection
    
    Args:
        input_file: Path to audio file (webm, mp3, wav, etc.)
    
    Returns:
        Path to processed WAV file (16kHz, mono, PCM)
    """
    preprocessor = _get_preprocessor()
    return preprocessor.convert(input_file)


def cleanup_temp_audio(file_path: str):
    """
    Clean up temporary audio file
    
    Args:
        file_path: Path to temporary file to delete
    """
    if file_path and os.path.exists(file_path) and 'preprocessed_' in file_path:
        try:
            os.remove(file_path)
            logger.debug(f"🧹 Cleaned up temp audio: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not clean up temp file {file_path}: {e}")
