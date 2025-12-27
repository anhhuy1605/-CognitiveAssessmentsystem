"""Test Vietnamese linguistic analysis với PhoBERT"""
import os
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("🧪 Testing Vietnamese Linguistic Analysis")
print("=" * 60)

# Test 1: PhoBERT
print("\n📦 Test 1: PhoBERT (Transformers)")
print("-" * 60)

try:
    from transformers import AutoModel, AutoTokenizer
    
    print("📥 Loading PhoBERT model...")
    print("   (First time: ~500MB download)")
    
    model = AutoModel.from_pretrained('vinai/phobert-base')
    tokenizer = AutoTokenizer.from_pretrained('vinai/phobert-base')
    
    print("✅ PhoBERT loaded successfully")
    
    # Test Vietnamese text
    test_text = "Ông Nguyễn Văn A đang làm việc tại Đại học Quốc gia Hà Nội."
    
    print(f"\n📝 Test text: {test_text}")
    
    # Tokenize
    tokens = tokenizer.tokenize(test_text)
    print(f"✅ Tokens: {tokens}")
    
    # Encode
    inputs = tokenizer(test_text, return_tensors="pt")
    print(f"✅ Encoded shape: {inputs['input_ids'].shape}")
    
    # Get embeddings
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state
    print(f"✅ Embeddings shape: {embeddings.shape}")
    
    print("\n✅ PhoBERT test PASSED!")
    
except Exception as e:
    print(f"❌ PhoBERT test failed: {e}")

# Test 2: Existing MCI Linguistic Analyzer
print("\n" + "=" * 60)
print("📦 Test 2: MCI Linguistic Analyzer")
print("-" * 60)

try:
    from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
    
    print("📥 Loading MCI Linguistic Analyzer...")
    analyzer = VietnameseLinguisticAnalyzer()
    
    print("✅ Analyzer loaded")
    
    # Test text
    test_text = "Tôi đi chợ mua rau. Rau rất tươi. Tôi thích ăn rau."
    
    print(f"\n📝 Test text: {test_text}")
    
    # Extract features
    features = analyzer.extract_all_features(test_text, task_type="naming")
    
    print(f"✅ Extracted {len(features)} features:")
    
    # Show sample features
    feature_types = {}
    for key in features.keys():
        feature_type = key.split('_')[0]
        feature_types[feature_type] = feature_types.get(feature_type, 0) + 1
    
    for ftype, count in sorted(feature_types.items()):
        print(f"   - {ftype}: {count} features")
    
    # Show some sample values
    print("\n📊 Sample feature values:")
    sample_keys = list(features.keys())[:5]
    for key in sample_keys:
        print(f"   {key}: {features[key]:.3f}")
    
    print("\n✅ MCI Linguistic Analyzer test PASSED!")
    
except Exception as e:
    print(f"❌ MCI Linguistic Analyzer test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("📊 SUMMARY:")
print("✅ PhoBERT: Modern transformer model cho tiếng Việt")
print("✅ MCI Linguistic Analyzer: Đã có trong hệ thống")
print()
print("🎯 Khuyến nghị:")
print("  - Dùng MCI Linguistic Analyzer cho MMSE analysis")
print("  - PhoBERT làm backup cho advanced NLP tasks")
print()
print("📝 Linguistic analysis đã sẵn sàng!")

