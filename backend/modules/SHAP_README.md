# SHAP Explainability Module

## Overview

The SHAP Explainability Module provides comprehensive, human-readable explanations for cognitive assessment predictions. It uses SHAP (SHapley Additive exPlanations) values to explain how each feature contributes to the risk assessment, making AI decisions transparent and actionable for elderly users and their caregivers.

## Features

- **SHAP Value Computation**: Calculates feature importance using TreeSHAP, KernelSHAP, or LinearSHAP
- **Human-Readable Explanations**: Converts technical SHAP values into plain Vietnamese/English
- **Interactive Visualizations**: Waterfall plots, radar charts, feature importance bars, and animated explanations
- **Comprehensive Reports**: PDF and HTML reports with all visualizations and recommendations
- **Edge Case Handling**: Detects and handles special cases (short audio, poor quality, etc.)
- **Validation**: Ensures SHAP values are correct and consistent

## Installation

```bash
# Install required dependencies
pip install shap scikit-learn matplotlib seaborn plotly reportlab
```

## Quick Start

### 1. Compute SHAP Values

```python
from modules.shap_explainer import compute_shap_for_assessment

# After getting assessment results
shap_result = compute_shap_for_assessment(
    audio_features=audio_features,
    linguistic_features=linguistic_features,
    mmse_score=mmse_score
)

print(shap_result['feature_contributions'])
print(shap_result['grouped_contributions'])
```

### 2. Generate Explanations

```python
from modules.explanation_generator import generate_explanation_for_assessment

explanation = generate_explanation_for_assessment(
    audio_features=audio_features,
    linguistic_features=linguistic_features,
    mmse_score=mmse_score,
    risk_level='mild',
    language='vi'  # or 'en'
)

print(explanation['summary'])
print(explanation['positive_factors'])
print(explanation['negative_factors'])
print(explanation['recommendations'])
```

### 3. Create Visualizations

```python
from modules.shap_visualizations import create_all_visualizations

visualizations = create_all_visualizations(
    shap_result=shap_result,
    grouped_contributions=shap_result['grouped_contributions'],
    mmse_score=mmse_score,
    language='vi'
)

# Visualizations are base64-encoded PNG images
# waterfall, importance_bar, radar_chart, risk_gauge
```

### 4. Generate Complete Report

```python
from modules.report_generator import generate_complete_report

report_package = generate_complete_report(
    audio_features=audio_features,
    linguistic_features=linguistic_features,
    mmse_score=mmse_score,
    risk_level='mild',
    language='vi',
    output_dir='./reports'  # Optional: save files
)

# Access reports
pdf_bytes = report_package['pdf']
html_report = report_package['html']
summary_card = report_package['summary_card']
```

### 5. Validate Explanations

```python
from modules.shap_validation import validate_shap_explanations, handle_edge_cases

# Validate SHAP values
validation = validate_shap_explanations(
    shap_result=shap_result,
    X_sample=combined_features,
    tolerance=0.01
)

if validation['is_valid']:
    print("✅ SHAP values are valid")
else:
    print("❌ Errors:", validation['errors'])

# Handle edge cases
edge_cases = handle_edge_cases(
    shap_result=shap_result,
    X_sample=combined_features,
    audio_metadata={'duration': 15, 'quality': 'good'}
)

if edge_cases['edge_cases']:
    print("⚠️ Edge cases detected:", edge_cases['warnings'])
```

## API Integration

### Backend Endpoint

Add to `backend/app.py`:

```python
@app.route('/api/shap-explanations/<session_id>', methods=['GET'])
def get_shap_explanations(session_id):
    """Get SHAP explanations for a session"""
    try:
        # Get assessment results from database
        results = get_assessment_results(session_id)
        
        # Generate SHAP explanations
        from modules.report_generator import generate_complete_report
        
        report = generate_complete_report(
            audio_features=results['audio_features'],
            linguistic_features=results['linguistic_features'],
            mmse_score=results['mmse_score'],
            risk_level=results.get('risk_level', 'low'),
            language='vi'
        )
        
        return jsonify({
            'success': True,
            'data': report['explanations'],
            'visualizations': report['visualizations']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Frontend Usage

```tsx
import SHAPDashboard from '@/components/shap/SHAPDashboard';

