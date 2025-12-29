# MCI/AD Patient Audio Analysis Script

## 📋 Tổng Quan

Script `analyze_mci_patients.py` phân tích đa chiều 4 file âm thanh M4A của bệnh nhân nghi ngờ MCI/AD và xuất ra các biểu đồ trực quan chất lượng cao.

## 🚀 Cài Đặt Dependencies

```bash
# Core dependencies
pip install numpy matplotlib seaborn librosa

# Optional but recommended
pip install parselmouth  # For accurate F0, jitter, shimmer
pip install noisereduce  # For noise reduction
pip install webrtcvad    # For better VAD
```

## 📁 Chuẩn Bị Files

Đặt 4 file M4A vào thư mục `backend/`:
- `Hoàng Thị Hạnh.m4a`
- `Phạm thị chiến.m4a`
- `Quán cơm ABC 2.m4a`
- `Đoàn Bình.m4a`

Script sẽ tự động tìm tất cả file `.m4a` trong thư mục `backend/`.

## ▶️ Chạy Script

```bash
cd backend
python analyze_mci_patients.py
```

## 📊 Output Files

Script sẽ tạo thư mục `backend/mci_analysis_output/` với các file sau:

### Biểu Đồ (PNG, 300 DPI):
1. **patient_analysis_fig1.png** - Waveform & Spectrogram Comparison
   - 4 rows × 2 cols
   - Waveform với amplitude envelope
   - Mel spectrogram với annotation pauses dài >2s

2. **patient_analysis_fig2.png** - Pitch Analysis
   - 4 rows × 2 cols
   - F0 contour với confidence band
   - Pitch variability over time với threshold lines

3. **patient_analysis_fig3.png** - Speech Rate & Pause Patterns
   - 4 rows × 3 cols
   - Speech rate timeline
   - Pause duration histogram
   - Cumulative pause time percentage

4. **patient_analysis_fig4.png** - Voice Quality Indicators
   - 4 rows × 2 cols
   - Jitter & Shimmer comparison với baseline
   - Energy contour với fatigue indicators

5. **patient_analysis_fig5.png** - MFCC Heatmap
   - 4 rows × 1 col
   - 13 MFCC coefficients heatmap
   - Highlight low variability regions

6. **patient_analysis_fig6.png** - Summary Dashboard
   - 2×2 radar charts
   - 8 risk indicators per patient
   - Color-coded risk levels

### Báo Cáo:
- **summary_report.txt** - Detailed metrics và risk assessment

## 🔍 Features Extracted

### Acoustic Features:
- F0 (pitch) contour
- Speech rate (syllables/second)
- Pause duration và frequency
- Jitter và Shimmer
- MFCC coefficients (13)
- Spectral features (centroid, rolloff, bandwidth)
- Energy/Intensity contour

### Temporal Features:
- Articulation rate
- Speaking time ratio
- Pause patterns

## 🎯 MCI/AD Indicators Detected

Script tự động phát hiện các dấu hiệu:
1. **Slow Speech Rate** (<100 words/min)
2. **High Pause Frequency** (>20% pauses >2s)
3. **Pitch Instability** (Std >30Hz)
4. **Abnormal Jitter** (>1.0%)
5. **Abnormal Shimmer** (>3.0%)
6. **Energy Decline** (Fatigue indicator)
7. **MFCC Irregularity** (Reduced variability)

## 📈 Risk Levels

- **Low Risk**: 0-2 indicators
- **Moderate Risk**: 3-4 indicators
- **High Risk**: 5-7 indicators

## ⚙️ Configuration

Có thể điều chỉnh thresholds trong script:
```python
THRESHOLDS = {
    'speech_rate_min': 100,      # words/min
    'pause_duration_abnormal': 2.0,  # seconds
    'jitter_normal_max': 1.0,    # %
    'shimmer_normal_max': 3.0,   # %
    'pitch_std_abnormal': 30,    # Hz
    'energy_drop_threshold': 0.3,
    'mfcc_variability_min': 0.5
}
```

## 🐛 Troubleshooting

### Lỗi: "No M4A files found"
- Kiểm tra file có đúng định dạng `.m4a`
- Đảm bảo file nằm trong thư mục `backend/`

### Lỗi: "parselmouth not available"
- Script vẫn chạy được nhưng F0, jitter, shimmer sẽ ít chính xác hơn
- Cài đặt: `pip install parselmouth`

### Lỗi: "webrtcvad not available"
- Script sẽ dùng librosa-based VAD (vẫn hoạt động tốt)
- Cài đặt: `pip install webrtcvad`

### Memory Error với file lớn
- Script tự động xử lý file lớn
- Nếu vẫn lỗi, có thể giảm sample rate trong code

## 📝 Notes

- Script tự động convert M4A → WAV 16kHz mono
- Noise reduction được áp dụng nếu có `noisereduce`
- VAD loại bỏ silence để tăng accuracy
- Tất cả biểu đồ dùng colorblind-friendly palette
- Output resolution: 300 DPI (suitable for publication)

## 🔗 References

- Fraser et al. (2016) - Linguistic features for dementia detection
- Pakhomov et al. (2011) - Computerized analysis in Alzheimer's
- MCI/AD acoustic markers research literature

