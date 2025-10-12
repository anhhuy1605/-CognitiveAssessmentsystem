"""
Generate Training Audio Data
Tạo audio files từ training sentences sử dụng TTS
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrainingAudioGenerator:
    """
    Tạo audio training data từ sentences
    """
    
    def __init__(self):
        self.training_data_dir = Path(__file__).parent / "training_data"
        self.audio_output_dir = self.training_data_dir / "audio"
        self.audio_output_dir.mkdir(exist_ok=True)
        
        # TTS settings
        self.sample_rate = 16000  # Whisper requirement
        self.audio_format = "wav"
        
    def _install_tts_dependencies(self):
        """Cài đặt TTS dependencies"""
        try:
            logger.info("📦 Installing TTS dependencies...")
            
            packages = [
                "gtts",           # Google Text-to-Speech
                "pyttsx3",       # Offline TTS
                "edge-tts",      # Microsoft Edge TTS
                "pydub",         # Audio processing
                "soundfile"      # Audio file handling
            ]
            
            for package in packages:
                logger.info(f"Installing {package}...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ])
            
            logger.info("✅ TTS dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to install TTS dependencies: {e}")
            return False
    
    def _load_training_sentences(self):
        """Load training sentences từ file JSON"""
        try:
            training_file = self.training_data_dir / "training_data.json"
            
            if not training_file.exists():
                logger.error("❌ Training data file not found. Run fine_tune_whisper.py first!")
                return []
            
            with open(training_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            sentences = [item["sentence"] for item in training_data]
            logger.info(f"✅ Loaded {len(sentences)} training sentences")
            return sentences
            
        except Exception as e:
            logger.error(f"❌ Failed to load training sentences: {e}")
            return []
    
    def _generate_audio_with_gtts(self, text: str, filename: str) -> bool:
        """Tạo audio sử dụng Google TTS"""
        try:
            from gtts import gTTS
            
            # Tạo TTS với tiếng Việt
            tts = gTTS(text=text, lang='vi', slow=False)
            
            # Lưu audio file
            audio_path = self.audio_output_dir / filename
            tts.save(str(audio_path))
            
            # Convert to 16kHz WAV nếu cần
            if audio_path.suffix != '.wav':
                self._convert_to_wav(audio_path)
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ gTTS failed for '{text[:30]}...': {e}")
            return False
    
    def _generate_audio_with_edge_tts(self, text: str, filename: str) -> bool:
        """Tạo audio sử dụng Microsoft Edge TTS"""
        try:
            import asyncio
            import edge_tts
            
            async def generate():
                communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")
                await communicate.save(str(self.audio_output_dir / filename))
            
            # Chạy async function
            asyncio.run(generate())
            
            # Convert to 16kHz WAV
            self._convert_to_wav(self.audio_output_dir / filename)
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Edge TTS failed for '{text[:30]}...': {e}")
            return False
    
    def _convert_to_wav(self, audio_path: Path):
        """Convert audio sang WAV 16kHz"""
        try:
            from pydub import AudioSegment
            
            # Load audio
            audio = AudioSegment.from_file(str(audio_path))
            
            # Convert to mono và 16kHz
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.sample_rate)
            
            # Lưu lại dưới dạng WAV
            wav_path = audio_path.with_suffix('.wav')
            audio.export(str(wav_path), format='wav')
            
            # Xóa file cũ nếu khác WAV
            if audio_path != wav_path:
                audio_path.unlink()
                
        except Exception as e:
            logger.warning(f"⚠️ Audio conversion failed: {e}")
    
    def _generate_audio_batch(self, sentences: List[str], batch_size: int = 10):
        """Tạo audio theo batch để tránh rate limiting"""
        try:
            logger.info(f"🎵 Generating audio for {len(sentences)} sentences...")
            
            successful_generations = 0
            
            for i in range(0, len(sentences), batch_size):
                batch = sentences[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(sentences) + batch_size - 1)//batch_size}")
                
                for j, sentence in enumerate(batch):
                    sentence_index = i + j
                    filename = f"training_{sentence_index:05d}.{self.audio_format}"
                    
                    # Thử các TTS methods khác nhau
                    success = False
                    
                    # Method 1: Edge TTS (Microsoft)
                    if not success:
                        success = self._generate_audio_with_edge_tts(sentence, filename)
                    
                    # Method 2: Google TTS
                    if not success:
                        success = self._generate_audio_with_gtts(sentence, filename)
                    
                    if success:
                        successful_generations += 1
                        logger.info(f"✅ Generated audio {sentence_index + 1}/{len(sentences)}: {sentence[:50]}...")
                    else:
                        logger.warning(f"⚠️ Failed to generate audio for: {sentence[:50]}...")
                    
                    # Delay để tránh rate limiting
                    time.sleep(0.5)
                
                # Delay giữa các batch
                if i + batch_size < len(sentences):
                    logger.info("⏳ Waiting between batches...")
                    time.sleep(2)
            
            logger.info(f"✅ Audio generation completed: {successful_generations}/{len(sentences)} successful")
            return successful_generations
            
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {e}")
            return 0
    
    def _update_training_data(self, successful_count: int):
        """Cập nhật training data với audio files thực tế"""
        try:
            training_file = self.training_data_dir / "training_data.json"
            
            if not training_file.exists():
                logger.warning("⚠️ Training data file not found")
                return
            
            # Load existing data
            with open(training_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            # Update với audio files thực tế
            for i, item in enumerate(training_data):
                audio_filename = f"training_{i:05d}.{self.audio_format}"
                audio_path = self.audio_output_dir / audio_filename
                
                if audio_path.exists():
                    item["audio_file_path"] = str(audio_path.relative_to(self.training_data_dir))
                    item["audio_exists"] = True
                    item["audio_duration"] = self._get_audio_duration(audio_path)
                else:
                    item["audio_exists"] = False
                    item["audio_duration"] = 0
            
            # Lưu updated data
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Updated training data with audio file information")
            
        except Exception as e:
            logger.error(f"❌ Failed to update training data: {e}")
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Lấy duration của audio file"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio) / 1000.0  # Convert to seconds
        except:
            return 0.0
    
    def _create_audio_summary(self):
        """Tạo summary về audio files"""
        try:
            audio_files = list(self.audio_output_dir.glob(f"*.{self.audio_format}"))
            
            summary = {
                "total_audio_files": len(audio_files),
                "audio_format": self.audio_format,
                "sample_rate": self.sample_rate,
                "total_duration": sum(self._get_audio_duration(f) for f in audio_files),
                "files": [
                    {
                        "filename": f.name,
                        "size_mb": f.stat().st_size / (1024 * 1024),
                        "duration": self._get_audio_duration(f)
                    }
                    for f in audio_files
                ]
            }
            
            summary_file = self.audio_output_dir / "audio_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Created audio summary")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to create audio summary: {e}")
            return None
    
    def generate_all_audio(self):
        """Tạo tất cả audio files"""
        try:
            logger.info("🚀 Starting audio generation for training data...")
            
            # 1. Install dependencies
            if not self._install_tts_dependencies():
                raise Exception("Failed to install TTS dependencies")
            
            # 2. Load training sentences
            sentences = self._load_training_sentences()
            if not sentences:
                raise Exception("No training sentences found")
            
            # 3. Generate audio files
            successful_count = self._generate_audio_batch(sentences)
            
            if successful_count > 0:
                # 4. Update training data
                self._update_training_data(successful_count)
                
                # 5. Create summary
                summary = self._create_audio_summary()
                
                logger.info("✅ Audio generation completed successfully!")
                logger.info(f"📁 Audio files saved to: {self.audio_output_dir}")
                logger.info(f"📊 Summary: {summary['total_audio_files']} files, {summary['total_duration']:.1f}s total")
                
                return True
            else:
                logger.error("❌ No audio files were generated successfully")
                return False
                
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {e}")
            return False

def main():
    """Main function"""
    try:
        generator = TrainingAudioGenerator()
        
        print("🎵 Vietnamese Training Audio Generator")
        print("1. Generate all audio files")
        print("2. Check existing audio files")
        
        choice = input("Chọn option (1 hoặc 2): ").strip()
        
        if choice == "1":
            generator.generate_all_audio()
        elif choice == "2":
            audio_dir = generator.audio_output_dir
            if audio_dir.exists():
                audio_files = list(audio_dir.glob("*.wav"))
                print(f"📁 Found {len(audio_files)} audio files in {audio_dir}")
                for f in audio_files[:5]:  # Show first 5
                    print(f"  - {f.name}")
                if len(audio_files) > 5:
                    print(f"  ... and {len(audio_files) - 5} more")
            else:
                print("❌ No audio directory found")
        else:
            print("❌ Invalid choice")
            
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
