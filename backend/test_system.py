#!/usr/bin/env python3
"""
Standalone test script for Cognitive Assessment System
Run this script to test the complete system flow
"""

import requests
import time
import json

def test_cognitive_assessment_system():
    """Test the complete cognitive assessment system"""
    base_url = "http://localhost:5001"

    print("🧪 Testing Cognitive Assessment System")
    print("=" * 50)

    # Test 1: Health Check
    print("\n1. Testing backend health...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

    # Test 2: Questions Endpoint
    print("\n2. Testing questions endpoint...")
    try:
        response = requests.get(f"{base_url}/api/mmse/questions")
        if response.status_code == 200:
            data = response.json()
            questions_count = len(data.get('data', {}).get('questions', []))
            print(f"✅ Questions endpoint passed - Found {questions_count} questions")
        else:
            print(f"❌ Questions endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Questions endpoint error: {e}")
        return False

    # Test 3: Queue System
    print("\n3. Testing queue system...")
    try:
        test_data = {
            "question_id": 1,
            "transcript": "This is a test transcript for cognitive assessment validation.",
            "user_id": "test_user_system",
            "session_id": "test_session_validation"
        }

        response = requests.post(f"{base_url}/api/test-queue-flow", json=test_data)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ Queue test passed - Task ID: {task_id}")

            # Wait for processing
            print("⏳ Waiting for processing...")
            time.sleep(3)

            # Check status
            status_response = requests.get(f"{base_url}/api/assessment-status/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                task_status = status_data.get("status", {}).get("status", "unknown")
                print(f"✅ Status check passed - Status: {task_status}")
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
        else:
            print(f"❌ Queue test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Queue test error: {e}")
        return False

    # Test 4: Results Retrieval
    print("\n4. Testing results retrieval...")
    try:
        response = requests.get(f"{base_url}/api/assessment-results/test_user_system")
        if response.status_code == 200:
            result = response.json()
            count = result.get("count", 0)
            print(f"✅ Results retrieval passed - Found {count} results")
            if count > 0:
                print(f"Sample result: {json.dumps(result.get('results', [{}])[0], indent=2)[:200]}...")
        else:
            print(f"❌ Results retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Results retrieval error: {e}")
        return False

    # Test 5: Queue Status
    print("\n5. Testing queue status...")
    try:
        response = requests.get(f"{base_url}/api/debug/queue-status")
        if response.status_code == 200:
            status = response.json()
            queue_size = status.get("queue_size", 0)
            total_tasks = status.get("total_tasks", 0)
            active_threads = status.get("active_threads", 0)
            print(f"✅ Queue status passed")
            print(f"   Queue size: {queue_size}")
            print(f"   Total tasks: {total_tasks}")
            print(f"   Active threads: {active_threads}")
        else:
            print(f"❌ Queue status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Queue status error: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All tests passed! Cognitive Assessment System is working correctly.")
    print("\nNext steps:")
    print("1. Start the frontend: cd frontend && npm run dev")
    print("2. Open browser to http://localhost:3000")
    print("3. Test the complete user flow")
    print("4. Use debug panel in development mode to troubleshoot")
    return True

if __name__ == "__main__":
    success = test_cognitive_assessment_system()
    exit(0 if success else 1)
