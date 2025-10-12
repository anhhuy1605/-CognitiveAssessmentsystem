#!/usr/bin/env python3
"""
Test the auto-transcribe endpoint to verify it returns audio features and GPT evaluation
"""

import requests
import os

def test_autotranscribe():
    """Test the auto-transcribe endpoint"""

    # Test with available audio files
    test_files = ['test_audio.wav', 'fresh_test_1756873289.wav', 'normal_speech_1756874142.wav']

    for audio_file in test_files:
        if not os.path.exists(audio_file):
            print(f"⚠️ {audio_file} not found, skipping")
            continue

        print(f"\n🎵 Testing with {audio_file}...")

        try:
            with open(audio_file, 'rb') as f:
                files = {'audio': (audio_file, f, 'audio/wav')}
                data = {
                    'language': 'vi',
                    'question': 'Hãy mô tả những gì bạn thấy trong hình ảnh này'
                }

                response = requests.post(
                    'http://localhost:5001/auto-transcribe',
                    files=files,
                    data=data,
                    timeout=30
                )

                print(f"📡 Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Success: {result.get('success')}")

                    # Check for audio features
                    audio_features = result.get('audio_features', {})
                    print(f"🎚️ Audio features present: {len(audio_features)} keys")
                    if audio_features:
                        print(f"   silence_mean: {audio_features.get('silence_mean', 'MISSING')}")
                        print(f"   speech_rate: {audio_features.get('speech_rate', 'MISSING')}")
                        print(f"   pitch_mean: {audio_features.get('pitch_mean', 'MISSING')}")

                    # Check for GPT evaluation
                    gpt_eval = result.get('gpt_evaluation', {})
                    print(f"🤖 GPT evaluation present: {len(gpt_eval)} keys")
                    if gpt_eval:
                        print(f"   analysis: {'YES' if gpt_eval.get('analysis') else 'NO'}")
                        print(f"   feedback: {'YES' if gpt_eval.get('feedback') else 'NO'}")
                        print(f"   overall_score: {gpt_eval.get('overall_score', 'MISSING')}")

                    # Check for ML prediction
                    ml_pred = result.get('ml_prediction', {})
                    print(f"🧠 ML prediction present: {len(ml_pred)} keys")
                    if ml_pred:
                        print(f"   predicted_score: {ml_pred.get('predicted_score', 'MISSING')}")

                    # Check transcript
                    transcription = result.get('transcription', {})
                    if isinstance(transcription, dict):
                        transcript_text = transcription.get('transcript', '')
                    else:
                        transcript_text = transcription
                    print(f"📝 Transcript: '{transcript_text[:50]}{'...' if len(transcript_text) > 50 else ''}'")

                else:
                    print(f"❌ Error: {response.text}")

        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_autotranscribe()
