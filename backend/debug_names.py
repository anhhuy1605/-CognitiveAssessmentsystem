"""
Debug script for Vietnamese name corrections
"""

import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

def debug_name_corrections():
    """Debug name corrections step by step"""
    try:
        from vietnamese_transcriber import VietnameseTranscriber

        print("🐛 Debugging Vietnamese Name Corrections...")

        # Create transcriber instance
        transcriber = VietnameseTranscriber()

        # Load name database
        print("\n📚 Loading name database...")
        name_corrections = transcriber._load_vietnamese_name_database()

        print(f"✅ Loaded {len(name_corrections)} corrections")

        # Show some sample corrections
        print("\n📝 First 10 corrections:")
        for i, (unsigned, signed) in enumerate(list(name_corrections.items())[:10]):
            print(f"  {i+1}. '{unsigned}' → '{signed}'")

        # Test specific cases
        test_cases = ["nguyen van minh", "tran thi mai", "le hoang quan"]

        print("\n🧪 Testing specific cases:")
        for test_case in test_cases:
            print(f"\nTesting: '{test_case}'")
            print(f"  Words: {test_case.split()}")

            # Check each word
            for word in test_case.split():
                if word in name_corrections:
                    print(f"  ✅ '{word}' found → '{name_corrections[word]}'")
                else:
                    print(f"  ❌ '{word}' not found in corrections")

            # Test full phrase replacement
            for unsigned, signed in name_corrections.items():
                if unsigned in test_case:
                    print(f"  🔄 Full match: '{unsigned}' → '{signed}'")

        # Test the actual correction function
        print("\n🎯 Testing correction function:")
        for test_case in test_cases:
            result = transcriber._apply_name_database_corrections(test_case)
            print(f"  '{test_case}' → '{result}'")

        print("\n✅ Debug completed!")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_name_corrections()
