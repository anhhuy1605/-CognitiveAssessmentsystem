#!/usr/bin/env python3
"""
Test Gemini API key loading and initialization
"""

import os
import sys
sys.path.append('.')
from dotenv import load_dotenv

def test_gemini_key():
    print("🔍 Testing Gemini API Key Loading")
    print("=" * 40)

    # Load .env file explicitly
    load_dotenv('config.env')
    print('✅ Loaded config.env')

    # Check environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    print(f'GEMINI_API_KEY found: {bool(api_key)}')

    if api_key:
        print(f'Key length: {len(api_key)}')
        print(f'Key starts with: {api_key[:20]}...')
    else:
        print('❌ GEMINI_API_KEY not found in environment')
        return False

    # Test direct Gemini initialization
    print('\n🔍 Testing Direct Gemini Initialization')
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print('✅ Direct Gemini initialization successful')
    except Exception as e:
        print(f'❌ Direct Gemini initialization failed: {e}')
        return False

    # Test AudioPipelineService
    print('\n🔍 Testing AudioPipelineService')
    try:
        from audio_pipeline_service import AudioPipelineService
        service = AudioPipelineService()

        if hasattr(service, 'gemini_model') and service.gemini_model is not None:
            print('✅ AudioPipelineService Gemini initialized successfully')
            return True
        else:
            print('❌ AudioPipelineService Gemini not initialized')
            return False

    except Exception as e:
        print(f'❌ AudioPipelineService test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_gemini_key()
    print(f'\n🎯 Final Result: {"✅ SUCCESS" if success else "❌ FAILED"}')
    sys.exit(0 if success else 1)
