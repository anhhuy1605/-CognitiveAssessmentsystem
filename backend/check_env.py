#!/usr/bin/env python3
"""
Environment Variables Check Script
Kiểm tra xem tất cả environment variables cần thiết đã được set chưa
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Kiểm tra file environment"""
    env_files = ['.env', 'config.env']

    for env_file in env_files:
        if os.path.exists(env_file):
            print("Found environment file: {}".format(env_file))
            return env_file

    print("ERROR: No environment file found (.env or config.env)")
    return None

def check_required_vars():
    """Kiểm tra các biến môi trường bắt buộc"""
    required_vars = [
        'OPENAI_API_KEY',
        'GEMINI_API_KEY',
        'DATABASE_URL',
        'SECRET_KEY'
    ]

    optional_vars = [
        'BLOB_READ_WRITE_TOKEN',
        'VI_ASR_MODEL',
        'PORT',
        'HOST',
        'DEBUG'
    ]

    print("\nChecking required environment variables:")

    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive info
            if 'KEY' in var or 'SECRET' in var or 'TOKEN' in var:
                display_value = "***{}".format(value[-4:] if len(value) > 4 else "***")
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print("OK {}: {}".format(var, display_value))
        else:
            print("MISSING {}: NOT SET".format(var))
            all_good = False

    print("\nChecking optional environment variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:50] + "..." if len(value) > 50 else value
            print("OK {}: {}".format(var, display_value))
        else:
            print("OPTIONAL {}: NOT SET (using defaults)".format(var))

    return all_good

def main():
    """Main function"""
    print("Backend Environment Check")
    print("=" * 50)

    # Check environment file
    env_file = check_env_file()

    # Load environment if file exists
    if env_file:
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("Loaded environment from: {}".format(env_file))
        except ImportError:
            print("python-dotenv not installed, checking current environment")

    # Check variables
    vars_ok = check_required_vars()

    print("\n" + "=" * 50)
    if vars_ok:
        print("SUCCESS: All required environment variables are set!")
        print("Backend should start successfully")
        sys.exit(0)
    else:
        print("ERROR: Missing required environment variables!")
        print("Please set the missing variables in your .env file")
        print("Check DEPLOYMENT.md for detailed instructions")
        sys.exit(1)

if __name__ == "__main__":
    main()
