# Enhanced Multimodal Cognitive Assessment ML

Comprehensive ML pipeline cho cognitive assessment và Alzheimer's detection với Vietnamese language support.

## 🚀 Key Features

### ✅ Enhanced Pipeline
- **Safe Data Loading**: Merge theo `participant_id`, không align order
- **SMOTE + Imblearn**: Chống mất cân bằng dữ liệu
- **Robust Scaling**: RobustScaler + feature selection
- **Early Stopping**: XGBoost với early stopping
- **Comprehensive Metrics**: ROC-AUC, confusion matrix, MSE, MAE, R²

### ✅ Model Architecture
- **Classification**: SMOTE → StandardScaler → XGBoost (optimize F1 & Recall)
- **Regression**: RobustScaler → SelectKBest → XGBoost (MMSE prediction)
- **Pipelines**: sklearn Pipeline + imblearn Pipeline
- **Persistence**: joblib model bundle với metadata

### ✅ Data Validation
- Participant ID consistency check
- Null values detection và handling
- Class balance analysis
- MMSE outlier clipping
- Comprehensive validation report

### ✅ Artifacts & Reports
- Confusion matrix, ROC curve plots
- MMSE scatter plot với metrics
- JSON và PDF reports
- Training results comprehensive
- Data validation report

## 📦 Installation

```bash
# Install dependencies
pip install numpy pandas scikit-learn imbalanced-learn xgboost matplotlib joblib

# Optional: Vietnamese NLP
pip install underthesea

# Optional: Chinese NLP  
pip install jieba
```

## 🎯 Quick Start

### Training Model

```python
from cognitive_assessment_ml import EnhancedMultimodalCognitiveModel

# Initialize model
model = EnhancedMultimodalCognitiveModel(language='vi', debug=True)

# Train with safe data loading
results = model.train_from_adress_data(
    dx_csv='dx-mmse.csv',
    progression_csv='progression.csv', 
    eval_csv='eval-data.csv',
    validate_data=True  # Export validation report
)

# Save model bundle
model.save_model('my_model_bundle')

# Generate comprehensive report
report_path = model.generate_report('training_report', format='pdf')
```

### Making Predictions

```python
# Load trained model
model = EnhancedMultimodalCognitiveModel()
model.load_model('my_model_bundle')

# Single prediction
result = model.predict_from_audio('patient_audio.wav')
print(f"Diagnosis: {result['predictions']['diagnosis']}")
print(f"Confidence: {result['predictions']['confidence']:.3f}")
print(f"MMSE Predicted: {result['predictions']['mmse_predicted']:.1f}")

# Batch prediction
batch_inputs = [
    'audio1.wav',
    {'audio': 'audio2.wav', 'transcript': 'transcript2.txt'}
]
batch_results = model.predict_batch(batch_inputs)
```

## 💻 CLI Usage

### Training
```bash
# Basic training
python cognitive_assessment_ml.py --dx dx-mmse.csv --progression progression.csv --train

# Training with validation
python cognitive_assessment_ml.py --dx dx-mmse.csv --progression progression.csv --eval eval.csv --train --validate-data --debug

# Custom model path
python cognitive_assessment_ml.py --dx dx-mmse.csv --train --model custom_model_bundle
```

### Prediction
```bash
# Single file prediction
python cognitive_assessment_ml.py --predict --input audio.wav --model my_model_bundle

# Directory batch prediction
python cognitive_assessment_ml.py --predict --input audio_directory/ --model my_model_bundle

# With custom output
python cognitive_assessment_ml.py --predict --input audio_dir/ --output predictions.json
```

### Reports & Validation
```bash
# Generate report
python cognitive_assessment_ml.py --report --model my_model_bundle --format pdf

# Data validation only
python cognitive_assessment_ml.py --dx dx-mmse.csv --validate-data

# Debug mode
python cognitive_assessment_ml.py --dx dx-mmse.csv --train --debug
```

## 📊 Output Structure

### Training Results
```json
{
  "classification": {
    "best_params": {...},
    "cv_scores": {
      "f1_mean": 0.75,
      "recall_mean": 0.80,
      "roc_auc_mean": 0.85
    },
    "test_scores": {
      "accuracy": 0.82,
      "f1": 0.78,
      "precision": 0.76,
      "recall": 0.81,
      "roc_auc": 0.87
    }
  },
  "regression": {
    "best_params": {...},
    "test_scores": {
      "mse": 12.5,
      "mae": 2.8,
      "r2": 0.65
    }
  },
  "data_info": {
    "n_samples": 237,
    "n_features": 25,
    "class_balance": {"control": 150, "dementia": 87}
  }
}
```

