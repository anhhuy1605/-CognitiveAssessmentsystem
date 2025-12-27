"""
Cài đặt models cho Vietnamese linguistic analysis
Sử dụng py_vncorenlp (tự động download models)
"""
import os
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("🔧 Cài đặt Vietnamese Linguistic Analysis Models")
print("=" * 60)

# Step 1: Install py_vncorenlp
print("\n📦 Step 1: Cài đặt py_vncorenlp package...")
os.system(f"{sys.executable} -m pip install py_vncorenlp -q")
print("✅ Đã cài đặt py_vncorenlp")

# Step 2: Download models automatically
print("\n📥 Step 2: Download VnCoreNLP models...")
print("   (Có thể mất 5-10 phút, ~300MB)")
print()

try:
    import py_vncorenlp
    
    # Set download directory
    vncorenlp_dir = os.path.join(os.getcwd(), "VnCoreNLP_py")
    
    print(f"📁 Download directory: {vncorenlp_dir}")
    
    # Download models
    py_vncorenlp.download_model(save_dir=vncorenlp_dir)
    print(f"\n✅ Models downloaded to: {vncorenlp_dir}")
    
    # Test the model
    print("\n🧪 Testing model...")
    model = py_vncorenlp.VnCoreNLP(save_dir=vncorenlp_dir)
    
    # Test Vietnamese text
    test_text = "Ông Nguyễn Văn A đang làm việc tại Đại học Quốc gia Hà Nội."
    
    print(f"📝 Test text: {test_text}")
    result = model.annotate_text(test_text)
    
    print(f"✅ Tokenization result:")
    for sent in result['sentences']:
        tokens = [token['wordForm'] for token in sent]
        print(f"   {' '.join(tokens)}")
    
    print("\n" + "=" * 60)
    print("✅ Linguistic analysis models cài đặt thành công!")
    print(f"📁 Location: {vncorenlp_dir}")
    print()
    print("📝 Để sử dụng trong code:")
    print("   import py_vncorenlp")
    print(f"   model = py_vncorenlp.VnCoreNLP(save_dir='{vncorenlp_dir}')")
    print("   result = model.annotate_text('text...')")
    
except Exception as e:
    print(f"\n❌ Lỗi khi download models: {e}")
    print()
    print("🔄 Thử cài đặt PhoBERT thay thế...")
    
    # Fallback: Install PhoBERT
    print("\n📦 Cài đặt PhoBERT (alternative)...")
    os.system(f"{sys.executable} -m pip install transformers torch -q")
    print("✅ Đã cài đặt PhoBERT dependencies")
    
    print()
    print("📝 Để sử dụng PhoBERT:")
    print("   from transformers import AutoModel, AutoTokenizer")
    print("   model = AutoModel.from_pretrained('vinai/phobert-base')")
    print("   tokenizer = AutoTokenizer.from_pretrained('vinai/phobert-base')")

