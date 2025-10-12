# 🎯 Fine-tune Whisper cho tiếng Việt - Hướng dẫn chi tiết

## 🚀 Tổng quan

Hệ thống fine-tune Whisper cho tiếng Việt sử dụng dữ liệu từ folder `tudien/` để tạo model transcription mạnh mẽ và chính xác cho tiếng Việt.

## 📊 Dữ liệu training

### 📚 Nguồn dữ liệu
- **Folder `tudien/`**: Chứa 29,000+ từ tiếng Việt
- **Files chính**:
  - `tudien.txt` - Từ điển chính
  - `tudien-khongdau.txt` - Từ không dấu
  - `danhtu.txt` - Danh từ
  - `dongtu.txt` - Động từ
  - `tinhtu.txt` - Tính từ
  - `tenrieng.txt` - Tên riêng
  - `photu.txt` - Phó từ
  - `lientu.txt` - Liên từ

### 🔤 Training sentences
- **Tự động tạo** từ vocabulary
- **Templates câu** cơ bản
- **Câu đặc biệt** cho cognitive assessment
- **Tổng cộng**: 1000+ câu training

## 🛠️ Cài đặt và Setup

### 1. Cài đặt dependencies
```bash
cd backend
pip install -r requirements_whisper.txt
```

### 2. Quick Setup (Khuyến nghị)
```bash
python run_vietnamese_fine_tune.py quick
```

### 3. Full Pipeline
```bash
python run_vietnamese_fine_tune.py
```

## 📁 Cấu trúc thư mục

```
backend/
├── fine_tune_whisper.py           # Script fine-tuning chính
├── generate_training_audio.py     # Tạo audio training data
├── run_vietnamese_fine_tune.py    # Pipeline hoàn chỉnh
├── vietnamese_transcriber.py      # Transcriber với fine-tuned model
├── training_data/                 # Dữ liệu training
│   ├── training_data.json         # Sentences và metadata
│   ├── fine_tune_config.json      # Cấu hình training
│   ├── train_whisper.py          # Script training
│   ├── requirements_fine_tune.txt # Dependencies
│   ├── README.md                  # Hướng dẫn
│   └── audio/                     # Audio files (nếu có)
├── fine_tuned_models/             # Models đã fine-tune
│   └── vietnamese-whisper-base/   # Model tiếng Việt
└── requirements_whisper.txt       # Dependencies chính
```

## 🎯 Quy trình Fine-tuning

### Bước 1: Chuẩn bị dữ liệu
```python
from fine_tune_whisper import VietnameseWhisperFineTuner

fine_tuner = VietnameseWhisperFineTuner()
fine_tuner.prepare_fine_tuning()
```

**Kết quả:**
- ✅ Training sentences từ vocabulary
- ✅ Dataset JSON format
- ✅ Training script
- ✅ Configuration file

### Bước 2: Tạo audio training data (Tùy chọn)
```python
from generate_training_audio import TrainingAudioGenerator

audio_generator = TrainingAudioGenerator()
audio_generator.generate_all_audio()
```

**Kết quả:**
- ✅ Audio files từ TTS
- ✅ 16kHz WAV format
- ✅ Updated training data

### Bước 3: Fine-tune model
```python
fine_tuner.start_fine_tuning()
```

**Kết quả:**
- ✅ Model đã fine-tune
- ✅ Vietnamese-optimized
- ✅ Higher accuracy

## ⚙️ Cấu hình Training

### Model Settings
```json
{
  "model_name": "openai/whisper-base",
  "num_train_epochs": 3,
  "per_device_train_batch_size": 4,
  "learning_rate": 1e-5,
  "warmup_steps": 500,
  "language": "vi",
  "task": "transcribe"
}
```

### Hardware Requirements
- **GPU**: NVIDIA GPU với CUDA (khuyến nghị)
- **RAM**: Tối thiểu 8GB
- **Storage**: 2GB cho model và data
- **Time**: 2-4 giờ training

