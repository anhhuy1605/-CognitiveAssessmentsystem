# MMSE Regression Pipeline (Spec-Compliant)

Implements the user-provided formulation:
- Task: supervised regression `y_hat_MMSE = f(x_acoustic, x_text)`
- Acoustic features: MFCC (mean/std/delta/delta2), F0 stats, speech rate, pause ratio, mean pause duration, energy (librosa).
- Linguistic features: TTR, MLU, POS noun ratio, disfluency rate, bigram log-prob, BERT [CLS] embedding (768d).
- Models: Ridge (grid alpha), SVR (RBF), GradientBoostingRegressor. StandardScaler inside pipeline. CV: KFold=5, seed=42.
- Metric: RMSE (mean/std).

## Structure
- `feature_extraction/acoustic.py` — librosa features per spec.
- `feature_extraction/linguistic.py` — spaCy + transformers features per spec.
- `train.py` — build features, train Ridge/SVR/GBR, select best by RMSE, save bundle to `models/`.
- `predict.py` — load bundle, extract features, emit JSON with predicted_mmse, model_used, rmse, feature_importance.
- `config.json` — paths and model names.

## Usage
1) CSV đầu vào:
   - Ưu tiên: có `audio_path, transcript, mmse`.
   - Nếu không có audio/transcript, script sẽ fallback dùng toàn bộ cột số (trừ id/target) với target là một trong `mmse/mms/mmse2`.
2) Cài deps: `pip install -r requirements.txt` (cần librosa, spacy, transformers, torch; tải spaCy model: `python -m spacy download en_core_web_sm`).
3) Train: `python train.py --config config.json`
4) Predict: `python predict.py --config config.json --audio /path/audio.wav --transcript "..."`  
   Nếu model được train trên feature sẵn có (không có audio_path), bạn cần cung cấp vec đặc trưng tương ứng thay vì audio+transcript (hiện script predict ưu tiên audio+transcript).  
   Script in ra JSON kết quả.

## Notes
- Features are numeric only; NaN/Inf are replaced with 0.0.
- Predictions are clipped to [0, 30].
- Reproducibility: random seed = 42. CV is subject-independent if the CSV is prepared that way. 
