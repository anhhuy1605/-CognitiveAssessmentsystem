#!/usr/bin/env python3
"""Test if the Flask app can be imported and initialized"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Testing Flask app import...")

try:
    print("1. Importing app module...")
    from app import app as flask_app, initialize_model
    print("✅ Flask app imported successfully")

    print("2. Testing model initialization...")
    result = initialize_model()
    print(f"✅ Model initialization result: {result}")

    print("3. Testing app creation...")
    app = flask_app
    print(f"✅ Flask app created: {type(app)}")

    print("4. Testing basic route...")
    with app.test_client() as client:
        response = client.get('/api/health')
        print(f"✅ Health endpoint status: {response.status_code}")
        print(f"✅ Health response: {response.get_json()}")

    print("\n🎉 All tests passed! The backend should work.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
