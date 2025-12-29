"""
Verify Imported Results
=======================
Check if test results were imported correctly to database
"""
import os
import sys
import requests
import json
from typing import Dict, Any

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
SESSION_ID = "test_session_1766891790"

def check_backend_results(session_id: str):
    """Check results in backend"""
    print("=" * 80)
    print("🔍 CHECKING BACKEND RESULTS")
    print("=" * 80)
    
    # Check MMSE chatbot results
    try:
        response = requests.get(f"{API_BASE_URL}/api/mmse/chatbot/results/{session_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ MMSE Chatbot Results found:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"❌ MMSE Chatbot Results not found: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error checking MMSE chatbot results: {e}")
    
    # Check MMSE results DB
    try:
        response = requests.get(f"{API_BASE_URL}/api/mmse/results/{session_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\n✅ MMSE Results DB found:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"\n❌ MMSE Results DB not found: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error checking MMSE results DB: {e}")

def check_frontend_database(session_id: str):
    """Check results in frontend database"""
    print("\n" + "=" * 80)
    print("🔍 CHECKING FRONTEND DATABASE")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{FRONTEND_URL}/api/get-cognitive-assessment-results?sessionId={session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Frontend API Response: success={data.get('success')}")
            print(f"   Count: {data.get('count', 0)}")
            
            if data.get('success') and data.get('data') and len(data.get('data', [])) > 0:
                result = data['data'][0]
                print("\n✅ Results found in frontend database:")
                print(f"   Session ID: {result.get('sessionId')}")
                print(f"   Final MMSE Score: {result.get('finalMmseScore')}")
                print(f"   Assessment Type: {result.get('assessmentType')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Question Results: {len(result.get('questionResults', [])) if isinstance(result.get('questionResults'), list) else 'N/A'}")
                
                # Check questionResults format
                qr = result.get('questionResults')
                if qr:
                    if isinstance(qr, str):
                        try:
                            qr_parsed = json.loads(qr)
                            print(f"   Question Results (parsed): {len(qr_parsed)} items")
                        except:
                            print(f"   Question Results: JSON string (could not parse)")
                    elif isinstance(qr, list):
                        print(f"   Question Results: Array with {len(qr)} items")
            else:
                print("❌ No results found in frontend database")
                print(f"   Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ Frontend API error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error checking frontend database: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        SESSION_ID = sys.argv[1]
    
    print(f"🔍 Verifying results for session: {SESSION_ID}\n")
    
    check_backend_results(SESSION_ID)
    check_frontend_database(SESSION_ID)
    
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

