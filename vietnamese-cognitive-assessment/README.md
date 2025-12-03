# Vietnamese Cognitive Assessment System

MMSE-Equivalent score estimation from Vietnamese speech. Implements feature extraction, quality control, modeling, and clinical validation per docs in `docs/`.

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt  # dev tools
```

## Structure

See `docs/` for specifications and `src/` for implementation. Run tests and coverage:

```bash
pytest -v
pytest --cov=src tests/ --cov-report=term-missing
```

## Quick usage

```python
from src.feature_pipeline import CognitiveAssessmentFeatureExtractor

extractor = CognitiveAssessmentFeatureExtractor()
df = extractor.extract_all_features('path/to/audio.wav', 'bản ghi âm...', 'PT001')
print(df.head())
```


