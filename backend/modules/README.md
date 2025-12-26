# MCI Screening Modules for Vietnamese Cognitive Assessment

Hệ thống sàng lọc suy giảm nhận thức nhẹ (MCI) cho người Việt Nam sử dụng phân tích đa phương thức (multimodal analysis).

## 📁 Project Structure

```
backend/
├── modules/
│   ├── __init__.py                    # Module exports
│   ├── acoustic_analyzer.py           # Acoustic feature extraction
│   ├── linguistic_analyzer.py         # Vietnamese linguistic analysis
│   ├── multimodal_fusion.py           # Feature fusion
│   ├── mci_predictor.py              # MCI prediction & MMSE estimation
│   ├── integration_service.py         # Unified service
│   └── README.md                      # This file
├── data/
│   ├── training_data/
│   │   ├── audio/                     # Training audio files
│   │   └── labels.csv                 # Labels: participant_id, mmse_score, mci_label, transcript
│   └── test_samples/                  # Test audio files
├── models/
│   └── mci_fusion_model.pkl          # Trained model (after training)
├── VnCoreNLP/                         # Vietnamese NLP tools (setup required)
├── main_pipeline.py                   # End-to-end pipeline
├── train_model.py                     # Training script
├── requirements_acoustic.txt          # Acoustic dependencies
├── requirements_linguistic.txt        # Linguistic dependencies
├── requirements_modules.txt           # All module dependencies
└── setup_vncorenlp.sh                # VnCoreNLP setup script
```

## 🚀 Installation

### Step 1: Install Dependencies

```bash
cd backend

# Option A: Install all at once
pip install -r requirements_modules.txt

# Option B: Install separately
pip install -r requirements_acoustic.txt
pip install -r requirements_linguistic.txt
```

### Step 2: Setup VnCoreNLP (Optional but recommended)

```bash
# Linux/macOS
chmod +x setup_vncorenlp.sh
./setup_vncorenlp.sh

# Windows - Manual download:
# 1. Download VnCoreNLP-1.1.1.jar from GitHub
# 2. Download models from VnCoreNLP repository
```

### Step 3: Verify Installation

```python
from modules import MCIScreeningService

service = MCIScreeningService()
print(service.get_status())
# Should show: {'is_ready': True, 'acoustic_analyzer': True, ...}
```

## 📖 Usage

### Quick Start

```python
from modules import analyze_for_mci

# Analyze audio + transcript
result = analyze_for_mci(
    audio_path='audio.wav',
    transcript='Xin chào tôi tên là Nguyễn Văn A...'
)

print(f"MCI Probability: {result['mci_prediction']['mci_probability']:.1%}")
print(f"MMSE Estimate: {result['mmse_estimate']:.1f}/30")
print(f"Severity: {result['severity']}")
```

### Using Individual Modules

```python
# 1. Acoustic Analysis Only
from modules import AcousticAnalyzer

analyzer = AcousticAnalyzer()
acoustic_features = analyzer.extract_all_features('audio.wav', transcript='optional')

# Key features:
print(f"F0 Mean: {acoustic_features.get('f0_f0_mean', 0):.2f} Hz")
print(f"Tone Flattening: {acoustic_features.get('tone_flattening_score', 0):.3f}")

# 2. Linguistic Analysis Only
from modules import VietnameseLinguisticAnalyzer

analyzer = VietnameseLinguisticAnalyzer()
ling_features = analyzer.extract_all_features(
    'Xin chào tôi tên là...',
    task_type='spontaneous_speech'  # or 'verbal_fluency', 'picture_description', 'qa'
)

# Key features:
print(f"TTR: {ling_features.get('lex_ttr', 0):.3f}")
print(f"Idea Density: {ling_features.get('sem_idea_density', 0):.2f}")

# 3. Prediction Only
from modules import MCIPredictor

predictor = MCIPredictor()
prediction = predictor.predict(combined_features)

print(f"MCI Class: {prediction.mci_class}")
print(f"MMSE: {prediction.mmse_estimate:.1f}")
print(f"Risk Factors: {prediction.risk_factors}")
```

### Full Pipeline with ASR

```python
from main_pipeline import MCIScreeningPipeline

# With your existing ASR module
from your_asr_module import YourASR

pipeline = MCIScreeningPipeline(
    asr_module=YourASR(),
    model_path='models/mci_fusion_model.pkl'  # Optional: trained model
)

# Process single file
result = pipeline.process_audio(
    audio_path='audio.wav',
    task_type='picture_description',
    reference_transcript='ground truth transcript'  # Optional, for WER
)

# Access results
print(f"MCI Risk: {result.mci_probability:.1%}")
print(f"MMSE: {result.mmse_score:.1f}/30")
print(f"Confidence: {result.confidence:.1%}")

# Or process with existing transcript
result = pipeline.process_with_transcript(
    audio_path='audio.wav',
    transcript='Pre-existing transcript...'
)

# Batch processing
results = pipeline.batch_process(
    audio_folder='data/audio/',
    output_file='results.json'
)
```

## 🎯 Training Custom Model

### Step 1: Prepare Dataset

