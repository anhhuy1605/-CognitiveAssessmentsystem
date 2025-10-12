#!/usr/bin/env python3
"""
Comprehensive Backend API Test Tool
Tests all API endpoints and provides detailed debugging information
"""

import requests
import json
import time
import sys
from datetime import datetime

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def test_endpoint(name, url, method='GET', data=None, timeout=10):
    """Test a single API endpoint with detailed logging"""
    print(f"\n📡 Testing {name}: {method} {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=timeout)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            json_data = response.json()
            print(f"   JSON Response: {json.dumps(json_data, indent=2, ensure_ascii=False)[:500]}...")
            return True, json_data
        except:
            print(f"   Text Response: {response.text[:200]}...")
            return response.status_code == 200, response.text
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - backend not running")
        return False, "Connection failed"
    except requests.exceptions.Timeout:
        print(f"   ⏰ Request timed out")
        return False, "Timeout"
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, str(e)

def main():
    print_section("COGNITIVE ASSESSMENT BACKEND API DIAGNOSTIC")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    base_url = "http://localhost:5001"
    
    # Test basic connectivity
    print_section("1. BACKEND CONNECTIVITY")
    health_ok, health_data = test_endpoint("Health Check", f"{base_url}/api/health")
    
    if not health_ok:
        print("\n❌ Backend is not running or not accessible!")
        print("Please start the backend server first:")
        print("   cd backend")
        print("   python app.py")
        return
    
    print("\n✅ Backend is running!")
    
    # Test all critical endpoints
    print_section("2. CRITICAL ENDPOINTS")
    
    endpoints = [
        ("MMSE Questions", f"{base_url}/api/mmse/questions", "GET"),
        ("User Profile", f"{base_url}/api/user/profile", "GET"),
        ("Backend Status", f"{base_url}/api/status", "GET"),
        ("Configuration", f"{base_url}/api/config", "GET"),
    ]
    
    results = {}
    
    for name, url, method in endpoints:
        success, data = test_endpoint(name, url, method)
        results[name] = {"success": success, "data": data}
    
    # Test POST endpoints
    print_section("3. POST ENDPOINTS")
    
    # Test assess-queue endpoint
    test_data = {
        "question_id": 1,
        "transcript": "Test transcript for debugging",
        "user_id": "test_user",
        "session_id": "test_session_123",
        "timestamp": datetime.now().isoformat()
    }
    
    success, data = test_endpoint(
        "Assessment Queue", 
        f"{base_url}/api/assess-queue", 
        "POST", 
        test_data
    )
    results["Assessment Queue"] = {"success": success, "data": data}
    
    # Test direct assessment endpoint
    success, data = test_endpoint(
        "Direct Assessment", 
        f"{base_url}/api/assess-domain", 
        "POST", 
        test_data
    )
    results["Direct Assessment"] = {"success": success, "data": data}
    
    # Test MMSE assessment
    print_section("4. MMSE ASSESSMENT")
    
    mmse_data = {
        "session_id": "test_mmse_session",
        "patient_info": {"name": "Test User", "age": 65}
    }
    
    success, data = test_endpoint(
        "MMSE Assessment", 
        f"{base_url}/api/mmse/assess", 
        "POST", 
        mmse_data
    )
    results["MMSE Assessment"] = {"success": success, "data": data}
    
    # Summary
    print_section("5. SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    print(f"📊 Test Results: {passed_tests}/{total_tests} endpoints working")
    print("\nDetailed Results:")
    
    for name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {name}: {status}")
        if not result["success"]:
            print(f"      Error: {result['data']}")
    
    # Recommendations
    print_section("6. RECOMMENDATIONS")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The backend is working correctly.")
    else:
        print("⚠️ Some endpoints failed. Common fixes:")
        print("1. Check if all required Python packages are installed")
        print("2. Verify environment variables (.env file)")
        print("3. Check if questions.json file exists")
        print("4. Ensure model files are properly loaded")
        print("5. Check backend logs for detailed error messages")
    
    print("\n📝 Next steps for frontend integration:")
    print("1. Update frontend API_BASE_URL to http://localhost:5001")
    print("2. Ensure CORS is properly configured")
    print("3. Test fetchWithFallback with these endpoints")
    print("4. Implement proper error handling for failed endpoints")

if __name__ == "__main__":
    main()
