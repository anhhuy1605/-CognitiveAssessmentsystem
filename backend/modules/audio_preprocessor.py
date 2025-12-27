"""
Audio Preprocessor for MMSE Assessment
Converts any audio format to analysis-ready WAV (16kHz, mono, PCM)
"""

import subprocess
import tempfile
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def preprocess_audio_for_analysis(input_file: str) -> str:
    """
    Convert any audio format to analysis-ready WAV
    
    Args:
        input_file: Path to audio file (webm, mp3, wav, etc.)
    
    Returns:
        Path to processed WAV file (16kHz, mono, PCM)
    """
    if not input_file or not os.path.exists(input_file):
        raise FileNotFoundError(f"Audio file not found: {input_file}")
    
    # Check if already correct format
    if input_file.endswith('.wav'):
        try:
            import soundfile as sf
            info = sf.info(input_file)
            if info.samplerate == 16000 and info.channels == 1:
                logger.info(f"✅ Audio already in correct format: {input_file}")
                return input_file  # Already correct
        except Exception as e:
            logger.warning(f"⚠️ Could not verify WAV format: {e}, will convert anyway")
    
    # Create temp WAV file
    output_file = tempfile.NamedTemporaryFile(
        delete=False, 
        suffix='.wav',
        prefix='preprocessed_'
    ).name
    
    # Convert with FFmpeg
    cmd = [
        'ffmpeg', '-y',
        '-i', input_file,
        '-ac', '1',              # Mono
        '-ar', '16000',          # 16kHz sample rate
        '-sample_fmt', 's16',    # 16-bit PCM (required by Parselmouth)
        '-acodec', 'pcm_s16le',  # PCM codec
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        logger.info(f"✅ Audio converted: {input_file} → {output_file}")
        
        # Verify output file exists and has content
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            raise RuntimeError("Conversion produced empty file")
        
        return output_file
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ FFmpeg conversion timeout for {input_file}")
        raise RuntimeError("Audio conversion timeout")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg failed: {e.stderr}")
        # Clean up failed output file
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass
        raise RuntimeError(f"Audio conversion failed: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ Audio preprocessing error: {e}")
        # Clean up on any error
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass
        raise


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