Create `data/training_data/labels.csv`:
```csv
participant_id,mmse_score,mci_label,transcript,task_type
P001,28,0,"Xin chào tôi tên là...",spontaneous_speech
P002,22,1,"Tôi... ừm... tên tôi là...",spontaneous_speech
P003,15,1,"Tên... à... quên rồi...",qa
```

Place audio files in `data/training_data/audio/`:
```
P001.wav
P002.wav
P003.wav
```

### Step 2: Run Training

```bash
python train_model.py \
    --data-folder data/training_data \
    --output-dir models \
    --test-size 0.2 \
    --n-folds 5
```

### Step 3: Use Trained Model

```python
from modules import MCIPredictor

predictor = MCIPredictor(model_path='models/mci_fusion_model.pkl')
prediction = predictor.predict(features)
```

## 🔌 API Endpoints

The modules are integrated into `app.py` with these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mci/status` | GET | Check module availability |
| `/api/mci/analyze` | POST | Full MCI analysis |
| `/api/mci/acoustic` | POST | Acoustic features only |
| `/api/mci/linguistic` | POST | Linguistic features only |
| `/api/mci/predict` | POST | Prediction from features |
| `/api/mci/batch-analyze` | POST | Batch analysis |

### Example API Calls

```bash
# Check status
curl http://localhost:5001/api/mci/status

# Full analysis
curl -X POST http://localhost:5001/api/mci/analyze \
  -F "audio=@audio.wav" \
  -F "transcript=Xin chào..." \
  -F "task_type=spontaneous_speech"

# Acoustic only
curl -X POST http://localhost:5001/api/mci/acoustic \
  -F "audio=@audio.wav"

# Linguistic only
curl -X POST http://localhost:5001/api/mci/linguistic \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Xin chào...", "task_type": "qa"}'
```

## 📊 Features Extracted

### Acoustic Features (~100 features)

| Category | Features | MCI Indicator |
|----------|----------|---------------|
| **eGeMAPS** | F0, jitter, shimmer, HNR, MFCCs | Standard voice features |
| **F0 Contour** | Mean, std, range, CV, skewness | Prosody changes |
| **Voice Quality** | Jitter, shimmer, HNR | Motor control decline |
| **Pause Stats** | Count, duration, rate | Word-finding difficulty |
| **Speaking Rate** | Words/min, syllables/sec | Processing speed |
| **🇻🇳 Tone Flattening** | Flattening score, F0 variability | **Vietnamese-specific biomarker** |

### Linguistic Features (~50 features)

| Category | Features | MCI Indicator |
|----------|----------|---------------|
| **Lexical Diversity** | TTR, MATTR, Brunet's Index | Vocabulary richness ↓ |
| **POS Distribution** | Pronoun, noun, verb ratios | Word-finding difficulty ↑ pronouns |
| **Syntactic** | MLU, incomplete sentences | Sentence complexity ↓ |
| **Semantic** | Idea density, coherence | **Strongest predictor** |
| **🇻🇳 Vietnamese** | Classifiers, reduplications, tense markers | Language-specific |

## 🇻🇳 Vietnamese-Specific Innovations

1. **Tone Flattening Analysis**
   - F0 variability reduction in MCI patients
   - Novel biomarker for Vietnamese speakers
   
2. **Vietnamese NLP**
   - VnCoreNLP / underthesea integration
   - PhoBERT for semantic coherence
   - Classifier and reduplication analysis

3. **Vietnamese Interpretations**
   - All risk factors in Vietnamese
   - Clinical recommendations in Vietnamese
   - Severity classifications in Vietnamese

## 📈 Key MCI Indicators

From literature (Fraser et al. 2016, Pakhomov et al. 2011):

| Feature | Normal | MCI | Description |
|---------|--------|-----|-------------|
| Idea Density | > 5 | < 3.5 | **Strongest predictor** |
| Pronoun Ratio | < 10% | > 15% | Word-finding difficulty |
| TTR | > 0.5 | < 0.35 | Vocabulary richness |
| MLU | > 8 words | < 5 words | Sentence complexity |
| Pause Rate | < 0.2/s | > 0.3/s | Processing difficulty |
| 🇻🇳 Tone Flat | < 0.25 | > 0.5 | Vietnamese-specific |

## 🔧 Troubleshooting

### Module Import Errors
```bash
# Install missing dependencies
pip install opensmile praat-parselmouth underthesea transformers torch
```

### VnCoreNLP Java Error
```bash
# Install Java 8+
sudo apt install openjdk-11-jdk  # Ubuntu
brew install openjdk@11          # macOS
```

### PhoBERT Memory Issues
```python
# Use without PhoBERT
analyzer = VietnameseLinguisticAnalyzer(use_phobert=False)
```

### Audio Format Issues
```bash
# Convert to 16kHz mono WAV
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## 📚 References

- Eyben et al. (2016) - eGeMAPS feature set
- Fraser et al. (2016) - Linguistic features for dementia detection
- Pakhomov et al. (2011) - Computerized analysis in Alzheimer's
- Tran et al. (2006) - Vietnamese tone modeling

## 📄 License

Part of Cognitive Assessment System for Vietnamese MCI Screening.

