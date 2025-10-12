# Test the retrained model with MMSE scale
print('🚀 Testing retrained model with MMSE scale (0-30)...')

# Import and force model reinitialization
import importlib
import app
importlib.reload(app)

from app import extract_audio_features, predict_cognitive_score, cognitive_model, feature_names

print(f'Model type: {type(cognitive_model)}')
print(f'Features: {feature_names}')

# Test with our existing audio files
import os
audio_files = [f for f in os.listdir('.') if f.endswith('.wav')][:2]

for i, audio_file in enumerate(audio_files, 1):
    print(f'\n🎵 Testing file {i}: {audio_file}')
    features = extract_audio_features(audio_file)
    prediction = predict_cognitive_score(features)
    
    print(f'  Duration: {features.get("duration"):.2f}s')
    print(f'  Pitch: {features.get("pitch_mean"):.1f} Hz')
    print(f'  Speech rate: {features.get("speech_rate"):.2f} words/sec')
    print(f'  MMSE Score: {prediction.get("predicted_score"):.1f}/30')
    print(f'  Model: {prediction.get("model_used")}')

# Test with synthetic data to verify scale
print('\n🧪 Testing with different synthetic features:')
test_cases = [
    {'speech_rate': 1.0, 'number_utterances': 5, 'silence_mean': 1.5, 'pitch_mean': 150},  # Low performance
    {'speech_rate': 3.0, 'number_utterances': 20, 'silence_mean': 0.2, 'pitch_mean': 250}, # High performance
    {'speech_rate': 2.0, 'number_utterances': 10, 'silence_mean': 0.8, 'pitch_mean': 200}, # Medium performance
]

for i, test_features in enumerate(test_cases, 1):
    prediction = predict_cognitive_score(test_features)
    score = prediction.get("predicted_score", 0)
    print(f'  Test {i}: MMSE = {score:.1f}/30 (speech_rate={test_features["speech_rate"]}, silence={test_features["silence_mean"]})')
