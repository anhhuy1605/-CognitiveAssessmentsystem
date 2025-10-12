import requests
import json

# Test backend API để xem có hoạt động không
try:
    response = requests.get('http://localhost:5001/api/assessment-results/session_1758969661499_b796f4nd7')
    data = response.json()
    print('Backend API working')
    print('Found {} results for session'.format(len(data.get("results", []))))

    # Check if results have the required fields
    if data.get('results'):
        result = data['results'][0]
        has_gpt = 'gpt_evaluation' in result
        has_audio = 'audio_analysis' in result
        has_clinical = 'clinical_feedback' in result
        print('GPT evaluation: {}'.format(has_gpt))
        print('Audio analysis: {}'.format(has_audio))
        print('Clinical feedback: {}'.format(has_clinical))
        print('Sample result keys:', list(result.keys())[:10])

except Exception as e:
    print('Backend API error: {}'.format(e))
