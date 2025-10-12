# Cognitive Assessment ML Setup

## Quick Start

### Option 1: Automatic Installation (Recommended)
```bash
cd backend
python setup_dependencies.py
```

### Option 2: Manual Installation
```bash
cd backend
pip install -r requirements.txt
```

### Option 3: Install Core Dependencies Only
```bash
cd backend
pip install numpy pandas scikit-learn xgboost torch transformers joblib
```

## Required Dependencies

### Core Dependencies
- **numpy**: Numerical computing
- **pandas**: Data manipulation
- **scikit-learn**: Machine learning algorithms
- **xgboost**: Gradient boosting
- **torch**: Deep learning framework
- **transformers**: NLP models and tokenizers
- **joblib**: Model serialization

### Audio Processing Dependencies
- **openai-whisper**: Speech recognition
- **librosa**: Audio feature extraction
- **soundfile**: Audio file I/O

### Optional Dependencies
- **matplotlib**: Plotting and visualization
- **underthesea**: Vietnamese NLP processing
- **jieba**: Chinese text processing

## Testing Installation

After installation, test the setup:
```bash
cd backend
python launch.py
```

Or run the main script directly:
```bash
cd backend
python cognitive_assessment_ml.py
```

You should see the class-based model demonstration run successfully.

## Troubleshooting

### Common Issues

1. **Permission Errors**: Try `pip install --user` or use a virtual environment
2. **Torch Installation**: Visit https://pytorch.org for platform-specific instructions
3. **XGBoost Issues**: Install from conda if pip fails: `conda install -c conda-forge xgboost`

### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv cognitive_env

# Activate environment
# Windows:
cognitive_env\Scripts\activate
# Linux/Mac:
source cognitive_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

Once dependencies are installed, you can:

1. **Train the model**:
```python
from cognitive_assessment_ml import EnhancedMultimodalCognitiveModel

model = EnhancedMultimodalCognitiveModel(language='vi')
results = model.train_from_adress_data('dx-mmse.csv', 'progression.csv', 'eval-data.csv')
```

2. **Make predictions**:
```python
result = model.predict_from_audio('patient_audio.wav')
print(result)
```

3. **Save and load models**:
```python
model.save_model('./saved_model')
model.load_model('./saved_model')
```
