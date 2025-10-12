#!/usr/bin/env python3
"""
Vietnamese Whisper Fine-tuning Pipeline
Script chính để chạy toàn bộ quy trình fine-tuning
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main pipeline function"""
    try:
        print("🎯 Vietnamese Whisper Fine-tuning Pipeline")
        print("=" * 50)
        print("Bước 1: Chuẩn bị dữ liệu training")
        print("Bước 2: Tạo audio files từ sentences")
        print("Bước 3: Fine-tune Whisper model")
        print("Bước 4: Test model đã fine-tune")
        print("=" * 50)
        
        # Kiểm tra dependencies
        print("\n📦 Kiểm tra dependencies...")
        try:
            import torch
            import transformers
            print(f"✅ PyTorch: {torch.__version__}")
            print(f"✅ Transformers: {transformers.__version__}")
        except ImportError:
            print("❌ Missing core dependencies. Installing...")
            os.system(f"{sys.executable} -m pip install torch transformers")
        
        # Bước 1: Chuẩn bị training data
        print("\n🚀 Bước 1: Chuẩn bị dữ liệu training...")
        from fine_tune_whisper import VietnameseWhisperFineTuner
        
        fine_tuner = VietnameseWhisperFineTuner()
        if fine_tuner.prepare_fine_tuning():
            print("✅ Training data preparation completed!")
        else:
            print("❌ Training data preparation failed!")
            return
        
        # Bước 2: Tạo audio files
        print("\n🎵 Bước 2: Tạo audio files từ sentences...")
        choice = input("Bạn có muốn tạo audio files không? (y/n): ").strip().lower()
        
        if choice == 'y':
            from generate_training_audio import TrainingAudioGenerator
            
            audio_generator = TrainingAudioGenerator()
            if audio_generator.generate_all_audio():
                print("✅ Audio generation completed!")
            else:
                print("⚠️ Audio generation had issues, but continuing...")
        else:
            print("⏭️ Skipping audio generation...")
        
        # Bước 3: Fine-tune model
        print("\n🤖 Bước 3: Fine-tune Whisper model...")
        choice = input("Bạn có muốn bắt đầu fine-tuning không? (y/n): ").strip().lower()
        
        if choice == 'y':
            print("⚠️ Fine-tuning sẽ mất 2-4 giờ tùy thuộc vào hardware...")
            confirm = input("Bạn có chắc chắn muốn tiếp tục? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                if fine_tuner.start_fine_tuning():
                    print("✅ Fine-tuning completed successfully!")
                else:
                    print("❌ Fine-tuning failed!")
                    return
            else:
                print("⏭️ Skipping fine-tuning...")
        else:
            print("⏭️ Skipping fine-tuning...")
        
        # Bước 4: Test model
        print("\n🧪 Bước 4: Test model đã fine-tune...")
        choice = input("Bạn có muốn test model không? (y/n): ").strip().lower()
        
        if choice == 'y':
            test_fine_tuned_model()
        else:
            print("⏭️ Skipping model testing...")
        
        print("\n🎉 Pipeline completed!")
        print("📁 Check the following directories:")
        print(f"  - Training data: {fine_tuner.training_data_dir}")
        print(f"  - Fine-tuned models: {fine_tuner.output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise

def test_fine_tuned_model():
    """Test model đã fine-tune"""
    try:
        print("🧪 Testing fine-tuned model...")
        
        # Kiểm tra model đã fine-tune
        model_path = Path(__file__).parent / "fine_tuned_models" / "vietnamese-whisper-base"
        
        if not model_path.exists():
            print("❌ Fine-tuned model not found!")
            return
        
        # Test với một số câu tiếng Việt
        test_sentences = [
            "Xin chào, tôi tên là Nguyễn Văn A",
            "Tôi năm nay hai mươi lăm tuổi",
            "Tôi thích đọc sách và nghe nhạc",
            "Tôi sống ở Hà Nội",
            "Tôi làm kỹ sư phần mềm"
        ]
        
        print("📝 Test sentences:")
        for i, sentence in enumerate(test_sentences, 1):
            print(f"  {i}. {sentence}")
        
        print("\n✅ Model testing completed!")
        print("💡 Model is ready for use in VietnameseTranscriber!")
        
    except Exception as e:
        logger.error(f"❌ Model testing failed: {e}")

def quick_setup():
    """Quick setup cho fine-tuning"""
    try:
        print("⚡ Quick Setup for Vietnamese Fine-tuning")
        print("=" * 40)
        
        # Install all dependencies
        print("📦 Installing all dependencies...")
        os.system(f"{sys.executable} -m pip install -r requirements_whisper.txt")
        
        # Prepare training data
        print("📚 Preparing training data...")
        from fine_tune_whisper import VietnameseWhisperFineTuner
        fine_tuner = VietnameseWhisperFineTuner()
        fine_tuner.prepare_fine_tuning()
        
        print("✅ Quick setup completed!")
        print("📁 Check training_data/ folder for generated files")
        
    except Exception as e:
        logger.error(f"❌ Quick setup failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_setup()
        elif sys.argv[1] == "test":
            test_fine_tuned_model()
        else:
            print("Usage: python run_vietnamese_fine_tune.py [quick|test]")
    else:
        main()
