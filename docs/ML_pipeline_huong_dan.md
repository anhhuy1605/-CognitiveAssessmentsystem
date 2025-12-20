# HƯỚNG DẪN SỬ DỤNG (Pipeline ML MMSE - V2.0)

## Bước 1: Feature Extraction

```bash
# Extract features từ 1 audio
python backend/robust_audio_features.py path/to/audio.wav

# Extract cho toàn bộ dataset (ví dụ)
for audio in audio_files/*.wav; do
    python backend/robust_audio_features.py "$audio" >> features.csv
done
```

## Bước 2: Training Model

```bash
# Train với REAL data (KHÔNG synthetic!)
python train_mmse_multifeature_model.py \
    --csv data/real_mmse_features.csv \
    --target-col mmse \
    --output-dir model_bundle/mmse_v2
```

## Bước 3: Integration vào Backend

```python
# app.py (hoặc service backend)
from backend.robust_audio_features import create_feature_extractor
from backend.clinical_scoring import create_scoring_engine

# Initialize
feature_extractor = create_feature_extractor()
scoring_engine = create_scoring_engine()

# Use in assessment
def assess_cognitive(audio_path):
    # 1. Extract features (with validation)
    try:
        features = feature_extractor.extract_features(audio_path)
    except ValueError as e:
        return {"error": str(e)}
    
    # 2. ML prediction (load model từ bundle đã train)
    ml_score = model.predict([features])[0]
    
    # 3. Unified scoring
    final_score = scoring_engine.score_from_ml_model(
        ml_prediction=ml_score,
        audio_quality=features["audio_quality_snr"] / 30.0  # chuẩn hóa 0–1
    )
    
    return {
        "score": final_score.total_score,
        "level": final_score.cognitive_level.value,
        "confidence": final_score.confidence,
        "recommendations": scoring_engine.get_clinical_recommendations(final_score),
    }
```

## ✅ Các vấn đề đã giải quyết
- Synthetic Data → Bắt buộc dùng real data, raise error nếu không đủ
- Overfitting → Train/Val/Test split + Cross-validation + Regularization
- Feature Extraction → Validation nghiêm ngặt, không dùng fallback values
- Scoring Logic → Unified engine theo clinical standards
- Pipeline Rối → Một pipeline duy nhất, rõ ràng

## 🎯 Điều quan trọng nhất
**THU THẬP DỮ LIỆU THỰC!**

- Tối thiểu 100–200 samples với nhãn MMSE chuẩn  
- Ghi âm chất lượng tốt (SNR > 10 dB)  
- Có validation từ chuyên gia  


