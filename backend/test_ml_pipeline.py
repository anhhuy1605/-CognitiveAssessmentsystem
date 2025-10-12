# Test the actual ML prediction pipeline
import sys
import tempfile
import wave
import numpy as np
from app import extract_audio_features, predict_cognitive_score

print('Testing ML prediction pipeline...')

# Create two different test audio files
def create_test_audio(filename, frequency, duration=2.0):
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2) 
        wav.setframerate(16000)
        samples = int(16000 * duration)
        audio_data = (np.sin(2 * np.pi * frequency * np.linspace(0, duration, samples)) * 32767).astype(np.int16)
        wav.writeframes(audio_data.tobytes())

# Create test files
test_file1 = tempfile.mktemp(suffix='.wav')
test_file2 = tempfile.mktemp(suffix='.wav')

create_test_audio(test_file1, 220, 2.0)  # Lower pitch, 2 seconds
create_test_audio(test_file2, 440, 1.0)  # Higher pitch, 1 second

print('\n🎵 Testing Audio File 1 (220Hz, 2s):')
features1 = extract_audio_features(test_file1)
prediction1 = predict_cognitive_score(features1)

print('Key features:')
for key in ['duration', 'pitch_mean', 'speech_rate', 'number_utterances', 'silence_mean']:
    if key in features1:
        print(f'  {key}: {features1[key]}')

print(f'ML Prediction: MMSE={prediction1.get("predicted_score", "N/A"):.2f}, Model={prediction1.get("model_used", "N/A")}')

print('\n🎵 Testing Audio File 2 (440Hz, 1s):')
features2 = extract_audio_features(test_file2)
prediction2 = predict_cognitive_score(features2)

print('Key features:')
for key in ['duration', 'pitch_mean', 'speech_rate', 'number_utterances', 'silence_mean']:
    if key in features2:
        print(f'  {key}: {features2[key]}')

print(f'ML Prediction: MMSE={prediction2.get("predicted_score", "N/A"):.2f}, Model={prediction2.get("model_used", "N/A")}')

# Compare results
print('\n📊 Comparison:')
print(f'File1 vs File2 - Same features? {features1 == features2}')
print(f'File1 vs File2 - Same MMSE? {prediction1.get("predicted_score") == prediction2.get("predicted_score")}')

# Show which features are different
print('\n🔍 Feature differences:')
for key in ['duration', 'pitch_mean', 'speech_rate', 'number_utterances', 'silence_mean']:
    if key in features1 and key in features2:
        if features1[key] != features2[key]:
            print(f'  {key}: {features1[key]} vs {features2[key]} - DIFFERENT ✅')
        else:
            print(f'  {key}: {features1[key]} vs {features2[key]} - SAME ❌')

# Clean up
import os
try:
    os.unlink(test_file1)
    os.unlink(test_file2)
except:
    pass
