# Check the actual model and pipeline status
from app import cognitive_model, feature_names
print('🔍 Current ML Model Status:')
print(f'Model loaded: {cognitive_model is not None}')
print(f'Feature names: {feature_names}')
if cognitive_model:
    print(f'Model type: {type(cognitive_model)}')
    if hasattr(cognitive_model, 'best_model_name'):
        print(f'Best model: {cognitive_model.best_model_name}')

# Test with some actual audio files
import os
audio_files = [f for f in os.listdir('.') if f.endswith(('.wav', '.mp3', '.webm'))]
print(f'\nFound audio files: {audio_files[:3]}')

if audio_files:
    from app import extract_audio_features, predict_cognitive_score
    test_file = audio_files[0]
    print(f'\n🎵 Testing with real file: {test_file}')
    try:
        features = extract_audio_features(test_file)
        prediction = predict_cognitive_score(features)
        print(f'Features: duration={features.get("duration")}, pitch_mean={features.get("pitch_mean"):.2f}')
        print(f'MMSE: {prediction.get("predicted_score"):.2f}')
        
        # Check if these are default features
        from app import get_default_audio_features
        default_features = get_default_audio_features()
        is_default = all(features.get(k) == default_features.get(k) for k in ['duration', 'pitch_mean', 'speech_rate'])
        print(f'Using default features: {is_default}')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

# Check if we have the 14.2 problem
print(f'\n🧮 MMSE conversion check:')
print(f'If MMSE raw = 14.2, converted = {14.2 / 3.0:.2f}')
print(f'If MMSE raw = 4.74, converted to 30-scale = {4.74 * 3.0:.2f}')