### Prediction Result
```json
{
  "audio_file": "patient_audio.wav",
  "transcript_file": null,
  "predictions": {
    "diagnosis": "dementia",
    "confidence": 0.87,
    "mmse_predicted": 18.5
  },
  "probabilities": {
    "control": 0.13,
    "dementia": 0.87
  }
}
```

## 📁 Generated Artifacts

```
artifacts/
├── confusion_matrix.png      # Confusion matrix plot
├── roc_curve.png             # ROC curve plot  
├── mmse_scatter.png          # True vs Predicted MMSE
└── training_results_comprehensive.json

reports/
├── data_validation_report.json
├── training_report.json
└── training_report.pdf

model_bundle/
├── model_bundle.pkl          # Complete model bundle
└── metadata.json             # Model metadata
```

## 🧪 Testing

### Smoke Test
```bash
cd backend
python tests/smoke_test.py
```

Smoke test sẽ kiểm tra:
- ✅ Class definition
- ✅ Training pipeline với synthetic data
- ✅ Artifacts generation
- ✅ Save/load model
- ✅ Prediction functionality
- ✅ Report generation
- ✅ Standalone functions compatibility

### Expected Output
```
🚀 Starting Enhanced Cognitive Assessment ML Smoke Tests
======================================================================
🧪 Test 1: Class Definition
✅ Class definition test passed

🧪 Test 2: Training Pipeline
✅ Training pipeline test passed
   - Classification F1: 0.750
   - Regression R²: 0.420

🧪 Test 3: Artifacts Generation
   ✅ Found: confusion_matrix.png
   ✅ Found: roc_curve.png
   ✅ Found: mmse_scatter.png
   ✅ Found: training_results_comprehensive.json
✅ Artifacts generation test passed

...

🏁 SMOKE TEST RESULTS SUMMARY
======================================================================
✅ ALL TESTS PASSED (7/7)
🎉 Enhanced Cognitive Assessment ML is ready for use!
```

## 🔧 Troubleshooting

### Common Issues

1. **"EnhancedMultimodalCognitiveModel is not defined"**
   ```python
   # Make sure to import correctly
   from cognitive_assessment_ml import EnhancedMultimodalCognitiveModel
   ```

2. **"No participant_id column found"**
   ```python
   # Your CSV must have participant_id column for safe merging
   # Or alternative: id, ID, participant columns
   ```

3. **"Model overfits, predictions unreliable"**
   - Check for R² < 0 in regression
   - Consider more training data
   - Review feature quality

4. **Low recall in classification**
   - Model missing positive cases
   - SMOTE should help with imbalance
   - Consider adjusting scale_pos_weight

### Performance Guidelines

- **Classification**: F1 > 0.6, Recall > 0.5 for clinical use
- **Regression**: R² > 0.3 for moderate accuracy, R² > 0.7 for excellent
- **Data**: Minimum 50 samples, prefer 200+ for robust training
- **Features**: 10-50 features optimal, avoid too many irrelevant features

## 🤝 Backward Compatibility

Enhanced model maintains full backward compatibility:

```python
# Old style still works
from cognitive_assessment_ml import train_from_adress_data, predict_from_audio

results = train_from_adress_data('dx.csv', 'prog.csv')
prediction = predict_from_audio('audio.wav')
```

## 📚 API Reference

### EnhancedMultimodalCognitiveModel

#### Constructor
```python
EnhancedMultimodalCognitiveModel(language='vi', random_state=42, debug=False)
```

#### Methods
- `train_from_adress_data(dx_csv, progression_csv=None, eval_csv=None, validate_data=False)`
- `train_from_audio_directory(audio_dir, transcript_dir=None)`
- `predict_from_audio(audio_file, transcript_file=None)`
- `predict_batch(input_list)`
- `generate_report(filename, format='json')`
- `save_model(path='model_bundle')`
- `load_model(path='model_bundle')`

### Standalone Functions
- `train_from_adress_data(csv_file1, csv_file2, ...)`
- `predict_from_audio(audio_file, transcript_file, ...)`
- `batch_predict_from_directory(audio_dir, ...)`

## 📈 Performance Metrics

### Classification Metrics
- **Accuracy**: Overall correctness
- **F1 Score**: Harmonic mean of precision/recall
- **Recall**: Sensitivity (true positive rate)
- **Precision**: Positive predictive value
- **ROC-AUC**: Area under ROC curve

### Regression Metrics
- **MSE**: Mean Squared Error
- **MAE**: Mean Absolute Error  
- **R²**: Coefficient of determination

## 🌍 Language Support

- **Vietnamese (vi)**: Full support với underthesea
- **English (en)**: Basic support
- **Chinese (zh)**: Basic support với jieba

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Run smoke tests
4. Submit pull request

---

**Enhanced Multimodal Cognitive Assessment ML** - Comprehensive, robust, và production-ready! 🎉