## 🧪 Sử dụng Model đã Fine-tune

### 1. Tự động load
```python
from vietnamese_transcriber import VietnameseTranscriber

transcriber = VietnameseTranscriber()
# Tự động detect và load fine-tuned model
```

### 2. Kiểm tra model info
```python
info = transcriber.get_model_info()
print(f"Model type: {info['model_type']}")
print(f"Is fine-tuned: {info['is_fine_tuned']}")
```

### 3. Transcription với model đã fine-tune
```python
result = transcriber.transcribe_audio("audio.wav")
print(f"Transcript: {result['transcript']}")
print(f"Confidence: {result['confidence']}")
```

## 📈 Kết quả mong đợi

### Trước Fine-tuning
- **Base accuracy**: 70-80%
- **Vietnamese words**: Có thể bị nhầm lẫn
- **Context**: Không tối ưu cho tiếng Việt

### Sau Fine-tuning
- **Improved accuracy**: 85-95%
- **Vietnamese vocabulary**: Nhận diện chính xác
- **Context awareness**: Hiểu ngữ cảnh tiếng Việt
- **Cognitive assessment**: Tối ưu cho bài test

## 🔍 Troubleshooting

### Lỗi thường gặp

#### 1. CUDA out of memory
```bash
# Giảm batch size
"per_device_train_batch_size": 2
"gradient_accumulation_steps": 8
```

#### 2. Training data không load
```bash
# Kiểm tra folder tudien
ls -la ../tudien/
# Chạy prepare_fine_tuning() trước
```

#### 3. Model không fine-tune
```bash
# Kiểm tra dependencies
pip install -r requirements_whisper.txt
# Kiểm tra GPU
nvidia-smi
```

### Debug commands
```bash
# Quick setup
python run_vietnamese_fine_tune.py quick

# Test model
python run_vietnamese_fine_tune.py test

# Check training data
ls -la training_data/
```

## 🚀 Tối ưu hóa

### 1. Vocabulary expansion
- Thêm từ mới vào folder `tudien/`
- Chạy lại `prepare_fine_tuning()`
- Fine-tune với vocabulary mới

### 2. Training data augmentation
- Thêm câu training đặc biệt
- Sử dụng audio thực tế
- Mix với synthetic audio

### 3. Model size optimization
- Sử dụng Whisper Small thay vì Base
- Quantization cho inference
- Model distillation

## 📊 Monitoring và Evaluation

### Training metrics
- **Loss**: Giảm dần theo epochs
- **Accuracy**: Tăng dần theo training
- **Vietnamese F1**: Score cho tiếng Việt

### Evaluation
```python
# Test với câu tiếng Việt
test_sentences = [
    "Xin chào, tôi tên là Nguyễn Văn A",
    "Tôi năm nay hai mươi lăm tuổi",
    "Tôi thích đọc sách và nghe nhạc"
]

for sentence in test_sentences:
    result = transcriber.transcribe_audio(sentence)
    print(f"Expected: {sentence}")
    print(f"Actual: {result['transcript']}")
    print(f"Confidence: {result['confidence']}")
```

## 🎉 Kết luận

Fine-tuning Whisper cho tiếng Việt sẽ cải thiện đáng kể:
- **Độ chính xác** transcription
- **Hỗ trợ từ vựng** tiếng Việt
- **Hiểu ngữ cảnh** tiếng Việt
- **Tối ưu** cho cognitive assessment

### Next steps
1. **Chạy fine-tuning** với dữ liệu hiện tại
2. **Test model** với audio thực tế
3. **Tích hợp** vào VietnameseTranscriber
4. **Monitor performance** trong production
5. **Iterative improvement** với dữ liệu mới

---

**💡 Tip**: Bắt đầu với `python run_vietnamese_fine_tune.py quick` để setup nhanh, sau đó chạy full pipeline khi sẵn sàng!
