# Test with real audio files to see if it's using real features
from app import extract_audio_features, get_default_audio_features
import os

# Find real audio files
audio_files = [f for f in os.listdir('.') if f.endswith('.wav')][:2]
print(f'🎵 Testing with real audio files: {audio_files}')

default_features = get_default_audio_features()
print(f'\n📊 Default features:')
for key in ['duration', 'pitch_mean', 'speech_rate', 'number_utterances', 'silence_mean']:
    print(f'  {key}: {default_features[key]}')

for i, audio_file in enumerate(audio_files, 1):
    print(f'\n🎵 File {i}: {audio_file}')
    features = extract_audio_features(audio_file)
    
    # Check if ANY feature matches default exactly
    matches_default = []
    for key in ['duration', 'pitch_mean', 'speech_rate', 'number_utterances', 'silence_mean']:
        if features.get(key) == default_features.get(key):
            matches_default.append(key)
    
    matches_str = matches_default if matches_default else "None - All real features!"
    print(f'  Features matching default: {matches_str}')
    print(f'  Duration: {features.get("duration"):.2f}s (default: {default_features["duration"]})')
    print(f'  Pitch: {features.get("pitch_mean"):.1f} Hz (default: {default_features["pitch_mean"]})')
    print(f'  Speech rate: {features.get("speech_rate"):.2f} (default: {default_features["speech_rate"]})')
    
    # Check if this looks like real extraction
    is_using_real_features = len(matches_default) == 0
    status = '✅ REAL FEATURES' if is_using_real_features else '❌ USING DEFAULTS'
    print(f'  Status: {status}')

# Additional debug: Check if librosa is actually in sys.modules during extraction
print('\n🔍 Checking librosa status during app import:')
import sys
print(f'librosa in sys.modules: {"librosa" in sys.modules}')

# Test the specific check in extract_audio_features
print(f'Check used in extract_audio_features: {"librosa" not in sys.modules}')
if 'librosa' not in sys.modules:
    print('❌ This would trigger default features!')
else:
    print('✅ This would use real librosa extraction')
