# Hướng dẫn Train Model với file M4A

Script `train_with_m4a.py` cho phép bạn train model MCI prediction sử dụng các file audio .m4a có trong thư mục backend.

## Cài đặt Dependencies

Đảm bảo bạn đã cài đặt các packages cần thiết:

```bash
pip install scikit-learn pandas numpy librosa soundfile
pip install -r requirements_modules.txt
```

## Cách sử dụng

### 1. Tạo file labels CSV (bước đầu tiên)

Chạy script với option `--create-labels-only` để tạo file labels CSV:

```bash
cd backend
python train_with_m4a.py --create-labels-only
```

Script sẽ:
- Tìm tất cả file `.m4a` trong thư mục backend
- Transcribe từng file audio (sử dụng Gemini API nếu có)
- Tạo file `data/training_data/labels_m4a.csv` với các giá trị mặc định

### 2. Cập nhật labels

Mở file `data/training_data/labels_m4a.csv` và cập nhật các giá trị:

- **mmse_score**: Điểm MMSE (0-30)
- **mci_label**: Nhãn MCI (0=Normal, 1=MCI, 2=Dementia)
- **age**: Tuổi
- **gender**: Giới tính (male/female)
- **education_years**: Số năm học
- **task_type**: Loại task (spontaneous_speech, picture_description, verbal_fluency, qa)
- **transcript**: Transcript (đã được tự động điền, có thể chỉnh sửa nếu cần)

### 3. Train model

Sau khi cập nhật labels, chạy script để train:

```bash
python train_with_m4a.py
```

Hoặc với các options:

```bash
# Chỉ định output directory
python train_with_m4a.py --output-dir models/my_model

# Bỏ qua transcription (sử dụng transcript có sẵn trong CSV)
python train_with_m4a.py --skip-transcription

# Không sử dụng PhoBERT (nhanh hơn nhưng kém chính xác)
python train_with_m4a.py --no-phobert

# Chỉ định đường dẫn labels CSV
python train_with_m4a.py --labels-csv data/my_labels.csv
```

## Workflow đầy đủ

```bash
# Bước 1: Tạo labels CSV
python train_with_m4a.py --create-labels-only

# Bước 2: Cập nhật labels trong data/training_data/labels_m4a.csv
# (Mở file bằng Excel/Notepad và cập nhật mmse_score, mci_label, etc.)

# Bước 3: Train model
python train_with_m4a.py --output-dir models/m4a_trained
```

## Output

Sau khi train xong, bạn sẽ có:

1. **Model file**: `models/m4a_trained/mci_predictor_model.pkl`
   - Model đã train, có thể load lại để dự đoán

2. **Metrics file**: `models/m4a_trained/training_metrics.json`
   - Các metrics đánh giá model (accuracy, AUC, RMSE, MAE, etc.)

## Các Options

- `--backend-dir`: Đường dẫn thư mục backend (mặc định: thư mục chứa script)
- `--labels-csv`: Đường dẫn file labels CSV (mặc định: `data/training_data/labels_m4a.csv`)
- `--output-dir`: Thư mục lưu model (mặc định: `models/m4a_trained`)
- `--skip-transcription`: Bỏ qua transcription (sử dụng transcript có sẵn)
- `--skip-features`: Bỏ qua feature extraction (chưa implement)
- `--no-phobert`: Không sử dụng PhoBERT (nhanh hơn nhưng kém chính xác)
- `--create-labels-only`: Chỉ tạo file labels CSV, không train

## Lưu ý

1. **Gemini API Key**: Để transcribe audio, bạn cần có GEMINI_API_KEY trong environment hoặc file `config.env`

2. **Labels**: Bạn cần cung cấp labels chính xác (mmse_score, mci_label) để model train đúng. Các giá trị mặc định chỉ để test.

3. **Số lượng samples**: Với ít samples, model có thể không train tốt. Khuyến nghị tối thiểu 20-30 samples.

4. **Feature extraction**: Script sử dụng các modules:
   - `modules.acoustic_analyzer.AcousticAnalyzer` - Trích xuất acoustic features
   - `modules.linguistic_analyzer.VietnameseLinguisticAnalyzer` - Trích xuất linguistic features
   - `modules.mci_predictor.MCIPredictor` - Train và predict

## Troubleshooting

### Lỗi: "Modules không khả dụng"
- Kiểm tra xem các modules đã được import đúng chưa
- Chạy: `python -c "from modules.acoustic_analyzer import AcousticAnalyzer"`

### Lỗi: "sklearn không khả dụng"
- Cài đặt: `pip install scikit-learn`

### Lỗi transcription
- Kiểm tra GEMINI_API_KEY
- Có thể bỏ qua bằng `--skip-transcription` và nhập transcript thủ công

### Lỗi feature extraction
- Kiểm tra file audio có hợp lệ không
- Kiểm tra các dependencies: librosa, soundfile, opensmile, parselmouth

## Ví dụ

```bash
# Tìm file m4a
ls *.m4a

# Tạo labels
python train_with_m4a.py --create-labels-only

# Sửa labels
notepad data/training_data/labels_m4a.csv

# Train
python train_with_m4a.py --output-dir models/my_m4a_model
```