// In your results page
<SHAPDashboard sessionId={sessionId} />
```

## Module Structure

```
backend/modules/
├── shap_explainer.py          # Core SHAP computation
├── explanation_generator.py   # Human-readable explanations
├── shap_visualizations.py    # Static & animated plots
├── report_generator.py        # PDF/HTML report generation
└── shap_validation.py         # Validation & edge case handling
```

## Feature Groups

Features are grouped into categories for easier interpretation:

- **Acoustic Prosodic**: Pitch, F0 variability
- **Acoustic Spectral**: Voice quality (MFCC, spectral features)
- **Acoustic Voice Quality**: Jitter, shimmer, HNR
- **Acoustic Temporal**: Speaking rate, pause duration
- **Acoustic Tone**: Vietnamese tone production
- **Linguistic Lexical**: Vocabulary diversity (TTR, MATTR)
- **Linguistic Syntactic**: Grammar complexity (MLU, sentence length)
- **Linguistic Semantic**: Coherence, idea density
- **Linguistic Vietnamese**: Vietnamese-specific features
- **Linguistic Pragmatic**: Filler words, repetition, pronouns

## Explanation Format

Each explanation includes:

1. **Summary**: 2-3 sentence overview
2. **Risk Level**: low, mild, moderate, severe
3. **Positive Factors**: Features supporting good cognition
4. **Negative Factors**: Features indicating risk
5. **Feature Interactions**: Combined effects
6. **Recommendations**: Actionable steps
7. **Confidence**: Assessment confidence level
8. **Next Steps**: What to do next

## Visualizations

### Waterfall Plot
Shows how each feature pushes the prediction up or down from the base value.

### Feature Importance Bar
Top N contributing features ranked by absolute importance.

### Radar Chart
Performance across cognitive domains (voice quality, fluency, vocabulary, etc.).

### Risk Gauge
Animated gauge showing MMSE score and risk zones.

### Contribution Animation
Step-by-step animation showing how features accumulate to the final prediction.

## Reports

### PDF Report
Professional PDF with:
- Cover page with summary
- Executive summary
- Detailed analysis with visualizations
- Recommendations
- Technical appendix

### HTML Report
Interactive HTML with:
- Embedded visualizations
- Collapsible sections
- Print-friendly CSS
- Shareable via link

### Summary Card
Mobile-friendly summary card for easy sharing via messaging apps.

## Validation

The module includes comprehensive validation:

- **SHAP Sum Check**: Ensures SHAP values sum to (prediction - base_value)
- **Range Validation**: Checks for reasonable SHAP values
- **NaN/Inf Detection**: Flags invalid values
- **Model Consistency**: Validates predictions match model output
- **Edge Case Detection**: Handles short audio, poor quality, etc.

## Testing

```python
from modules.shap_validation import test_shap_pipeline

test_results = test_shap_pipeline(
    audio_features=audio_features,
    linguistic_features=linguistic_features,
    mmse_score=mmse_score,
    risk_level='mild'
)

print(f"Tests passed: {test_results['tests_passed']}")
print(f"Tests failed: {test_results['tests_failed']}")
print(f"Performance: {test_results['performance']}")
```

## Performance

Target performance:
- SHAP computation: < 2 seconds
- Explanation generation: < 1 second
- Visualization creation: < 2 seconds
- Total pipeline: < 5 seconds

## Language Support

Currently supports:
- **Vietnamese (vi)**: Full support with diacritics
- **English (en)**: Full support

To add more languages, extend `FEATURE_INTERPRETATIONS` in `explanation_generator.py`.

## Clinical Relevance

The module is designed based on:

- Lundberg & Lee (2017): SHAP framework
- Martinc et al. (2021): Speech-based dementia detection
- Balagopalan et al. (2020): Linguistic feature importance
- Mirheidari et al. (2019): Clinical interpretation

All feature interpretations are clinically validated and use plain language suitable for elderly users and caregivers.

## Troubleshooting

### SHAP library not available
```bash
pip install shap
```

### ReportLab not available (PDF generation)
```bash
pip install reportlab
```

### Plotly not available (interactive charts)
```bash
pip install plotly
```

### Very slow SHAP computation
- Use TreeExplainer for tree-based models (fastest)
- Reduce background data size for KernelSHAP
- Cache explainers for repeated use

### Missing visualizations
- Check that matplotlib backend is set to 'Agg'
- Ensure base64 encoding is working
- Verify image data is not corrupted

## References

1. Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. NIPS.

2. Martinc, M., et al. (2021). Tackling the ADReSS Challenge: A multimodal approach to the automated recognition of Alzheimer's dementia.

3. Balagopalan, A., et al. (2020). To BERT or Not to BERT: Comparing speech and language-based approaches for Alzheimer's Disease Detection.

4. Mirheidari, B., et al. (2019). Toward the automation of diagnostic conversation analysis in patients with memory complaints.

## License

Part of the Cognitive Assessment System.

