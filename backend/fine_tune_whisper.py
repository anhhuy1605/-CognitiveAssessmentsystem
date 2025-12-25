"""
Fine-tune Whisper cho tiếng Việt
Sử dụng dữ liệu từ folder tudien để tạo model tiếng Việt mạnh mẽ
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VietnameseWhisperFineTuner:
    """
    Fine-tune Whisper model cho tiếng Việt
    """
    
    def __init__(self):
        self.base_model = "openai/whisper-base"
        self.fine_tuned_model_name = "vietnamese-whisper-base"
        self.tudien_path = Path(__file__).parent.parent / "tudien"
        self.output_dir = Path(__file__).parent / "fine_tuned_models"
        self.training_data_dir = Path(__file__).parent / "training_data"
        
        # Tạo thư mục output
        self.output_dir.mkdir(exist_ok=True)
        self.training_data_dir.mkdir(exist_ok=True)
        
        # Vietnamese vocabulary từ tudien
        self.vietnamese_vocab = set()
        self.training_sentences = []
        
    def _install_fine_tune_dependencies(self):
        """Cài đặt dependencies cần thiết cho fine-tuning"""
        try:
            logger.info("📦 Installing fine-tuning dependencies...")
            
            # Cài đặt các packages cần thiết
            packages = [
                "torch>=2.0.0",
                "torchaudio>=2.0.0", 
                "transformers>=4.35.0",
                "datasets>=2.14.0",
                "accelerate>=0.20.0",
                "peft>=0.4.0",
                "bitsandbytes>=0.41.0",
                "sentencepiece>=0.1.99",
                "protobuf>=3.20.0"
            ]
            
            for package in packages:
                logger.info(f"Installing {package}...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ])
            
            logger.info("✅ Fine-tuning dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to install fine-tuning dependencies: {e}")
            return False
    
    def _load_vietnamese_vocabulary(self):
        """Load từ điển tiếng Việt từ folder tudien"""
        try:
            logger.info("📚 Loading Vietnamese vocabulary from tudien...")
            
            # Danh sách file từ điển quan trọng
            vocab_files = [
                "tudien.txt",           # Từ điển chính
                "tudien-khongdau.txt",  # Từ không dấu
                "danhtu.txt",           # Danh từ
                "dongtu.txt",           # Động từ
                "tinhtu.txt",           # Tính từ
                "tenrieng.txt",         # Tên riêng
                "photu.txt",            # Phó từ
                "lientu.txt",           # Liên từ
                "danhtunhanxung.txt"    # Danh từ nhân xưng
            ]
            
            total_words = 0
            for vocab_file in vocab_files:
                file_path = self.tudien_path / vocab_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        words = f.read().splitlines()
                        # Lọc từ có ý nghĩa
                        valid_words = [
                            word.strip().lower() for word in words 
                            if len(word.strip()) > 1 and 
                            not word.strip().isdigit() and
                            not word.strip().startswith('#') and
                            word.strip().isalpha()
                        ]
                        self.vietnamese_vocab.update(valid_words)
                        total_words += len(valid_words)
                        logger.info(f"Loaded {len(valid_words)} words from {vocab_file}")
            
            logger.info(f"✅ Total Vietnamese vocabulary: {len(self.vietnamese_vocab)} words")
            
            # Tạo training sentences từ vocabulary
            self._generate_training_sentences()
            
        except Exception as e:
            logger.error(f"❌ Failed to load Vietnamese vocabulary: {e}")
            raise
    
    def _generate_training_sentences(self):
        """Tạo câu training từ vocabulary"""
        try:
            logger.info("🔤 Generating training sentences...")
            
            # Các mẫu câu cơ bản
            sentence_templates = [
                "Tôi tên là {name}",
                "Tôi {age} tuổi",
                "Tôi là {gender}",
                "Tôi sống ở {place}",
                "Tôi làm {job}",
                "Tôi thích {hobby}",
                "Tôi có {family}",
                "Tôi học {subject}",
                "Tôi ăn {food}",
                "Tôi đi {transport}",
                "Tôi gặp {person}",
                "Tôi thấy {object}",
                "Tôi nghe {sound}",
                "Tôi cảm thấy {emotion}",
                "Tôi nghĩ về {topic}",
                "Tôi muốn {desire}",
                "Tôi cần {need}",
                "Tôi có thể {ability}",
                "Tôi sẽ {future_action}",
                "Tôi đã {past_action}"
            ]
            
            # Tạo câu từ templates và vocabulary
            for template in sentence_templates:
                # Thay thế placeholder bằng từ thực tế
                if "{name}" in template:
                    names = [w for w in self.vietnamese_vocab if len(w) >= 3 and w in ["nguyễn", "trần", "lê", "phạm", "hoàng", "huỳnh", "phan", "vũ", "võ", "đặng", "bùi", "đỗ", "hồ", "ngô", "dương", "lý"]]
                    for name in names[:10]:  # Giới hạn 10 tên
                        sentence = template.replace("{name}", name.title())
                        self.training_sentences.append(sentence)
                
                elif "{age}" in template:
                    for age in range(18, 80, 5):
                        sentence = template.replace("{age}", str(age))
                        self.training_sentences.append(sentence)
                
                elif "{gender}" in template:
                    for gender in ["nam", "nữ", "nam", "nữ"]:
                        sentence = template.replace("{gender}", gender)
                        self.training_sentences.append(sentence)
                
                elif "{place}" in template:
                    places = [w for w in self.vietnamese_vocab if len(w) >= 4 and w in ["hà nội", "tp hcm", "đà nẵng", "hải phòng", "cần thơ", "nha trang", "vũng tàu", "đà lạt", "huế", "sapa"]]
                    for place in places[:5]:
                        sentence = template.replace("{place}", place.title())
                        self.training_sentences.append(sentence)
                
                elif "{job}" in template:
                    jobs = [w for w in self.vietnamese_vocab if len(w) >= 4 and w in ["giáo viên", "bác sĩ", "kỹ sư", "nhân viên", "sinh viên", "học sinh", "công nhân", "nông dân", "thương nhân", "nghệ sĩ"]]
                    for job in jobs[:5]:
                        sentence = template.replace("{job}", job)
                        self.training_sentences.append(sentence)
                
                elif "{hobby}" in template:
                    hobbies = [w for w in self.vietnamese_vocab if len(w) >= 3 and w in ["đọc sách", "nghe nhạc", "xem phim", "chơi thể thao", "du lịch", "nấu ăn", "vẽ tranh", "chụp ảnh", "đan len", "làm vườn"]]
                    for hobby in hobbies[:5]:
                        sentence = template.replace("{hobby}", hobby)
                        self.training_sentences.append(sentence)
                
                else:
                    # Tạo câu đơn giản từ vocabulary
                    words = list(self.vietnamese_vocab)[:100]  # Lấy 100 từ đầu
                    for word in words:
                        if len(word) >= 3:
                            sentence = f"Tôi thích {word}"
                            self.training_sentences.append(sentence)
                            break
            
            # Thêm các câu đặc biệt cho cognitive assessment
            cognitive_sentences = [
                "Xin chào, tôi tên là Nguyễn Văn A",
                "Tôi năm nay hai mươi lăm tuổi",
                "Tôi là nam giới",
                "Tôi sống ở Hà Nội",
                "Tôi làm kỹ sư phần mềm",
                "Tôi thích đọc sách và nghe nhạc",
                "Tôi có gia đình nhỏ",
                "Tôi học công nghệ thông tin",
                "Tôi ăn cơm Việt Nam",
                "Tôi đi xe máy đi làm",
                "Tôi gặp bạn bè cuối tuần",
                "Tôi thấy hoa đào nở",
                "Tôi nghe tiếng chim hót",
                "Tôi cảm thấy hạnh phúc",
                "Tôi nghĩ về tương lai",
                "Tôi muốn học thêm tiếng Anh",
                "Tôi cần mua sách mới",
                "Tôi có thể nấu cơm",
                "Tôi sẽ đi du lịch",
                "Tôi đã hoàn thành công việc"
            ]
            
            self.training_sentences.extend(cognitive_sentences)
            
            # Thêm câu từ vocabulary
            vocab_words = list(self.vietnamese_vocab)[:500]  # Lấy 500 từ đầu
            for word in vocab_words:
                if len(word) >= 3:
                    self.training_sentences.append(f"Từ {word} có nghĩa là gì")
                    self.training_sentences.append(f"Tôi biết từ {word}")
                    self.training_sentences.append(f"Từ {word} rất hay")
            
            logger.info(f"✅ Generated {len(self.training_sentences)} training sentences")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate training sentences: {e}")
            raise
    
    def _create_training_dataset(self):
        """Tạo dataset training cho Whisper"""
        try:
            logger.info("📊 Creating training dataset...")
            
            # Tạo file JSON cho training
            training_data = []
            
            for i, sentence in enumerate(self.training_sentences):
                # Tạo audio file giả (sẽ được thay thế bằng TTS thực)
                audio_filename = f"training_{i:05d}.wav"
                
                training_item = {
                    "audio_file_path": audio_filename,
                    "sentence": sentence,
                    "language": "vi",
                    "task": "transcribe"
                }
                training_data.append(training_item)
            
            # Lưu training data
            training_file = self.training_data_dir / "training_data.json"
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Created training dataset with {len(training_data)} samples")
            return training_file
            
        except Exception as e:
            logger.error(f"❌ Failed to create training dataset: {e}")
            raise
    
    def _create_fine_tune_config(self):
        """Tạo config cho fine-tuning"""
        try:
            logger.info("⚙️ Creating fine-tuning configuration...")
            
            config = {
                "model_name": self.base_model,
                "output_dir": str(self.output_dir / self.fine_tuned_model_name),
                "num_train_epochs": 3,
                "per_device_train_batch_size": 4,
                "per_device_eval_batch_size": 4,
                "gradient_accumulation_steps": 4,
                "learning_rate": 1e-5,
                "warmup_steps": 500,
                "logging_steps": 100,
                "save_steps": 1000,
                "eval_steps": 1000,
                "save_total_limit": 3,
                "prediction_loss_only": True,
                "remove_unused_columns": False,
                "dataloader_pin_memory": False,
                "language": "vi",
                "task": "transcribe",
                "vocabulary_size": len(self.vietnamese_vocab),
                "training_samples": len(self.training_sentences)
            }
            
            config_file = self.training_data_dir / "fine_tune_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Created fine-tuning configuration")
            return config_file
            
        except Exception as e:
            logger.error(f"❌ Failed to create fine-tuning configuration: {e}")
            raise
    
    def _create_training_script(self):
        """Tạo script training"""
        try:
            logger.info("📝 Creating training script...")
            
            script_content = f'''#!/usr/bin/env python3
"""
Fine-tune Whisper cho tiếng Việt
Auto-generated training script
"""

import os
import sys
import json
import logging
from pathlib import Path
from datasets import Dataset
from transformers import (
    WhisperProcessor, 
    WhisperForConditionalGeneration,
    TrainingArguments,
    Trainer,
    DataCollatorSpeechSeq2SeqWithPadding
)
import torch
from dataclasses import dataclass
from typing import Any, Dict, List, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: WhisperProcessor
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Tạo input features giả (trong thực tế sẽ load từ audio)
        input_features = [{{"input_features": torch.randn(80, 3000)}} for _ in features]
        label_features = [{{"input_ids": torch.tensor(feature["labels"])}} for feature in features]
        
        # Pad input features
        input_features = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        label_features = self.processor.tokenizer.pad(label_features, return_tensors="pt")
        
        labels = label_features["input_ids"].masked_fill(
            label_features.attention_mask.ne(1), -100
        )
        
        return {{
            "input_features": input_features.input_features,
            "labels": labels,
        }}

def load_training_data(config_path: str):
    """Load training data"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    training_data_path = Path(config_path).parent / "training_data.json"
    with open(training_data_path, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    return config, training_data

def create_dataset(training_data: List[Dict]):
    """Tạo dataset từ training data"""
    # Tạo dataset giả (trong thực tế sẽ load audio thực)
    dataset_dict = {{
        "input_features": [torch.randn(80, 3000) for _ in training_data],
        "labels": [item["sentence"] for item in training_data]
    }}
    
    dataset = Dataset.from_dict(dataset_dict)
    return dataset

def main():
    """Main training function"""
    try:
        # Load config
        config_path = "{self.training_data_dir / "fine_tune_config.json"}"
        config, training_data = load_training_data(config_path)
        
        logger.info(f"Starting fine-tuning with {{len(training_data)}} samples")
        
        # Load base model
        processor = WhisperProcessor.from_pretrained(config["model_name"])
        model = WhisperForConditionalGeneration.from_pretrained(config["model_name"])
        
        # Set language to Vietnamese
        processor.tokenizer.set_prefix_tokens(language="vi", task="transcribe")
        
        # Create dataset
        dataset = create_dataset(training_data)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=config["output_dir"],
            num_train_epochs=config["num_train_epochs"],
            per_device_train_batch_size=config["per_device_train_batch_size"],
            gradient_accumulation_steps=config["gradient_accumulation_steps"],
            learning_rate=config["learning_rate"],
            warmup_steps=config["warmup_steps"],
            logging_steps=config["logging_steps"],
            save_steps=config["save_steps"],
            eval_steps=config["eval_steps"],
            save_total_limit=config["save_total_limit"],
            prediction_loss_only=config["prediction_loss_only"],
            remove_unused_columns=config["remove_unused_columns"],
            dataloader_pin_memory=config["dataloader_pin_memory"],
            report_to=None,
            push_to_hub=False
        )
        
        # Data collator
        data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=processor,
            decoder_start_token_id=processor.tokenizer.pad_token_id
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
            tokenizer=processor.tokenizer
        )
        
        # Start training
        logger.info("Starting training...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        processor.save_pretrained(config["output_dir"])
        
        logger.info(f"✅ Training completed! Model saved to {{config['output_dir']}}")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {{e}}")
        raise

if __name__ == "__main__":
    main()
'''
            
            script_file = self.training_data_dir / "train_whisper.py"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            
            logger.info("✅ Created training script")
            return script_file
            
        except Exception as e:
            logger.error(f"❌ Failed to create training script: {e}")
            raise
    
    def _create_requirements_file(self):
        """Tạo requirements file cho fine-tuning"""
        try:
            requirements = [
                "torch>=2.0.0",
                "torchaudio>=2.0.0",
                "transformers>=4.35.0",
                "datasets>=2.14.0",
                "accelerate>=0.20.0",
                "peft>=0.4.0",
                "bitsandbytes>=0.41.0",
                "sentencepiece>=0.1.99",
                "protobuf>=3.20.0",
                "numpy>=1.24.0",
                "scipy>=1.11.0"
            ]
            
            req_file = self.training_data_dir / "requirements_fine_tune.txt"
            with open(req_file, 'w') as f:
                for req in requirements:
                    f.write(f"{req}\n")
            
            logger.info("✅ Created requirements file")
            return req_file
            
        except Exception as e:
            logger.error(f"❌ Failed to create requirements file: {e}")
            raise
    
    def prepare_fine_tuning(self):
        """Chuẩn bị tất cả cho fine-tuning"""
        try:
            logger.info("🚀 Preparing Vietnamese Whisper fine-tuning...")
            
            # 1. Install dependencies
            if not self._install_fine_tune_dependencies():
                raise Exception("Failed to install dependencies")
            
            # 2. Load Vietnamese vocabulary
            self._load_vietnamese_vocabulary()
            
            # 3. Create training dataset
            training_file = self._create_training_dataset()
            
            # 4. Create fine-tune config
            config_file = self._create_fine_tune_config()
            
            # 5. Create training script
            script_file = self._create_training_script()
            
            # 6. Create requirements file
            req_file = self._create_requirements_file()
            
            # 7. Create README
            self._create_readme()
            
            logger.info("✅ Fine-tuning preparation completed!")
            logger.info(f"📁 Training data: {training_file}")
            logger.info(f"⚙️ Config: {config_file}")
            logger.info(f"📝 Script: {script_file}")
            logger.info(f"📦 Requirements: {req_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fine-tuning preparation failed: {e}")
            raise
    
    def _create_readme(self):
        """Tạo README cho fine-tuning"""
        try:
            readme_content = f"""# 🎯 Fine-tune Whisper cho tiếng Việt

## 📊 Thống kê dữ liệu
- **Vocabulary size**: {len(self.vietnamese_vocab)} từ
- **Training sentences**: {len(self.training_sentences)} câu
- **Base model**: {self.base_model}
- **Target language**: Vietnamese (vi)

## 🚀 Cách sử dụng

### 1. Cài đặt dependencies
```bash
pip install -r requirements_fine_tune.txt
```

### 2. Chạy training
```bash
python train_whisper.py
```

### 3. Sử dụng model đã fine-tune
```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration

# Load model đã fine-tune
model_path = "{self.output_dir / self.fine_tuned_model_name}"
processor = WhisperProcessor.from_pretrained(model_path)
model = WhisperForConditionalGeneration.from_pretrained(model_path)

# Sử dụng cho transcription
# ... (code sử dụng model)
```

## 📁 Cấu trúc thư mục
```
{self.training_data_dir}/
├── training_data.json          # Dữ liệu training
├── fine_tune_config.json       # Cấu hình training
├── train_whisper.py           # Script training
└── requirements_fine_tune.txt  # Dependencies

{self.output_dir}/
└── {self.fine_tuned_model_name}/  # Model đã fine-tune
```

## 🎯 Mục tiêu
- Tăng độ chính xác cho tiếng Việt
- Hỗ trợ từ vựng tiếng Việt phong phú
- Tối ưu cho cognitive assessment
- Giảm lỗi transcription

## ⚠️ Lưu ý
- Cần GPU để training hiệu quả
- Training time: ~2-4 giờ (tùy hardware)
- Model size: ~244MB (base)
- Memory requirement: ~8GB RAM
"""
            
            readme_file = self.training_data_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info("✅ Created README file")
            
        except Exception as e:
            logger.error(f"❌ Failed to create README: {e}")
    
    def start_fine_tuning(self):
        """Bắt đầu fine-tuning"""
        try:
            logger.info("🎯 Starting Vietnamese Whisper fine-tuning...")
            
            # Chuẩn bị
            if not self.prepare_fine_tuning():
                raise Exception("Preparation failed")
            
            # Chạy training script
            script_path = self.training_data_dir / "train_whisper.py"
            
            logger.info(f"🚀 Running training script: {script_path}")
            logger.info("⏳ This may take 2-4 hours depending on your hardware...")
            
            # Chạy training
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Fine-tuning completed successfully!")
                logger.info(f"📁 Model saved to: {self.output_dir / self.fine_tuned_model_name}")
                return True
            else:
                logger.error(f"❌ Fine-tuning failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fine-tuning failed: {e}")
            return False

def main():
    """Main function"""
    try:
        fine_tuner = VietnameseWhisperFineTuner()
        
        # Chọn mode
        print("🎯 Vietnamese Whisper Fine-tuning")
        print("1. Prepare only (không training)")
        print("2. Prepare and start training")
        
        choice = input("Chọn option (1 hoặc 2): ").strip()
        
        if choice == "1":
            fine_tuner.prepare_fine_tuning()
            print("✅ Preparation completed! Check training_data/ folder")
        elif choice == "2":
            fine_tuner.start_fine_tuning()
        else:
            print("❌ Invalid choice")
            
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
