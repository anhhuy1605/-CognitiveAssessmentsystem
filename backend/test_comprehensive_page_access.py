#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Comprehensive Page Access
================================
Test xem session đã lưu có thể được truy cập từ Comprehensive page không
"""

import os
import sys
import requests
import json
from typing import Dict, Any, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import service to check session
try:
    from services.mmse_chatbot_service import MMSEChatbotService
except ImportError as e:
    print(f"Failed to import service: {e}")
    sys.exit(1)

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')

def check_session_exists(session_id: str) -> bool:
    """Check if session exists in service"""
    try:
        service = MMSEChatbotService()
        state = service.get_session(session_id)
        if state:
            print(f"[OK] Session {session_id} exists in service")
            print(f"   Completed: {state.completed_at is not None}")
            print(f"   Total Score: {state.total_score}")
            print(f"   Final Acoustic Features: {len(getattr(state, 'final_acoustic_features', {}))}")
            print(f"   Final Linguistic Features: {len(getattr(state, 'final_linguistic_features', {}))}")
            print(f"   Q&A Pairs: {len(getattr(state, 'qa_pairs', []))}")
            return True
        else:
            print(f"[ERROR] Session {session_id} NOT found in service")
            return False
    except Exception as e:
        print(f"[ERROR] Error checking session: {e}")
        return False

def test_api_endpoint(session_id: str) -> Optional[Dict[str, Any]]:
    """Test API endpoint for comprehensive results"""
    try:
        url = f"{API_BASE_URL}/api/mmse/chatbot/results/{session_id}"
        print(f"\nTesting API endpoint: {url}")
        
        response = requests.get(url, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("[OK] API returned success")
                print(f"   Session ID: {data.get('session_id')}")
                print(f"   Completed At: {data.get('completed_at')}")
                
                comprehensive_data = data.get('data', {})
                if comprehensive_data:
                    print(f"   Comprehensive Results Sections: {list(comprehensive_data.keys())}")
                    
                    # Check key sections
                    assessment = comprehensive_data.get('assessment_result', {})
                    if assessment:
                        print(f"   MMSE Score: {assessment.get('mmse_score')}/35")
                        print(f"   Risk Level: {assessment.get('risk_level')}")
                    
                    multimodal = comprehensive_data.get('multimodal_analysis', {})
                    if multimodal:
                        acoustic_count = len(multimodal.get('acoustic_features', {}))
                        linguistic_count = len(multimodal.get('linguistic_features', {}))
                        print(f"   Multimodal - Acoustic: {acoustic_count}, Linguistic: {linguistic_count}")
                    
                    qa_history = comprehensive_data.get('qa_history', [])
                    print(f"   Q&A History: {len(qa_history)} pairs")
                    
                    question_features = comprehensive_data.get('question_features', {})
                    print(f"   Per-question Features: {len(question_features)} questions")
                
                return data
            else:
                print(f"[ERROR] API returned error: {data.get('error')}")
                return None
        else:
            print(f"[ERROR] API request failed: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to API at {API_BASE_URL}")
        print("   Make sure backend is running: python app.py")
        return None
    except Exception as e:
        print(f"[ERROR] Error testing API: {e}")
        return None

def list_all_sessions() -> list:
    """List all completed sessions"""
    try:
        service = MMSEChatbotService()
        # Get all sessions from service (if available)
        # Note: This depends on how sessions are stored
        print("\nListing all sessions...")
        print("   (Note: Service may not have list_all_sessions method)")
        return []
    except Exception as e:
        print(f"[ERROR] Error listing sessions: {e}")
        return []

def main():
    """Main test function"""
    print("=" * 80)
    print("COMPREHENSIVE PAGE ACCESS TEST")
    print("=" * 80)
    
    # Get session ID from command line or use test session
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        # Try to find latest test session
        import glob
        result_files = glob.glob("test_results_test_db_*.json")
        if result_files:
            latest = max(result_files, key=os.path.getctime)
            session_id = latest.replace("test_results_", "").replace(".json", "")
            print(f"Found latest test session: {session_id}")
        else:
            print("[ERROR] No test session found. Please provide session_id as argument")
            print("   Usage: python test_comprehensive_page_access.py <session_id>")
            sys.exit(1)
    
    print(f"\nTesting session: {session_id}")
    print("=" * 80)
    
    # 1. Check if session exists in service
    print("\n[1] Checking session in service...")
    exists = check_session_exists(session_id)
    
    if not exists:
        print("\n[WARNING] Session not found in service. Cannot test API.")
        sys.exit(1)
    
    # 2. Test API endpoint
    print("\n[2] Testing API endpoint...")
    api_result = test_api_endpoint(session_id)
    
    # 3. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if api_result and api_result.get('success'):
        print("[OK] Session is accessible via API")
        print(f"[OK] Comprehensive results are available")
        print(f"\nTo view on Comprehensive page:")
        print(f"   URL: http://localhost:3000/results/comprehensive?sessionId={session_id}")
        print(f"\n   Or use the API directly:")
        print(f"   GET {API_BASE_URL}/api/mmse/chatbot/results/{session_id}")
    else:
        print("[ERROR] Session is NOT accessible via API")
        print("   Check:")
        print("   1. Backend is running (python app.py)")
        print("   2. API endpoint is correct")
        print("   3. Session exists in service")

if __name__ == "__main__":
    main()

