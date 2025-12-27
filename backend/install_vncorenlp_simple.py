"""Install VnCoreNLP bằng Python"""
import os
import urllib.request
import zipfile
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("📦 Installing VnCoreNLP...")
print("=" * 60)

# Create VnCoreNLP directory
vncorenlp_dir = os.path.join(os.getcwd(), "VnCoreNLP")
if not os.path.exists(vncorenlp_dir):
    os.makedirs(vncorenlp_dir)
    print(f"✅ Created directory: {vncorenlp_dir}")
else:
    print(f"📁 Directory exists: {vncorenlp_dir}")

# Download JAR
jar_url = "https://github.com/vncorenlp/VnCoreNLP/raw/master/VnCoreNLP-1.2.jar"
jar_path = os.path.join(vncorenlp_dir, "VnCoreNLP-1.2.jar")

if not os.path.exists(jar_path):
    print(f"\n📥 Downloading JAR file... (~50MB)")
    try:
        urllib.request.urlretrieve(jar_url, jar_path)
        print(f"✅ Downloaded: {jar_path}")
    except Exception as e:
        print(f"❌ Failed to download JAR: {e}")
        sys.exit(1)
else:
    print(f"✅ JAR already exists: {jar_path}")

# Download models
models_url = "https://github.com/vncorenlp/VnCoreNLP/raw/master/models.zip"
models_zip = os.path.join(vncorenlp_dir, "models.zip")
models_dir = os.path.join(vncorenlp_dir, "models")

if not os.path.exists(models_dir):
    print(f"\n📥 Downloading models... (~100MB, có thể mất vài phút)")
    try:
        urllib.request.urlretrieve(models_url, models_zip)
        print(f"✅ Downloaded: {models_zip}")
        
        print(f"\n📦 Extracting models...")
        with zipfile.ZipFile(models_zip, 'r') as zip_ref:
            zip_ref.extractall(vncorenlp_dir)
        print(f"✅ Extracted to: {vncorenlp_dir}")
        
        # Clean up zip
        os.remove(models_zip)
        print(f"🧹 Cleaned up zip file")
        
    except Exception as e:
        print(f"❌ Failed to download/extract models: {e}")
        sys.exit(1)
else:
    print(f"✅ Models already exist: {models_dir}")

# Install Python package
print(f"\n🐍 Installing vncorenlp Python package...")
os.system(f"{sys.executable} -m pip install vncorenlp -q")
print(f"✅ Installed vncorenlp package")

print("\n" + "=" * 60)
print("✅ VnCoreNLP installation complete!")
print(f"📁 Location: {vncorenlp_dir}")
print("\n📝 To use in Python:")
print("from vncorenlp import VnCoreNLP")
print(f"annotator = VnCoreNLP('{jar_path}', annotators='wseg,pos', max_heap_size='-Xmx2g')")

