"""
Training script for Vietnamese Name Database corrections
"""

import os
import sys
import json

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

def test_name_database_loading():
    """Test loading and using Vietnamese Name Database"""
    try:
        from vietnamese_transcriber import VietnameseTranscriber

        print("🧪 Testing Vietnamese Name Database Training...")

        # Create transcriber instance
        transcriber = VietnameseTranscriber()

        # Test loading name database
        print("\n📚 Loading Vietnamese Name Database...")
        name_corrections = transcriber._load_vietnamese_name_database()

        print(f"✅ Loaded {len(name_corrections)} name corrections")

        # Show some examples
        print("\n📝 Sample name corrections:")
        sample_corrections = list(name_corrections.items())[:10]
        for unsigned, signed in sample_corrections:
            print(f"  '{unsigned}' → '{signed}'")

        # Test name corrections on sample text
        test_cases = [
            "Toi ten la Nguyen Van Minh",
            "Co gai ten la Tran Thi Mai",
            "Ban be cua toi la Le Hoang Quan",
            "Gia dinh toi co ba nguoi: bo me va toi",
            "Toi gap ban Nguyen Thi Lan hom qua",
        ]

        print("\n🔄 Testing name corrections on sample text:")
        for test_text in test_cases:
            print(f"\nInput: '{test_text}'")
            result = transcriber._apply_name_database_corrections(test_text)
            print(f"Output: '{result}'")

            # Highlight changes
            if result != test_text:
                print("✅ Names were corrected!")
            else:
                print("ℹ️ No name corrections applied")

        # Test comprehensive corrections with names
        print("\n🎯 Testing comprehensive corrections with names:")
        complex_cases = [
            "hom nay toi gap nguoi ban cu la tran thi thu",
            "ban than toi ten la nguyen van nam",
            "co giao ten la le thi hoa day lop mot",
            "bac si pham van duc kham benh cho toi",
        ]

        for test_text in complex_cases:
            print(f"\n📝 Input: '{test_text}'")
            result = transcriber._apply_comprehensive_vietnamese_corrections(test_text)
            print(f"📝 Output: '{result}'")

        print("\n✅ Vietnamese Name Database training test completed!")

        # Save corrections for inspection
        output_file = "vietnamese_name_corrections.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Convert to JSON serializable format
            json_corrections = {k: v for k, v in list(name_corrections.items())[:100]}  # First 100 for demo
            json.dump(json_corrections, f, ensure_ascii=False, indent=2)

        print(f"💾 Sample corrections saved to {output_file}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def analyze_name_database():
    """Analyze the Vietnamese Name Database structure"""
    try:
        print("📊 Analyzing Vietnamese Name Database...")

        name_db_path = os.path.join(os.path.dirname(__file__), '..', 'vietnamese-namedb')

        # Analyze boy names
        boy_file = os.path.join(name_db_path, 'boy.txt')
        if os.path.exists(boy_file):
            with open(boy_file, 'r', encoding='utf-8') as f:
                boy_names = [line.strip() for line in f if line.strip()]
            print(f"👦 Boy names: {len(boy_names)} names")
            print(f"   Sample: {boy_names[:5]}")

        # Analyze girl names
        girl_file = os.path.join(name_db_path, 'girl.txt')
        if os.path.exists(girl_file):
            with open(girl_file, 'r', encoding='utf-8') as f:
                girl_names = [line.strip() for line in f if line.strip()]
            print(f"👧 Girl names: {len(girl_names)} names")
            print(f"   Sample: {girl_names[:5]}")

        # Analyze JSON data
        json_file = os.path.join(name_db_path, 'uit_member.json')
        if os.path.exists(json_file):
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                members = json.load(f)
            print(f"👥 Full names: {len(members)} entries")
            print(f"   Sample: {members[0]}")

        print("\n✅ Database analysis completed!")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Vietnamese Name Database Training System")
    print("=" * 50)

    analyze_name_database()
    test_name_database_loading()
